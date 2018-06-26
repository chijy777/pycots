import logging
import asyncio
import aiocoap
from pycots.test.aiocoap_test import cfg

logging.basicConfig(level=logging.INFO)

async def main():
    """Perform a single PUT request to localhost on the default port, URI
    "/other/block". The request is sent 2 seconds after initialization.

    The payload is bigger than 1kB, and thus sent as several blocks."""

    context = await aiocoap.Context.create_client_context()
    await asyncio.sleep(2)

    payload = b"The quick brown fox jumps over the lazy dog.\n" * 30
    request = aiocoap.Message(code=aiocoap.Code.PUT, payload=payload)
    # These direct assignments are an alternative to setting the URI like in
    # the GET example:
    request.opt.uri_host = '%s' %cfg.SERVER_IP
    request.opt.uri_path = ("other", "block")
    print(request)

    response = await context.request(request).response
    print('Result: %s\n%r'%(response.code, response.payload))

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
