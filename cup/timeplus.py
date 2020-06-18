#!/usr/bin/python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:desc:
    time related module. looking forward to accepting new patches
"""
from __future__ import print_function
import time
import datetime

import pytz


__all__ = ['get_str_now', 'TimePlus']


def get_str_now(fmt='%Y-%m-%d-%H-%M-%S'):
    """
    return string of 'now'

    :param fmt:
        print-format, '%Y-%m-%d-%H-%M-%S' by default
    """
    return str(time.strftime(fmt, time.localtime()))


class TimePlus(object):
    """arrow time"""
    def __init__(self, timezone):
        """
        initialize with timezone setup
        """
        if not isinstance(timezone, pytz.BaseTzInfo):
            raise ValueError('not a object of pytz.timezone("xxx/xxx")')
        self._timezone = timezone
        self._utc_tz = pytz.timezone('UTC')

    def get_timezone(self):
        """
        return current pytz timezone object
        """
        return self._timezone

    def set_newtimezone(self, pytz_timezone):
        """
        refresh timezone

        :return:
            True if refreshing is done. False otherwise
        """
        self._timezone = pytz_timezone

    @classmethod
    def utc_now(cls):
        """return utc_now"""
        return datetime.datetime.now(pytz.UTC)

    def local2utc(self, dateobj):
        """
        local timezone to utc conversion

        :return:
            a datetime.datetime object with utc timezone enabled

        :raise:
            ValueError if dateobj is not a datetime.datetime object
        """
        if not isinstance(dateobj, datetime.datetime):
            raise ValueError('dateobj is not a datetime.datetime')
        return dateobj.astimezone(self._utc_tz)

    def utc2local(self, dateobj):
        """
        utc datetime to local timezone datetime.datetime
        """
        if not isinstance(dateobj, datetime.datetime):
            raise ValueError('dateobj is not a datetime.datetime')
        return dateobj.astimezone(self._timezone)


if __name__ == '__main__':
    print(get_str_now())
