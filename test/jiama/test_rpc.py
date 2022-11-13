import asyncio
import subprocess
import sys

import pytest

from jiama.client import RpcProxy
from jiama.util import load_service, merge_dict


@pytest.fixture(scope='module')
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='module')
def config():
    config = {
        'rpc': {
            'client_id': 'test',
            'amqp_uri': 'amqp://guest:guest@localhost/',
        }
    }
    return config


async def test_add(config):
    async with await RpcProxy().create(config) as rpc:
        r = await rpc.Service1.add(3, 2)
        assert r == 5


async def test_sub(config):
    async with await RpcProxy().create(config) as rpc:
        r = await rpc.Service2.sub(30, 9)
        assert r == 21


async def test_mul(config):
    async with await RpcProxy().create(config) as rpc:
        r = await rpc.Service3.mul(5)
        assert r == 10


async def test_list():
    p = subprocess.Popen(
        ['jiama', 'list', '-u', 'http://guest:guest@localhost:15672'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = p.communicate()
    assert not err
    assert out


async def test_status():
    p = subprocess.Popen(
        ['jiama', 'status', '-u', 'http://guest:guest@localhost:15672'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = p.communicate()
    assert not err
    assert out


def test_load_service():
    if '.' not in sys.path:
        sys.path.insert(0, '.')

    services = load_service('jiama.sample')
    assert len(services) == 3


def test_merge():
    one = {
        't1': {'k1': 123, 'k2': 345},
        't2': {'o1': 'abc', 'o2': 'efg'},
        't3': [{'n1': 'n1'}],
        't4': [1, 2, 3, 4],
        't5': 't5',
    }
    two = {
        't1': {'k1': 'ccc', 'k2': 'ddd'},
        't2': {'o1': 'abcdddd'},
        't3': [{'n1': 'n2'}],
        't4': [1, 2, 6, 7],
        't6': 't6',
    }
    three = merge_dict(one, two)

    assert three['t6'] == 't6'
    assert three['t5'] == 't5'
    assert three['t4'] == [1, 2, 3, 4, 1, 2, 6, 7]
    assert three['t3'] == [{'n1': 'n1'}, {'n1': 'n2'}]
    assert three['t2'] == {'o1': 'abcdddd', 'o2': 'efg'}
    assert three['t1'] == {'k1': 'ccc', 'k2': 'ddd'}


if __name__ == '__main__':
    pytest.main(['-s', '-q'])
