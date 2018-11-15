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
    logline = ('INFO: 2015-10-14 16:13:11,700  '
        '* [18635:139901983938272] [util.py:167] '
        'to compress folder into tarfile:'
        '/home/disk2/szjjh-ccdb280.szjjh01.baidu.com.1444810391.7.tar.gz'
    )
    kvs = log.parse(logline)
    unittest.assert_eq(kvs['loglevel'], 'INFO')
    unittest.assert_eq(kvs['date'], '2015-10-14')
    unittest.assert_eq(kvs['time'], '16:13:11,700')
    unittest.assert_eq(kvs['pid'], '18635')
    unittest.assert_eq(kvs['tid'], '139901983938272')
    unittest.assert_eq(kvs['srcline'], 'util.py:167')
    unittest.assert_startswith(kvs['msg'], 'to compress')

    newlog = 'xxxxxxxxsdfsdf  sdfsdf'
    unittest.assert_none(log.parse(newlog))


def _main():
    test_gen_wf()
    test_log_parse()


if __name__ == '__main__':
    _main()

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
