from aio_pika import Message, connect_robust
from aio_pika.pool import Pool
from yujian.api import Client

from jiama.constant import CONTENT_ENCODING, CONTENT_TYPE, EXCHANGE_NAME, EXCHANGE_TYPE
from jiama.util import seperate_uri, singleton


class Agent:
    def init(self, config):
        self.uri = config['amqp_uri']
        self.max_connection = config['max_connection']
        self.max_channel = config['max_channel']
        self.prefetch_count = config['prefetch_count']
        self.delivery_mode = config['delivery_mode']
        self.durable = config['durable']
        self.timeout = config['timeout']
        self.expiration = config['expiration']
        self.conn_pool = Pool(self._connect, max_size=self.max_connection)
        self.channel_pool = Pool(self._channel, max_size=self.max_channel)
        return self

    async def _connect(self):
        return await connect_robust(self.uri, timeout=self.timeout)

    async def _channel(self):
        async with self.conn_pool.acquire() as conn:
            return await conn.channel()

    async def exchange(self):
        async with self.channel_pool.acquire() as channel:
            return await channel.declare_exchange(
                EXCHANGE_NAME,
                EXCHANGE_TYPE,
                durable=self.durable,
                auto_delete=False if self.durable else True,
            )

    async def queue(self, queue_name):
        async with self.channel_pool.acquire() as channel:
            await channel.set_qos(prefetch_count=self.prefetch_count)
            return await channel.declare_queue(
                queue_name,
                durable=self.durable,
                auto_delete=False if self.durable else True,
            )

    def message(self, body, reply_to, correlation_id, **kwargs):
        return Message(
            body,
            reply_to=reply_to,
            correlation_id=correlation_id,
            delivery_mode=self.delivery_mode,
            expiration=self.expiration,
            content_type=CONTENT_TYPE,
            content_encoding=CONTENT_ENCODING,
            **kwargs,
        )

    async def publish(
        self, payload, routing_key, reply_to=None, correlation_id=None, **kwargs
    ):
        '''
        如果是响应请求, routing_key 直接使用 reply_to
        另外，在实例化 Message 时 使用参数默认值和关键字参数 方便不需要传入值的参数
        '''
        exchange = await self.exchange()
        message = self.message(
            payload, reply_to=reply_to, correlation_id=correlation_id, **kwargs
        )
        await exchange.publish(message, routing_key=routing_key, timeout=self.timeout)

    async def subscribe(self, queue_name, binding_key, callback=None):
        exchange = await self.exchange()
        queue = await self.queue(queue_name)
        await queue.bind(exchange, binding_key)
        consumer = None
        if callback:
            consumer = await queue.consume(callback)
        return queue, consumer

    async def close(self):
        await self.channel_pool.close()
        await self.conn_pool.close()


class Admin:
    def init(self, api_uri):
        parts = seperate_uri(api_uri)
        self.uri = '{}{}'.format(parts.get('protocol'), parts.get('address'))
        self.user = parts.get('user')
        self.password = parts.get('password')
        return self

    async def overview(self):
        return await self.yujian.overview()

    async def list_queue(self, vhost: str = None, columns: list[str] = None, **kwargs):
        qs = await self.yujian.list_queue(vhost=vhost, columns=columns, **kwargs)
        return [q for q in qs if q['name'].startswith('Jiama')]

    async def destroy(self):
        await self.yujian.close()

    async def __aenter__(self):
        self.yujian = await Client().init(self.uri, self.user, self.password)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.destroy()
