#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    ut for cup.services.generator
"""

import os
import sys
import time

from cup import cache
from cup import unittest
from cup.services import generator


def test_generator():
    a_gen = generator.CGeneratorMan()
    b_gen = generator.CGeneratorMan()
    print a_gen
    print b_gen
    assert a_gen == b_gen


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
