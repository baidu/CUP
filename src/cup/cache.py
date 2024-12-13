#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    decorators related module
"""
import time
import uuid
try:
    import queue
except ImportError:
    import Queue as queue # type: ignore
import collections
import contextlib

import cup
from cup import log
from cup import err
from cup.util import thread


__all__ = ['CacheFull', 'KVCache', 'KvCache']


class CacheFull(err.BaseCupException):
    """
    CacheFull for cache.KvCache

    """
    def __init__(self, msg):
        err.BaseCupException.__init__(self, msg)


TIME_EXTENSION_DEFAULT = 5 * 60
class KVCache:
    """
    Key-Value Cache object.

    You can use function set/get to access KeyValue Cache.

    When a k-v is hit by function **get**,
    the expire_sec will be expanded to 2 * (expire_sec)
    """
    _STAT = collections.namedtuple(
        'kvcache_stat', 'key_num expired_num'
    )
    INFINITE_TIME = 10000 * 365 * 24 * 60 * 60 # 10000 years, enough for cache
    TIME_EXTENSION = 5 * 60   # 5 mins

    def __init__(self, 
        name: str='', maxsize=0, time_extension: int=TIME_EXTENSION_DEFAULT,
    ) :
        """
        :param maxsize:
            0 by default which means store as more cache k/v as the system can
        :param time_extension:
            When a cache item has been hit, the expire_time will be refreshed
            to the greater one, either (TIME_EXTENSION + time.time() or
              (TIME_EXTENSION + expire_sec)
        """
        if name != '':
            self._name = name
        else:
            self._name = 'cache.noname.{0}'.format(uuid.uuid4())
            log.warn(
                'You initialize the KVCache with no name. Strongly suggest'
                'you pick up a meaningful name for it in order to debug'
            )
        self._sorted_keys = queue.PriorityQueue()
        self._maxsize = maxsize
        self._kv_data = {}
        self._lock = thread.RWLock()
        if time_extension is None:
            self._time_extension: int = self.TIME_EXTENSION
        else:
            self._time_extension: int = time_extension

    def set_time_extension(self, time_extension: int) -> None:
        """set time extension"""
        if time_extension <= 0:
            raise ValueError('time extension should > 0')
        log.info('KVCache set time extension to {0}'.format(time_extension))
        self._time_extension = time_extension

    @contextlib.contextmanager
    def _lock_release(self, writelock):
        if writelock is True:
            self._lock.acquire_writelock()
        else:
            self._lock.acquire_readlock()
        try:
            yield
        # pylint: disable=W0703
        except Exception as error:
            cup.log.error('something happend in cache:%s' % error)
        finally:
            if writelock is True:
                self._lock.release_writelock()
            else:
                self._lock.release_readlock()

    def set(self, kvdict, expire_sec=TIME_EXTENSION_DEFAULT):
        """
        set cache with kvdict
        ::

            {
                'key1': 'value1',
                'key2': 'value2',
                ....
            }

        :param kvdict:
            kvdict is a dict that contains your cache.
        :param expire_sec:
            if expire_sec is None, the cache will never expire.
            By default, will use

        :return:
            True if set cache successfully. False otherwise.
        """
        if all([
                self._maxsize != 0,
                len(kvdict) > self._maxsize
        ]):
            log.error(
                'KVCache {0} cannot insert more '
                'elements than the maxsize'.format(self._name)
            )
            return False
        expire_value = None
        if expire_sec is not None and expire_sec != self.INFINITE_TIME:
            expire_value = expire_sec + time.time()
        else:
            expire_value = self.INFINITE_TIME
        with self._lock_release(writelock=True):
            for key in kvdict:
                val = self._kv_data.get(key, None)
                if val is not None:   # key exists / replace
                    cup.log.debug(
                        'KVCache: Key:{0} updated.'.format(key)
                    )
                    self._kv_data[key] = (expire_value, kvdict[key])
                    if val[0] < expire_sec:
                        self._sorted_keys.put((expire_sec, val[1]))
                    continue
                # not exist
                if not self._heapq_newset(key, kvdict[key], expire_value):
                    return False
        return True
    
    def replace(self, key, value, ex):
        """
        
        :return:
            value of the key if found.
            Otherwise return None
        """
        with self._lock_release(writelock=True):
            val = self._kv_data.get(key, None)
            if val is not None:
                expire_time = time.time() + ex
                self._kv_data[key] = (expire_time, val[1])
                if expire_time < val[0]:
                    self._sorted_keys.put((expire_time, key))
                return value
            else:
                return None

    def _heapq_newset(self, key, value, expire_value):
        """
        headp set
        """
        if any([
                self._maxsize == 0,
                len(self._kv_data) < self._maxsize
        ]):
            # no limit, just insert it into the queue
            self._sorted_keys.put((expire_value, key))
            self._kv_data[key] = (expire_value, value)
            return True
        else:
            # need replace the smallest one
            while True:
                try:
                    pop_value = self._sorted_keys.get_nowait()
                except queue.Empty:
                    return False
                volitile_expire4sort, popkey = pop_value
                kvitem = self._kv_data.get(popkey, None)
                # key exipred, key deleted in self._kv_data
                if kvitem is None:
                    # only item in self._sorted_keys, not in real self._kv_data
                    # abondon it, continue to find 
                    continue
                real_expire, real_val = kvitem
                if real_expire > volitile_expire4sort:  # need resort
                    # which means it has a larger expire item 
                    # in self._sorted_keys. expiration changed
                    self._sorted_keys.put((real_expire, key)) 
                    continue
                else:
                    del self._kv_data[popkey]
                    self._kv_data[key] = (expire_value, value)
                    self._sorted_keys.put((expire_value, key))
                    break
        return True

    def _get_refreshed_exipre_time(self, expire_sec):
        new_refresh = time.time() + self._time_extension
        new_expire = expire_sec + self._time_extension
        return new_expire if new_expire < new_refresh else new_refresh

    def get(self, key, ex=None):
        """
        Get your cache with key.
        If the cache is expired, it will return None.
        If the key does not exist, it will return None.
        
        Notice that if the cached item exists and expired, it will be deleted
        when you cann `get` function
        
        :param ex:
            if ex is None, will not extend the expiration time
            if ex is not None, expire time will be time.time() + ex
        """
        with self._lock_release(writelock=False):
            if key not in self._kv_data:
                return None
            expire_sec, value = self._kv_data[key]
            if time.time() > expire_sec:
                log.info('KVCache {0}: key {1} hit, but exipred {1}'.format(
                    self._name, key
                ))
                del self._kv_data[key]
                self.pop_n_expired(num=1)
                return None
            log.debug('key:%s of kvCache fetched.' % key)
            if ex is None:
                log.debug('will not refresh expire time for key {}'.format(key))
            else:
                expire_time = time.time() + ex
                self._kv_data[key] = (expire_time, value)
            return value

    def pop_n_expired(self, num=0):
        """
        :param num:
            if num is 0, will get all expired key/values

        :return:
            A dict.
            Return expired items. Return type is a dict
            ::

                {
                    'key' : (value, expire_time)
                }
        """
        kvlist = {}
        nowtime = time.time()
        allexpire = True if num == 0 else False
        with self._lock_release(writelock=False):
            while True:
                try:
                    pop_value = self._sorted_keys.get_nowait()
                except queue.Empty:
                    break
                real_value = self._kv_data.get(pop_value[1], None)
                # has already been deleted
                if real_value is None:
                    continue
                if real_value[0] > pop_value[0]:
                    # resort, adjust real
                    self._sorted_keys.put((real_value[0], pop_value[1]))
                    continue
                else:
                    if real_value[0] > nowtime:  # not expired
                        self._sorted_keys.put((real_value[0], pop_value[1]))
                        break
                    else:  # expired
                        kvlist[pop_value[1]] = real_value
                        del self._kv_data[pop_value[1]]
                        if not allexpire:
                            num -= 1
                if not allexpire and num <= 0:
                    break
        return kvlist

    def size(self):
        """
        :return:
            cached item size
        """
        return len(self._kv_data)

    def clear(self):
        """
        remove all kv cache inside.
        """
        with self._lock_release(writelock=True):
            del self._kv_data
            self._kv_data = {}
            del self._sorted_keys
            self._sorted_keys = queue.PriorityQueue(self._maxsize)
    
    def expire(self, key, ex):
        """
        return True or False
        """
        if ex < 0:
            raise ValueError('ex cannot be less 0')
        with self._lock_release(writelock=True):
            val = self._kv_data.get(key, None)
            if val is None:
                log.error('failed expire a key, not found {0}'.format(key))
                return False
            # if self._sorted_keys find out that this key need to be removed
            # coz of expiration. will check if  expiration (expiration, key)
            # equels expiration from a kvitem(expiration, val)
            expiration = ex + time.time()
            if expiration < val[0]:
                self._sorted_keys.put((expiration, key))
            self._kv_data[key] = (expiration, val)
            return True
    
    def mapupdate(self, key, valuedict, ex=None):
        """
        
        :param ex:
            if ex is 0, will expire immediately.
            if ex > 0 , expire time updated to ex
        """
        if ex < 0:
            raise ValueError('ex cannot be less than 0')
        with self._lock_release(writelock=True):
            oldex, valmap = self._kv_data.get(key)
            if isinstance(valmap, dict):
                valmap.update(valuedict)
            else:
                return False
            if ex is None:
                self._kv_data = (oldex, valmap)
            else:
                self._kv_data = (ex, valmap)
                if ex < oldex:
                    self._sorted_keys.put((ex, key))
        return True
                


class KVMemCache(KVCache):
    """KVMem Cache"""


# for compatibility
KvCache = KVCache
# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
