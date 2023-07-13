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
# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
