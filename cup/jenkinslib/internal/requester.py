#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: liushuxian(liushuxian)
"""
This module provides some requester to access jenkins.
"""

import requests

from cup.jenkinslib.internal import exception


class Requester(object):
    """A class which help you access jenkins."""
    VALID_STATUS_CODES = [200]

    def __init__(self, username=None, password=None):
        """initialize Requester object."""
        self.username = username
        self.password = password

    def get(self, url, params=None, headers=None, allow_redirects=True):
        """request url in GET method.

        Returns:
            Response object.
        """
        requests_kwargs = self.__build_request(params=params, headers=headers,
                                               allow_redirects=allow_redirects)
        try:
            return requests.get(url, **requests_kwargs)
        except requests.RequestException as err:
            raise exception.RequestError(url, "GET", err=err)

    def post(self, url, params=None, data=None, files=None, headers=None, allow_redirects=True):
        """request url in POST method.

        Returns:
            Response object.
        """
        requests_kwargs = self.__build_request(params=params, headers=headers,
                                               data=data, files=files,
                                               allow_redirects=allow_redirects)
        try:
            return requests.post(url, **requests_kwargs)
        except requests.RequestException as err:
            raise exception.RequestError(url, "POST", err=err)

    def get_and_confirm_status(self, url, params=None, headers=None, valid=None):
        """request url in GET method, and check status code.

        Returns:
            Response object.
        """
        valid = valid or self.VALID_STATUS_CODES
        response = self.get(url, params, headers)
        if response.status_code not in valid:
            if response.status_code == 405:         # POST required
                raise exception.PostRequired(response.url, "GET", response.status_code)
            else:
                raise exception.InvalidRequestStatus(
                    response.url,
                    method="GET",
                    status=response.status_code,
                    msg="operation failed.",
                    response=response)
        return response

    def post_and_confirm_status(self, url, params=None, data=None, files=None,
                                headers=None, valid=None, allow_redirects=True):
        """request url in POST method, and check status code.

        Returns:
            Response object.
        """
        valid = valid or self.VALID_STATUS_CODES
        if not isinstance(data, (str, dict)):
            raise exception.ParamTypeError(
                "unexpected type of parameter 'data': %s. Expected (str, dict)" % type(data))

        if not headers and not files:
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        response = self.post(url, params, data, files, headers, allow_redirects)
        if response.status_code not in valid:
            raise exception.InvalidRequestStatus(
                response.url,
                method="POST",
                status=response.status_code,
                msg="operation failed.",
                response=response)
        return response

    def post_xml_and_confirm_status(self, url, params=None, data=None, valid=None):
        """request url in POST method with text/xml context, and check status code.

        Returns:
            Response object.
        """
        headers = {'Content-Type': 'text/xml'}
        return self.post_and_confirm_status(
            url, params=params, data=data, headers=headers, valid=valid)

    def __build_request(self, params=None, data=None, files=None, headers=None, **kwargs):
        """build kwargs for requests."""
        requests_kwargs = kwargs

        if self.username:
            requests_kwargs["auth"] = (self.username, self.password)

        if headers:
            if not isinstance(headers, dict):
                raise exception.ParamTypeError(
                    "unexpected type of parameter 'headers': %s. Expected (dict)" % type(data))
            requests_kwargs["headers"] = headers

        if params:
            if not isinstance(params, dict):
                raise exception.ParamTypeError(
                    "unexpected type of parameter 'params': %s. Expected (dict)" % type(data))
            requests_kwargs["params"] = params

        if data:
            if not isinstance(data, (str, dict)):
                raise exception.ParamTypeError(
                    "unexpected type of parameter 'data': %s. Expected (str, dict)" % type(data))
            requests_kwargs["data"] = data

        if files:
            requests_kwargs["files"] = files

        return requests_kwargs

