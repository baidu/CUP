#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Yang Honggang
"""
:description:
    ut for cup.logging
"""
import os
import sys
import logging

_TOP = os.path.dirname(os.path.abspath(__file__)) + '/../'
sys.path.insert(0, _TOP)

from cup import log
from cup import unittest

def test_gen_wf():
    """
    init_comlog指定ge_wf参数为True时，将大于等于WARING级别的消息
    写入${logfile}.wf日志文件中。本case用来验证相关功能是否符合
    预期。
    """
    log.init_comlog(
        "Yang Honggang", logging.DEBUG, "cup.log",
        log.ROTATION, gen_wf=True
    )

    log.info("info")
    log.critical("critical")
    log.error("error")
    log.warn("warning")
    log.debug("debug")

    # 检查是否生成了cup.log和cup.log.wf文件
    try:
        flog = open('cup.log')
        flog_wf = open('cup.log.wf')
    except IOError:
        assert(False), "can not find cup.log or cup.log.wf file"
    # 检查cup.log的内容是否包括“debug”、"info"
    flog_str = flog.read()
    assert('debug' in flog_str and 'info' in flog_str), "cup.log's content error"
    # 检查cup.log.wf的内容是否包括"critical"、“error”和“warning”
    flog_wf_str = flog_wf.read()
    assert('critical' in flog_wf_str and 'error' in flog_wf_str and \
            'warning' in flog_wf_str), "cup.log.wf's content error"

    assert('debug' not in flog_wf_str and 'info' not in flog_wf_str), \
            "cup.log.wf's content error"
    # cup.log的内容不应该包括"critical"、“error”和“warning”
    assert('critical' not in flog_str and 'error' not in flog_str and \
            'warning' not in flog_str), "cup.log's content error"


def test_log_parse():
    """cup.log.parse"""
    logline = ('INFO:    2023-01-04 22:29:25,456 +0800(CST) '
            '* [34666:115f70600] [log.py:327]'
        ' to compress folder into tarfile:'
        '/home/disk2/szjjh-ccdb280.szjjh01.baidu.com.1444810391.7.tar.gz'
    )
    kvs = log.parse(logline)
    unittest.assert_eq(kvs['loglevel'], 'INFO')
    unittest.assert_eq(kvs['date'], '2023-01-04')
    unittest.assert_eq(kvs['time'], '22:29:25,456')
    unittest.assert_eq(kvs['pid'], '34666')
    unittest.assert_eq(kvs['tid'], '115f70600')
    unittest.assert_eq(kvs['srcline'], 'log.py:327')
    unittest.assert_startswith(kvs['msg'], 'to compress')


def test_log_reinitcomlog():
    """test reinitcom log"""
    log.reinit_comlog(
        "Yang Honggang1", logging.DEBUG, "cup.new.log",
        log.ROTATION, gen_wf=True
    )
    log.info("new info")
    log.critical("new critical")
    log.error("new error")
    log.warn("new warning")
    log.debug("new debug")


def test_log_xfuncs():
    """test x log functions"""
    logparams = log.LoggerParams(
        log.DEBUG, 'cup.x.log', log.ROTATION, 100 * 1024 * 1024,
        True, True
    )
    log.xinit_comlog('log.x', logparams)
    log.xdebug('log.x', 'xdebug')
    log.xinfo('log.x', 'xinfo')
    log.xerror('log.x', 'xerror')
    logparams = log.LoggerParams(
        log.DEBUG, 'cup.y.log', log.ROTATION, 100 * 1024 * 1024,
        True, True
    )
    log.xinit_comlog('log.y', logparams)
    log.xdebug('log.y', 'ydebug')
    log.xinfo('log.y', 'yinfo')
    log.xerror('log.y', 'yerror')



def _main():
    test_gen_wf()
    test_log_parse()


if __name__ == '__main__':
    _main()

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
