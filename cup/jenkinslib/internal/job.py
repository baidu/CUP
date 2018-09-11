#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: liushuxian(liushuxian)
"""
This module provides Job object.
"""

import json
import logging

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import cup
from cup.jenkinslib.internal import base
from cup.jenkinslib.internal import exception
from cup.jenkinslib.internal import queue


class Job(base.JenkinsBase):
    """Represents a job."""
    def __init__(self, url, name, jenkins):
        """initialize Job object.

        Args:
            url: url of job.
            name: name of job.
            job: Job object.
        """
        self.name = name
        self.jenkins = jenkins
        super(Job, self).__init__(url, static=jenkins.is_static)
        self._config = None         # element tree object of config
        self._config_text = None    # text of config
        self._promotions = None     # promotions object

    def get_jenkins_obj(self):
        """get object of current jenkins."""
        return self.jenkins

    def __str__(self):
        return self.name

    def invoke(self, block=False, build_params=None, cause=None, files=None, delay=15):
        """trigger a new build.

        Args:
            block: block until the new build stopped.
            build_params: trigger new build with params.
            cause: set cause info.
            files: send build params in files.
            delay: if `block` is True, check status every `delay` seconds.
        """
        if not isinstance(block, bool):
            raise exception.ParamTypeError("block")

        if build_params and not self.has_params:
            raise exception.BadParams("%s does not support parameters" % str(self))

        params = {}  # Via Get string

        # Either copy the params dict or make a new one.
        build_params = dict(build_params.items()) if build_params else {}

        if cause:
            build_params['cause'] = cause

        url = self.get_build_trigger_url(files)

        # Build require params as form fields and as Json.
        data = {'json': self.mk_json_from_build_parameters(build_params, files)}
        data.update(build_params)

        response = self.jenkins.requester.post_and_confirm_status(
            url,
            data=data,
            params=params,
            files=files,
            valid=[200, 201, 303],
            allow_redirects=False)

        redirect_url = response.headers['location']

        if not redirect_url.startswith("%s/queue/item" % self.jenkins.url):
            raise exception.BadValue("Not a Queue URL: %s" % redirect_url)

        qi = queue.QueueItem(redirect_url, self.jenkins)
        if block:
            qi.block_until_complete(delay=delay)
        return qi

    # set build same as invoke
    build = invoke

    @property
    def is_enabled(self):
        """check if job is enabled."""
        data = self.poll(tree='color')
        return data.get('color', None) != 'disabled'

    def disable(self):
        """disable job."""
        url = "%s/disable" % self.url
        return self.jenkins.requester.post(url, data='')

    def enable(self):
        """enable job."""
        url = "%s/enable" % self.url
        return self.jenkins.requester.post(url, data='')

    @property
    def is_queued(self):
        """check job is queued or not."""
        data = self.poll(tree='inQueue')
        return data.get('inQueue', False)

    @property
    def is_running(self):
        """check job is running or not."""
        try:
            return self.last_build.is_running
        except NoBuildData:
            logging.info("no build info for %s, assume not running" % str(self))
        return False

    @property
    def is_queued_or_running(self):
        """check job is queued/running or not."""
        return self.is_queued or self.is_running

    @property
    def upstream_job_names(self):
        """get list of upstream job names."""
        upstream_jobs = []
        try:
            for j in self._data['upstreamProjects']:
                upstream_jobs.append(j['name'])
        except KeyError:
            return []
        return upstream_jobs

    @property
    def upstream_jobs(self):
        """get list of upstream job objects."""
        upstream_jobs = []
        try:
            for j in self._data['upstreamProjects']:
                upstream_jobs.append(self.jenkins.get_job(j['name']))
        except KeyError:
            return []
        return upstream_jobs

    @property
    def downstream_job_names(self):
        """get list of downstream job names."""
        downstream_jobs = []
        try:
            for j in self._data['downstreamProjects']:
                downstream_jobs.append(j['name'])
        except KeyError:
            return []
        return downstream_jobs

    @property
    def downstream_jobs(self):
        """get list of downstream job objects."""
        downstream_jobs = []
        try:
            for j in self._data['downstreamProjects']:
                downstream_jobs.append(self.jenkins.get_job(j['name']))
        except KeyError:
            return []
        return downstream_jobs

    def _get_build_number(self, build_type):
        """get special build number by type.

        Args:
            build_type:
                firstBuild
                lastBuild
                lastStableBuild
                lastSuccessfulBuild
                lastCompletedBuild
                lastFailedBuild
        """
        data = self.poll(tree='%s[number]' % build_type)

        info = data.get(build_type)
        if not info:
            raise exception.NoBuildData(build_type)
        return info["number"]

    @property
    def first_build_number(self):
        """get number of first build."""
        return self._get_build_number("firstBuild")

    @property
    def last_build_number(self):
        """get number of last build."""
        return self._get_build_number("lastBuild")

    @property
    def last_stable_build_number(self):
        """get number of last stable build."""
        return self._get_build_number("lastStableBuild")

    @property
    def last_successful_build_number(self):
        """get number of last successful build."""
        return self._get_build_number("lastSuccessfulBuild")

    @property
    def last_completed_build_number(self):
        """get number of last completed build."""
        return self._get_build_number("lastCompletedBuild")

    @property
    def last_failed_build_number(self):
        """get number of last failed build."""
        return self._get_build_number("lastFailedBuild")

    @property
    def next_build_number(self):
        """get number of next build."""
        return self._data.get("nextBuildNumber", 0)

    @property
    def builds(self):
        """get container of all builds."""
        data = self.poll(tree='builds[number,url]')
        builds = data.get("builds", [])
        return dict((build["number"], build["url"]) for build in builds)

    def get_build(self, build_number, depth=None):
        """get build by number.

        Also support special build:
                firstBuild
                lastBuild
                lastStableBuild
                lastSuccessfulBuild
                lastCompletedBuild
                lastFailedBuild
        """
        # if build_number is not int, maybe it is like "lastStableBuild"
        if not isinstance(build_number, int):
            build_number = self._get_build_number(build_number)

        url = self.builds.get(build_number)
        if not url:
            if build_number >= self.next_build_number:
                raise exception.NoBuildData(build_number)
            else:
                raise exception.DeletedBuild(build_number)

        return self.jenkins.Build(url, build_number, job=self, depth=depth)

    @property
    def first_build(self):
        """get first build."""
        return self.get_build(self.first_build_number)

    @property
    def last_build(self):
        """get last build."""
        return self.get_build(self.last_build_number)

    @property
    def last_stable_build(self):
        """get last stable build."""
        return self.get_build(self.last_stable_build_number)

    @property
    def last_successful_build(self):
        """get last successful build."""
        return self.get_build(self.last_successful_build_number)

    @property
    def last_completed_build(self):
        """get last completed build."""
        return self.get_build(self.last_completed_build_number)

    @property
    def last_failed_build(self):
        """get last failed build."""
        return self.get_build(self.last_failed_build_number)

    def __getitem__(self, key):
        """get build by number.

        Suppport promotions.

        Also support special build:
                firstBuild
                lastBuild
                lastStableBuild
                lastSuccessfulBuild
                lastCompletedBuild
                lastFailedBuild
        """
        if key == "promotions":
            return self.promotions

        return self.get_build(key)

    def __contains__(self, build_number):
        """build exists or not."""
        return build_number in self.builds

    def __iter__(self):
        """iterator for builds."""
        builds = self.builds
        numbers = self.builds.keys()
        numbers.sort()
        return (self.jenkins.Build(builds[number], number, job=self) for number in numbers)

    @property
    def promotions(self):
        """get promotions of job."""
        if self._promotions is None:
            self._promotions = self.jenkins.Promotions(self)

        return self._promotions

    @property
    def config_text(self):
        """get config.xml text of job.

        Returns:
            config.xml text in Unicode type.
            You can encode it in 'utf-8' or 'gb18030'.
        """
        if self._config_text is not None:
            return self._config_text

        url = "%s/config.xml" % self.url
        response = self.jenkins.requester.get_and_confirm_status(url)
        self._config_text = response.text
        return self._config_text

    @config_text.setter
    def config_text(self, config):
        """update config by text.

        Args:
            config: str format of config.xml text.
        """
        config = str(config)
        url = "%s/config.xml" % self.url
        response = self.jenkins.requester.post(url, params={}, data=config)
        self._config_text = config
        self._config = None
        return self._config_text

    @property
    def config(self):
        """get config element tree object of job."""
        if self._config is not None:
            return self._config

        return ET.fromstring(self.config_text.encode('utf-8'))

    @config.setter
    def config(self, config):
        """update config by element tree object.

        Args:
            config: element tree object of config.
        """
        self.config_text = ET.tostring(config)
        return self.config

    @property
    def description(self):
        """get description of job."""
        return self._data["description"]

    @property
    def has_params(self):
        """check build has params or not."""
        return any("parameterDefinitions" in a for a in self._data["actions"] if a)

    def get_build_trigger_url(self, files):
        """get trigger url of job."""
        if files or not self.has_params:
            return "%s/build" % self.url
        return "%s/buildWithParameters" % self.url

    def get_delete_url(self):
        """get delete url of job."""
        return "%s/doDelete" % self.url

    def get_rename_url(self):
        """get rename url of job."""
        return "%s/doRename" % self.url

    @staticmethod
    def _mk_json_from_build_parameters(build_params, file_params=None):
        """make build parameters to json format."""
        if not isinstance(build_params, dict):
            raise exception.ParamTypeError("Build parameters must be a dict")

        build_p = [{'name': k, 'value': str(v)}
                   for k, v in sorted(build_params.items())]
        out = {'parameter': build_p}
        if file_params:
            file_p = [{'name': k, 'file': k}
                      for k in file_params.keys()]
            out['parameter'].extend(file_p)

        if len(out['parameter']) == 1:
            out['parameter'] = out['parameter'][0]

        return out

    @staticmethod
    def mk_json_from_build_parameters(build_params, file_params=None):
        """make build parameters to json format."""
        json_structure = Job._mk_json_from_build_parameters(
            build_params,
            file_params)
        json_structure['statusCode'] = "303"
        json_structure['redirectTo'] = "."
        return json.dumps(json_structure)

