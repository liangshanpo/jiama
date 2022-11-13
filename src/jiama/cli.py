import asyncio
import sys

import click
import tomli

from loguru import logger

from jiama.constant import DEFAULT_CONFIG
from jiama.manage import list_entity, stats
from jiama.rmq import Admin, Agent
from jiama.server import Rpc
from jiama.util import iter_dict, load_service, merge_dict


@click.group()
def jiama():
    pass


@jiama.command()
@click.argument('module_list', nargs=-1)
@click.option('--config', '-c', default='', help='The configuration file')
@click.option(
    '--broker', '-b', default='amqp://guest:guest@localhost', help='RabbitMQ broker uri'
)
def run(config, broker, module_list=[]):
    '''
    Run services. E.g.\n
    jiama run module:ServiceClass
    '''
    if config:
        with open(config, 'rb') as fp:
            config = tomli.load(fp)
    else:
        config = {'rpc': {'amqp_uri': broker}}
    log_config, rpc_config = merge_dict(DEFAULT_CONFIG, config).values()
    logger.configure(**log_config)

    rpc = Rpc(rpc_config)

    if '.' not in sys.path:
        sys.path.insert(0, '.')

    services = {}
    for m in module_list:
        services.update(load_service(m))
    asyncio.run(rpc.start(services))


@jiama.command()
@click.argument('entity', nargs=1, required=False)
@click.option(
    '--uri',
    '-u',
    default='http://guest:guest@localhost:15672/',
    help='RabbitMQ management API URI',
)
def list(uri, entity):
    '''
    List services or clients. E.g.\n
    jiama list [service | client] -u http://guest:guest@localhost:15672/
    '''
    logger.remove(handler_id=None)

    entity_list = asyncio.run(list_entity(uri, entity))
    for k, v in entity_list.items():
        click.secho(f'{k} list:'.capitalize(), fg='green', bold=True)
        for p in v:
            click.secho(f'    {p}', fg='green', bold=True)


@jiama.command()
@click.option(
    '--uri',
    '-u',
    default='http://guest:guest@localhost:15672/',
    help='RabbitMQ management API URI',
)
def status(uri):
    '''
    Show the RPC system status. E.g.\n
    jiama status -u http://guest:guest@localhost:15672/
    '''
    logger.remove(handler_id=None)

    result = asyncio.run(stats(uri))
    for i in iter_dict(result):
        click.secho(i, fg='blue', bold=True)
