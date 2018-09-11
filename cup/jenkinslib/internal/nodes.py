#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: liushuxian(liushuxian)
"""
This module provides Nodes object.

Nodes is a container of Node.
"""

from cup.jenkinslib.internal import base
from cup.jenkinslib.internal import exception


class Nodes(base.JenkinsBase):
    """A container of Node objects."""
    def __init__(self, jenkins):
        """initialize Nodes object."""
        url = "%s/computer" % jenkins.url
        self.jenkins = jenkins
        super(Nodes, self).__init__(url, static=jenkins.is_static)

    def get_jenkins_obj(self):
        """get object of current jenkins."""
        return self.jenkins

    def __str__(self):
        return "Nodes @ %s" % self.jenkins.url

    def iterkeys(self):
        """get all node name."""
        for item in self._data["computer"]:
            yield item["displayName"]

    def keys(self):
        """get all node name."""
        return list(self.iterkeys())

    def __contains__(self, node_name):
        """node exists or not."""
        return node_name in self.keys()

    def __iter__(self):
        """iterator for node names."""
        return (node_name for node_name in self.iterkeys())

    def iteritems(self):
        """get all nodes."""
        for node_name in self.iterkeys():
            node_url = self.get_node_url(node_name)
            yield node_name, self.jenkins.Node(node_url, node_name, self.jenkins)

    def __getitem__(self, node_name):
        """get node by name."""
        for key in self.iterkeys():
            if key == node_name:
                node_url = self.get_node_url(node_name)
                return self.jenkins.Node(node_url, node_name, self.jenkins)

        raise exception.UnknownNode(node_name)

    def __len__(self):
        """get node num."""
        return len(self.keys())

    def get_node_url(self, node_name):
        """get url of node.

        Args:
            node_name: node name.

        Returns:
            node url.
        """
        if node_name.lower() == "master":
            return "%s/(%s)" % (self.url, node_name)
        else:
            return "%s/%s" % (self.url, node_name)

