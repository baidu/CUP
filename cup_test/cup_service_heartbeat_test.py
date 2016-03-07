#!/usr/bin/env python
# -*- coding: utf-8 -*
# #############################################################
#
#  Copyright (c) 2014 Baidu.com, Inc. All Rights Reserved
#
# #############################################################
"""
:authors:
    Guannan Ma maguannan@baidu.com @mythmgn
:create_date:
    2015/03/12
"""
import os
import sys
import time

_NOW_PATH = os.path.dirname(os.path.abspath(__file__)) + '/'
sys.path.insert(0, _NOW_PATH + '../')

import cup
from cup import net
from cup import unittest
from cup import log
from cup.services import heartbeat


class TestMyCase(unittest.CUTCase):
    """
    test class for cup
    """
    def __init__(self):
        super(self.__class__, self).__init__(
            b_logstd=False
        )
        log.info('Start to run ' + str(__file__))
        self._hb = heartbeat.HeartbeatService(
            judge_lost_in_sec=5, keep_lost=True
        )
        self._tmpfile = _NOW_PATH + '_tmp_file'

    def setup(self):
        """
        setup
        """

    @classmethod
    def _check(cls, key, devices, should_in=False):
        in_it = False
        for device in devices:
            if device.get_name() == key:
                in_it = True

        if should_in:
            assert in_it, 'key:%s should in devices' % key
        else:
            assert not in_it, 'key:%s should not in devices' % key

    def _lost_heartbeat(self):
        hostname = net.get_local_hostname()
        self._hb.activate(hostname, heartbeat.Device(hostname))
        lost_devices = self._hb.get_lost()
        self._check(hostname, lost_devices, should_in=False)
        time.sleep(6)
        lost_devices = self._hb.get_lost()
        self._check(hostname, lost_devices, should_in=True)
        self._hb.cleanup_oldlost(self._tmpfile)

    def test_run(self):
        """
        @author: maguannan
        """
        self._lost_heartbeat()

    def teardown(self):
        """
        teardown
        """
        cup.log.info('End running ' + str(__file__))
        os.unlink(self._tmpfile)

if __name__ == '__main__':
    cup.unittest.CCaseExecutor().runcase(TestMyCase())
# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
