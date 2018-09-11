#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: liushuxian(liushuxian)
"""
This module provides Promotions object.

Promotions is a container of Promotion.
"""

from cup.jenkinslib.internal import base
from cup.jenkinslib.internal import exception


class Promotions(base.JenkinsBase):
    """A container of Promotions objects."""
    def __init__(self, job, depth=None):
        """initialize Promotions object.

        Args:
            job: Job object.
            depth: set param 'depth' for jenkins api,
                   the more deeper it is, the more data you can get back.
        """
        self.job = job
        self.depth = depth
        url = "%s/promotion" % job.url
        super(Promotions, self).__init__(url, static=job.is_static)

    def get_jenkins_obj(self):
        """get object of current jenkins."""
        return self.job.jenkins

    def _poll(self, tree=None):
        """poll out api info.

        If there is no promotion, api will return 404, catch it and build empty data.
        """
        url = self.python_api_url(self.url)
        params = {} if self.depth is None else {'depth': self.depth}
        try:
            return self.get_data(url, params=params, tree=tree)
        except exception.UnsupportedAPI:
            return {}

    def __getitem__(self, promotion_name):
        """get promotion by name."""
        for row in self._data.get('processes', []):
            if row["name"] == promotion_name:
                return self.get_jenkins_obj().Promotion(row['url'], promotion_name, self.job)

        raise exception.UnknownPromotion(promotion_name)

    def __contains__(self, promotion_name):
        """promotion exists or not."""
        return promotion_name in self.keys()

    def __len__(self):
        """promotion num."""
        return len(self.keys())

    def __iter__(self):
        """iterator for job names."""
        return (row['name'] for row in self._data.get('processes', []))

    def iterkeys(self):
        """get all promotion name."""
        for row in self._data.get('processes', []):
            yield row['name']

    def keys(self):
        """get all promotion name."""
        return list(self.iterkeys())

