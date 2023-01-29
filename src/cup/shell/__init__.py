#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn), Zhao Minghao, Zhange Yuetian
"""
:description:
    shell related module
"""
import os
import time
import sys
import shutil
import signal
import random
import hashlib
import warnings
import datetime
import threading
import traceback
import subprocess
import collections

import cup
from cup import err
from cup.shell import expect
from cup.shell import oper

## for backwards support
from cup.shell.oper import md5file
from cup.shell.oper import kill9_byname
from cup.shell.oper import del_if_exist
from cup.shell.oper import execshell
from cup.shell.oper import execshell_withpipe
from cup.shell.oper import execshell_withpipe_exwitherr
from cup.shell.oper import is_proc_alive
from cup.shell.oper import forkexe_shell
from cup.shell.oper import execshell_withpipe_ex
from cup.shell.oper import execshell_withpipe_str
from cup.shell.oper import ShellExec
from cup.shell.oper import rmtree
from cup.shell.oper import Asynccontent


_DEPRECATED_MSG = '''Plz use class cup.shell.ShellExec instead. Function %s
 deprecated'''


def _test():
    pass


__all__ = [
    'oper',
    'expect'
]


if __name__ == '__main__':
    _test()

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
