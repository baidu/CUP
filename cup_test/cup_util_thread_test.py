#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    unittest for cup.util.thread
"""

from cup.util import thread


# for RWLock unittest
def test_rw_rw_lock():
    lock = thread.RWLock()
    lock.acquire_writelock(None)
    try:
        lock.acquire_writelock(1)
    except RuntimeError as error:
        pass
    try:
        lock.acquire_readlock(1)
    except RuntimeError as error:
        pass
    lock.release_writelock()


def test_rd_rw_lock():
    lock = thread.RWLock()
    lock.acquire_readlock(None)
    lock.acquire_readlock(1)
    lock.acquire_readlock(2)
    try:
        lock.acquire_writelock(1)
    except RuntimeError as error:
        pass
    lock.release_readlock()
    lock.release_readlock()
    lock.release_readlock()
    try:
        lock.acquire_writelock(1)
    except RuntimeError as error:
        assert False
    lock.release_writelock()

#vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
