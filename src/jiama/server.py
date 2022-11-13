import asyncio
import json
import signal

from loguru import logger

from jiama.constant import EXCHANGE_NAME, REQUEST_BINDING_KEY, REQUEST_QUEUE_NAME
from jiama.rmq import Agent
from jiama.util import singleton


@singleton
class Rpc:
    def __init__(self, rpc_config):
        self.agent = Agent().init(rpc_config)
        self.listeners = []

    async def start(self, services):
        logger.info('Starting {}', list(services.keys()))

        loop = asyncio.get_running_loop()
        for s in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                s, lambda s=s: asyncio.create_task(self.shutdown(loop, s))
            )

        self.services = services
        try:
            await asyncio.wait(
                [asyncio.create_task(self.listen(s)) for s in self.services.keys()]
            )
        except asyncio.CancelledError:
            logger.info('Tasks were cancelled ')
        finally:
            logger.info("Successfully shutdown services")

    async def listen(self, service):
        queue, consumer = await self.agent.subscribe(
            REQUEST_QUEUE_NAME.format(service_name=service),
            REQUEST_BINDING_KEY.format(service_name=service),
            self.on_request,
        )
        self.listeners.append((queue, consumer))
        await asyncio.Future()

    async def on_request(self, message):
        await message.ack()

        service, method = message.routing_key.split('.')
        logger.info('Processing {}.{}', service, method)

        body = json.loads(message.body.decode())
        args = body['args']
        kwargs = body['kwargs']

        service_instance = self.services[service]()
        method_instance = getattr(service_instance, method)
        if asyncio.iscoroutinefunction(method_instance):
            result = await method_instance(*args, **kwargs)
        else:
            result = method_instance(*args, **kwargs)

        payload = json.dumps(result).encode()
        routing_key = message.reply_to

        logger.info('Sending result to {}', routing_key)
        await self.agent.publish(
            payload, routing_key=routing_key, correlation_id=message.correlation_id
        )

    async def shutdown(self, loop, signal):
        logger.info(f'Received exit signal {signal.name}')
        for queue, consumer in self.listeners:
            if consumer:
                await queue.cancel(consumer)
                del consumer
            await queue.unbind(EXCHANGE_NAME)
            await queue.delete()
        await self.agent.close()

        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for t in tasks:
            t.cancel()
        logger.info(f'Cancelling {len(tasks)} outstanding tasks')
        await asyncio.gather(*tasks, return_exceptions=True)

        loop.stop()

    @staticmethod
    def decorator(method_func):
        if getattr(method_func, 'jiama_rpc_entrypoint', False):
            return
        setattr(method_func, 'jiama_rpc_entrypoint', True)
        return method_func


rpc = Rpc.decorator
