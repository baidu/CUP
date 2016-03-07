#!/usr/bin/env python
# -*- coding: utf-8 -*
# #############################################################
#
#  Copyright (c) 2014 Baidu.com, Inc. All Rights Reserved
#
# #############################################################
"""
:authors:
    Guannan Ma maguannan@baidu.com @mythmgn
:create_date:
    2015/2/5 15:42
:modify_date:
    2015/2/5 15:42
:description:
    unittest of cup.util.conf
"""


from cup.util import conf

confdict = conf.Configure2Dict('./conf_mock.conf', False).get_dict()

print confdict

newdict = {
<<<<<<< HEAD
    'minghao' : 'abc',
    'liuxuan': [1,2,3,4],
    'layer1' : {
        'layer2': 'abc',
        'layer2-array' : [ {'key-1': 1}, {'key-1': 2}],
    },
    'layer1-array' : [ {'key-1': 1}, {'key-1': 2}],
    'zksdfjk' : 'abc',
    'kehyrj' : 1
}

confdict['layer2']['newtest']  = newdict
=======
    'minghao': 'abc',
    'liuxuan': [1, 2, 3, 4],
    'layer1': {
        'layer2': 'abc',
        'layer2-array': [{'key-1': 1}, {'key-1': 2}],
    },
    'layer1-array': [{'key-1': 1}, {'key-1': 2}],
    'zksdfjk': 'abc',
    'kehyrj': 1
}

confdict['layer2']['newtest'] = newdict
>>>>>>> origin/master

confobj = conf.Dict2Configure(confdict)
confobj.write_conf('./test.conf')


newconfdict = {}

newconfdict['test'] = '123'
newconfdict['arr'] = [1, 2, 3, 4]
confobj = conf.Dict2Configure(newconfdict)
confobj.write_conf('./test_normal.conf')
<<<<<<< HEAD
# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent

=======

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
>>>>>>> origin/master
