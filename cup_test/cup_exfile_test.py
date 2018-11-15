#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
:authors:
    Guannan Ma maguannan @mythmgn
:description:

"""
import os
import sys

_TOP = os.path.dirname(os.path.abspath(__file__)) + '/../'
sys.path.insert(0, _TOP)

from cup import err
from cup import exfile
from cup import unittest


LOCK_FILE = './.file_test.lock'


def _cleanup():
    """cleanup things"""
    if os.path.exists(LOCK_FILE):
        os.unlink(LOCK_FILE)


def setup():
    """setup"""
    _cleanup()


def teardown():
    """teardown"""
    _cleanup()


def test_sharedlockfile():
    """test lockfile"""
    # shared lockfile
    _lockfile = exfile.LockFile(LOCK_FILE, exfile.FILELOCK_SHARED)
    ret = _lockfile.lock(blocking=False)
    print ret
    _lockfile2 = exfile.LockFile(LOCK_FILE, exfile.FILELOCK_SHARED)
    ret = _lockfile2.lock(blocking=False)
    print ret
    _lockfile3 = exfile.LockFile(LOCK_FILE, exfile.FILELOCK_EXCLUSIVE)
    unittest.expect_raise(
        _lockfile3.lock,
        err.LockFileError,
        False
    )


def test_exclusive_lockfile():
    """test exclusive lockfile"""
    # shared lockfile
    _lockfile = exfile.LockFile(LOCK_FILE, exfile.FILELOCK_EXCLUSIVE)
    _lockfile.lock()
    _lockfile2 = exfile.LockFile(LOCK_FILE, exfile.FILELOCK_EXCLUSIVE)
    unittest.expect_raise(
        _lockfile2.lock,
        err.LockFileError,
        blocking=False
    )
    _lockfile3 = exfile.LockFile(LOCK_FILE, exfile.FILELOCK_SHARED)
    unittest.expect_raise(
        _lockfile3.lock,
        err.LockFileError,
        blocking=False
    )
# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
