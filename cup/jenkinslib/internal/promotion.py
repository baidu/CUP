#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: liushuxian(liushuxian)
"""
This module provides Promotion object.
"""

import logging

from cup.jenkinslib.internal import base
from cup.jenkinslib.internal import exception


class Promotion(base.JenkinsBase):
    """Represents a promotion."""
    def __init__(self, url, name, job):
        """initialize Promotion object.

        Args:
            url: url of promotion.
            name: name of promotion.
            job: Job object.
        """
        self.name = name
        self.job = job
        super(Promotion, self).__init__(url, static=job.is_static)

    def get_jenkins_obj(self):
        """get object of current jenkins."""
        return self.job.jenkins

    def __str__(self):
        return self.name

    @property
    def is_queued(self):
        """check promotion is queued or not."""
        data = self.poll(tree='inQueue')
        return data.get('inQueue', False)

    @property
    def is_running(self):
        """check promotion is running or not."""
        try:
            return self.last_build.is_running
        except NoBuildData:
            logging.info("no build info for %s, assume not running" % str(self))
        return False

    @property
    def is_queued_or_running(self):
        """check promotion is queued/running or not."""
        return self.is_queued or self.is_running

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
            if build_number >= self.next_number:
                raise exception.NoBuildData(build_number)
            else:
                raise exception.DeletedBuild(build_number)

        return self.job.jenkins.PromotionBuild(url, build_number, promotion=self, depth=depth)

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

    def __getitem__(self, build_number):
        """get build by number.

        Also support special build:
                firstBuild
                lastBuild
                lastStableBuild
                lastSuccessfulBuild
                lastCompletedBuild
                lastFailedBuild
        """
        return self.get_build(build_number)

    @property
    def description(self):
        """get description of promotion."""
        return self._data["description"]

