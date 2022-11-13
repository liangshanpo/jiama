import asyncio
import sys

from loguru import logger

from jiama.client import RpcProxy
from jiama.server import rpc


class Service1:
    @rpc
    def add(self, x=1, y=2):
        return x + y


class Service2:
    @rpc
    def sub(self, x=10, y=1):
        return x - y


class Service3:
    def __init__(self):
        self.config = {
            'rpc': {
                'client_id': 'abc',
                'amqp_uri': 'amqp://guest:guest@localhost/',
            }
        }

    @rpc
    async def mul(self, x=1):
        async with await RpcProxy().create(self.config) as rpc:
            y = await rpc.Service1.add(1, 1)
        return x * y


class Client:
    def __init__(self):
        self.config = {
            'rpc': {
                'client_id': 'test',
                'amqp_uri': 'amqp://guest:guest@localhost/',
            }
        }

    async def init(self):
        '''
        这是一个需要被你的框架自动调用的初始化方法，比如: fastAPI 的 startup
        This is a initialization method invoked by you framework like fastAPI's startup
        '''
        self.rpc = await RpcProxy().create(self.config)
        return self

    async def req(self):
        r = await self.rpc.Service1.add(3, 2)
        logger.info(f'Result of add is {r}')

        r = await self.rpc.Service2.sub(30, 9)
        logger.info(f'Result of sub is {r}')

        r = await self.rpc.Service3.mul(5)
        logger.info(f'Result of mul with nested rpc is {r}')

    async def destroy(self):
        await self.rpc.close()


async def main():
    c = await Client().init()
    await c.req()
    await c.destroy()


if __name__ == '__main__':
    config = {
        "handlers": [
            {
                "sink": sys.stdout,
                "format": "<green>{time:YYYY-MM-DD at HH:mm:ss}</green> {level} <level>{message}</level>",
            },
        ],
    }
    logger.configure(**config)

    asyncio.run(main())
