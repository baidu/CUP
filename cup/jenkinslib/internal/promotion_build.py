#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: liushuxian(liushuxian)
"""
This module provides PromotionBuild object.
"""

import contextlib
import logging
import time

from cup.jenkinslib.internal import base
from cup.jenkinslib.internal import exception
from cup.jenkinslib.internal import utils


class PromotionBuild(base.JenkinsBase):
    """Represents a promotion build."""
    def __init__(self, url, build_number, promotion, depth=None):
        """initialize PromotionBuild object

        Args:
            url: url of promotion build.
            build_number: build number.
            promotion: Promotion object.
            depth: set param 'depth' for jenkins api,
                   the more deeper it is, the more data you can get back.
        """
        self.build_number = build_number
        self.promotion = promotion
        self.depth = depth
        super(PromotionBuild, self).__init__(url, static=promotion.is_static)

    def get_jenkins_obj(self):
        """get object of current jenkins."""
        return self.promotion.job.jenkins

    def _poll(self, tree=None):
        """poll out api info.

        Add param 'depth', so we can get more information of \
        upstream and downstream.
        """
        url = self.python_api_url(self.url)
        params = {} if self.depth is None else {'depth': self.depth}
        return self.get_data(url, params=params, tree=tree)

    def __str__(self):
        return self._data['fullDisplayName']

    @property
    def name(self):
        """get build name."""
        return str(self)

    @property
    def number(self):
        """get build number."""
        return self._data["number"]

    @property
    def job_build_number(self):
        """get build number of target job build."""
        return self._data["target"]["number"]

    @property
    def job_build(self):
        """get Build object of target job build."""
        return self.promotion.job[self.job_build_number]

    @property
    def description(self):
        """get description of build if exists, otherwise None.

        Returns:
            description info of this build, encoding in utf-8.
            return None if not exists.
        """
        return self._data["description"]

    @description.setter
    def description(self, description=""):
        """submit description to this build.

        Args:
            description: description content, should encode in utf-8.
        """
        url = "%s/submitDescription" % self.url
        data = {"description": description}
        self.get_jenkins_obj().requester. \
            post_and_confirm_status(url, data=data)
        # update info
        self._data["description"] = self.poll(tree="description")["description"]

    @property
    def result(self):
        """get build result."""
        return self._data["result"]

    @property
    def revision(self):
        """get latest revision, only support svn."""
        vcs = self._data['changeSet']['kind'] or "svn"
        if vcs != "svn":
            raise exception.UnknownVCS(vcs)

        max_revision = 0
        for info in self._data["changeSet"]["revisions"]:
            max_revision = max(info["revision"], max_revision)
        return max_revision

    @property
    def duration_ms(self):
        """get build duration(ms)."""
        return self._data["duration"]

    @property
    def duration(self):
        """get build duration(s)."""
        return int(self.duration_ms / 1000)

    @property
    def is_success(self):
        """check build is success or not, return False if is running."""
        return not self.is_running and self._data["result"] == utils.STATUS_SUCCESS

    @property
    def is_running(self):
        """check build is running or not."""
        data = self.poll(tree='building')
        return data.get("building", False)

    def block(self):
        """block until this build stop running.

        Do not use this method too often,
        because it will request jenkins server every second.
        """
        if self.is_static:
            raise exception.ImappropriateMethodInStaticMode("block")
        while self.is_running:
            time.sleep(1)

        # update info
        self.poll()

    def block_until_complete(self, delay=15, timeout=None):
        """block until this build stop running.

        Args:
            delay: check status every `delay` seconds, default is 15s.
            timeout: wait `timeout` seconds at most, default is forever.

        Returns:
            True if stopped, False if still running.
        """
        if self.is_static:
            raise exception.ImappropriateMethodInStaticMode("block_until_complete")

        stime = time.time()
        while self.is_running:
            waited = time.time() - stime
            logging.info("waited %is for %s to complete" % (waited, str(self)))
            if timeout is not None and timeout < waited:
                raise exception.RunTimeout("wait %is > %is, timeout!" % (waited, timeout))

            time.sleep(delay)

        # update info
        self.poll()
        return True

    @property
    def user_name(self):
        """get name of user who invoke this build if exists, otherwise None."""
        try:
            return self.actions["causes"][0]["userName"]
        except KeyError:
            return None

    @property
    def cause_description(self):
        """get short description of causes."""
        try:
            return self.actions["causes"][0]["shortDescription"]
        except KeyError:
            return ""

    @property
    def is_started_by_timer(self):
        """check if is started by timer."""
        return self.cause_description.startswith("Started by timer")

    @property
    def is_started_by_user(self):
        """check if is started by user."""
        return self.cause_description.startswith("Started by user")

    @property
    def is_started_by_upstream_project(self):
        """check if is started by upstream project."""
        return self.cause_description.startswith("Started by upstream project")

    @property
    def is_started_by_scm_change(self):
        """check if is started by an SCM change."""
        return self.cause_description.startswith("Started by an SCM change")

    @property
    def actions(self):
        """get actions of build."""
        all_actions = {}
        for dct_action in self._data["actions"]:
            if dct_action:
                all_actions.update(dct_action)
        return all_actions

    @property
    def causes(self):
        """get causes of build, empty causes will be ignored."""
        all_causes = []
        for dct_action in self._data["actions"]:
            if dct_action is None:
                continue
            causes = dct_action.get("causes")
            if causes:
                all_causes.extend(causes)
        return all_causes

    @property
    def timestamp(self):
        """get build timestamp."""
        return self._data["timestamp"] / 1000.0

    @property
    def console(self):
        """get text console of build."""
        url = "%s/logText/progressiveText?start=0" % self.url
        with contextlib.closing(self.get_jenkins_obj().requester.get(url)) as fd:
            return fd.content

    def stop(self):
        """Stops the build execution if it's running."""
        if self.is_running:
            url = "%s/stop" % self.url
            self.get_jenkins_obj().requester.post_and_confirm_status(url, data='')

            # update info
            self.poll()
            return True
        return False

