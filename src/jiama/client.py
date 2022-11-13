import asyncio
import json
import uuid

from loguru import logger

from jiama.constant import (
    DEFAULT_CONFIG, EXCHANGE_NAME, REQUEST_ROUTING_KEY, RESPONSE_BINDING_KEY,
    RESPONSE_QUEUE_NAME, RESPONSE_ROUTING_KEY
)
from jiama.rmq import Agent
from jiama.util import merge_dict, singleton


class RpcProxy:
    async def create(self, config: dict):
        rpc_config = merge_dict(DEFAULT_CONFIG, config, ignore=['log'])['rpc']
        self.client_id = rpc_config.get('client_id', None) or str(uuid.uuid4())
        self.timeout = rpc_config['timeout']
        self.agent = Agent().init(rpc_config)
        self.loop = asyncio.get_running_loop()
        self.futures = {}
        self.services = {}
        self.queue, self.consumer = await self.agent.subscribe(
            RESPONSE_QUEUE_NAME.format(client_id=self.client_id),
            RESPONSE_BINDING_KEY.format(client_id=self.client_id),
            self.on_response,
        )
        return self

    async def on_response(self, message):
        await message.ack()

        future = self.futures.pop(message.correlation_id, None)
        if future is None:
            return

        future.set_result(json.loads(message.body))

    def ensure_future(self, correlation_id):
        future = self.loop.create_future()
        self.futures[correlation_id] = future
        return future

    async def close(self):
        logger.info(f'Closing client: {self.client_id}')
        if self.consumer:
            await self.queue.cancel(self.consumer)
            del self.consumer
        await self.queue.unbind(EXCHANGE_NAME)
        for future in self.futures.values():
            if future.done():
                continue
            future.set_exception(asyncio.CancelledError)
        await self.queue.delete()
        await self.agent.close()

    def __getattr__(self, service_name):
        if service_name not in self.services:
            self.services[service_name] = Service(self, service_name)
        return self.services[service_name]

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()


class Service:
    def __init__(self, proxy, name):
        self.proxy = proxy
        self.name = name

    def __getattr__(self, method):
        return Method(self.proxy, self.name, method)


class Method:
    def __init__(self, proxy, service, name):
        self.proxy = proxy
        self.service = service
        self.name = name

    async def __call__(self, *args, **kwargs):
        payload = {'args': args, 'kwargs': kwargs}
        payload = json.dumps(payload).encode()
        routing_key = REQUEST_ROUTING_KEY.format(
            service_name=self.service, method_name=self.name
        )
        reply_to = RESPONSE_ROUTING_KEY.format(client_id=self.proxy.client_id)
        correlation_id = str(uuid.uuid4())

        logger.info('Requesting {} with {}', routing_key, payload)
        future = self.proxy.ensure_future(correlation_id)
        await self.proxy.agent.publish(payload, routing_key, reply_to, correlation_id)

        return await asyncio.wait_for(future, timeout=self.proxy.timeout)
