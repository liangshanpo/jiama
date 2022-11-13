import sys


EXCHANGE_NAME = 'Jiama.rpc'
EXCHANGE_TYPE = 'topic'

REQUEST_QUEUE_NAME = 'Jiama.{service_name}'
REQUEST_BINDING_KEY = '{service_name}.*'
REQUEST_ROUTING_KEY = '{service_name}.{method_name}'

RESPONSE_QUEUE_NAME = 'Jiama.result.{client_id}'
RESPONSE_BINDING_KEY = '#.{client_id}'
RESPONSE_ROUTING_KEY = 'Jiama.result.{client_id}'

CONTENT_TYPE = 'application/json'
CONTENT_ENCODING = 'UTF8'

DEFAULT_CONFIG = {
    'rpc': {
        'amqp_uri': 'amqp://guest:guest@localhost',
        'max_channel': 10,
        'max_connection': 2,
        'prefetch_count': 5,
        'delivery_mode': 2,  # Marks a message as persistent (with a value of 2) or transient (any other value).
        'expiration': 180,  # expiration in seconds (or datetime or timedelta)
        'timeout': 5,  # connection timeout in seconds
        'durable': True,  # 队列和交换机都设置为durable的，这个设置将保证消息能够持久化
    },
    'log': {
        'handlers': [
            {
                'sink': sys.stdout,
                'level': 'DEBUG',
                'colorize': True,
                'format': '<green>{time:YYYY-MM-DD at HH:mm:ss}</green> {level}: <level>{message}</level>',
            },
        ]
    },
}
