#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    unittest for cup.util.conf
"""
import unittest

from cup.util import conf
from cup import unittest as ut


class TestUtilConf(unittest.TestCase):
    """test cup.util.conf"""
    def test_arrary_special_chars(self):
        """test arrary"""
        # test conf arrary
        list_conf = conf.Configure2Dict('./conf/test.list.conf', False).get_dict()
        ut.assert_eq(len(list_conf['arrary_test']['a']), 4)
        ut.assert_eq(len(list_conf['arrary_test']['b']), 2)
        ut.assert_eq(len(list_conf['arrary_test']['c']), 1)
        # test special chars
        ut.assert_eq(list_conf['sepecial_chars']['with_back_slash_d'],
            r'^/((home(/disk\d+)*)|tmp)/(normandy|work|mapred)/.*')
        # test disorder of arrays
        confdict = conf.Configure2Dict('./conf/conf_mock.conf', False).get_dict()
        ut.assert_eq('123' in confdict['test']['nice']['prefix'], True)
        ut.assert_eq(len(confdict['test']['nice']['prefix']), 2)

        newdict = {
            'minghao': 'abc',
            'liuxuan': [1, 2, 3, 4],
            'layer1': {
                'layer2': 'abc',
                'layer2-array': [{'key-1': 1}, {'key-1': 2}],
            },
            'layer1-array': [{'key-1': 1}, {'key-1': 2}],
            'zksdfjk': 'abc',
            'kehyrj': 1,
            'test': 'abcdefg\d'
        }


        confdict['layer2']['newtest'] = newdict

        confobj = conf.Dict2Configure(confdict)
        confobj.write_conf('./conf/test.conf')

        test_dict = conf.Configure2Dict('./conf/test.conf').get_dict()
        print 'test_comments:', confdict['test_comments']


    def test_include_files(self):
        """test include"""
        include_conf = conf.Configure2Dict('./conf/test.include.conf')
        include_dict = include_conf.get_dict(ignore_error=True)
        ut.assert_in(
            './conf/test.included.conf', include_dict['$include'].keys()
        )
        in_confdict = include_dict['$include']['./conf/test.included.conf']
        ut.assert_eq(in_confdict['layer_included']['layer1-option00'],
            'layer1-option00'
        )

    def test_include_wrong_file(self):
        """test wrong include"""
        include_conf = conf.Configure2Dict('./conf/test.include.wrong.conf')
        include_dict = include_conf.get_dict(ignore_error=True)
        ut.assert_in(
            './conf/test.included.conf', include_dict['$include'].keys()
        )
        in_confdict = include_dict['$include']['./conf/test.included.conf']
        ut.assert_eq(in_confdict['layer_included']['layer1-option00'],
            'layer1-option00'
        )
        conf.Dict2Configure(include_dict).write_conf('./conf/test.include.write')
        try:
            include_dict = include_conf.get_dict(ignore_error=False)
            ut.assert_eq('should raise IOError', 1)
        except IOError as _:
            pass


if __name__ == '__main__':
    unittest.main()

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
