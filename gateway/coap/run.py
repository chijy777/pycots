"""
COT Service

Author: Tony Chi
Updated at: 2018-06
Content : CoAP gateway application module. 
"""
# -*- coding: utf-8 -*-
import sys
import logging
import tornado.platform.asyncio
from tornado.options import define, options
from pycots.common.auth import check_key_file
from pycots.common.helpers import start_application, parse_command_line
from pycots.gateway.coap.gateway import CoapGateway
from pycots.gateway.settings import GATEWAY_COAP_MAX_RETENTION_TIME, GATEWAY_COAP_SERVER_PORT

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)14s - %(levelname)5s - %(message)s'
)
logger = logging.getLogger("pycots.gw.coap")


def extra_args():
    """
    Parse command line arguments for CoAP gateway application.
    """
    if not hasattr(options, "coap_port"):
        define(
            "coap_port", default=GATEWAY_COAP_SERVER_PORT, help="Gateway CoAP server port"
        )

    if not hasattr(options, "max_time"):
        define(
            "max_time", default=GATEWAY_COAP_MAX_RETENTION_TIME, help="Maximum retention time (in s) for CoAP dead nodes"
        )


def run(arguments=[]):
    """
    Start the CoAP gateway instance.
    """
    if arguments != []:
        sys.argv[1:] = arguments

    try:
        parse_command_line(extra_args_func=extra_args)
    except SyntaxError as exc:
        logger.critical("Invalid config file: {}".format(exc))
        return
    except FileNotFoundError as exc:
        logger.error("Config file not found: {}".format(exc))
        return

    try:
        keys = check_key_file(options.key_file)
    except ValueError as exc:
        logger.error(exc)
        return

    if not tornado.platform.asyncio.AsyncIOMainLoop().initialize():
        tornado.platform.asyncio.AsyncIOMainLoop().install()

    start_application(
        CoapGateway(keys, options=options),
        port=options.coap_port,
        close_client=True
    )


if __name__ == '__main__':
    run()
