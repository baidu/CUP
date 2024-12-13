#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    ut for cup.services.generator
"""
from __future__ import print_function
import os
import sys
import time

from cup import cache
from cup import unittest
from cup.services import generator


def test_generator():
    """ generate general data"""
    a_gen = generator.CGeneratorMan()
    b_gen = generator.CGeneratorMan()
    print(a_gen)
    print(b_gen)
    assert a_gen == b_gen


def test_uuid_py3_compatibility():
    """generate uuid"""
    uuidgen = generator.CachedUUID()
    print(uuidgen.get_uuid()[0])


def test_cycleid_gen():
    """
    test cycle id 
    """
    uuidgen = generator.CycleIDGenerator(
        '127.0.0.1', 65000
    )
    hexid = uuidgen.id2_hexstring(uuidgen.next_id())
    
    ret = uuidgen.ipport(hexid)
    assert ret[0] == '127.0.0.1'
    assert ret[1] == 65000


def test_cacheduuid():
    """
    generate uuid
    """
    gen = generator.CachedUUID.singleton_instance()
    ret = gen.get_uuid()
    assert len(ret) == 1
    assert len(gen.get_uuid(num=99)) == 99
    assert len(gen.get_uuid(num=100)) == 100
    assert len(gen.get_uuid(num=101)) == 101
    assert len(gen.get_uuid(num=102)) == 102
    
    gen2 = generator.CachedUUID.singleton_instance()
    assert gen is gen2
    

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
