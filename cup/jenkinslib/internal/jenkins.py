#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: liushuxian(liushuxian)
"""
This module provides Jenkins object.
"""

import os

import cup
import cup.jenkinslib.internal
from cup.jenkinslib.internal import artifacts
from cup.jenkinslib.internal import base
from cup.jenkinslib.internal import build
from cup.jenkinslib.internal import exception
from cup.jenkinslib.internal import job
from cup.jenkinslib.internal import jobs
from cup.jenkinslib.internal import promotion
from cup.jenkinslib.internal import promotion_build
from cup.jenkinslib.internal import promotions
from cup.jenkinslib.internal import node
from cup.jenkinslib.internal import nodes
from cup.jenkinslib.internal import label
from cup.jenkinslib.internal import requester


class Jenkins(base.JenkinsBase):
    """Represents a jenkins server."""

    Job = job.Job
    Jobs = jobs.Jobs
    Build = build.Build

    Promotion = promotion.Promotion
    Promotions = promotions.Promotions
    PromotionBuild = promotion_build.PromotionBuild

    Artifacts = artifacts.Artifacts
    FTPArtifacts = artifacts.FTPArtifacts

    Node = node.Node
    Nodes = nodes.Nodes
    Label = label.Label

    Requester = requester.Requester

    def __init__(self, url, username=None, password=None, static=False):
        """initialize Jenkins object.

        Args:
            url: url of jenkins server.
            username: username to login jenkins.
            password: password or API token of username.
            static: never update info.
        """
        self.username = username
        self.password = password
        self.requester = self.Requester(username, password)
        # host address of ftp server.
        # use self.enable_ftp() to set it before connecting to ftp server.
        self.ftp_host = None
        super(Jenkins, self).__init__(url, poll=static, static=static)

    def __str__(self):
        return "Jenkins server at %s" % self.url

    def get_jenkins_obj(self):
        """get object of current jenkins."""
        return self

    @property
    def jobs(self):
        """get container of all jobs."""
        return self.Jobs(self)

    def get_job(self, job_name):
        """get job by name."""
        return self.jobs[job_name]

    def has_job(self, job_name):
        """job exists or not."""
        return job_name in self.jobs

    def create_job(self, job_name, config):
        """create a new job.

        create a new job named 'job_name'.
        same as self.jobs['job_name'] = config.

        Args:
            job_name: name of new job.
            config: configure for new job, xml text.

        Returns:
            new job object.
        """
        return self.jobs.create(job_name, config)

    def rename_job(self, job_name, new_job_name):
        """rename a job.

        Args:
            job_name: name of a existing job.
            new_job_name: new job name.

        Returns:
            new job object.
        """
        return self.jobs.rename(job_name, new_job_name)

    def delete_job(self, job_name):
        """delete a job by name.

        Args:
            job_name: job name.
        """
        del self.jobs[job_name]

    def __getitem__(self, job_name):
        """get job by name."""
        return self.get_job(job_name)

    @property
    def nodes(self):
        """get nodes."""
        return self.Nodes(self)

    def get_node(self, node_name):
        """get node by name."""
        return self.nodes[node_name]

    def get_label(self, label):
        """get label by name."""
        return self.Label(label, self)

    def get_create_url(self):
        """url for creating job."""
        return "%s/createItem" % self.url

    def enable_ftp(self, host, username="", password="", port=0):
        """enable ftp server and set host, username, password, port."""
        self.ftp_host = host
        self.ftp_username = username
        self.ftp_password = password
        self.ftp_port = port

    @staticmethod
    def register_special_jenkins(url, cls):
        """register special jenkins.

        Args:
            url: url of jenkins server.
            cls: special jenkins class.
        """
        _url_to_jenkins[url.rstrip("/")] = cls
        _name_to_jenkins[cls.__name__] = cls

    @staticmethod
    def get_jenkins_by_name(name):
        """get special jenkins class by name.

        Args:
            name: name of jenkins server.

        Returns:
            special jenkins class or Jenkins.
        """
        return _name_to_jenkins.get(name, Jenkins)

    @staticmethod
    def get_jenkins_by_url(url):
        """get special jenkins class by url.

        Args:
            url: url of jenkins server.

        Returns:
            special jenkins class or Jenkins.
        """
        return _url_to_jenkins.get(url.rstrip("/"), Jenkins)

_url_to_jenkins = {}
_name_to_jenkins = {}

