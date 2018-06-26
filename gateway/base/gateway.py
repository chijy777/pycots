"""
COT Service

Author: Tony Chi
Updated at: 2018-06
Content : Base class for gateways. 
"""
# -*- coding: utf-8 -*-
import json
import logging
from abc import ABCMeta, abstractmethod
from tornado import web, gen
from tornado.websocket import websocket_connect
from pycots.common.auth import auth_token
from pycots.common.messaging import check_broker_data, Message

logger = logging.getLogger("pycots.gw.base.gateway")
logger.setLevel(logging.DEBUG)

class GatewayBaseMixin():
    """
    Class that manages the internal behaviour of a node controller.
    """
    PROTOCOL = None
    # nodes = None

    def has_node(self, uid):
        """
        Check if the node uid is already present.
        """
        return uid in self.nodes

    @gen.coroutine
    def add_node(self, node):
        """
        Add a new node to the list of nodes and notify the broker.
        """
        node.set_resource_value('protocol', self.PROTOCOL)
        self.nodes.update({node.uid: node})
        self.send_to_broker(Message.new_node(node.uid))
        # for res, value in node.resources.items():
        #     self.send_to_broker(Message.update_node(node.uid, res, value))
        yield self.discover_node(node)

    def reset_node(self, node, default_resources={}):
        """
        Reset a node: clear the current resource and reinitialize them.
        """
        node.clear_resources()
        node.set_resource_value('protocol', self.PROTOCOL)
        for resource, value in default_resources.items():
            node.set_resource_value(resource, value)
        self.send_to_broker(Message.reset_node(node.uid))
        self.discover_node(node)

    def remove_node(self, node):
        """
        Remove the given node from known nodes and notify the broker.
        """
        self.nodes.pop(node.uid)
        logger.debug("Remaining nodes {}".format(self.nodes))
        self.send_to_broker(Message.out_node(node.uid))

    def get_node(self, uid):
        """
        Return the node matching the given uid.
        """
        return self.nodes[uid]

    @gen.coroutine
    def forward_data_from_node(self, node, resource, value):
        """
        Send data received from a node to the broker via the gateway.
        """
        logger.debug(
            "Sending data received from node '{}': '{}', '{}'.".format(node, resource, value)
        )
        node.set_resource_value(resource, value)
        self.send_to_broker(
            Message.update_node(node.uid, resource, value)
        )

    @gen.coroutine
    def fetch_nodes_cache(self, client):
        """
        Send cached nodes information to a given client.
        :param client: the ID of the client
        """
        logger.debug(
            "Fetching cached information of registered nodes '{}'.".format(self.nodes)
        )
        for node in self.nodes.values():
            self.send_to_broker(Message.new_node(node.uid, dst=client))
            for resource, value in node.resources.items():
                self.send_to_broker(
                    Message.update_node(node.uid, resource, value, dst=client)
                )

    def close_client(self):
        """
        Close client websocket
        """
        logger.warning("Closing connection with broker.")
        self.broker.close()

    @gen.coroutine
    def create_broker_connection(self, url):
        """
        Create an asynchronous connection to the broker.
        """
        while True:
            try:
                self.broker = yield websocket_connect(url)
            except ConnectionRefusedError:
                logger.warning("Cannot connect, retrying in 3s")
            else:
                logger.info("Connected to broker, sending auth token")
                self.broker.write_message(auth_token(self.keys))
                yield gen.sleep(1)
                self.fetch_nodes_cache('all')
                while True:
                    message = yield self.broker.read_message()
                    if message is None:
                        logger.warning("Connection with broker lost.")
                        break
                    self.on_broker_message(message)

            yield gen.sleep(3)

    @gen.coroutine
    def send_to_broker(self, message):
        """
        Send a string message to the parent broker.
        """
        if self.broker is not None:
            logger.debug("Sending message '{}' to broker.".format(message))
            self.broker.write_message(message)

    def on_broker_message(self, message):
        """
        Handle a message received from the broker websocket.
        """
        logger.debug("Handling message '{}' received from broker.".format(message))
        message = json.loads(message)

        if message['type'] == "new":
            # Received when a new client connects => fetching the nodes
            # in controller's cache
            self.fetch_nodes_cache(message['src'])
        elif (message['type'] == "update" and
              check_broker_data(message['data'])):
            data = message['data']
            logger.debug(
                "Forwarding message ('{}') received from broker to node".format(data)
            )
            # Received when a client update a node
            uid = data['uid']
            endpoint = data['endpoint']
            payload = data['payload']
            for node in self.nodes.values():
                if node.uid == uid:
                    self.update_node_resource(node, endpoint, payload)
                    break
        else:
            logger.debug(
                "Invalid data received from broker '{}'." .format(message['data'])
            )


class GatewayBase(web.Application, GatewayBaseMixin, metaclass=ABCMeta):
    """
    Base gateway application.
    All abstractmethods should be reimplemented to match the specific
    communication protocols used by subclasses (CoAP, MQTT, websocket, etc).
    """
    def __init__(self, keys, options, handlers=[]):
        if options.debug:
            logger.setLevel(logging.DEBUG)

        self.options = options
        self.nodes = {}
        self.broker = None
        self.keys = keys
        settings = {'debug': True}

        # Create connection to broker @chijy update
        # self.create_broker_connection(
        #     "ws://{}:{}/gw".format(options.broker_host, options.broker_port)
        # )
        super().__init__(handlers, **settings)
        logger.debug('Base Gateway application started')


    @abstractmethod
    def update_node_resource(self, node, resource, value):
        """
        Send an update to a node to change its resource with given value.
        This is dependent on the protocol used to communicate with nodes (CoAP,
        MQTT, etc) and has to be implemented in the protocol specific nodes
        controller.
        
        Should be a coroutine.
        """

    @abstractmethod
    def discover_node(self, node):
        """
        Start a discovery procedure on a node.

        After the discovery is done, all resources (or endpoints) exposed by a
        node are available using the `resource` attribute of the given node.

        This is dependent on the protocol used to communicate with nodes (CoAP,
        MQTT, etc) and has to be implemented in the protocol specific nodes
        controller.

        Should be a coroutine.
        """
