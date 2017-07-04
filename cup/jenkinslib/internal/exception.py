# -*- coding: utf-8 -*-
################################################################################
#
# Copyright (c) 2015 Baidu.com, Inc. All Rights Reserved
#
################################################################################
"""
This module defines all excptions of this project.

Authors: liushuxian(liushuxian)
Date:    2015/01/20
"""


class Error(Exception):
    """Base exception of jenkins module."""
    pass


class NotRunningOnJenkins(Error):
    """Cueent environment is not on jenkins slave node."""
    pass


class BadParam(Error):
    """Inappropriate params."""
    pass


class ParamTypeError(TypeError, BadParam):
    """Param type is error."""
    pass


class BadValue(ValueError, Error):
    """Value is error."""
    pass


class RunTimeout(RuntimeError, Error):
    """Run timeout."""
    pass


class NotFound(Error):
    """Resource not found."""
    pass


class UnknownNode(KeyError, NotFound):
    """Node not found."""
    pass


class UnknownJob(KeyError, NotFound):
    """Job not found."""
    pass


class UnknownPromotion(KeyError, NotFound):
    """Promotion not found."""


class UnknownQueueItem(KeyError, NotFound):
    """QueueItem not found."""
    pass


class NotBuiltYet(KeyError, NotFound):
    """Task still in queue, not built yet."""
    pass


class NoBuildData(KeyError, NotFound):
    """Build data not exist."""
    pass


class DeletedBuild(NoBuildData):
    """Build data not exist because it is deleted."""
    pass


class NoArtifacts(KeyError, NotFound):
    """Artifacts data not exist."""


class JenkinsAPIError(Error):
    """something wrong with jenkins api."""
    pass


class UnsupportedAPI(NotFound, JenkinsAPIError):
    """Jenkins api not supported on this jenkens server version."""
    pass


class NotStopYet(RuntimeError, Error):
    """Task still running, not stopped yet."""
    pass


class ImappropriateMethod(Error):
    """Method is imappropriate."""
    pass


class ImappropriateMethodInStaticMode(ImappropriateMethod):
    """Method should not be called in static mode."""
    pass


class NotImplementedMethod(NotImplementedError, ImappropriateMethod):
    """Method is not implemented."""
    pass


class OSIOError(OSError, IOError, Error):
    """OS or IO errors."""
    pass


class RequestError(OSIOError):
    """Something error while access jenkins."""
    def __init__(self, url, method=None, status=None, msg=None, err=None, response=None):
        self.url = url
        self.method = method
        self.status = status
        self.msg = msg
        self.err = err
        self.response = response

    def __str__(self):
        err_msg = ""
        if self.msg:
            err_msg = ", error: %s" % self.msg
        elif self.err:
            err_msg = ", error: %s" % self.err

        return "request failed. url={url}, method={method}, status={status}{err_msg}".format(
            url = self.url,
            method=self.method,
            status=self.status,
            err_msg=err_msg)


class PostRequired(RequestError):
    """Jenkins API requires POST and not GET."""
    pass


class InvalidRequestStatus(RequestError):
    """Request status code is invalid."""
    pass


class UnauthorizedError(InvalidRequestStatus):
    """Username or password is invalid."""
    pass


class NetworkError(OSIOError):
    """Something wrong on network."""
    pass


class FtpError(NetworkError):
    """Something wrong with ftp."""
    pass


