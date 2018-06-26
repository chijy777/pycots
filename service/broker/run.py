#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Broker application module.
"""
import sys
from tornado.options import options

from pycots.common.auth import check_key_file
from pycots.common.helpers import start_application, parse_command_line
from pycots.broker.broker import Broker, logger


def run(arguments=[]):
    """
    Start a broker instance.
    """
    if arguments != []:
        sys.argv[1:] = arguments

    try:
        parse_command_line()
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
        Broker(keys, options=options), port=options.broker_port
    )

if __name__ == '__main__':
    run()
