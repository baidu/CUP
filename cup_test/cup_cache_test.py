#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    unittest for cup.cache
"""

import time

from cup import cache
from cup import unittest


def test_cache_basic_set_get():
    """test basic cache set/get"""
    kvcache = cache.KVCache('basic_test')
    kvcache.set(
        {
            'test-0': 'test_value0',
            'test-1': 'test_value1'
        }
    )
    kvcache.get('test-0')
    unittest.assert_eq(kvcache.get('test-0'), 'test_value0')
    kvcache.set(
        {
            'test-0': 'test_value0',
            'test-1': 'test_value1'
        },
        2
    )
    time.sleep(3)
    unittest.assert_eq(kvcache.get('test-0'), None)
    unittest.assert_eq(kvcache.get('test-1'), None)


def test_cache_refresh_with_get():
    """
    test cache refresh
    """
    kvcache = cache.KVCache('basic_test', 5)
    kvcache.set_time_extension(3)
    kvcache.set(
        {
            'test-0': 'test_value0',
            'test-1': 'test_value1'
        },
        2
    )
    time.sleep(1)
    kvcache.get('test-0')
    time.sleep(2)
    assert kvcache.get('test-0') == 'test_value0'
    assert kvcache.get('test-1') is None


def test_cache_replace():
    """test cache replace"""
    kvcache = cache.KVCache('basic_test', 3)
    kvcache.set_time_extension(3)
    assert not kvcache.set(
        {
            'test-0': 'test_value0',
            'test-1': 'test_value1',
            'test-2': 'test_value1',
            'test-3': 'test_value1'
        },
        2
    )
    kvcache.set(
        {
            'test-0': 'test_value0',
            'test-1': 'test_value1',
            'test-2': 'test_value1',
        },
        1
    )
    assert kvcache.set({'test-3':'test_value3'}, 2) is True
    # print(kvcache._kv_data)
    assert kvcache.get('test-0') is None
    assert kvcache.get('test-3') == 'test_value3'
    time.sleep(2)
    # print(kvcache._kv_data)
    assert kvcache.get('test-3') == 'test_value3'
    kvcache.set({'test-4': 'test_value4'}, 1)
    kvcache.set({'test-5': 'test_value5'}, 1)
    # print(kvcache._kv_data)


def test_cache_getexpired():
    """test get expired"""
    kvcache = cache.KvCache('basic_test', 5)
    kvcache.set_time_extension(3)
    kvcache.set({'k0': 'v0'}, 1)
    kvcache.set({'k1': 'v1'}, 1)
    kvcache.set({'k1': 'v1'}, 50)
    kvcache.get('k1')
    time.sleep(2)
    # print(kvcache.pop_n_expired(1)
    assert kvcache.pop_n_expired(1).get('k0') is not None
    time.sleep(3)
    # print(kvcache.pop_n_expired())
    assert kvcache.pop_n_expired(1).get('k1') is not None

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
