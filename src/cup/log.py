#!/usr/bin/python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    common log related module
"""
# pylint: disable=unspecified-encoding,broad-except
from __future__ import print_function

__all__ = [
    'debug', 'info', 'warning', 'critical',
    'init_comlog', 'setloglevel', 'ROTATION', 'INFINITE',
    'reinit_comlog', 'parse',
    'backtrace_info', 'backtrace_debug', 'backtrace_error',
    'backtrace_critical',
    'info_if', 'debug_if', 'warn_if', 'error_if', 'critical_if',

    # x* functions are for loggers other than logging.root (the global logger)
    'xinit_comlog', 'xdebug', 'xinfo', 'xwarn', 'xerror', 'xcritical'
]


import os
import re
import sys
import time
import logging
from logging import handlers
import threading
import collections

import cup
from cup import err
from cup import platforms


ROTATION = 0
INFINITE = 1

ROTATION_COUNTS = 30
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL
G_INITED_LOGGER = []


info = logging.info
warn = logging.warning
warning = logging.warning
error = logging.error
debug = logging.debug
critical = logging.critical


LoggerParams = collections.namedtuple('LoggerParams', [
    'loglevel',   # one of logging.INFO logging.DEBUG logging.xxx levels
    'logfile',    # valid logfile position,  e.g.   /home/test/test.log
    'logtype',    # log.ROTATION  log.INFINITE
    'maxlogsize', # logsize for one log, in bytes
    'bprint_console', # True, logger will printn to stdout, False, otherwise
    'gen_wf'          # True/False, generate log lines with level >= WARNNING
])


class _Singleton:  # pylint: disable=R0903
    """
    internal use for logging.  Plz use @Singoleton in cup.decorators
    """
    _LOCK = threading.Lock()

    def __init__(self, cls):
        self.__instance = None
        self.__cls = cls

    def __call__(self, *args, **kwargs):
        # pylint: disable=consider-using-with
        self._LOCK.acquire()
        if self.__instance is None:
            self.__instance = self.__cls(*args, **kwargs)
        self._LOCK.release()
        return self.__instance


# pylint: disable=too-few-public-methods
class _MsgFilter(logging.Filter):
    """
    Msg filters by log levels
    """
    # pylint: disable= super-init-not-called
    def __init__(self, msg_level=logging.WARNING):
        self.msg_level = msg_level

    def filter(self, record):
        if record.levelno >= self.msg_level:
            return False
        return True


class LogInitializer:
    """
    default log initalizer
    """
    # def config_filelogger(self,
    #     logger, loglevel, strlogfile, logtype,
    #     maxsize, bprint_console, gen_wf=False
    # ):  # too many arg pylint: disable=R0913
    # pylint:disable=too-many-locals
    @classmethod
    def setup_filelogger(cls, logger, logparams):
        """
        config logger
        """
        loglevel = logparams.loglevel
        strlogfile = logparams.logfile
        logtype = logparams.logtype
        maxsize = logparams.maxlogsize
        bprint_console = logparams.bprint_console
        gen_wf = logparams.gen_wf
        if not os.path.exists(strlogfile):
            try:
                if platforms.is_linux():
                    os.mknod(strlogfile)
                else:
                    # for py2 compatibility use

                    with open(strlogfile, 'w+') as fhandle:
                        fhandle.write('\n')
            except IOError as errinfo:
                raise IOError(
                    'logfile does not exist. '
                    'try to create it. but file creation failed'
                ) from errinfo
        logger.setLevel(loglevel)
        # '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s'
        tznum = time.strftime('%z')
        tzkey = time.strftime('%Z')
        formatter = logging.Formatter(
            fmt='%(levelname)s:\t %(asctime)s {0}({1}) * '
            '[%(process)d:%(thread)x] [%(filename)s:%(lineno)s] %(message)s'
            .format(tznum, tzkey)
        )
        if bprint_console:
            info('bprint_console enabled, will print to stdout')
            streamhandler = logging.StreamHandler()
            streamhandler.setLevel(loglevel)
            streamhandler.setFormatter(formatter)
            logger.addHandler(streamhandler)
        fdhandler = None
        if logtype == ROTATION:
            fdhandler = handlers.RotatingFileHandler(
                strlogfile, 'a', maxsize, ROTATION_COUNTS, encoding='utf-8'
            )
        else:
            fdhandler = logging.FileHandler(
                strlogfile, 'a', encoding='utf-8'
            )
        fdhandler.setFormatter(formatter)
        fdhandler.setLevel(loglevel)
        if gen_wf:
            # add .wf handler
            file_wf = str(strlogfile) + '.wf'
            warn_handler = logging.FileHandler(file_wf, 'a', encoding='utf-8')
            warn_handler.setLevel(logging.WARNING)
            warn_handler.setFormatter(formatter)
            logger.addHandler(warn_handler)
            fdhandler.addFilter(_MsgFilter(logging.WARNING))
        logger.addHandler(fdhandler)

    @classmethod
    def proc_thd_id(cls):
        """return proc thread id"""
        return '{0}:{1}'.format(
            os.getpid(), threading.current_thread().ident
        )

    @classmethod
    def get_codeline(cls, back=0):
        """get code line"""
        return sys._getframe(back + 1).f_lineno  # traceback pylint:disable=W0212

    @classmethod
    def get_codefile(cls, back=0):
        """
        get code file
        """
        # pylint: disable=W0212
        # to get code filename
        return os.path.basename(sys._getframe(back + 1).f_code.co_filename)

    @classmethod
    def log_file_func_info(cls, msg, back_trace_len=0):
        """return log traceback info"""
        tempmsg = ' * [%s] [%s:%s] ' % (
            cls.proc_thd_id(), cls.get_codefile(2 + back_trace_len),
            cls.get_codeline(2 + back_trace_len)
        )
        msg = '{0}{1}'.format(tempmsg, msg)
        if platforms.is_py2():
            # pylint: disable=undefined-variable
            if isinstance(msg, unicode):
                return msg
            return msg.decode('utf8')
        return msg


# pylint: disable=R0903
@_Singleton
class _RootLogerMan:
    _instance = None
    _rootlogger = None
    _b_rotation = False
    _logfile = ''
    _logtype = ROTATION
    _loggername = None

    def __init__(self):
        pass

    def get_rootlogger(self):
        """
        get default(root) logger
        """
        if self._rootlogger is None:
            raise err.LoggerException(
                'The Cup logger has not been initalized Yet. '
                'Call init_comlog first'
            )
        return self._rootlogger

    def set_rootlogger(self, loggername, logger):
        """
        set default(root) logger with a new loggername
        """
        if self._rootlogger is not None:
            raise err.LoggerException(
                """WARNING!!! The cup logger has been initalized already\
                .Plz do NOT init_comlog twice""")
        self._rootlogger = logger
        self._loggername = loggername

    def reset_rootlogger(self, logger):
        """reset root logger"""
        global G_INITED_LOGGER
        tmplogger = self._rootlogger
        while len(tmplogger.handlers) > 0:
            tmplogger.removeHandler(tmplogger.handlers[0])
        del tmplogger
        self._rootlogger = logger
        logging.root = logger

    def is_initalized(self):
        """
            Initialized or not
        """
        if self._rootlogger is None:
            return False
        return True


# too many arg pylint: disable=R0913
def init_comlog(loggername, loglevel=logging.INFO, logfile='cup.log',
                logtype=ROTATION, maxlogsize=1073741824, bprint_console=False,
                gen_wf=False):
    """
    Initialize your default logger

    :param loggername:
        Unique logger name for default logging.
    :param loglevel:
        4 default levels: log.DEBUG log.INFO log.ERROR log.CRITICAL
    :param logfile:
        log file. Will try to create it if no existence
    :param logtype:
        Two type candidiates: log.ROTATION and log.INFINITE

        log.ROTATION will let logfile switch to a new one (30 files at most).
        When logger reaches the 30th logfile, will overwrite from the
        oldest to the most recent.

        log.INFINITE will write on the logfile infinitely
    :param maxlogsize:
        maxmum log size with byte
    :param b_printcmd:
        print to stdout or not?
    :param gen_wf:
        print log msges with level >= WARNING to file (${logfile}.wf)

    *E.g.*
    ::

        import logging
        from cup import log
        log.init_comlog(
            'test',
            log.DEBUG,
            '/home/work/test/test.log',
            log.ROTATION,
            1024,
            False
        )
        log.info('test xxx')
        log.critical('test critical')

    """
    loggerman = _RootLogerMan()
    rootloger = logging.getLogger()
    if not loggerman.is_initalized():
        loggerman.set_rootlogger(loggername, rootloger)
        if os.path.exists(logfile) is False:
            if platforms.is_linux():
                os.mknod(logfile)
            else:
                with open(logfile, 'w+') as fhandle:
                    fhandle.write('\n')
        elif os.path.isfile(logfile) is False:
            raise err.LoggerException(
                'The log file exists. But it\'s not regular file'
            )
        loggerparams = LoggerParams(
            loglevel, logfile, logtype, maxlogsize, bprint_console, gen_wf
        )
        LogInitializer.setup_filelogger(rootloger, loggerparams)
        info('-' * 20 + 'Log Initialized Successfully' + '-' * 20)
        global G_INITED_LOGGER
        G_INITED_LOGGER.append(loggername)
    else:
        print('[{0}:{1}] init_comlog has been already initalized'.format(
            LogInitializer.get_codefile(1), LogInitializer.get_codeline(1)
        ))


# too many arg pylint: disable=R0913
def reinit_comlog(loggername, loglevel=logging.INFO, logfile='cup.log',
                  logtype=ROTATION, maxlogsize=1073741824,
                  bprint_console=False, gen_wf=False):
    """
    reinitialize default root logger for cup logging

    :param loggername:
        logger name, should be different from the original one
    """
    global G_INITED_LOGGER
    if loggername in G_INITED_LOGGER:
        msg = ('loggername:{0} has been already used!!! Change a name'.format(
            loggername))
        raise ValueError(msg)
    G_INITED_LOGGER.append(loggername)
    tmplogger = logging.getLogger(loggername)
    if os.path.exists(logfile) is False:
        if platforms.is_linux():
            os.mknod(logfile)
        else:
            with open(logfile, 'w+') as fhandle:
                fhandle.write('\n')
    elif os.path.isfile(logfile) is False:
        raise err.LoggerException(
            'The log file exists. But it\'s not regular file'
        )
    loggerman = _RootLogerMan()
    loggerparms = LoggerParams(
        loglevel, logfile, logtype, maxlogsize, bprint_console, gen_wf
    )
    LogInitializer.setup_filelogger(tmplogger, loggerparms)
    loggerman.reset_rootlogger(tmplogger)
    info('-' * 20 + 'Log Reinitialized Successfully' + '-' * 20)
    return


def _fail_handle(msg, e):
    if platforms.is_py2():
        # pylint: disable=undefined-variable
        if not isinstance(msg, unicode):
            msg = msg.decode('utf8')
        print('{0}\nerror:{1}'.format(msg, e))
    elif platforms.is_py3():
        print('{0}\nerror:{1}'.format(msg, e))


def backtrace_info(msg, back_trace_len=0):
    """
    info with backtrace support
    """
    try:
        msg = LogInitializer.log_file_func_info(msg, back_trace_len)
        loggerman = _RootLogerMan()
        loggerman.get_rootlogger().info(msg)
    except err.LoggerException:
        return
    except Exception as errinfo:
        _fail_handle(msg, errinfo)


def backtrace_debug(msg, back_trace_len=0):
    """
    debug with backtrace support
    """
    try:
        msg = LogInitializer.log_file_func_info(msg, back_trace_len)
        loggerman = _RootLogerMan()
        loggerman.get_rootlogger().debug(msg)
    except err.LoggerException:
        return
    except Exception as errinfo:
        _fail_handle(msg, errinfo)


def backtrace_warn(msg, back_trace_len=0):
    """
    warning msg with backtrace support
    """
    try:
        msg = LogInitializer.log_file_func_info(msg, back_trace_len)
        loggerman = _RootLogerMan()
        loggerman.get_rootlogger().warning(msg)
    except err.LoggerException:
        return
    # pylint: disable=broad-except
    except Exception as errinfo:
        _fail_handle(msg, errinfo)


def backtrace_error(msg, back_trace_len=0):
    """
    error msg with backtarce support
    """
    try:
        msg = LogInitializer.log_file_func_info(msg, back_trace_len)
        loggerman = _RootLogerMan()
        loggerman.get_rootlogger().error(msg)
    except err.LoggerException:
        return
    except Exception as errinfo:
        _fail_handle(msg, errinfo)


def backtrace_critical(msg, back_trace_len=0):
    """
    logging.CRITICAL with backtrace support
    """
    try:
        msg = LogInitializer.log_file_func_info(msg, back_trace_len)
        loggerman = _RootLogerMan()
        loggerman.get_rootlogger().critical(msg)
    except err.LoggerException:
        return
    # pylint:disable=broad-except
    except Exception as errinfo:
        _fail_handle(msg, errinfo)


def setloglevel(logginglevel):
    """
    change log level during runtime
    ::

        from cup import log
        log.setloglevel(log.DEBUG)
    """
    loggerman = _RootLogerMan()
    loggerman.get_rootlogger().setLevel(logginglevel)


def parse(logline):
    """
    return a dict if the line is valid.
    Otherwise, return None

    :raise Exception:
        ValueError if logline is invalid

    ::

        dict_info:= {
           'loglevel': 'DEBUG',
           'date': '2015-10-14',
           'time': '16:12:22,924',
           'pid': 8808,
           'tid': 1111111,
           'srcline': 'util.py:33',
           'msg': 'this is the log content',
           'tznum': 8,
           'tzstr': 'CST'
        }

    """
    content = logline[logline.rfind(']') + 1:].strip()
    # content = content[(content.find(']') + 1):]
    # content = content[(content.find(']') + 1):].strip()
    regex = re.compile('[ \t]+')
    items = regex.split(logline)
    loglevel, date, time_, timezone, _, pid_tid, src = items[0:7]
    pid, tid = pid_tid.strip('[]').split(':')
    tznum, tzkey = timezone.strip('+)').split('(')
    try:
        return {
            'loglevel': loglevel.strip(':'),
            'date': date,
            'time': time_,
            'pid': pid,
            'tid': tid,
            'srcline': src.strip('[]'),
            'msg': content,
            'tznum': int(tznum),
            'tzkey': tzkey
        }
    # pylint: disable = W0703
    except Exception as errinfo:
        raise ValueError(errinfo) from errinfo


def info_if(bol, msg, back_trace_len=1):
    """log msg with info loglevel if bol is true"""
    if bol:
        info(msg, back_trace_len)


def error_if(bol, msg, back_trace_len=1):
    """log msg with error loglevel if bol is true"""
    if bol:
        error(msg, back_trace_len)


def warn_if(bol, msg, back_trace_len=1):
    """log msg with error loglevel if bol is true"""
    if bol:
        warn(msg, back_trace_len)


def critical_if(bol, msg, back_trace_len=1):
    """log msg with critical loglevel if bol is true"""
    if bol:
        critical(msg, back_trace_len)


def debug_if(bol, msg, back_trace_len=1):
    """log msg with critical loglevel if bol is true"""
    if bol:
        debug(msg, back_trace_len)


def xinit_comlog(loggername, logger_params):
    """
    xinit_comlog along with xdebug xinfo xwarn xerror are functions for
    different loggers other than logging.root (the global logger).

    :param loggername:
        loggername, example:  http.access,

    :param logger_params:
        object of LoggerParams

    Code example:
    ::

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

    """
    if not isinstance(logger_params, LoggerParams):
        raise TypeError('logger_params should be a object of log.LoggerParams')
    logger = logging.getLogger(loggername)
    LogInitializer.setup_filelogger(logger, logger_params)


def xdebug(loggername, msg, back_trace_len=1):
    """
    :param loggername:
        shoule be xinit_comlog before calling xdebug/xinfo/xerror/xcritical
    :param msg:
        log msg
    :back_trace_len:
        1 by default, ignore this if you don't need this
    """
    logger = logging.getLogger(loggername)
    logger.debug(LogInitializer.log_file_func_info(msg, back_trace_len))


def xinfo(loggername, msg, back_trace_len=1):
    """
    :param loggername:
        shoule be xinit_comlog before calling xdebug/xinfo/xerror/xcritical
    :param msg:
        log msg
    :back_trace_len:
        default 1, just ignore this param if you don't know what it is.
        This param will trace back 1 layer and get the
        [code_filename:code_lines]

    """
    logger = logging.getLogger(loggername)
    logger.info(LogInitializer.log_file_func_info(msg, back_trace_len))


def xwarn(loggername, msg, back_trace_len=1):
    """
    :param loggername:
        shoule be xinit_comlog before calling xdebug/xinfo/xerror/xcritical
    :param msg:
        log msg
    :back_trace_len:
        default 1, just ignore this param if you don't know what it is.
        This param will trace back 1 layer and get the
        [code_filename:code_lines]

    """
    logger = logging.getLogger(loggername)
    logger.warning(LogInitializer.log_file_func_info(msg, back_trace_len))


def xerror(loggername, msg, back_trace_len=1):
    """
    :param loggername:
        shoule be xinit_comlog before calling xdebug/xinfo/xerror/xcritical
    :param msg:
        log msg
    :back_trace_len:
        default 1, just ignore this param if you don't know what it is.
        This param will trace back 1 layer and get the
        [code_filename:code_lines]

    """
    logger = logging.getLogger(loggername)
    logger.error(LogInitializer.log_file_func_info(msg, back_trace_len))


def xcritical(loggername, msg, back_trace_len=1):
    """
    :param loggername:
        shoule be xinit_comlog before calling xdebug/xinfo/xerror/xcritical
    :param msg:
        log msg
    :back_trace_len:
        default 1, just ignore this param if you don't know what it is.
        This param will trace back 1 layer and get the
        [code_filename:code_lines]

    """
    logger = logging.getLogger(loggername)
    logger.critical(LogInitializer.log_file_func_info(msg, back_trace_len))


if __name__ == '__main__':
    cup.log.debug('中文')
    cup.log.init_comlog(
        'test', cup.log.DEBUG, './test.log',
        cup.log.ROTATION, 102400000, False
    )
    cup.log.init_comlog(
        'test', cup.log.DEBUG, './test.log',
        cup.log.ROTATION, 102400000, False
    )
    cup.log.info('test info')
    cup.log.debug('test debug')
    cup.log.info('中文'.decode('utf8'))
    cup.log.reinit_comlog(
        're-test', cup.log.DEBUG, './re.test.log',
        cup.log.ROTATION, 102400000, False
    )
    cup.log.reinit_comlog(
        're-test', cup.log.DEBUG, './re.test.log',
        cup.log.ROTATION, 102400000, False
    )
    cup.log.info('re:test info')
    cup.log.debug('re:test debug')
    cup.log.debug('re:中文')


# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
