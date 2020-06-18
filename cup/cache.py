#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    decorators related module
"""
import time
import collections
import contextlib

import cup
from cup.util import thread


class KvCache(object):
    """
    Key-Value Cache object

    When a k-v is hit, the expire_sec will be expanded to 2 * (expire_sec)
    """
    _STAT = collections.namedtuple(
        'kvcache_stat', 'key_num expired_num'
    )

    def __init__(self, maxsize=0):
        # store kv_data
        self._kv_data = {}
        self._lock = thread.RWLock()

    @contextlib.contextmanager
    def _lock_release(self, b_rw_lock):
        if b_rw_lock is True:
            self._lock.acquire_writelock()
        else:
            self._lock.acquire_readlock()
        try:
            yield
        # pylint: disable=W0703
        except Exception as error:
            cup.log.warn('something happend in cache:%s' % error)
        finally:
            if b_rw_lock is True:
                self._lock.release_writelock()
            else:
                self._lock.release_readlock()

    def set(self, kvdict, expire_sec=None):
        """
        set cache with kvdict

        :param kvdict:
            kvdict is a dict that contains your cache.
        :param expire_sec:
            if expire_sec is None, the cache will never expire.
        """
        expire_value = None
        if expire_sec is not None:
            expire_value = expire_sec + time.time()
        with self._lock_release(b_rw_lock=True):
            for key in kvdict:
                if key in self._kv_data:
                    cup.log.debug('Key:%s of KvCache updated.' % key)
                self._kv_data[key] = (kvdict[key], expire_value)

    def get(self, key):
        """
        Get your cache with key.
        If the cache is expired, it will return None.
        If the key does not exist, it will return None.
        """
        with self._lock_release(b_rw_lock=False):
            if key not in self._kv_data:
                return None
            value, expire_sec = self._kv_data[key]
            if expire_sec is not None and time.time() > expire_sec:
                return None
            else:
                cup.log.debug('key:%s of kvCache fetched.' % key)
                self._kv_data[key] = (value, 2 * expire_sec)
                return value
        return None

    def _get_expired_keys(self):
        """get expired key of keys"""
        expired_keys = []
        keys = self._kv_data.keys()
        for key in keys:
            expire_sec = self._kv_data[key][1]
            if expire_sec is not None and time.time() > expire_sec:
                expired_keys.append(key)
        return expired_keys

    def cleanup_expired(self):
        """
        Delete all expired items
        """
        expired_keys = None
        with self._lock_release(b_rw_lock=True):
            expired_keys = self._get_expired_keys()
            for key in expired_keys:
                del self._kv_data[key]
                cup.log.debug('key:%s cleaned up' % key)
        return expired_keys

    def get_expired(self):
        """
        :return:
            A dict.
            Return expired items. Return type is a dict (
                {
                    'key' : (value, expire_time)
                }
            )
        """
        kvlist = {}
        with self._lock_release(b_rw_lock=False):
            keys = self._get_expired_keys()
            for key in keys:
                value = self._kv_data[key]
                kvlist[key] = (value)
        return kvlist

    def stat(self):
        """
        :return:
            a tuple with (item_num, expired_num)
        """
        with self._lock_release(b_rw_lock=False):
            key_num = len(self._kv_data)
            expired_num = len(self._get_expired_keys())
        return (key_num, expired_num)

    def clear(self):
        """
        remove all kv cache inside.
        """
        with self._lock_release(b_rw_lock=True):
            del self._kv_data
            self._kv_data = {}

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
