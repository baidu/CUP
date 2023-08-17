#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma
"""
:description:
    host route info related module
"""
import requests

__all__ = ['realip_v4']


def realip_v4():
    """
    get real ip for the current device

    :raise ValueError:
        if it cannot fetch the same real ip
    """
    get_ip_list = [
        'http://ident.me',
        'http://ifconfig.me',
        'http://ipinfo.io/ip'
    ]
    ipvalue = {}
    retvalue = None
    counts = 0
    for webcheck in get_ip_list:
        try:
            value = requests.get(webcheck, timeout=1).text
            if value in ipvalue:
                ipvalue[value] += 1
            else:
                ipvalue[value] = 1
            if ipvalue[value] > counts:
                retvalue = value
                counts = ipvalue[value]
        # pylint: disable=broad-except
        except Exception:
            continue
    if retvalue is None:
        raise ValueError('cannot get realip')
    return retvalue
