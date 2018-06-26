#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CoAP gateway tornado application module.
"""
import logging
import time
import uuid
import asyncio
from tornado import gen
from tornado.ioloop import PeriodicCallback
import aiocoap
import aiocoap.resource as resource
from pycots.gateway.base import GatewayBase, Node
from pycots.config import config as config

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)14s - %(levelname)5s - %(message)s'
)
logger = logging.getLogger("pycots.gw.coap")
# COAP_PORT = 5683
# MAX_TIME = 120

def _coap_endpoints(link_header):
    link = link_header.replace(' ', '')
    return link.split(',')

@gen.coroutine
def _coap_resource(url, method=aiocoap.Code.GET, payload=b''):
    protocol = yield from aiocoap.Context.create_client_context()
    request = aiocoap.Message(
        code=method, payload=payload
    )
    request.set_request_uri(url)
    try:
        response = yield from protocol.request(request).response
        print(response)
    except Exception as exc:
        code = "Failed to fetch resource"
        payload = '{0}'.format(exc)
    else:
        code = response.code
        payload = response.payload.decode('utf-8')
    finally:
        yield from protocol.shutdown()

    logger.debug('Code: {0} - Payload: {1}'.format(code, payload))
    print('Code: {0} - Payload: {1}'.format(code, payload))
    return code, payload


class CoapAliveResource(resource.Resource):
    """
    CoAP server running within the tornado application.
    """
    def __init__(self, gateway):
        super(CoapAliveResource, self).__init__()
        self._gateway = gateway

    @asyncio.coroutine
    def render_post(self, request):
        """
        Triggered when a node post an alive check to the gateway.
        """
        payload = request.payload.decode('utf8')
        print('1======================')
        print(request)
        print(payload)
        try:
            remote = request.remote[0]
        except TypeError:
            remote = request.remote.sockaddr[0]

        logger.debug("CoAP Alive POST received from {}".format(remote))

        # Let the controller handle this message
        self._gateway.handle_coap_check(
            remote, reset=(payload=='reset')
        )

        # Kindly reply the message has been processed
        return aiocoap.Message(
            code=aiocoap.Code.CHANGED,
            payload="Received '{}'".format(payload).encode('utf-8')
        )


class CoapServerResource(resource.Resource):
    """
    CoAP server running within the tornado application.
    """
    def __init__(self, gateway):
        super(CoapServerResource, self).__init__()
        self._gateway = gateway

    @asyncio.coroutine
    def render_post(self, request):
        """
        Triggered when a node post a new value to the gateway.
        """
        payload = request.payload.decode('utf-8')
        print('2======================')
        print(request)
        print(payload)
        try:
            remote = request.remote[0]
        except TypeError:
            remote = request.remote.sockaddr[0]

        logger.debug(
            "CoAP POST received from {} with payload: {}" .format(remote, payload)
        )

        path, data = payload.split(":", 1)
        self._gateway.handle_coap_post(remote, path, data)

        return aiocoap.Message(
            code=aiocoap.Code.CHANGED, payload="Received '{}'".format(payload).encode('utf-8')
        )


class CoapGateway(GatewayBase):
    """
    Tornado based gateway application for managing CoAP nodes.
    """
    PROTOCOL = 'CoAP'

    def __init__(self, keys, options):
        self.port = options.coap_port
        self.max_time = options.max_time
        self.node_mapping = {}  # map node address to its uuid (TODO: FIXME)

        super().__init__(keys, options)

        # Configure the CoAP server
        root_coap = resource.Site()
        root_coap.add_resource(
            ('server', ), CoapServerResource(self)
        )
        root_coap.add_resource(
            ('alive', ), CoapAliveResource(self)
        )
        asyncio.async(
            aiocoap.Context.create_server_context(
                root_coap, bind=(config.COAP_SERVER_IP, self.port)
            )
        )

        # Start the periodic node cleanup task
        PeriodicCallback(
            self.check_dead_nodes, 1000
        ).start()

        logger.info('CoAP gateway application started')

    @gen.coroutine
    def discover_node(self, node):
        """
        Discover resources available on a node.
        """
        address = node.resources['ip']
        coap_node_url = 'coap://[{}]'.format(address)
        logger.debug("Discovering CoAP node {}".format(address))

        _, payload = yield _coap_resource(
            '{0}/.well-known/core'.format(coap_node_url),
            method=aiocoap.Code.GET
        )
        endpoints = [
            endpoint for endpoint in _coap_endpoints(payload)
            if 'well-known/core' not in endpoint
        ]
        logger.debug("Fetching CoAP node resources: {}".format(endpoints))

        for endpoint in endpoints:
            elems = endpoint.split(';')
            path = elems.pop(0).replace('<', '').replace('>', '')
            try:
                code, payload = yield _coap_resource(
                    '{0}{1}'.format(coap_node_url, path),
                    method=aiocoap.Code.GET
                )
            except:
                logger.debug("Cannot discover resource {} on node {}".format(endpoint, address))
                return

            # Remove '/' from path
            self.forward_data_from_node(node, path[1:], payload)

        logger.debug("CoAP node resources '{}' sent to broker".format(endpoints))

    @gen.coroutine
    def update_node_resource(self, node, endpoint, payload):
        """"""
        address = node.resources['ip']
        logger.debug("Updating CoAP node '{}' resource '{}'".format(address, endpoint))

        code, p = yield _coap_resource(
            'coap://[{0}]/{1}'.format(address, endpoint),
            method=aiocoap.Code.PUT,
            payload=payload.encode('ascii')
        )
        if code == aiocoap.Code.CHANGED:
            self.forward_data_from_node(node, endpoint, payload)

    def handle_coap_post(self, address, endpoint, value):
        """
        Handle CoAP post message sent from coap node.
        """
        if address not in self.node_mapping:
            logger.debug("Unknown CoAP node '{}'".format(address))
            return

        node = self.get_node(self.node_mapping[address])
        self.forward_data_from_node(node, endpoint, value)

    def handle_coap_check(self, address, reset=False):
        """
        Handle check message received from coap node.
        """
        if address not in self.node_mapping:
            # This is a totally new node: create uid, initialized cached node
            # send 'new' node notification, 'update' notification.
            node = Node(str(uuid.uuid4()), ip=address)
            self.node_mapping.update({address: node.uid})
            self.add_node(node)
        elif reset:
            # The data of the node need to be reset without removing it. This
            # is particularly the case after a reboot of the node or a
            # firmware update of the node that triggered the reboot.
            node = self.get_node(self.node_mapping[address])
            self.reset_node(node, default_resources={'ip': address})
        else:
            # The node simply sent a check message to notify that it's still online.
            node = self.get_node(self.node_mapping[address])
            node.update_last_seen()

    def check_dead_nodes(self):
        """
        Check and remove nodes that are not alive anymore.
        """
        to_remove = [ node for node in self.nodes.values()
            if int(time.time()) > node.last_seen + self.max_time
        ]
        for node in to_remove:
            logger.info("Removing inactive node {}".format(node.uid))
            self.node_mapping.pop(node.resources['ip'])
            self.remove_node(node)
