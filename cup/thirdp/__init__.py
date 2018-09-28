#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
    thirdp is short for thirdparty.
"""
import os
import sys
import platform
from cup import version

sys.path.insert(
    0, os.path.dirname(os.path.abspath(__file__)) + '/'
)

# pylint:disable=R0911
def _check_if_import_scientistlib():
    """check if it contains scientist lib"""
    # Only CUP 1.4.0  support numpy scipy.......
    if version.VERSION == '1.4.0':
        return True
    else:
        return False

    if sys.version_info < (2, 7):
        return False
    platinfo = str(platform.platform())
    if platinfo.lower().find('centos-6.3') >= 0:
        return True
    if platinfo.lower().find('redhat-4.3') >= 0:
        return True
    if platinfo.lower().find('redhat-4-nahant_update_3') >= 0:
        return True
    return False


if _check_if_import_scientistlib():
    _LIB_PATH = os.path.abspath(
        os.path.dirname(os.path.abspath(__file__)) +
        '/../../cup_thirdp/numpy/cupso/'
    )
    import ctypes
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/../../libpython2.7.so')
    # ====== for numpy - scipy
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/libgcc_s.so')
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/libgmp.so')
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/libquadmath.so')
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/libgfortran.so')
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/libblas.so')
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/libmpfr.so')
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/libgmpxx.so')
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/liblapack.so')
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/libmpc.so')
    # ====== end numpy -scipy
    # ====== for opencv
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/../../cv/libopencv_core.so')
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/../../cv/libopencv_imgproc.so')
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/../../cv/libopencv_highgui.so')
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/../../cv/libopencv_flann.so')
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/../../cv/libopencv_features2d.so')
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/../../cv/libopencv_calib3d.so')
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/../../cv/libopencv_ml.so')
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/../../cv/libopencv_video.so')
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/../../cv/libopencv_legacy.so')
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/../../cv/libopencv_objdetect.so')
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/../../cv/libopencv_photo.so')
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/../../cv/libopencv_gpu.so')
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/../../cv/libopencv_ocl.so')
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/../../cv/libopencv_nonfree.so')
    ctypes.cdll.LoadLibrary(_LIB_PATH + '/../../cv/libopencv_contrib.so')
    # ====== end opencv
    sys.path.insert(
        0, os.path.dirname(os.path.abspath(__file__)) + '/../../cup_thirdp/'
    )
    import numpy
    import scipy
    import matplotlib
    import sklearn
    import theano
    import bson
    import pymongo
    import cv
# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
