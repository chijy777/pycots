"""
COT Service

Author: Tony Chi
Updated at: 2018-06
Content : 
"""
# encoding -*- utf-8 -*-
import logging
import asyncio
import random
import aiocoap
from pycots.gateway.settings import COAP_GATEWAY_HOST, COAP_GATEWAY_PORT

logging.basicConfig(level=logging.INFO)


async def main():
    protocol = await aiocoap.Context.create_client_context()

    # request = aiocoap.Message(
    #     code=aiocoap.Code.POST,
    #     uri='coap://%s:5683/alive'%(setting.SERVER_IP)
    # )
    # _, _ = yield from _coap_resource(
    #     '{}/{}'.format(COAP_GATEWAY, "alive"),
    #     method=aiocoap.Code.POST,
    #     payload='Alive'.encode('utf-8')
    # )

    request = aiocoap.Message(
        code=aiocoap.Code.POST,
        uri='coap://%s:%s/server' % ( COAP_GATEWAY_HOST, COAP_GATEWAY_PORT ),
        payload = (
            "temperature:{}°C卡卡".format(28).encode('utf-8')
        )
    )
    # payload = (
    #     "temperature:{}°C".format(random.randrange(20, 30, 1)).encode('utf-8')
    # )
    # _, _ = yield from _coap_resource(
    #     '{}/{}'.format(COAP_GATEWAY, "server"),
    #     method=aiocoap.Code.POST,
    #     payload=payload
    # )

    try:
        response = await protocol.request(request).response
    except Exception as e:
        print('Failed to fetch resource:')
        print(e)
    else:
        print('Result: %s\n%r'%(response.code, response.payload))


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
