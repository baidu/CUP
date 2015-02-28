#!/bin/env python
# -*- coding: utf-8 -*
"""

    @FileName: setup.py
    @Author: liuxuan05
    @CreatTime: 2014-10-22 13:25:59
    @LastModif: 2014-10-22 13:54:37
    @Note:
"""

import os
import re
import sys
import traceback
from distutils.core import setup

try:
    # pylint: disable=W0622
    __name__ = 'cup'
    __author__ = __import__(__name__).version.AUTHOR
    __version__ = __import__(__name__).version.VERSION
# pylint: disable=W0703
except Exception:
    print traceback.print_exc()
    exit(-1)


# Guannan add windows platform support on 2014/11/4 20:04
def _find_packages(prefix=''):
    packages = []
    path = '.'
    prefix = prefix
    for root, _, files in os.walk(path):
        if '__init__.py' in files:
            if sys.platform.startswith('linux'):
                packages.append(
                    re.sub('^[^A-z0-9_]', '', root.replace('/', '.'))
                )
            elif sys.platform.startswith('win'):
                packages.append(
                    re.sub('^[^A-z0-9_]', '', root.replace('\\', '.'))
                )
    print packages
    return packages


setup(
    name=__name__,
    version=__version__,
    author=__author__,
    packages=_find_packages(__name__),
    package_data={'': ['*.so']}
)

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
