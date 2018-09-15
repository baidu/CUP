#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    resource related module
"""

import sys

if sys.platform.startswith('linux'):
    from cup.res import linux
    Process = linux.Process

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
