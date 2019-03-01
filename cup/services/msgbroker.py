#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    Msg Broker Service. Every component of a process can produce_msg.

    This msg broker feature is still exprimental. Do not use it in production
    until this comment is deleted.
"""


MSG_ERROR_DISK_ERROR = 1

__all__ = ['BrokerCenter', 'SystemErrmsgBroker']


MSG_TYPE_FATAL = 0
MSG_TYPE_WARN = 1


class BaseBroker(object):
    """
    Base Broker for a system
    """
    _name = None
    def __init__(self, name):
        self._name = name


class BrokerCenter(BaseBroker):
    """
    Errmsg broker center
    """
    def __init__(self, name):
        BaseBroker.__init__(self, name)

    def produce_msg(self, msg_type, extra_info, error):
        """register msg"""

    def comsume_msg(self, msg_type):
        """
        get msg_type from the broker center
        """


class SystemErrmsgBroker(BrokerCenter):
    """
    system errmsg broker, you can use it to determine whether
    exiting from the system is on the way
    """
    def __init__(self, name):
        BrokerCenter.__init__(self, name)

    def need_stop(self, path):
        """
        return True if the system registered on
            the path needs to stop immediately
        """

    def fatal_alert(self, path, msg, need_stop=True):
        """fatal alert systems"""

    def warnning_alert(self, path, msg):
        """
        warnning alert
        """

    def register_msg(self, path, msgtype, msg):
        """register msg into the system"""

    def get_fatal_alerts(self, path):
        """
        get fatal alerts of the current running round
        """

    def clean_data(self, path, exclude_msgtypes=None):
        """
        clean data of the remaining data
        """

    def register_wakeup(self, path, msgtype, alert_cap_num, callfunc):
        """
        register wakeups.

        :param alert_cap_num:
            If alert_cap_num is 0, whenever a msg of msgtype is received,
            the callfunc will be called.
        :param msgtype:
            [msgbroker.FATAL|msgbroker.WARN]
        """

    def _wakeup(self, path, msgtype, alert_cap_num, callfunc):
        """
        wake up callfunc
        """

    def register_msgtype_callback(self, path, msg_type, callback_func):
        """
        register msgtype with callback functions
        """

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
