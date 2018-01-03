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
    2016/04/05 17:23:06
:modify_date:

:description:

"""

# from cup.net.async import msg
from cup.services import heartbeat


class BufferSerilizer(object):
    """
    buffer serializer
    """
    def __init__(self, buff):
        pass

    def serialize(self):
        """serialize the buffer"""

    def deserialize(self, buff):
        """deserialize the buffer"""


class AgentResource(heartbeat.LinuxHost):
    """
    resource
    """
    def __init__(self, init_this_host=False, iface='eth0'):
        super(self.__class__).__init__(self, init_this_host, iface)


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
