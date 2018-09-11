#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: liushuxian(liushuxian)
"""
This module provides Node object.
"""

from cup.jenkinslib.internal import base


class Node(base.JenkinsBase):
    """Represents a node."""
    def __init__(self, url, name, jenkins):
        """initialize Node object.

        Args:
            url: url of node.
            name: name of node.
            node: Node object.
        """
        self.name = name
        self.jenkins = jenkins
        super(Node, self).__init__(url, static=jenkins.is_static)

    def get_jenkins_obj(self):
        """get object of current jenkins."""
        return self.jenkins

    def __str__(self):
        return self.name

    @property
    def is_online(self):
        """node is online or not."""
        return not self.poll(tree="offline")["offline"]

    @property
    def is_temporarily_offline(self):
        """node is temporarily offline or not."""
        return not self.poll(tree="temporarilyOffline")["temporarilyOffline"]

    @property
    def is_idle(self):
        """node is idle or not."""
        return self.poll(tree="idle")["idle"]

