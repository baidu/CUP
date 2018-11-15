#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    unittest for cup.cache
"""
import os
import sys

_NOW_PATH = os.path.dirname(os.path.abspath(__file__)) + '/'
sys.path.insert(0, _NOW_PATH + '../')

from cup import unittest
from cup.storage import obj

def test_s3_object():
    """test s3 object"""
    config = {
        'endpoint': 'abcd',
        'ak': 'xxxx',
        'sk': 'yyyy',
        'bucket': 'cup-test'
    }
    s3obj = obj.S3ObjectSystem(config)
    print s3obj.delete_bucket('cup-test', forcely=True)
    unittest.assert_eq(s3obj.create_bucket('cup-test')['returncode'], 0)
    unittest.assert_eq(
        s3obj.put('test-obj', './cup_storage_object_test.py')['returncode'],
        0
    )
    unittest.assert_eq(
        s3obj.head('test-obj')['returncode'],
        0
    )
    s3obj.get('test-obj', './test-obj')
    os.unlink('test-obj')



# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent

