#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: liushuxian(liushuxian)
"""
This module provides Jenkins object.
"""

import ast
import logging
import pprint

import cup
from cup.jenkinslib.internal import exception

INVALID_CHARS = ['\0', '\12', '\15']


class JenkinsBase(object):
    """Base object of all jenkins objects."""
    JENKINS_API = "api/python"

    def __init__(self, url, poll=True, static=False):
        """initialize

        Args:
            url: url address of jenkins objects.
            poll: poll out api info while initialization.
            static: never update info.
        """
        self._data = None
        self.url = url.rstrip('/')
        self.is_static = static
        if poll:
            self.poll()

    def __repr__(self):
        return """<%s.%s %s>""" % (self.__class__.__module__,
                                   self.__class__.__name__,
                                   str(self))

    def __str__(self):
        raise exception.NotImplementedMethod("__str__")

    def get_jenkins_obj(self):
        """get object of current jenkins."""
        raise exception.NotImplementedMethod("get_jenkins_obj")

    def poll(self, tree=None):
        """poll out api info."""
        # never update info in static mode
        if self.is_static and self._data is not None:
            return self._data

        data = self._poll(tree=tree)
        if not tree:
            self._data = data
        return data

    def _poll(self, tree=None):
        """poll out api info."""
        url = self.python_api_url(self.url)
        return self.get_data(url, tree=tree)

    def pprint(self):
        """print all the data of this object."""
        return pprint.pprint(self._data)

    def get_data(self, url, params=None, tree=None):
        """get data by url."""
        requester = self.get_jenkins_obj().requester
        if tree:
            if not params:
                params = {'tree': tree}
            else:
                params.update({'tree': tree})

        response = requester.get(url, params)
        if response.status_code != 200:
            if response.status_code == 404 and url.endswith(self.JENKINS_API):
                # if url is python api, and response status code is 404,
                # it means current jenkins server does not support this api.
                raise exception.UnsupportedAPI(url)
            elif response.status_code == 401:
                # unauthorized error, username or password is invalid
                raise exception.UnauthorizedError(
                    response.url, "GET", 401,
                    msg="username or password is invalid")
            logging.error("fail to request at %s with params: %s %s",
                          url, params, tree if tree else '')
            raise exception.InvalidRequestStatus(response.url, "GET", response.status_code)

        # try to parse original api info
        try:
            return ast.literal_eval(response.text)
        except Exception:
            pass

        # replace invalid chars
        api_info = response.text
        for char in INVALID_CHARS:
            if char in api_info:
                api_info = api_info.replace(char, '')

        # parse api info again
        try:
            return ast.literal_eval(api_info)
        except Exception:
            logging.exception('Inappropriate content found at %s', url)
            raise exception.Error('Cannot parse %s' % response.content)

    @classmethod
    def python_api_url(cls, url):
        """generate python api of url."""
        if url.endswith(cls.JENKINS_API):
            return url
        else:
            return "%s/%s" % (url.rstrip("/"), cls.JENKINS_API)

