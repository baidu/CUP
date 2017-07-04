#!/usr/bin/env python
# -*- coding: utf-8 -*
# #############################################################
#
#  Copyright (c) Baidu.com, Inc. All Rights Reserved
#
# #############################################################
"""
:authors:
    Guannan Ma maguannan @mythmgn
:description:
    Msg Broker Service. Every component of a process can produce_msg
"""
from cup import decorators


MSG_ERROR_DISK_ERROR = 1

__all__ = ['BrokerCenter']


class BaseBroker(object):
    """
    Base Broker for a system
    """


@decorators.Singleton
class BrokerCenter(BaseBroker):
    """
    Errmsg broker center
    """
    def __init__(self, name):
        self._name = name

    def produce_msg(self, msg_type, extra_info, error):
        """register msg"""

    def comsume_msg(self, msg_type):
        """
        get msg_type from the broker center
        """


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
