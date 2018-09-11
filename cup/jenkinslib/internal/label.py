#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: liushuxian(liushuxian)
"""
This module provides Label object.

Label is a container of Node.
"""

from cup.jenkinslib.internal import base
from cup.jenkinslib.internal import exception


class Label(base.JenkinsBase):
    """A container of Node objects."""
    def __init__(self, label, jenkins):
        """initialize Label object."""
        self.label = str(label)
        url = "%s/label/%s" % (jenkins.url, self.label)
        self.jenkins = jenkins
        super(Label, self).__init__(url, static=jenkins.is_static)

    def get_jenkins_obj(self):
        """get object of current jenkins."""
        return self.jenkins

    def __str__(self):
        return "Label %s @ %s" % (self.label, self.jenkins.url)

    @property
    def is_online(self):
        """label is online or not."""
        return not self.poll(tree="offline")["offline"]

    @property
    def busy_node_num(self):
        """busy node num."""
        return self.poll(tree="busyExecutors")["busyExecutors"]

    def iterkeys(self):
        """get all node name."""
        for item in self._data["nodes"]:
            yield item["nodeName"]

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

    @property
    def node_num(self):
        """get node num."""
        return len(self.keys())

    def __len__(self):
        """get node num."""
        return self.node_num

    @property
    def tied_jobs(self):
        """get all tied job name on this label."""
        return list(self.tied_jobs_iterator)

    @property
    def tied_jobs_iterator(self):
        """get all tied job name on this label."""
        for item in self._data["tiedJobs"]:
            yield item["name"]

    @property
    def tied_job_num(self):
        """get tied job num."""
        return len(self.tied_jobs)

    def get_node_url(self, node_name):
        """get url of node.

        Args:
            node_name: node name.

        Returns:
            node url.
        """
        if node_name.lower() == "master":
            return "%s/computer/(%s)" % (self.jenkins.url, node_name)
        else:
            return "%s/computer/%s" % (self.jenkins.url, node_name)

