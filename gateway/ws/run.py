"""
COT Service

Author: Tony Chi
Updated at: 2018-06
Content : Broker application module.
"""
# -*- coding: utf-8 -*-
import sys
import logging
from tornado.options import define, options
from pycots.common.auth import check_key_file
from pycots.common.helpers import start_application, parse_command_line
from pycots.gateway.settings import WS_GATEWAY_PORT
from pycots.gateway.ws.gateway import WebsocketGateway

logger = logging.getLogger("pycots.gw.ws")


def extra_args():
    """
    Parse command line arguments for websocket gateway application.
    """
    if not hasattr(options, "gateway_port"):
        define("gateway_port", default=WS_GATEWAY_PORT, help="Node gateway websocket port")


def run(arguments=[]):
    """
    Start the websocket gateway instance.
    """
    if arguments != []:
        sys.argv[1:] = arguments

    try:
        parse_command_line(extra_args_func=extra_args)
    except SyntaxError as exc:
        logger.error("Invalid config file: {}".format(exc))
        return
    except FileNotFoundError as exc:
        logger.error("Config file not found: {}".format(exc))
        return

    try:
        keys = check_key_file(options.key_file)
    except ValueError as exc:
        logger.error(exc)
        return

    start_application(
        WebsocketGateway(keys, options=options),
        port=options.gateway_port,
        close_client=True
    )


if __name__ == '__main__':
    run()
