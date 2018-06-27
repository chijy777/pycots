"""
COT Service

Author: Tony Chi
Updated at: 2018-06
Content : MQTT gateway application module.
"""
# -*- coding: utf-8 -*-
import sys
import logging
import tornado.platform.asyncio
from tornado.options import define, options
from pycots.common.auth import check_key_file
from pycots.common.helpers import start_application, parse_command_line
from pycots.gateway.settings import MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_RETENT_MAX_TIME
from pycots.gateway.mqtt.gateway import MQTTGateway

logger = logging.getLogger("pycots.gw.mqtt")


def extra_args():
    """
    Parse command line arguments for MQTT gateway application.
    """
    if not hasattr(options, "mqtt_host"):
        define(
            "mqtt_host", default=MQTT_BROKER_HOST, help="Gateway MQTT broker host"
        )
    if not hasattr(options, "mqtt_port"):
        define(
            "mqtt_port", default=MQTT_BROKER_PORT, help="Gateway MQTT broker port"
        )
    if not hasattr(options, "max_time"):
        define(
            "max_time", default=MQTT_RETENT_MAX_TIME, help="Maximum retention time (in s) for MQTT dead nodes"
        )


def run(arguments=[]):
    """
    Start the MQTT gateway instance.
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

    # Application ioloop initialization
    if not tornado.platform.asyncio.AsyncIOMainLoop().initialize():
        tornado.platform.asyncio.AsyncIOMainLoop().install()

    start_application(
        MQTTGateway(keys, options=options),
        close_client=True
    )

if __name__ == '__main__':
    run()
