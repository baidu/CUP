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

with open('README.md', 'r') as fh:
    LONG_DESCRIPTION = fh.read()

# Guannan add windows platform support on 2014/11/4 20:04
def _find_packages(prefix=''):
    """find pckages"""
    packages = []
    path = '.'
    prefix = prefix
    for root, _, files in os.walk(path):
        if '__init__.py' in files:
            item = None
            if sys.platform.startswith('linux'):
                item = re.sub('^[^A-z0-9_]', '', root.replace('/', '.'))
            elif sys.platform.startswith('win'):
                item = re.sub('^[^A-z0-9_]', '', root.replace('\\', '.'))
            else:
                item = re.sub('^[^A-z0-9_]', '', root.replace('/', '.'))
            if item is not None:
                packages.append(item.lstrip('.'))
    return packages


setup(
    name=__name__,
    version=__version__,
    description='A common useful python library',
    # long_description=(
    #     'Wish CUP to be a popular common useful python-lib in the world! '
    #     '(Currently, Most popular python lib in baidu)'
    # ),
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url='https://cup.iobusy.com',
    author=__author__,
    maintainer='Guannan Ma mythmgn@gmail.com @mythmgn',
    author_email='mythmgn@gmail.com',
    classifiers=textwrap.dedent("""
        Development Status :: 5 - Production/Stable
        Intended Audience :: Developers
        Operating System :: MacOS
        Operating System :: POSIX :: Linux
        Programming Language :: Python :: 2.6
        Programming Language :: Python :: 2.7
        Topic :: Software Development :: Libraries :: Python Modules
        Topic :: Utilities
        """).strip().splitlines(),
    license='Apache 2',
    keywords='library common network threadpool baselib framework',
    packages=_find_packages(__name__),
    package_data={
        '': [
            '*.so', '*.pyo',
            # for matplotlib
            '*.ttf', '*.afm', '*.png', '*.svg', '*.xpm',
            'Matplotlib.nib/classes.nib', 'Matplotlib.nib/info.nib',
            'Matplotlib.nib/keyedobjects.nib',
            'mpl-data/lineprops.glade',
            'mpl-data/matplotlibrc',
        ]
    }
)

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
