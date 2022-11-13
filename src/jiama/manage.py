import re

from jiama.constant import EXCHANGE_NAME, REQUEST_QUEUE_NAME, RESPONSE_QUEUE_NAME
from jiama.rmq import Admin


async def list_entity(uri, entity=None):
    entity_queue = {'service': REQUEST_QUEUE_NAME, 'client': RESPONSE_QUEUE_NAME}
    async with Admin().init(uri) as admin:
        qs = await admin.list_queue(columns=['name'], sort='name')
    return {
        e: [
            g.group(1)
            for q in qs
            if (g := re.match(re.sub(r'{.*?}', r'([^.]*)?$', qn), q['name']))
        ]
        for e, qn in entity_queue.items()
        if not entity or entity == e or entity not in entity_queue
    }


async def stats(uri):
    entity_dict = await list_entity(uri)

    async with Admin().init(uri) as admin:
        overview = await admin.overview()
    return {
        'exchange name': EXCHANGE_NAME,
        'service number': len(entity_dict.get('service', [])),
        'client number': len(entity_dict.get('client', [])),
        'broker overview': overview,
    }
