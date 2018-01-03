#!/usr/bin/env python
# -*- coding: utf-8 -*
# #############################################################
#
#  Copyright (c) 2014 Baidu.com, Inc. All Rights Reserved
#
# #############################################################
"""
:authors:
    Guannan Ma maguannan @mythmgn
:create_date:
    [% date('%c') %]
:modify_date:

:description:

"""

class ServiceStatus(object):
    """
    BaseService for arrow
    """
    INITED = 0
    RUNNING = 1
    STOPPING = 2
    STOPPED = 3

    def __init__(self):
        self._statuslist = [
            self.INITED, self.RUNNING, self.STOPPING, self.STOPPED
        ]
        self._status = self.INITED

    def set_status(self, status):
        """set status, return true if set successfully"""
        if status not in self._statuslist:
            return False
        else:
            self._status = status
            return True

    def get_status(self):
        """get status"""
        return self._status


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
