#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
消息管理.
"""
import json
import logging

logger = logging.getLogger("pycots.messaging")


def check_broker_data(data):
    """"
    Utility function that checks the data object.
    :param data: a dict with only 'uid', 'endpoint' and 'payload' keys.
    :return True of the data is correct, False otherwise
    
    # >>> check_broker_data({'uid':1, 'endpoint':'/test', 'payload': 'ok'})
    # True
    # >>> check_broker_data({'endpoint':'/test', 'payload': 'ok'})
    # False
    # >>> check_broker_data({'uid':1, 'payload': 'ok'})
    # False
    # >>> check_broker_data({'uid':1, 'endpoint':'/test'})
    # False
    # >>> check_broker_data({'uid':1, 'endpoint':'/test', 'payload': 'ok', 'extra': 'too many'})
    # False
    """
    if 'uid' not in data:
        logger.debug("Invalid broker data: missing uid")
    elif 'endpoint' not in data:
        logger.debug("Invalid broker data: missing endpoint")
    elif 'payload' not in data:
        logger.debug("Invalid broker data: missing payload")
    elif len(data.keys()) > 3:
        logger.debug("Invalid broker data: too many keys")
    else:
        return True
    return False


class Message():
    """
    Utility class for generating and parsing service messages.
    """
    @staticmethod
    def serialize(message):
        return json.dumps(message, ensure_ascii=False)

    @staticmethod
    def new_node(uid, dst="all"):
        """
        生成新节点消息. 
        Generate a text message indicating a new node.
        """
        return Message.serialize({
            'type': 'new', 'uid': uid, 'dst': dst
        })

    @staticmethod
    def out_node(uid):
        """
        删除节点消息. 
        Generate a text message indicating a node to remove.
        """
        return Message.serialize({
            'type': 'out', 'uid': uid
        })

    @staticmethod
    def reset_node(uid):
        """
        重置节点消息. 
        Generate a text message indicating a node reset.
        """
        return Message.serialize({'type': 'reset', 'uid': uid})

    @staticmethod
    def update_node(uid, endpoint, data, dst="all"):
        """
        更新节点消息. 
        Generate a text message indicating a node update.
        """
        return Message.serialize({
            'type': 'update',
            'uid': uid,
            'endpoint': endpoint,
            'data': data,
            'dst': dst
        })

    @staticmethod
    def discover_node():
        """
        发现websocket节点消息
        Generate a text message for websocket node discovery.
        """
        return Message.serialize({'request': 'discover'})

    @staticmethod
    def check_message(raw):
        """
        消息格式检查. 
        Verify a received message is correctly formatted.
        """
        reason = None
        try:
            message = json.loads(raw)
        except TypeError as exc:
            logger.warning(exc)
            reason = "Invalid message '{}'.".format(raw)
            message = None
        except json.JSONDecodeError:
            reason = ("Invalid message received '{}'. Only JSON format is supported.".format(raw))
            message = None

        if message is not None:
            if not hasattr(message, '__iter__'):
                reason = "Invalid message '{}'.".format(message)
            elif 'type' not in message and 'data' not in message:
                reason = "Invalid message '{}'.".format(message)
            elif ( message['type'] != 'new' and message['type'] != 'update'
                   and message['type'] != 'out' and message['type'] != 'reset'):
                reason = "Invalid message type '{}'.".format(message['type'])

        if reason is not None:
            logger.warning(reason)
            message = None

        return message, reason

