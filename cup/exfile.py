#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    file related functions
"""
import os
import sys
import fcntl

from cup import err
from cup import decorators
from cup import platforms

if platforms.is_linux():
    import tempfile

__all__ = [
    'LockFile', 'FILELOCK_SHARED', 'FILELOCK_EXCLUSIVE',
    'FILELOCK_NONBLOCKING', 'FILELOCK_UNLOCK', 'TempFile'
]


FILELOCK_EXCLUSIVE = fcntl.LOCK_EX
FILELOCK_SHARED = fcntl.LOCK_SH
FILELOCK_NONBLOCKING = fcntl.LOCK_NB
FILELOCK_UNLOCK = fcntl.LOCK_UN


class LockFile(object):
    """
    lock file class
    """

    def __init__(self, fpath, locktype=FILELOCK_EXCLUSIVE):
        """
        exclusive lockfile, by default.

        Notice that the file CANNOT exist before you intialize a LockFile obj.
        Otherwise, it will raise cup.err.LockFileError

        :raise:
            cup.err.LockFileError if we encounter errors
        """
        self._fpath = fpath
        self._locktype = locktype
        self._fhandle = None
        try:
            # if FILELOCK_EXCLUSIVE == locktype:
            #     self._fhandle = os.open(
            #         self._fpath, os.O_CREAT|os.O_EXCL|os.O_RDWR
            #     )
            # else:
            self._fhandle = os.open(
                self._fpath, os.O_CREAT | os.O_RDWR
            )
        except IOError as error:
            raise err.LockFileError(error)
        except OSError as error:
            raise err.LockFileError(error)
        except Exception as error:
            raise err.LockFileError(
                'catch unkown error type:{0}'.format(error)
            )

    def __del__(self):
        """del the instance"""
        try:
            if self._fhandle is not None:
                os.close(self._fhandle)
        # pylint: disable=W0703
        except Exception as error:
            sys.stderr.write('failed to close lockfile:{0}, msg:{1}'.format(
                self._fpath, error)
            )
            sys.stderr.flush()

    @decorators.needposix
    def lock(self, blocking=True):
        """
        lock the file

        :param blocking:
            If blocking is True, will block there until cup gets the lock.
            True by default.

        :return:
            return False if locking fails

        :raise Exception:
            raise cup.err.LockFileError if blocking is False and
            the lock action failed
        """
        flags = 0x1
        if FILELOCK_SHARED == self._locktype:
            flags = FILELOCK_SHARED
        elif FILELOCK_EXCLUSIVE == self._locktype:
            flags = FILELOCK_EXCLUSIVE
        else:
            raise err.LockFileError('does not support this lock type')
        if not blocking:
            flags |= FILELOCK_NONBLOCKING
        ret = None
        try:
            ret = fcntl.flock(self._fhandle, flags)
        except IOError as error:
            raise err.LockFileError(error)
        except Exception as error:
            raise err.LockFileError(error)
        return ret

    def unlock(self):
        """unlock the locked file"""
        try:
            fcntl.flock(self._fhandle, FILELOCK_UNLOCK)
        except Exception as error:
            raise err.LockFileError(error)


class TempFile(object):
    """
    The temp file will be deleted immediately after the lifetime of it ends.

    You can use cup TempFile like the original Python File Object.

    ::

        tmp = TempFile('./', prefix='xxxx', suffix='.tmp')
        tmp.write / read /seek / etc
        tmp.close()
    """
    def __init__(self, filedir, prefix='', suffix=''):
        """
        :param filedir:
            temp file dir which contains the temp file

        :prefix:
            prefix of the temp filename

        :suffix:
            suffix of the file name. e.g. '.tmp'.
        """
        self._fdir = filedir
        self._fp = None
        self._prefix = prefix
        self._suffix = suffix

    def __enter__(self):
        """enter"""
        if platforms.is_linux():
            self._fp = tempfile.TemporaryFile(
                dir=self._fdir,
                prefix=self._prefix,
                suffix=self._suffix
            )
            return self._fp
        else:
            raise err.NotImplementedYet('TemporaryFile')

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        exit
        """
        if platforms.is_linux():
            self._fp.close()

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
