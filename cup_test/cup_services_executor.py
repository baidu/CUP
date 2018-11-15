#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    unittest for cup.services.executor
"""
import os
import sys
import time

_NOW_PATH = os.path.dirname(os.path.abspath(__file__)) + '/'
sys.path.insert(0, _NOW_PATH + '../')

import cup
from cup import unittest
from cup import log
from cup.services import executor


class TestMyCase(unittest.CUTCase):
    """
    test class for cup
    """
    def __init__(self):
        super(self.__class__, self).__init__(
            './test.log', log.DEBUG
        )
        log.info('Start to run ' + str(__file__))
        self._executor = executor.ExecutionService(
        )

    def setup(self):
        """
        setup
        """
        self._executor.run()
        self._info = time.time()

    def _change_data(self, data=None):
        self._info = time.time() + 100

    def test_run(self):
        """
        @author: maguannan
        """
        self._executor.delay_exec(5, self._change_data, 1)
        time.sleep(2)
        assert time.time() > self._info
        time.sleep(5)
        assert time.time() < self._info

    def teardown(self):
        """
        teardown
        """
        cup.log.info('End running ' + str(__file__))
        self._executor.stop()

if __name__ == '__main__':
    cup.unittest.CCaseExecutor().runcase(TestMyCase())

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent

