# encoding -*- utf-8 -*-
import logging
import asyncio
import aiocoap
from pycots.test.aiocoap_test import cfg

logging.basicConfig(level=logging.INFO)

async def main():
    protocol = await aiocoap.Context.create_client_context()
    request = aiocoap.Message(
        code=aiocoap.Code.GET, uri='coap://%s:5683/time'%(cfg.SERVER_IP)
    )

    try:
        response = await protocol.request(request).response
    except Exception as e:
        print('Failed to fetch resource:')
        print(e)
    else:
        print('Result: %s\n%r'%(response.code, response.payload))

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
