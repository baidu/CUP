#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    unittest for cup.mail
"""
import os
import sys

_NOW_PATH = os.path.dirname(os.path.abspath(__file__)) + '/'
sys.path.insert(0, _NOW_PATH + '../')

from cup import mail
from cup import unittest


class CTestAsync(unittest.CUTCase):
    """
    cup.mail test
    """
    def __init__(self):
        super(self.__class__, self).__init__()
        self._enable = False

    def setup(self):
        """
        setup
        """
        pass

    def teardown(self):
        """teardown"""
        pass

    def test_run(self):
        """
        run test
        """
        if self._enable:
            mailer = mail.SmtpMailer(
                'maguannan ',
                is_html=True
            )
            mailer.sendmail(
                'maguannan ',
                'subject',
                'body-hello world',
                None,
                'liuxuan05 ',
                'zhaominghao '
            )
            mailer.sendmail(
                'maguannan ',
                'test only 1 reciept',
                'body-',
                None,
                None,
                None
            )
            mailer.sendmail(
                ['maguannan ', 'liuxuan05 '],
                'test 2 reciepts',
                'body-',
                None,
                None,
                None
            )
            mailer.sendmail(
                '',
                'test only cc',
                'body-',
                None,
                'maguannan ',
                None
            )
            mailer.sendmail(
                '',
                'test two cc items',
                'body-',
                None,
                ['maguannan ', 'liuxuan05 '],
                None
            )
            mailer.sendmail(
                '',
                'test two bcc items',
                'body-',
                None,
                None,
                ['maguannan ', 'liuxuan05 '],
            )
            lines = None
            with open('./hello.html', 'r') as fhandle:
                lines = ''.join(fhandle.readlines())
            mailer.sendmail(
                ['chenyuan02 ', 'maguannan '],
                'test hello',
                lines
            )






if __name__ == '__main__':
    unittest.CCaseExecutor().runcase(CTestAsync())


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent

