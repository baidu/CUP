#!/usr/bin/python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Minghao Zhao, Liu Xuan, Guannan Ma
"""
:desc:
    unittest module
"""
from __future__ import print_function
import os
import sys
import hashlib
import traceback
import logging

from cup import log
from cup import err

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
    'expect_raise'
]


def _assert_bool(val, exp, errmsg=''):
    """assert bool, val should be exp (either True or False)"""
    if val is not exp:
        msg = 'got {0}, expect {1}\nUser ErrMsg: {2}'.format(val, exp, errmsg)
        try:
            log.backtrace_critical(msg, 2)
        # pylint: disable=W0703
        except Exception:
            pass
        assert False, msg


def assert_true(val, errmsg=''):
    """
    If val is not True, assert False and print to stdout.

    Plz notice, log.critical(errmsg) will be invoked if logging system has
    been initialized with cup.log.init_comlog.
    """
    if not isinstance(val, bool):
        raise TypeError('The type of val is not bool')
    _assert_bool(val, True, errmsg)


def assert_false(val, errmsg=''):
    """
    val should be False. Assert False otherwise.
    """
    if not isinstance(val, bool):
        raise TypeError('The type of val is not bool')
    _assert_bool(val, False, errmsg)


def assert_eq(val, exp, errmsg=''):
    """
    if val != exp, aseert False and print errmsg
    """
    if val != exp:
        msg = 'got {0}, expect {1}\nUser ErrMsg: {2}'.format(val, exp, errmsg)
        try:
            log.backtrace_critical(msg, 1)
        # pylint: disable=W0703
        except Exception:
            pass
        assert False, msg


def assert_not_eq(val, exp, errmsg=''):
    """
    assert not equal to
    """
    if val == exp:
        msg = 'got {0} which is equal, expect not equal \n'\
            'User ErrMsg: {1}'.format(val, errmsg)
        try:
            log.backtrace_critical(msg, 1)
        # pylint: disable=W0703
        except Exception:
            pass
        assert False, msg


def assert_eq_one(val, array, errmsg=''):
    """
    assert val equals one of the items in the [array]
    """
    equal = False
    str_arr = ''
    for i in array:
        str_arr += '|' + str(i) + '|'
        if i == val:
            equal = True
            break
    if not equal:
        msg = 'got {0}, expect one in the array: {1}\nUser ErrMsg: {2}'.format(
            val, str_arr, errmsg
        )
        try:
            log.backtrace_critical(msg, 1)
        # pylint: disable=W0703
        except Exception:
            pass
        assert False, msg


def assert_in(val, array, errmsg=''):
    """
    same to assert_eq_one, for backward compatibility
    """
    assert_eq_one(val, array, errmsg)


def assert_not_in(val, iteratables, errmsg=''):
    """
    assert val not equal any item in [iteratables (e.g. a list)]
    """
    if val in iteratables:
        assert False, 'val :%s in iteratables. ErrMsg:%s' % (val, errmsg)


def assert_lt(val, exp, errmsg=''):
    """
    assert_lt, expect val < exp
    """
    if val >= exp:
        msg = 'got {0}, expect less than {1}\nUser ErrMsg:{2}'.format(
            val, exp, errmsg
        )
        try:
            log.backtrace_critical(msg, 1)
        # pylint: disable=W0703
        except Exception:
            pass
        assert False, msg


def assert_gt(val, exp, errmsg=''):
    """
    assert_gt, expect val > exp
    """
    if val <= exp:
        msg = 'got {0}, expect greater than {1}\nUser ErrMsg: {2}'.format(
            val, exp, errmsg
        )
        try:
            log.backtrace_critical(msg, 1)
        # pylint: disable=W0703
        except Exception:
            pass
        assert False, msg


def assert_ge(val, exp, errmsg=''):
    """
    expect val >= exp
    """
    if val < exp:
        msg = ('got {0}, expect greater than (or equal to) {1}\n'\
            'User ErrMsg:{2}'.format(val, exp, errmsg))
        try:
            log.backtrace_critical(msg, 1)
        # pylint: disable=W0703
        except Exception:
            pass
        assert False, msg


def assert_le(val, exp, errmsg=''):
    """
    expect val <= exp
    """
    if val > exp:
        msg = 'got {0}, expect less than (or equal to) {1}\n'\
            'User ErrMsg:{2}'.format(val, exp, errmsg)
        try:
            log.backtrace_critical(msg, 1)
        # pylint: disable=W0703
        except Exception:
            pass
        assert False, msg


def assert_ne(val, exp, errmsg=''):
    """
    expect val != exp
    """
    if val == exp:
        msg = 'Expect non-equal, got two equal values'\
            '{0}:{1}\nUser Errmsg:{2}'.format(val, exp, errmsg)
        try:
            log.backtrace_critical(msg, 1)
        # pylint: disable=W0703
        except Exception:
            pass
        assert False, errmsg


def assert_boundary(val, low, high, errmsg=None):
    """
    expect low <= val <= high
    """
    if val < low:
        msg = 'Expect low <= val <= high, '\
            'but val:{0} < low:{1}, msg:{2}'.format(val, low, errmsg)
        assert False, msg
    if val > high:
        msg = 'Expect low <= val <= high, but val:%s > high:%s, msg:%s' % (
            val, high, errmsg
        )
        assert False, msg


def _get_md5_hex(src_file):
    """get md5 hext string of a file"""
    with open(src_file, 'rb') as fhandle:
        md5obj = hashlib.md5()
        while True:
            strtmp = fhandle.read(131072)  # read 128k
            if len(strtmp) <= 0:
                break
            md5obj.update(strtmp.encode('utf-8'))
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
    CUTCase is compatible with nosetests. You can inherit this class
    and implement your own TestClass.

    Notice class method [set_result] will set case status to True/False after
    executing the case. Then you can get case status in teardown through
    calling class method [get_result]
    """
    def __init__(self, logfile='./test.log', b_logstd=False, b_debug=False):
        """
        :param logfile:
            will invoke log.init_comlog to intialize logging in order to
            support invoking logging functions log.info/debug/warn
        :param b_logstd:
            print to stdout or not
        :param b_debug:
            enable debug mode or not.
            If enabled, log level will be set to log.DEBUG.
            log.INFO (log level) will be set by default.
        """
        self._result = False
        if b_debug:
            debuglevel = logging.DEBUG
        else:
            debuglevel = logging.INFO

        log.init_comlog(
            'test_case', debuglevel,
            logfile, log.ROTATION, 5242880, b_logstd
        )

    def setup(self):
        """
        set up
        """
        pass

    def test_run(self):
        """
        test_run function
        """
        pass

    def set_result(self, b_result):
        """
        set case running status
        """
        self._result = b_result

    def get_result(self):
        """
        get case status during case teardown
        """
        return self._result

    def teardown(self):
        """
        teardown
        """
        pass


# pylint: disable=R0903
class CCaseExecutor(object):
    """
    Executor class for executing CUTCase test cases. See the example below

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
                for i in range( 0, times ):
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
            print(traceback.format_exc())
            case.set_result(False)
            failed = True
        # case.teardown()
        if failed:
            try:
                case.fail_teardown()
            # pylint: disable=W0703
            except Exception:
                pass
            print('========================')
            print('======== Failed ========')
            print('========================')
            sys.exit(-1)
        case.teardown()
        print('========================')
        print('======== Passed ========')
        print('========================')


def expect_raise(function, exception, *argc, **kwargs):
    """expect raise exception"""
    try:
        function(*argc, **kwargs)
        raise err.ExpectFailure(exception, None)
    except exception:
        pass
    else:
        raise err.ExpectFailure(exception, None)

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
