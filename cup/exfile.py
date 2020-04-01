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
import copy
import shutil


from cup import err
from cup import decorators
from cup import platforms

__all__ = [
    'LockFile', 'FILELOCK_SHARED', 'FILELOCK_EXCLUSIVE',
    'FILELOCK_NONBLOCKING', 'FILELOCK_UNLOCK', 'mk_newnode', 'safe_rmtree',
    'safe_delete'
]


CANNOT_DEL_PATHLIST = [
    '/',
    '/proc',
    '/boot',
    '/sys'
]


if platforms.is_linux() or platforms.is_mac():
    import fcntl
    FILELOCK_EXCLUSIVE = fcntl.LOCK_EX
    FILELOCK_SHARED = fcntl.LOCK_SH
    FILELOCK_NONBLOCKING = fcntl.LOCK_NB
    FILELOCK_UNLOCK = fcntl.LOCK_UN
elif platforms.is_windows():
    import msvcrt

    def file_size(fobj):
        """win file size"""
        return os.path.getsize(os.path.realpath(fobj.name) )

    def win_lockfile(fobj, blocking=True):
        """win lock file"""
        flags = msvcrt.LK_RLCK
        if not blocking:
            flags = msvcrt.LK_NBRLCK
        msvcrt.locking(fobj.fileno(), flags, file_size(fobj))

    def win_unlockfile(fobj):
        """win unlock file"""
        msvcrt.locking(fobj.fileno(), msvcrt.LK_UNLCK, file_size(fobj))


class LockFile(object):
    """
    lock file class
    """

    def __init__(self, fpath, locktype=FILELOCK_EXCLUSIVE):
        """
        exclusive lockfile, by default.

        Notice that the file CANNOT exist before you intialize a LockFile obj.
        Otherwise, it will raise cup.err.LockFileError

        Plz notice that on windows, cup only support EXCLUSIVE lock

        :raise:
            cup.err.LockFileError if we encounter errors
        """
        self._fpath = fpath
        self._locktype = locktype
        self._fhandle = None
        try:
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
        if platforms.is_linux():
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
        elif platforms.is_windows():
            win_lockfile(self._fhandle, blocking)

    def unlock(self):
        """unlock the locked file"""
        if platforms.is_linux():
            try:
                fcntl.flock(self._fhandle, FILELOCK_UNLOCK)
            except Exception as error:
                raise err.LockFileError(error)
        elif platforms.is_windows():
            win_unlockfile(self._fhandle)

    def filepath(self):
        """
        return filepath
        """
        return self._fpath



def mk_newnode(abspath, check_exsistence=False):
    """
    :param abspath:
        plz use absolute path. Not relative path

    :param check_exsistence:
        if True, will check if the abspath existence (
        raise IOError if abspath exists)
    :raise Exception:
        IOError
    """
    if check_exsistence:
        if os.path.exists(abspath):
            raise IOError('{0} already exists'.format(abspath))
    with open(abspath, 'w+') as _:
        pass


def safe_rmtree(abspath, not_del_list=None):
    """
    :param abspath:
        pass in absolute path
    :param not_del_list:
        cannot del path list

    :raise Exception:
        ValueError, if abspath is in exfile.CANNOT_DEL_PATHLIST or not_del_list
        IOError, if cup encounters any problem
    """
    normpath = os.path.normpath(abspath)
    tmplist = copy.deepcopy(CANNOT_DEL_PATHLIST)
    if not_del_list is not None:
        tmplist.extend(not_del_list)
    if abspath in tmplist:
        raise ValueError(
            'cannot delete path in {0}'.format(tmplist)
        )
    shutil.rmtree(normpath)


def safe_delete(abspath, not_del_list):
    """
    :param abspath:
        pass in absolute path
    :param not_del_list:
        cannot del path list

    :raise Exception:
        ValueError, if abspath is in exfile.CANNOT_DEL_PATHLIST or not_del_list
        IOError, if cup encounters any problem
    """
    if os.path.isdir(abspath):
        safe_rmtree(abspath, not_del_list)
    else:
        os.unlink(abspath)

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
