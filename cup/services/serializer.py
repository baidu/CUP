#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    serilizers including local file serilizer
"""
import os
import time
import traceback
import threading
import collections

from cup import log
from cup import exfile

__all__ = [
    'LOGFILE_GOOD', 'LOGFILE_EOF', 'LOGFILE_BAD_RECORD', 'LOG_MOD_ADD',
    'LOG_MOD_SET', 'LOG_MOD_DEL', 'LogRecord', 'LocalFileSerilizer'
]

LOGFILE_GOOD = 0
LOGFILE_EOF = 1
LOGFILE_BAD_RECORD = 2

LOG_MOD_ADD = 0
LOG_MOD_SET = 1
LOG_MOD_DEL = 3

LogRecord = collections.namedtuple(
    'LogRecord', ['length', 'log_id', 'log_type', 'log_mode', 'log_binary']
)


class BaseSerilizer(object):
    """base serilizer for agent"""
    def __init__(self):
        """pass"""

    def add_log(self, log_type, log_mode, log_binary):
        """add one log"""

    def load_logs(self, record_num):
        """pass"""

    @classmethod
    def asign_uint2byte_bybits(cls, num, bits):
        """uint to byte"""
        asign_len = bits / 8
        tmp = ''
        i = 0
        while True:
            quotient = int(num / 256)
            remainder = num % 256
            tmp += chr(remainder)
            if quotient < 256:
                tmp += chr(quotient)
                break
            else:
                num = quotient
            i += 1
        length = len(tmp)
        if length < asign_len:
            for _ in range(0, asign_len - length):
                tmp += chr(0)
        return tmp

    @classmethod
    def convert_bytes2uint(cls, str_data):
        """convert bytes into uint"""
        num = 0
        b_ind = 0
        for i in str_data:
            num += pow(256, b_ind) * ord(i)
            b_ind += 1
        return num


MsgPostRevision = collections.namedtuple(
    'MsgPostRevision', ['hostkey', 'revision_id', 'is_post']
)


class LocalFileSerilizer(BaseSerilizer):
    """ local file serilizer"""
    def __init__(
        self, storage_dir, skip_badlog=False, max_logfile_size=1024 * 1024,
        persist_after_sec=10 * 60
    ):
        """

        :param skip_badlog:
            Attention. Plz use this parameter very carefully.
            It will skip bad records which means you have high chance
            losing data!!!
        :param persist_after_sec:

        """
        BaseSerilizer.__init__(self)
        self._skip_badlog = skip_badlog
        self._storage = os.path.abspath(storage_dir)
        self._logid = 0
        self._max_log_file_size = max_logfile_size
        self._current_filesize = 0
        self._writestream = None
        self._load_stream = None
        self._current_loadfile = None
        self._buffer_files = None
        self._persist_sec = persist_after_sec
        self._record_lenbytes = 4

        self._loglist_stream = None
        self._loglist_switching = False
        self._logfile_list = '{0}/logfile.list'.format(storage_dir)
        self._logfile_listnew = '{0}.new'.format(self._logfile_list)
        self._logfile_listold = '{0}.old'.format(self._logfile_list)
        self._loglist_switch = '{0}.switch'.format(self._logfile_list)
        self._mlock = threading.Lock()
        self._name = self.__class__

    def set_name(self, name):
        """set a name of str for the serializer"""
        self._name = 'serilizer: ({0})'.format(name)

    @classmethod
    def __cmp_logfile_id(cls, first, second):
        """compare first and second"""
        key_first, value_first = first.split('.')
        key_second, value_second = second.split('.')
        if key_first < key_second:
            return -1
        elif key_first > key_second:
            return 1
        elif key_first == key_second:
            if int(value_first) <= int(value_second):
                return -1
            else:
                return 1

    def _get_storage_dir(self, logid=-1, logtype=None, logmode=None):
        """get storage dir"""
        folder = '{0}/{1}'.format(self._storage, self.get_subdir())
        return folder

    def _recover_from_lastwriting(self, truncate_last_failure=True):
        """
        recovery from last log writing

        :raise Exception:
            IOError, if any error happened
        """
        folder = self._get_storage_dir()
        files = self._get_ordered_logfiles(folder)
        need_finish_file = False
        if len(files) < 1:
            log.info('no need recovery. Does not contain any files')
            return
        file_start_logid = -1
        seek_file = None
        if files[-1].find('writing') < 0:
            # does not need recovery
            log.info('does not have unfinished logfile, return')
            file_start_logid = int(files[-1].split('.')[-1]) + 1
            seek_file = files[-1]
            log.info('next logid will be {0}'.format(self._logid))
        else:
            # need recovery, checkup, must <= 0 writing log file
            count = 0
            for fname in files:
                if fname.find('writing') >= 0:
                    count += 1
            if count > 1:
                errmsg = 'has more than 1 writing log files, count:{0}'
                log.error(errmsg.format(count))
                raise IOError(errmsg)
            log.info('has not finished log file, recovery start')

            seek_file = files[-1]
            file_start_logid = int(seek_file.split('.')[-1])
        fullname = os.path.normpath('{0}/{1}'.format(folder, seek_file))
        done_id = file_start_logid
        read_length = 0
        try:
            reader = open(fullname, 'r')
            while True:
                ret, _ = self._try_read_one_log(reader)
                if ret == LOGFILE_BAD_RECORD:
                    if truncate_last_failure:
                        log.info(
                            'to truncate last writing file:{0}'
                            ', size:{1}'.format(
                                files[-1], read_length)
                        )
                        reader.close()
                        reader = open(fullname, 'w')
                        reader.truncate(read_length)
                        reader.close()
                        reader = open(fullname, 'r')
                        break
                    else:
                        raise IOError(
                            'truncate_last_failure is not enabled &&'
                            ' Bad record found'
                        )
                elif ret == LOGFILE_EOF:
                    log.info('log file is intact, no need truncating')
                    break
                elif ret == LOGFILE_GOOD:
                    done_id += 1
                    read_length = reader.tell()
                newname = os.path.normpath('{0}/{1}'.format(
                    folder, 'done.{0}'.format(file_start_logid))
                )
            if fullname != newname:
                log.info('move last writing file {0} to {1}'.format(
                    fullname, newname)
                )
                os.rename(fullname, newname)
                self._loglist_stream.write('{0}\n'.format(newname))
                self._loglist_stream.flush()
                os.fsync(self._loglist_stream.fileno())
            self._logid = done_id
            log.info('next logid will be {0}'.format(self._logid))
        except Exception as err:
            log.error('failed to recover from last log:{0}'.format(err))
            raise IOError(err)
        return

    def __del__(self):
        try:
            if self._writestream is not None:
                self._writestream.close()
            if self._load_stream is not None:
                self._load_stream.close()
        # pylint:disable=W0703
        except Exception:
            pass

    def _stream_close(self):
        """close the current stream"""
        self._writestream.close()

    def _stream_wbopen(self, fname):
        """open new stream"""
        ret = False
        try:
            parent = os.path.dirname(fname)
            if not os.path.exists(parent):
                os.makedirs(parent)
            self._writestream = open(fname, 'w+b')
            log.debug('open new stream succeed')
            ret = True
        except IOError as err:
            log.error(
                'IOError, failed to open stream, err:{0}, file:{1}'.format(
                    err, fname
                )
            )
        except OSError as err:
            log.error(
                'OSError, failed to open stream, err:{0}, file:{1}'.format(
                    err, fname
                )
            )
        return ret

    def is_stream_wbopen(self):
        """is stream open"""
        if self._writestream is None:
            return False
        else:
            return True

    def _get_next_logfile(self, logid):
        """get current logfile"""
        folder = self._get_storage_dir(logid=logid)
        fname = '{0}/writing.{1}'.format(folder, logid)
        return fname

    def get_subdir(self, log_id=-1):
        """get log dir"""
        return "0"

    def _get_ordered_logfiles(self, folder):
        """get log files in order"""
        try:
            files = sorted(os.listdir(folder), cmp=self.__cmp_logfile_id)
        except TypeError:
            import functools
            files = sorted(os.listdir(folder), key=functools.cmp_to_key(
                self.__cmp_logfile_id)
            )
        retfiles = []
        for item in files:
            if any([
                len(item.split('.')) != 2,
                item.find('done.') < 0 and item.find('writing.') < 0
            ]):
                log.info('file name {0} invalid, will skip'.format(item))
                continue
            retfiles.append(item)
        return retfiles

    def set_current_logid(self, logid):
        """reset current log id"""
        if logid < 0:
            raise ValueError('cannot setup logid less than 0')
        self._logid = logid
        fname = self._get_next_logfile(self._logid)
        if not self._stream_wbopen(fname):
            log.error('failed to open stream, return False')
            return False
        log.info('reset current log id to {0}'.format(logid))
        return True

    def _write_data(self, binary):
        """ write data into the local file"""
        try:
            self._writestream.write(binary)
            self._writestream.flush()
            os.fsync(self._writestream.fileno())
            self._logid += 1
        # pylint: disable=W0703
        # need to catch such general exeception
        except Exception as error:
            log.error(
                'failed to write data into LocalFileSerilizer, err:{0}'.format(
                    error)
            )
            return False
        return True

    def _check_need_new_logfile(self):
        """if need new log file"""
        if os.path.exists(self._loglist_switch) and \
                (not self._loglist_switching):
            # start to switch
            log.info('{0} loglist start to switch'.format(self._name))
            self._loglist_switching = True
            self._loglist_stream.write('NEED_SWITCH_LOCALFILE\n')
            self._loglist_stream.flush()
            os.fsync(self._loglist_stream)
            self._loglist_stream.close()
            if not os.path.exists(self._logfile_listnew):
                try:
                    exfile.mk_newnode(self._logfile_listnew)
                # pylint: disable=W0703
                except Exception as err:
                    log.error('switch loglist file failed:{0}'.format(err))
                    return False
            log.info('{0} loglist file {1} switched'.format(
                self._name, self._logfile_list)
            )
            os.rename(self._logfile_list, self._logfile_listold)
            os.rename(self._logfile_listnew, self._logfile_list)
            self._loglist_stream = open(self._logfile_list, 'a')
            self._loglist_switching = False
        if self._current_filesize >= self._max_log_file_size:
            # log.info('serilizer file needs moving to a new one')
            last_logid = self._writestream.name.split('.')[-1]
            newname = os.path.normpath('{0}/done.{1}'.format(
                os.path.dirname(self._writestream.name), last_logid
            ))
            log.info(
                'finish one log file, logid, range:{0}-{1}'.format(
                    last_logid, self._logid - 1
                )
            )
            os.rename(self._writestream.name, newname)
            self._stream_close()
            self._loglist_stream.write('{0}\n'.format(newname))
            self._loglist_stream.flush()
            os.fsync(self._loglist_stream.fileno())
            self._current_filesize = 0
            fname = self._get_next_logfile(self._logid)
            if not self._stream_wbopen(fname):
                return False
        return True

    def is_empty(self):
        """return if there is no log"""
        folder = self._get_storage_dir()
        files = self._get_ordered_logfiles(folder)
        if len(files) < 1:
            return True
        else:
            return False

    def switch_logfilelist(self):
        """switch logfile to logfile.old"""
        log.info('serializer ({0}) to swtich loglist'.format(self._name))
        if not os.path.exists(self._loglist_switch):
            exfile.mk_newnode(self._loglist_switch)

    def add_log(self, log_type, log_mode, log_binary):
        """add log into the local file

        :return:
            a tuple (result_True_or_False, logid_or_None)
        """
        self._mlock.acquire()
        ret = (True, None)
        if not self.is_stream_wbopen():
            fname = self._get_next_logfile(self._logid)
            if not self._stream_wbopen(fname):
                ret = (False, None)
        if ret[0]:
            # binary :=
            # 32bit len | 128bit logid | log_type 16bit | log_mode 16bit| bin
            bin_logid = self.asign_uint2byte_bybits(self._logid, 128)
            bin_type = self.asign_uint2byte_bybits(log_type, 16)
            bin_mode = self.asign_uint2byte_bybits(log_mode, 16)
            data = '{0}{1}{2}{3}'.format(
                bin_logid, bin_type, bin_mode, log_binary
            )
            data_len = len(data)
            str_data_len = self.asign_uint2byte_bybits(
                data_len, self._record_lenbytes * 8)
            write_data = '{0}{1}'.format(str_data_len, data)
            log.info('{0} add_log, type {1} mode {2}, logid {3}, '
                'datelen:{4}'.format(
                self._name, log_type, log_mode, self._logid, data_len)
            )
            if self._write_data(write_data):
                self._current_filesize += (data_len + len(str_data_len))
                if not self._check_need_new_logfile():
                    ret = (False, None)
                else:
                    ret = (True, self._logid)
            else:
                log.error('failed to add_log(type:{} mode {}'.format(
                    log_type, log_mode)
                )
                ret = (False, None)
        self._mlock.release()
        return ret

    def purge_data(self, before_logid):
        """
        log files which contains log (less than before_logid) will be purged.
        """
        folder = self._get_storage_dir()
        logfiles = self._get_ordered_logfiles(folder)
        last_logid = None
        last_fname = None
        purge_list = []
        for fname in logfiles:
            if fname.find('writing') >= 0:
                continue
            current = int(fname.split('.')[-1])
            if last_logid is not None and (current - 1) < before_logid:
                purge_list.append(last_fname)
            last_fname = fname
            last_logid = current
        log.info('log id < before_logid will be purged:purged:{0}'.format(
            purge_list)
        )
        ind = 0
        for fname in purge_list:
            full = '{0}/{1}'.format(folder, fname)
            log.info('to purge log file:{0}'.format(full))
            try:
                os.remove(full)
                ind += 1
            except StandardError as err:
                log.error(
                    'failed to purge log file:{0}, {1}'.format(full, err)
                )
            if ind % 1000:
                time.sleep(0.1)
        log.info(
            '{0} purge data finished, to switch loglist'.format(self._name)
        )
        self.switch_logfilelist()

    def _do_open4read(self, start_logid=-1):
        """
        get open load stream

        :TODO:
            read starting from logid
        """
        load_dir = self._get_storage_dir(logid=self._logid)
        self._buffer_files = self._get_ordered_logfiles(load_dir)
        to_open = None
        if len(self._buffer_files) <= 0:
            log.warn('does not have any log record yet')
        else:
            if -1 == start_logid:
                to_open = self._buffer_files[0]
            else:
                pass
                # if self._load_stream is None:
                #     log.error('load stream should not be None')
                #     return False
                # name = os.path.basename(self._load_stream.name)
                # ind = -1
                # try:
                #     ind = self._buffer_files.index(name)
                # except ValueError:
                #     log.error('does not find the log: {0}'.format(name))
                #     return False
                # to_open = self._buffer_files[ind]
            try:
                fname = '{0}/{1}'.format(load_dir, to_open)
                self._load_stream = open(fname, 'rb')
                return True
            # pylint:disable=W0703
            # need such an exception
            except Exception as err:
                log.error('failed to open log stream :{0}'.format(err))
                return False

    def close_read(self):
        """close open4read"""
        if self._load_stream is None:
            self._load_stream.close()

    def open4read(self):
        """open logs for read"""
        if self._load_stream is None:
            if not self._do_open4read():
                log.error('failed to open4read, return')
                return False
            else:
                return True

    def open4write(self, truncate_last_failure=True):
        """
        open4write

        :raise Exception:
            if encounter any IOError, will raise IOError(errmsg)
        """
        try:
            if not os.path.exists(self._logfile_list):
                exfile.mk_newnode(self._logfile_list)
            self._loglist_stream = open(self._logfile_list, 'a')
        except Exception as err:
            log.error('cannot create loglist, raise IOError')
            raise IOError('cannot create loglist, {0}'.format(err))
        log.info(
            '{0} try to recover from last '
            'write if there is any need, truncate_last_failure:{1}'.format(
                self._name, truncate_last_failure)
        )
        self._recover_from_lastwriting(truncate_last_failure)

    def close_write(self):
        """close the writer"""
        if self._writestream is not None:
            self._writestream.close()

    def _try_read_one_log(self, stream):
        """
        read one log record from the stream_close.

        :return:

        """
        if stream is None:
            return (LOGFILE_EOF, None)
        str_datalen = datalen = str_data = None
        try:
            str_datalen = stream.read(self._record_lenbytes)
            if len(str_datalen) == 0:
                return (LOGFILE_EOF, None)
            if len(str_datalen) < self._record_lenbytes:
                log.warn('got a bad log from stream:{0}'.format(stream.name))
                return (LOGFILE_BAD_RECORD, None)
            datalen = self.convert_bytes2uint(str_datalen)
            str_data = stream.read(datalen)
            if len(str_data) < datalen:
                log.warn(
                    'got less than data len from stream:{0}'.format(
                        stream.name)
                )
                return (LOGFILE_BAD_RECORD, None)
            log_id = self.convert_bytes2uint(str_data[0: 16])
            log_type = self.convert_bytes2uint(str_data[16: 16 + 2])
            log_mode = self.convert_bytes2uint(str_data[18: 18 + 2])
            log_binary = str_data[20:]
            return (
                LOGFILE_GOOD, LogRecord(
                    datalen, log_id, log_type, log_mode, log_binary
                )
            )
        except Exception as err:
            log.error('failed to parse log record:{0}'.format(err))
            log.error(traceback.format_exc())
            return (LOGFILE_BAD_RECORD, None)

    def _move2next_load_fname(self):
        """ get next load fname"""
        folder = self._get_storage_dir()
        fname = os.path.basename(self._load_stream.name)
        files = self._get_ordered_logfiles(folder)
        length = len(files)
        ind = -1
        try:
            ind = files.index(fname)
        except ValueError:
            log.error('cannot find current log stream:{0}'.format(fname))
            return LOGFILE_BAD_RECORD
        newfile = None
        if ind < (length - 2):
            newfile = '{0}/{1}'.format(folder, files[ind + 1])
        elif ind == (length - 2):
            if files[length - 1].find('writing') < 0:
                newfile = '{0}/{1}'.format(folder, files[length - 1])
            else:
                log.debug('does not have more finished log edits to read')
                return LOGFILE_EOF
        elif ind == (length - 1):
            log.info('does not have more log edits to read, return')
            return LOGFILE_EOF
        try:
            self._load_stream.close()
            self._load_stream = open(newfile, 'rb')
            return LOGFILE_GOOD
        except StandardError as err:
            log.error('failed to move to next load stream:{0}'.format(newfile))
            log.error('err:{0}'.format(err))
            return LOGFILE_BAD_RECORD

    def read(self, record_num=128):
        """
        load log into memory

        :notice:
            If skip_badlog is not True, will raise IOError if the stream
            encounters any error.

            Otherwise, the stream will skip the bad log file, move to next one
            and continue reading

        :return:
            a. return a list of "record_num" of LogRecord.

            b. If the count number of list is less than record_num,
            it means the stream encounter EOF, plz read again afterwards.

            c. If the returned is None, it means the stream got nothing, plz
                try again.
        """
        recordlist = []
        count = 0
        move2nextstream = False
        while count < record_num:
            ret, retval = self._try_read_one_log(self._load_stream)
            if ret == LOGFILE_EOF:
                # need read next log file
                move2nextstream = True
            elif ret == LOGFILE_GOOD:
                recordlist.append(retval)
                count += 1
                continue
            elif ret == LOGFILE_BAD_RECORD:
                if not self._skip_badlog:
                    raise IOError(
                        'find bad records in {0}'.format(
                            self._load_stream.name)
                    )
                else:
                    log.warn(
                        'Bad record! '
                        'But skip_badlog is on, will skip the file:{0}'.format(
                            self._load_stream.name)
                    )
                    move2nextstream = True
            if move2nextstream:
                move2nextstream = False
                ret = self._move2next_load_fname()
                if LOGFILE_EOF == ret:
                    log.debug('no more log edits to read, plz retry')
                    break
                elif LOGFILE_GOOD == ret:
                    log.debug('moved to next log edit file, to read new log')
                    continue
                elif LOGFILE_BAD_RECORD == ret:
                    log.error('IOError happended, read_logs failed')
                    if self._skip_badlog:
                        log.error('skip bad log is on, try moving to next one')
                        move2nextstream = True
                        continue
                    else:
                        raise IOError('encounter bad records, raise exception')
        return recordlist

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
