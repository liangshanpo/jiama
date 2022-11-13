import importlib
import inspect
import re

from functools import wraps


# 使用 __init__ 作为工厂方法 不要传入任何参数，
# 使用另外一个方法作为初始化方法接收参数 同时可以实现异步初始化 需提前初始化
def singleton(cls):
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


def load_service(module_path):
    path, _, name = module_path.partition(':')
    module = importlib.import_module(path)
    services = {}
    if name:
        services[name] = getattr(module, name)
    else:
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if inspect.getmembers(cls, is_entrypoint):
                services[name] = cls
    return services


def is_entrypoint(method):
    return getattr(method, 'jiama_rpc_entrypoint', False)


def merge_dict(a, b, ignore=[]):
    if not (isinstance(a, dict) and isinstance(b, dict)):
        if isinstance(a, list) and isinstance(b, list):
            return a + b
        return b

    result = {}
    for k in sorted(set(list(a.keys()) + list(b.keys()))):
        if k in ignore:
            continue
        v1 = a.get(k, None)
        v2 = b.get(k, None)

        if v2:
            result[k] = merge_dict(v1, v2, ignore)
        else:
            result[k] = v1
    return result


def seperate_uri(uri):
    p = r'^(?P<protocol>.+?//)(?P<user>.+?):(?P<password>.+?)@(?P<address>.+)$'
    m = re.match(p, uri)
    return (
        {
            'protocol': m.group('protocol'),
            'address': m.group('address'),
            'user': m.group('user'),
            'password': m.group('password'),
        }
        if m
        else None
    )


def iter_dict(d, i=0, s='    '):
    for k, v in d.items():
        if isinstance(v, dict):
            yield f'{s*i}{k}: '
            yield from iter_dict(v, i + 1, s)
        else:
            yield f'{s*i}{k}: {v}'
