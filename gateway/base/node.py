"""
COT Service

Author: Tony Chi
Updated at: 2018-06
Content : Class for managed node. 
"""
# -*- coding: utf-8 -*-
import logging
import time

logger = logging.getLogger("pycots.gw.base.node")


class Node():
    """
    Class for managed nodes.
    """
    def __init__(self, uid, **default_resources):
        self.uid = uid
        self.last_seen = time.time()
        self.resources = default_resources

    def __eq__(self, other):
        return self.uid == other.uid

    def __gt__(self, other):
        return self.uid > other.uid

    def __repr__(self):
        return "Node <{}>".format(self.uid)

    def update_last_seen(self):
        self.last_seen = time.time()

    def set_resource_value(self, resource, value):
        if resource not in self.resources:
            self.resources.update({resource: value})
        else:
            self.resources[resource] = value

    def clear_resources(self):
        self.resources = {}
