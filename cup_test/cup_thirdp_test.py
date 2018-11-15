#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    unittest for thirdp-party
"""
import os
import sys
import platform
_NOW_PATH = os.path.dirname(os.path.abspath(__file__)) + '/'
sys.path.insert(0, _NOW_PATH + '../')


# if the case is run under baidu's env
_ = platform.linux_distribution()
# if _[0] == 'CentOS' and (_[1] == '6.3' or _[1] == '4.3'):
#     from cup.thirdp import numpy
#     from cup.thirdp import scipy
#     from cup.thirdp import matplotlib
#     from cup.thirdp import sklearn
#     from cup.thirdp import theano
#     from cup.thirdp import pymongo
#     from cup.thirdp import cv

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
