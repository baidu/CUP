#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    unittest for cup.services.buffers
"""


import os
import sys
import logging

_TOP = os.path.dirname(os.path.abspath(__file__)) + '/../'
sys.path.insert(0, _TOP)

from cup.services import buffers
from cup import unittest

class CTestServiceBuffer(unittest.CUTCase):
    """
    service buffer
    """
    def __init__(self):
        super(self.__class__, self).__init__()
        self._buffpool = buffers.BufferPool(
            buffers.MEDIUM_BLOCK_SIZE,
            102400,
        )

    def setup(self):
        """
        setup
        """
        pass

    def teardown(self):
        """
        teardown
        """
        pass

    def test_run(self):
        """test_run"""
        ret, buff = self._buffpool.allocate(102401)
        unittest.assert_eq(ret, False)

        ret, buff = self._buffpool.allocate(10)
        unittest.assert_eq(ret, True)
        # pylint: disable=W0212
        unittest.assert_eq(self._buffpool._used_num, 10)
        unittest.assert_eq(self._buffpool._free_num, 102390)
        ret = buff.set('a' * 10 * buffers.MEDIUM_BLOCK_SIZE)
        unittest.assert_eq(ret[0], True)
        ret = buff.set('a' * (10 * buffers.MEDIUM_BLOCK_SIZE + 1))
        unittest.assert_ne(ret[0], True)
        self._buffpool.deallocate(buff)
        # pylint: disable=W0212
        unittest.assert_eq(self._buffpool._used_num, 0)
        unittest.assert_eq(self._buffpool._free_num, 102400)
        unittest.assert_eq(len(self._buffpool._free_list), 102400)
        unittest.assert_eq(len(self._buffpool._used_dict), 0)


if __name__ == '__main__':
    unittest.CCaseExecutor().runcase(CTestServiceBuffer())

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
