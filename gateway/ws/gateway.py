"""
COT Service

Author: Tony Chi
Updated at: 2018-06
Content : Websocket nodes gateway module. 
"""
# -*- coding: utf-8 -*-
import logging
import uuid
import json
from tornado import gen, websocket
from pycots.common.messaging import Message
from pycots.gateway.base import GatewayBase, Node
from pycots.gateway.settings import LOG_LEVEL

logger = logging.getLogger("pycots.gw.ws")
logger.setLevel(LOG_LEVEL)


class WebsocketNodeHandler(websocket.WebSocketHandler):
    def check_origin(self, origin):
        """
        Allow connections from anywhere.
        """
        return True


    @gen.coroutine
    def open(self):
        """
        Discover nodes on each opened connection.
        """
        self.set_nodelay(True)
        logger.debug("New node websocket opened")
        node = Node(str(uuid.uuid4()))
        self.application.node_mapping.update({self: node.uid})
        self.application.add_node(node)


    @gen.coroutine
    def on_message(self, raw):
        """
        Triggered when a message is received from the web client.
        """
        message, reason = Message.check_message(raw)
        if message is not None:
            self.application.on_node_message(self, message)
        else:
            logger.debug("Invalid message, closing websocket")
            self.close(code=1003, reason="{}.".format(reason))


    def on_close(self):
        """
        Remove websocket from internal list.
        """
        logger.debug("Node websocket closed")
        self.application.remove_ws(self)


class WebsocketGateway(GatewayBase):
    """
    Gateway application for websocket nodes on a network.
    """
    PROTOCOL = 'WebSocket'

    def __init__(self, keys, options):
        if options.debug:
            logger.setLevel(logging.DEBUG)

        handlers = [
            (r"/node", WebsocketNodeHandler),
        ]

        GatewayBase.__init__(self, keys, options, handlers=handlers)

        self.node_mapping = {}

        logger.info(
            'WS gateway started, listening on port {}'.format(options.gateway_port)
        )


    @gen.coroutine
    def discover_node(self, node):
        for ws, uid in self.node_mapping.items():
            if node.uid == uid:
                yield ws.write_message(Message.discover_node())
                break


    @gen.coroutine
    def update_node_resource(self, node, resource, value):
        for ws, uid in self.node_mapping.items():
            if node.uid == uid:
                ws.write_message(
                    json.dumps({"endpoint": resource, "payload": value})
                )
                break


    def on_node_message(self, ws, message):
        """
        Handle a message received from a node websocket.
        """
        if message['type'] == "update":
            logger.debug("New update message received from node websocket")
            for key, value in message['data'].items():
                node = self.get_node(self.node_mapping[ws])
                self.forward_data_from_node(node, key, value)
        else:
            logger.debug("Invalid message received from node websocket")


    def remove_ws(self, ws):
        """
        Remove websocket that has been closed.
        """
        if ws in self.node_mapping:
            self.remove_node(self.get_node(self.node_mapping[ws]))
            self.node_mapping.pop(ws)
