"""
COT Service

Author: Tony Chi
Updated at: 2018-06
Content : 
"""
# -*- coding: utf-8 -*-
import sys
import asyncio
import json
import logging
import random
import argparse
import tornado.platform.asyncio
from tornado import gen
from tornado.ioloop import PeriodicCallback
import aiocoap
import aiocoap.resource as resource
from pycots.gateway.settings import GATEWAY_COAP_SERVER_PORT, GATEWAY_COAP_SERVER_IP

internal_logger = logging.getLogger("tornado.internal")
internal_logger.setLevel(logging.DEBUG)

parser = argparse.ArgumentParser(description="Test CoAP client")
parser.add_argument(
    '--gateway-host', type=str, default=GATEWAY_COAP_SERVER_IP, help="Gateway Coap server host."
)
parser.add_argument(
    '--gateway-port', type=int, default=GATEWAY_COAP_SERVER_PORT, help="Gateway Coap server port."
)
parser.add_argument('--imu', action="store_true", help="Activate IMU endpoint.")
parser.add_argument('--led', action="store_true", help="Activate LED endpoint.")
parser.add_argument('--temperature', action="store_true", help="Activate Temperature endpoint.")
parser.add_argument('--pressure', action="store_true", help="Activate Pressure endpoint.")
parser.add_argument('--robot', action="store_true", help="Activate Robot endpoint.")
parser.add_argument('--js', action="store_true", help="Activate Javascript endpoint.")
parser.add_argument('--version', action="store_true", help="Activate Version endpoint.")
args = parser.parse_args()

COAP_GATEWAY = 'coap://{}:{}'.format( args.gateway_host, args.gateway_port )
print(COAP_GATEWAY)

@asyncio.coroutine
def _coap_resource(url, method=aiocoap.Code.GET, payload=b''):
    protocol = yield from aiocoap.Context.create_client_context(
        # loop=None
    )
    request = aiocoap.Message(
        code=method, payload=payload
    )
    request.set_request_uri(url)
    try:
        response = yield from protocol.request(request).response
    except Exception as e:
        code = "Failed to fetch resource"
        payload = '{0}'.format(e)
    else:
        code = response.code
        payload = response.payload.decode('utf-8')
    finally:
        yield from protocol.shutdown()

    internal_logger.debug('Code: {0} - Payload: {1}'.format(code, payload))
    return code, payload


@gen.coroutine
def _send_alive():
    _, _ = yield from _coap_resource(
        '{}/{}'.format(COAP_GATEWAY, "alive"),
         method=aiocoap.Code.POST,
         payload='Alive'.encode('utf-8')
    )


@gen.coroutine
def _send_temperature():
    payload = (
        "temperature:{}°C".format(random.randrange(20, 30, 1)).encode('utf-8')
    )
    _, _ = yield from _coap_resource(
        '{}/{}'.format(COAP_GATEWAY, "server"),
         method=aiocoap.Code.POST,
         payload=payload
    )


@gen.coroutine
def _send_pressure():
    payload = (
        "pressure:{}hPa".format(random.randrange(990, 1015, 1)).encode('utf-8')
    )
    _, _ = yield from _coap_resource(
        '{}/{}'.format(COAP_GATEWAY, "server"),
         method=aiocoap.Code.POST,
         payload=payload
    )


@gen.coroutine
def _send_imu():
    imu = json.dumps(
        [{"type": "acc", "values": [
            random.randrange(-500, 500, 1), random.randrange(-500, 500, 1), random.randrange(-500, 500, 1)]
          },
          {"type": "mag", "values": [
              random.randrange(-500, 500, 1), random.randrange(-500, 500, 1), random.randrange(-500, 500, 1)]
           },
          {"type": "gyro", "values": [
              random.randrange(-500, 500, 1), random.randrange(-500, 500, 1), random.randrange(-500, 500, 1)]
        }]
    )
    _, _ = yield from _coap_resource(
        '{}/{}'.format(COAP_GATEWAY, "server"),
        method=aiocoap.Code.POST,
        payload="imu:{}".format(imu).encode('utf-8')
    )


@gen.coroutine
def _send_version():
    payload = (
        "version:{}.{}.{}" .format(
            random.randrange(1, 9, 1), random.randrange(1, 9, 1), random.randrange(1, 9, 1)
        ).encode('utf-8')
    )
    _, _ = yield from _coap_resource(
        '{}/{}'.format(COAP_GATEWAY, "server"),
        method=aiocoap.Code.POST,
        payload=payload
    )


class BoardResource(resource.Resource):
    """
    Test node board resource.
    """
    def __init__(self):
        super(BoardResource, self).__init__()
        self.value = "test_board".encode('utf-8')

    @asyncio.coroutine
    def render_get(self, request):
        response = aiocoap.Message(
            code=aiocoap.CONTENT, payload=self.value
        )
        return response


class NameResource(resource.Resource):
    """
    Test node name resource.
    """
    def __init__(self):
        super(NameResource, self).__init__()
        self.value = "Python Test Node".encode('utf-8')

    @asyncio.coroutine
    def render_get(self, request):
        response = aiocoap.Message(
            code=aiocoap.CONTENT, payload=self.value
        )
        return response


class VersionResource(resource.Resource):
    """
    Test node firmware version resource.
    """
    def __init__(self):
        super(VersionResource, self).__init__()
        self.value = "1.0.0".encode('utf-8')

    @asyncio.coroutine
    def render_get(self, request):
        response = aiocoap.Message(
            code=aiocoap.CONTENT, payload=self.value
        )
        return response


class LedResource(resource.Resource):
    """
    Example resource which supports GET and PUT methods. It sends large
    responses, which trigger blockwise transfer.
    """
    def __init__(self):
        super(LedResource, self).__init__()
        self.value = "0".encode("utf-8")

    @asyncio.coroutine
    def render_get(self, request):
        response = aiocoap.Message(
            code=aiocoap.CONTENT, payload=self.value
        )
        return response

    @asyncio.coroutine
    def render_put(self, request):
        self.value = request.payload.decode()
        payload = ("Updated").encode('utf-8')

        yield from _coap_resource(
            '{}/{}'.format(COAP_GATEWAY, "server"),
            method=aiocoap.Code.POST,
            payload="led:{}".format(self.value).encode()
        )

        return aiocoap.Message(
            code=aiocoap.CHANGED, payload=payload
        )


class PressureResource(resource.Resource):
    """
    Test node pressure resource.
    """
    def __init__(self):
        super(PressureResource, self).__init__()
        self.value = "1015.03hPa".encode("utf-8")

    @asyncio.coroutine
    def render_get(self, request):
        response = aiocoap.Message(
            code=aiocoap.CONTENT, payload=self.value
        )
        return response


class TemperatureResource(resource.Resource):
    """
    Test node temperature resource.
    """
    def __init__(self):
        super(TemperatureResource, self).__init__()
        self.value = "23°C".encode("utf-8")

    @asyncio.coroutine
    def render_get(self, request):
        response = aiocoap.Message(
            code=aiocoap.CONTENT, payload=self.value
        )
        return response


class ImuResource(resource.Resource):
    """
    Test node IMU resource.
    """
    def __init__(self):
        super(ImuResource, self).__init__()
        self.value = json.dumps(
            [{"type": "acc", "values": [304, 488, 448]},
             {"type": "mag", "values": [460, 122, -104]},
             {"type": "gyro", "values": [1, 0, 0]}]
        ).encode("utf-8")

    @asyncio.coroutine
    def render_get(self, request):
        response = aiocoap.Message(
            code=aiocoap.CONTENT, payload=self.value
        )
        return response


class RobotResource(resource.Resource):
    """
    Test node Robot resource.
    """
    def __init__(self):
        super(RobotResource, self).__init__()
        self.action = "s".encode("utf-8")

    @asyncio.coroutine
    def render_get(self, request):
        response = aiocoap.Message(
            code=aiocoap.CONTENT, payload=self.action
        )
        return response

    @asyncio.coroutine
    def render_put(self, request):
        self.action = request.payload
        payload = ("Updated").encode('utf-8')
        response = aiocoap.Message(
            code=aiocoap.CONTENT, payload=payload
        )
        return response


class JavascriptResource(resource.Resource):
    """
    Test node Javascript resource.
    """
    def __init__(self):
        super(JavascriptResource, self).__init__()
        self.script = """
            this.ledorange = saul.get_by_name("led");
            value = 0;
            count = 10;
            
            this.blink = function () {
                if (count > 0) {
                    value = (value + 1) % 2;
                    this.ledorange.write(value);
                    t = timer.setTimeout(this.blink, 1000000);
                    count = count -1;
                }
            }
            
            this.blink();
        """.encode("utf-8")

    @asyncio.coroutine
    def render_get(self, request):
        response = aiocoap.Message(
            code=aiocoap.CONTENT, payload=self.script
        )
        return response

    @asyncio.coroutine
    def render_put(self, request):
        self.script = request.payload
        print("New script:\n '{}'".format(self.script))
        payload = ("Updated").encode('utf-8')
        response = aiocoap.Message(
            code=aiocoap.CONTENT, payload=payload
        )
        return response


if __name__ == '__main__':
    try:
        # Tornado ioloop initialization
        ioloop = asyncio.get_event_loop()
        tornado.platform.asyncio.AsyncIOMainLoop().install()

        PeriodicCallback(_send_alive, 30000).start()
        PeriodicCallback(_send_temperature, 5000).start()
        # PeriodicCallback(_send_pressure, 5000).start()
        # PeriodicCallback(_send_imu, 200).start()
        # PeriodicCallback(_send_version, 2000).start()


        # if args.temperature:
        #     PeriodicCallback(_send_temperature, 5000).start()
        # if args.pressure:
        #     PeriodicCallback(_send_pressure, 5000).start()
        # if args.imu:
        #     PeriodicCallback(_send_imu, 200).start()
        # if args.version:
        #     PeriodicCallback(_send_version, 2000).start()

        # Aiocoap server initialization
        root = resource.Site()
        # root.add_resource(
        #     ('board', ), BoardResource()
        # )
        # root.add_resource(
        #     ('name', ), NameResource()
        # )
        # if args.led:
        #     root.add_resource(('led', ), LedResource())
        # if args.temperature:
        #     root.add_resource(('temperature', ), TemperatureResource())
        # if args.pressure:
        #     root.add_resource(('pressure', ), PressureResource())
        # if args.imu:
        #     root.add_resource(('imu', ), ImuResource())
        # if args.robot:
        #     root.add_resource(('robot', ), RobotResource())
        # if args.js:
        #     root.add_resource(('js', ), JavascriptResource())
        # if args.version:
        #     root.add_resource(('version', ), VersionResource())
        # root.add_resource(
        #     ('.well-known', 'core'),
        #     resource.WKCResource(root.get_resources_as_linkheader)
        # )
        #
        # asyncio.async(
        #     aiocoap.Context.create_server_context(
        #         root, bind=(config.COAP_SERVER_IP, config.COAP_SERVER_PORT)
        #     )
        # )
        _send_alive()
        ioloop.run_forever()

    except KeyboardInterrupt:
        print("Exiting")
        ioloop.stop()
        sys.exit()
