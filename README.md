# 甲马 jiama
一个基于 RabbitMQ 的异步 RPC 框架。
An asyncio RPC framework based on RabbitMQ.


俗话说：外事不决用 REST，内事不决用 RPC，找一圈只发现一个 Nameko，却是同步的，遂有 Jiama 问世。


### 安装 install
```shell
pip install jiama
```



Rabbitmq 的安装可以使用 docker 方式，具体参见[官网](https://www.rabbitmq.com/download.html)。
```shell
sudo docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.10-management
```



### 接口 API
#### jiama run module_path:ServiceClass -c config.toml
jiama run 是一个 Shell 命令，用于启动远程服务，后跟多个模块路径和服务类作为参数，用 -c 指定配置文件。



#### jiama.server.rpc
服务端装饰器，用于标志一个方法为远程服务方法。



#### jiama.client.RpcProxy()
RPC 服务代理，单例模式，提供在客户端访问远程服务的能力。



#### jiama.client.RpcProxy().create(config: dict)
创建 RPC 服务代理
- `config` dict - 配置选项，包括 RPC 和 log 配置，具体参见 test/jiama/config.toml



#### jiama.client.RpcProxy.close()
关闭远程服务代理



#### rpc.service.method()
访问远程服务方法


### 示例 examples

#### 服务端
jiama/sample.py

```python
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
        self.config = {'uri': 'amqp://guest:guest@localhost'}

    @rpc
    async def mul(self, x=1):
        async with await RpcProxy().create(self.config) as rpc:
            y = await rpc.Service1.add(1, 1)
        return x * y
```

```shell
jiama run jiama.sample -c ./config.toml
```


#### 客户端

```python
import asyncio

from jiama.client import RpcProxy


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
    asyncio.run(main())
```



### License
[MIT](LICENSE) © Li zhigang