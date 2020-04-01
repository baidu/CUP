#!/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Liuxuan,
"""
installation py
"""
import os
import re
import sys
import textwrap
import traceback
import setuptools
# from distutils import core

try:
    # pylint: disable=W0622
    __name__ = 'cup'
    __author__ = __import__(__name__).version.AUTHOR
    __version__ = __import__(__name__).version.VERSION
# pylint: disable=W0703
except Exception:
    print traceback.print_exc()
    exit(-1)

setuptools.setup(
    name=__name__,
    version=__version__
)

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
