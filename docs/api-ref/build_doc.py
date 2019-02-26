#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    decorators related module
"""
import os
import sys
import argparse

_NOW_PATH = os.path.dirname(os.path.abspath(__file__)) + '/'
_TOP_PATH = os.path.abspath(_NOW_PATH + '/../')

# sys.path.insert(0, _NOW_PATH)
sys.path.insert(0, _TOP_PATH)

from cup import version
from cup.shell import oper


class DocGenerator(object):
    """
    doc generator for cup
    """
    def __init__(self, opts):
        """
        doc generator by invoking sphinx
        """
        self._kv_opts = opts

    def build_rst(self, github=True):
        """build rst for cup"""
        exclude = ''
        if github:
            exclude = ' cup/thirdp cup/bidu '
        else:
            exclude = ' cup/thirdp'
        cmd = 'sphinx-apidoc {0}'
        for key in self._kv_opts:
            cmd = '{0} {1} {2}'.format(cmd, key, self._kv_opts[key])
        print cmd
        shell = oper.ShellExec()
        shell.run(cmd, timeout=600)


if __name__ == '__main__':
    kvs = {
        '-F': ' ',
        '-o': '{0}/cup'.format(_NOW_PATH),
        '--doc-version': version.VERSION,
        '--doc-author': version.AUTHOR,
        '--ext-todo': ' ',
        '--module-first': ' ',
    }
    gen = DocGenerator(kvs)
    gen.build_rst()

    helpinfo = "generate cup html docs"
    parser = argparse.ArgumentParser(description=helpinfo)
    helpinfo = "conf file of sphinx"
    parser.add_argument('-c', '--conf', type=str, help=helpinfo)
    parser.parse_args()

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
