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
    2014/04/05 17:23:06
:modify_date:

:description:

"""
from cup import log

ARROW_MASTER_DEFAULT_PARAMS = {
    'control': {
        # internal
        'queue_delay_exe_thdnum': 4,
        'queue_exec_thdnum': 3,
        'local_datadir': './data/',

        # default values which can be configure from outside
        'check_heartbeat_interval': 10,
        'judge_agent_dead_in_sec': 30,
        'keep_lost': 1,
    },
}

ARROW_AGENT_DEFAULT_PARAMS = {
    'control': {
        'heartbeat_interval': 10,
        'master_ip': '127.0.0.1',
        'master_port': '51100',
        'interface': 'eth1'
    },
    'log': {
        'path': './log/agent.log'
    }
}


MSG_TYPE2NUM = {
    'HEART_BEAT': 1,
    'RESOURCE_ACQUIRE': 2,
    'RESOURCE_RELEASE': 3,
    'ACK_OK': 4,
    'ACK_FAILURE': 5,
    'ACK_HEART_BEAT': 6
}


class ConfItemError(Exception):
    """conf item error"""
    def __init__(self, msg):
        """
        """


    def repr(self):
        """ repr the error msg """
        return self._msg


def check_and_load_existence(user_confdict, default_dict, key, required=False):
    """
    check if the conf item is required to be existent.
    Use default if it's not required and does not exist.
    Raise ConfItemError if it's required and does not exists
    """
    confitem = None
    try:
        # try user conf dict
        confitem = eval('user_confdict{0}'.format(key))
    except KeyError:
        log.debug('user conf does not have {0} in user_confdict'.format(key))

    if confitem is None:
        try:
            # try user conf dict
            confitem = eval('default_dict{0}'.format(key))
            log.info('{0} will use default value:{1}'.format(
                key, confitem)
            )
        except KeyError:
            log.warn('default conf does not have {0}'.format(key))
    if confitem is None and required:
        raise ConfItemError('{0} should exist'.format(key))
    return confitem

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
