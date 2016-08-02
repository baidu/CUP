#!/usr/bin/python
# -*- coding: utf-8 -*
# #############################################################################
#
#  Copyright (c) 2014 Baidu.com,  Inc. All Rights Reserved
#
# #############################################################################

"""
:author:
    Guannan Ma maguannan@baidu.com @mythmgn
:create_date:
    2014
:last_date:
    2014
:descrition:
    Null
"""

import os
import sys
import hashlib
import traceback
import logging

import cup

__all__ = [
    'assert_true',
    'assert_false',
    'assert_eq',
    'assert_not_eq',
    'assert_eq_one',
    'assert_lt',
    'assert_gt',
    'assert_ge',
    'assert_le',
    'assert_ne',
    'CUTCase',
    'CCaseExecutor',
]


def _assert_bool(val, exp, errmsg=''):
    if (val is not exp):
        msg = 'got %s, expect %s\nUser ErrMsg: %s' % (val, exp, errmsg)
        try:
            cup.log.critical(msg)
        # pylint: disable=W0703
        except Exception:
            pass
        assert False, msg


def assert_true(val, errmsg=''):
    """
    如果val is not True， assert并打印到stdout.
    errmsg参数为assert后提示到stderr的调用者错误信息
    如果开启过cup.log.init_comlog的log， 同时打印critical log到log文件
    """
    if type(val) != bool:
        raise ValueError('The type of val is not bool')
    _assert_bool(val, True, errmsg)


def assert_false(val, errmsg=''):
    """
    如果val is not False， assert并打印到stdout.
    errmsg参数为assert后提示到stderr的调用者错误信息
    如果开启过cup.log.init_comlog的log， 同时打印critical log到log文件
    """
    if type(val) != bool:
        raise ValueError('The type of val is not bool')
    _assert_bool(val, False, errmsg)


def assert_eq(val, exp, errmsg=''):
    """
    assert_eq， 如果val!=exp， assert并打印到stdout.
    errmsg参数为assert后提示到stderr的调用者错误信息
    如果开启过cup.log.init_comlog的log， 同时打印critical log到log文件
    """
    if (val != exp):
        msg = 'got %s, expect %s\nUser ErrMsg: %s' % (val, exp, errmsg)
        try:
            cup.log.critical(msg)
        # pylint: disable=W0703
        except Exception:
            pass
        assert False, msg


def assert_not_eq(val, exp, errmsg=''):
    """
    assert_not_eq. val不能等于exp, 如果等于则assert
    """
    if (val == exp):
        msg = 'got %s which is equal, expect not equal \nUser ErrMsg: %s' % (
            val, errmsg
        )
        try:
            cup.log.critical(msg)
        # pylint: disable=W0703
        except Exception:
            pass
        assert False, msg


def assert_eq_one(val, array, errmsg=''):
    """
    assert_eq_one, 如果val!=array(可遍历类型)里面的任何item, assert
    """
    equal = False
    str_arr = ''
    for i in array:
        str_arr += '|' + str(i) + '|'
        if i == val:
            equal = True
            break
    if not equal:
        msg = 'got %s, expect one in the array: %s\nUser ErrMsg: %s' % (
            val, str_arr, errmsg
        )
        try:
            cup.log.critical(msg)
        # pylint: disable=W0703
        except Exception:
            pass
        assert False, msg


def assert_in(val, array, errmsg=''):
    """
    同assert_eq_one, 如果val不在可遍历array里面， assert
    """
    assert_eq_one(val, array, errmsg)


def assert_not_in(val, iteratables, errmsg=''):
    """
    如果val不存在于iteratables中，则assert
    """
    if val in iteratables:
        assert False, 'val :%s in iteratables. ErrMsg:%s' % (val, errmsg)


def assert_lt(val, exp, errmsg=''):
    """
    assert_lt, expect val < exp
    """
    if val > exp:
        msg = 'got %s, expect less than %s\nUser ErrMsg: %s' % (
            val, exp, errmsg
        )
        try:
            cup.log.critical(msg)
        # pylint: disable=W0703
        except Exception:
            pass
        assert False, msg


def assert_gt(val, exp, errmsg=''):
    """
    assert_gt, expect val > exp
    """

    if val <= exp:
        msg = 'got %s, expect greater than %s\nUser ErrMsg: %s' % (
            val, exp, errmsg
        )
        try:
            cup.log.critical(msg)
        except Exception:
            pass
        assert False, msg


def assert_ge(val, exp, errmsg=''):
    """
    expect val >= exp
    """
    if val < exp:
        msg = 'got %s, expect greater than (or equal to) %s\n User ErrMsg:%s'\
            % (val, exp, errmsg)
        try:
            cup.log.critical(msg)
        # pylint: disable=W0703
        except Exception:
            pass
        assert False


def assert_le(val, exp, errmsg=''):
    """
    expect val <= exp
    """
    if val > exp:
        msg = 'got %s, expect less than (or equal to) %s\nUser ErrMsg: %s' % (
            val, exp, errmsg
        )
        try:
            cup.log.critical(msg)
        # pylint: disable=W0703
        except Exception:
            pass
        assert False, msg


def assert_ne(val, exp, errmsg=''):
    """
    expect val != exp
    """
    if val == exp:
        msg = 'Expect non-equal, got two equal values %s:%s\nUser Errmsg: %s' \
            % (val, exp, errmsg)
        try:
            cup.log.critical(msg)
        # pylint: disable=W0703
        except Exception:
            pass
        assert False, errmsg


def assert_boundary(val, low, high, errmsg=None):
    """
    expect low <= val <= high
    """
    if val < low:
        msg = 'Expect low <= val <= high, but val:%s < low:%s, msg:%s' % (
            val, low, errmsg
        )
        assert False, msg
    if val > high:
        msg = 'Expect low <= val <= high, but val:%s > high:%s, msg:%s' % (
            val, high, errmsg
        )
        assert False, msg


def _get_md5_hex(src_file):
    with open(src_file, 'rb') as fhandle:
        md5obj = hashlib.md5()
        while True:
            strtmp = fhandle.read(131072)  # read 128k one time
            if len(strtmp) <= 0:
                break
            md5obj.update(strtmp)
    return md5obj.hexdigest()


def assert_local_file_eq(srcfile, dstfile, errmsg=None):
    """
    expect same md5 value of the two files
    """
    assert os.path.exists(srcfile)
    assert os.path.isfile(srcfile)
    assert os.path.exists(dstfile)
    assert os.path.isfile(dstfile)
    srcmd5 = _get_md5_hex(srcfile)
    dstmd5 = _get_md5_hex(dstfile)
    msg = 'expect same md5 value. src:%s, dst:%s, errmsg:%s' % (
        srcmd5, dstmd5, errmsg
    )
    assert srcmd5 == dstmd5, msg


def assert_startswith(source, comp, errmsg=None):
    """
    if source does NOT start with comp, assert False
    """
    errmsg = 'expect source:{0} starts with:{1}'.format(source, comp)
    if not source.startswith(comp):
        assert False, errmsg


def assert_none(source):
    """
    assert None
    """
    if source is not None:
        assert False, 'expect source is None, but now is {0}'.format(source)


class CUTCase(object):
    """
    cup库拥有的测试class. 支持nosetests. 可派生此类来实现测试class.
    其中set_result函数会在nosetests执行case后设置，case成功则设置True,
    case fail设置False. 在teardown阶段可调用get_result函数
    来获得case是否执行成功。
    """
    def __init__(self, logfile='./test.log', b_logstd=False, b_debug=False):
        """
        :param logfile:
            调用cup.log.init_comlog来进行log文件的初始化，case可直接调用
            cup.log.[info|debug|critical|warn]来打印日志。
        :param b_logstd:
            是否打印日志到logfile的同时还打印stdout, 默认不打印
        :param b_debug:
            是否开启DEBUG Level的日志打印， 默认是INFO Level
        """
        self._result = False
        if b_debug:
            debuglevel = logging.DEBUG
        else:
            debuglevel = logging.INFO

        cup.log.init_comlog(
            'test_case', debuglevel,
            logfile, cup.log.ROTATION, 5242880, b_logstd
        )

    def setup(self):
        """
        Case的setup虚函数, 实际case需事先该函数
        """
        pass

    def test_run(self):
        """
        Case的setup虚函数, 实际case需事先该函数
        """
        pass

    def set_result(self, b_result):
        """
        cup ut 类用来设置case是否失败的函数。 一般不需要显示调用，
        内部自动处理。
        """
        self._result = b_result

    def get_result(self):
        """
        在teardown或者fail_teardown阶段获得是否case执行成功
        """
        return self._result

    def teardown(self):
        """
        Case的setup虚函数, 实际case需实现该函数
        """
        pass
    # def fail_teardown(self):
    #     """
    #     Case的setup虚函数, 实际case需实现该函数
    #     """
    #     pass


# pylint: disable=R0903
class CCaseExecutor(object):
    """
    可调用CCaseExecutor类来执行cup.unittest.CUTCase的派生类case.
    代码示例, 可nosetests执行， 也可python test_xxx.py执行的例子
    ::

        #!/usr/bin/env python

        import sys
        import os
        import logging

        import cup
        import sb_global

        from nfsinit import CClearMan
        from nfs import CNfs
        from cli import CCli

        class TestMyCase(cup.unittest.CUTCase):
            def __init__(self):
                super(self.__class__, self).__init__(
                    logfile=sb_global.G_CASE_RUN_LOG,
                    b_logstd=False
                )
                cup.log.info( 'Start to run ' + str(__file__ ) )
                self._cli = CCli()
                self._nfs = CNfs()
                self._uniq_strman = cup.util.CGeneratorMan()
                self._clearman = CClearMan()

            def setup(self):
                str_uniq = self._uniq_strman.get_uniqname()
                self._workfolder = os.path.abspath(os.getcwd()) \
                    + '/' + str_uniq
                self._work_remote_folder = \
                    self._nfs.translate_path_into_remote_under_rw_folder(
                    str_uniq
                    )
                os.mkdir(self._workfolder)
                self._clearman.addfolder(self._workfolder)

            def _check_filemd5(self, src, dst):
                ret = os.system('/usr/bin/diff --brief %s %s' % (src, dst) )
                cup.unittest.assert_eq( 0, ret )

            def test_run(self):
                #
                # @author: maguannan
                #
                inited_bigfile = sb_global.G_NFS_DISK_RD + \
                    sb_global.G_TEST_BIGFILE
                bigfile = self._workfolder + \
                    '/test_big_file_offsite_write_random_write'
                self.tmpfile = sb_global.G_TMP4USE + \
                    '/test_big_file_offsite_write_random_write'
                os.system( 'cp %s %s' % (inited_bigfile, bigfile) )
                os.system( 'cp %s %s' % (bigfile, self.tmpfile) )
                times = 50
                baseOffsite = 1000
                fp0 = open(bigfile, 'r+b')
                fp1 = open(self.tmpfile, 'rb+')
                for i in xrange( 0, times ):
                    fp0.seek(baseOffsite)
                    fp1.seek(baseOffsite)
                    fp0.write( 'a' * 100 )
                    fp1.write( 'a' * 100 )
                    baseOffsite += 1000
                fp0.close()
                fp1.close()

                self._check_filemd5(bigfile, self.tmpfile)

            def teardown(self):
                if self.get_result():
                    # if case succeeded, do sth
                    os.unlink(self.tmpfile)
                    self._clearman.teardown()
                else:
                    # if case failed, do sth else.
                    print 'failed'
                cup.log.info( 'End running ' + str(__file__ ) )

        if __name__ == '__main__':
            cup.unittest.CCaseExecutor().runcase(TestMyCase())
    """

    @classmethod
    def runcase(cls, case):
        """
        run the case
        """
        failed = False
        try:
            case.setup()
            case.test_run()
            case.set_result(True)
        # pylint: disable=W0703
        except Exception:
            print traceback.format_exc()
            case.set_result(False)
            failed = True
        # case.teardown()
        if failed:
            try:
                case.fail_teardown()
            # pylint: disable=W0703
            except Exception:
                pass
            print '========================'
            print '======== Failed ========'
            print '========================'
            sys.exit(-1)
        case.teardown()
        print '========================'
        print '======== Passed ========'
        print '========================'

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
