#!/usr/bin/python
# -*- coding: utf-8 -*
# #############################################################################
#
#  Copyright (c) 2014 Baidu.com,  Inc. All Rights Reserved
#
# #############################################################################
"""
:author:
    Guannan Ma
:create_date:
    2014
:last_date:
    2016.6
:descrition:
    netmsg related module
"""

import json

import cup
from cup import log
from cup.util import misc
from cup.net.async import common


__all__ = ['CMsgType', 'CMsgFlag', 'CNetMsg', 'CAckMsg']


# TODO serilize the msg
# class MsgSerilizer(object):
#     def __init__(self, body):
#         pass
#
#     def serilize(self):
#         pass
#
#     def deserlize(self, pack):
#         pass

@cup.decorators.Singleton
class CMsgType(object):
    """
    for netmsg types
    """
    def __init__(self):
        self._type2number = {}
        self._number2type = {}

    def register_types(self, kvs):
        """
        register types
        """
        for key_value in kvs.items():
            self._type2number[key_value[0]] = key_value[1]
            self._number2type[str(key_value[1])] = key_value[0]

    def gettype_bynumber(self, number):
        """
        get type by number
        """
        return self._number2type[str(number)]

    def getnumber_bytype(self, str_type):
        """
        get number by type
        """
        return self._type2number[str_type]


@cup.decorators.Singleton
class CMsgFlag(object):
    """
    msg flag class
    """
    def __init__(self):
        self._flag2number = {}
        self._number2flag = {}

    def register_flags(self, kvs):
        """
        register flags
        """
        for key_value in kvs.keys():
            self._flag2number[key_value[0]] = key_value[1]
            self._number2flag[str(key_value[1])] = key_value[0]

    def getflag_bynumber(self, number):
        """
        get flag by number
        """
        return self._number2flag[str(number)]

    def getnumber_byflag(self, str_flag):
        """
        get number by flag
        """
        return self._flag2number[str_flag]


class CNetMsg(object):
    """
    CNetMsg
        flag: System use only.
        type: System will use type > 65535. Users will use type <=65535

        #head 0, \SAGIT\0\1 for building connection
        #len - uint64
        #fromip,port, stub -uint64
        #toip,port, stub   -uint64
        #msg_type          -uint32
        #uniqid            -uint64
        #body           -no limit (length:uint64)

    """

    # length 8
    MSG_SIGN = 'CUP012-3'

    _ORDER = [
        'head', 'flag', 'len', 'from', 'to', 'type', 'uniq_id', 'body'
    ]
    _ORDER_BYTES = [8, 4, 8, 16, 16, 4, 8, 0]
    _SIZE_EXCEPT_BODY = 64
    _SIZE_EXCEPT_HEAD_BODY = 56
    _ORDER_COUNTS = 8

    # Default flags
    MSG_FLAG_MAN = CMsgFlag()
    _MSG_FLAGS = {
        'URGENT': 0x00000001,
        'NORMAL': 0X00000002
    }
    MSG_FLAG_MAN.register_flags(_MSG_FLAGS)

    # Default types.
    MSGTYPE = CMsgType()
    _SYS_MSG_TYPES = {
        'ACK': 65536
    }
    MSGTYPE.register_types(_SYS_MSG_TYPES)

    def __init__(self, is_postmsg=True):
        super(self.__class__, self).__init__()
        self._is_postmsg = is_postmsg
        self._need_head = False
        self._data = {}
        self._readindex = 0
        self._writeindex = 0
        self._msg_finish = False
        self._context = None
        self._msglen = None
        self._bodylen = None
        self._type = None
        self._flag = None
        self._uniqid = None
        self._fromaddr = None
        self._toaddr = None
        self._dumpdata = None

    def __del__(self):
        """del the msg"""
        if 'body' in self._data:
            del self._data['body']
        if self._data is not None:
            del self._data
        if self._dumpdata is not None:
            del self._dumpdata

    def get_order_counts(self):
        """
        get order counts
        """
        return self._ORDER_COUNTS

    def _get_msg_order_ind(self, index):
        ind = index
        if self._need_head is not True:
            i = 1
        else:
            i = 0
        log.debug('msg index:{0}'.format(
            index)
        )
        log.debug('msg index type:{0}'.format(
            self._ORDER[index])
        )

        while ind >= 0:
            ind -= self._ORDER_BYTES[i]
            if ind > 0:
                i += 1
                continue
            else:
                return (i, ind + self._ORDER_BYTES[i])

    @classmethod
    def _asign_uint2byte_bybits(cls, num, bits):
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
            for _ in xrange(0, asign_len - length):
                tmp += chr(0)
        return tmp

    @classmethod
    def _convert_bytes2uint(cls, str_data):
        num = 0L
        b_ind = 0
        for i in str_data:
            num += pow(256, b_ind) * ord(i)
            b_ind += 1
        return num

    def push_data(self, data):
        """
        push data into the msg. Return pushed length.

        Return -1 if we should shutdown the socket channel.
        """
        if self._msg_finish:
            log.warn('The CNetMsg has already been pushed enough data')
            return 0
        if len(data) == 0:
            log.warn(
                'You just pushed into the msg with a zero-length data'
            )
            return 0
        sign = True
        data_ind = 0
        data_max = len(data)
        order, offsite = self._get_msg_order_ind(self._readindex)
        data_key = self._ORDER[order]
        while sign:
            msg_data_loop_end = False
            # One loop handle one data_key until there all the data is handled.
            try:
                self._data[data_key]
            except KeyError:
                self._data[data_key] = ''
            loop_data_max = (
                self._ORDER_BYTES[order] - len(self._data[data_key])
            )
            if (data_max - data_ind) >= loop_data_max:
                # can fill up the msg
                self._data[data_key] += (
                    data[data_ind: loop_data_max + data_ind]
                )
                data_ind += loop_data_max
                msg_data_loop_end = True
                self._readindex += loop_data_max
                if data_key != 'body':
                    log.debug(
                        'data_key {0} full filled'.format(data_key)
                    )
                    if data_key == 'head':
                        if self._data[data_key] != self.MSG_SIGN:
                            return -1
                else:
                    pass
                    # log.debug('body_len:%d' % len(self._data['body']))
            else:
                # cannot fill up the msg in this round
                sign = False
                push_bytes = data_max - data_ind
                self._data[data_key] += data[data_ind: data_max]
                self._readindex += push_bytes
                data_ind += push_bytes

            if (data_key == 'len') and (msg_data_loop_end):
                # set up the length of the body
                total_len = self._convert_bytes2uint(self._data['len'])
                if self._need_head:
                    self._ORDER_BYTES[7] = total_len - self._SIZE_EXCEPT_BODY
                else:
                    self._ORDER_BYTES[7] = (
                        total_len - self._SIZE_EXCEPT_HEAD_BODY
                    )
                log.debug('total len %d' % total_len)
            if msg_data_loop_end and (order == self._ORDER_COUNTS - 1):
                self._msg_finish = True
                sign = False
                log.debug('congratulations. This msg has been fullfilled')
            elif msg_data_loop_end and order < self._ORDER_COUNTS:
                order += 1
                data_key = self._ORDER[order]
                log.debug('This round has finished')
        return data_ind

    def _addr2pack(self, ip_port, stub_future):
        misc.check_type(ip_port, tuple)
        misc.check_type(stub_future, tuple)
        pack = common.ip_port2connaddr(ip_port)
        pack = common.add_stub2connaddr(pack, stub_future[0])
        pack = common.add_future2connaddr(pack, stub_future[1])
        return pack

    def set_flag(self, flag):
        """
        set flag for the msg
        """
        # misc.check_type(flag, int)
        self._data['flag'] = self._asign_uint2byte_bybits(flag, 32)
        self._flag = flag

    def set_need_head(self, b_need=False):
        """
        :note:
            By default, the msg does not need to have a head unless
            it's the first msg that posted/received.
        """
        self._need_head = b_need
        if self._is_postmsg and self._need_head:
            self._data['head'] = self.MSG_SIGN
        log.debug('to set msg need head:%s' % str(self._need_head))

    @classmethod
    def _check_addr(cls, ip_port, stub_future):
        ip, port = ip_port
        stub, future = stub_future
        misc.check_type(ip, str)

    def _set_msg_len(self):
        if self._need_head:
            size_except_body = self._SIZE_EXCEPT_BODY
        else:
            size_except_body = self._SIZE_EXCEPT_HEAD_BODY
        body_len = len(self._data['body'])
        self._ORDER_BYTES[7] = body_len
        self._msglen = body_len + size_except_body
        self._data['len'] = self._asign_uint2byte_bybits(
            self._msglen, 64
        )
        tempstr = ''
        for i in xrange(0, self._ORDER_COUNTS - 1):
            if i == 0 and not self._need_head:
                continue
            tempstr += self._data[self._ORDER[i]]
        self._dumpdata = '{0}{1}'.format(tempstr, self._data['body'])

    def set_from_addr(self, ip_port, stub_future):
        """
        set msg from addr
        """
        self._check_addr(ip_port, stub_future)
        pack = self._addr2pack(ip_port, stub_future)
        self._data['from'] = self._asign_uint2byte_bybits(pack, 128)
        self._fromaddr = (ip_port, stub_future)

    def set_to_addr(self, ip_port, stub_future):
        """
        set msg to addr
        """
        self._check_addr(ip_port, stub_future)
        pack = self._addr2pack(ip_port, stub_future)
        self._data['to'] = self._asign_uint2byte_bybits(pack, 128)
        self._toaddr = (ip_port, stub_future)

    def set_msg_type(self, msg_type):
        """
        set msg type
        """
        misc.check_type(msg_type, int)
        self._data['type'] = self._asign_uint2byte_bybits(msg_type, 32)
        self._type = msg_type

    def set_uniq_id(self, uniq_id):
        """
        set msg unique id
        """
        # misc.check_type(uniq_id, int)
        self._data['uniq_id'] = self._asign_uint2byte_bybits(uniq_id, 64)
        self._uniqid = uniq_id

    def set_body(self, body):
        """
        set msg body
        """
        misc.check_type(body, str)
        self._data['body'] = body
        self._bodylen = len(body)

    def _pack_toaddr(self, pack):
        (ip, port) = common.get_ip_and_port_connaddr(pack)
        stub = common.getstub_connaddr(pack)
        future = common.getfuture_connaddr(pack)
        return ((ip, port), (stub, future))

    def get_flag(self):
        """
        get msg flag
        """
        if self._flag is None:
            self._flag = self._convert_bytes2uint(self._data['flag'])
        return self._flag

    def get_to_addr(self):
        """
        get to addr
        """
        if self._toaddr is None:
            pack = self._convert_bytes2uint(self._data['to'])
            self._toaddr = self._pack_toaddr(pack)
        return self._toaddr

    def get_from_addr(self):
        """
        get from addr. ((ip, port), (stub, future))
        """
        if self._fromaddr is None:
            pack = self._convert_bytes2uint(self._data['from'])
            self._fromaddr = self._pack_toaddr(pack)
        return self._fromaddr

    def get_msg_type(self):
        """
        get msg type
        """
        if self._type is None:
            self._type = self._convert_bytes2uint(self._data['type'])
        return self._type

    def get_msg_len(self):
        """
        get msg len
        """
        if self._msglen is None:
            self._msglen = self._convert_bytes2uint(self._data['len'])
        return self._msglen

    def get_uniq_id(self):
        """
        get unique msg id
        """
        if self._uniqid is None:
            self._uniqid = self._convert_bytes2uint(self._data['uniq_id'])
        return self._uniqid

    def get_body(self):
        """
        get msg body
        """
        if 'body' not in self._data:
            raise KeyError('Body not set yet')
        return self._data['body']

    def get_bodylen(self):
        """
        get body length
        """
        return self._bodylen

    def is_a_sendmsg(self):
        """
        is a msg being sent
        """
        return self._is_postmsg

    def is_a_recvmsg(self):
        """
        is a msg being received
        """
        return (not self._is_postmsg)

    def is_recvmsg_complete(self):
        """
        is msg received already
        """
        if not self._is_postmsg and self._msg_finish:
            return True
        else:
            return False

    # the head in self._data should be set before sent.
    # Thus, the self._data.keys will be 1 less than
    # self.get_order_counts()
    def is_sendmsg_complete(self):
        """
        is msg sent complete
        """
        if (self._bodylen + self._SIZE_EXCEPT_BODY) == self._msglen:
            return True
        else:
            return False

    def get_write_bytes(self, length):
        """
        get write bytes from the msg
        """
        if length <= 0:
            return
        return self._dumpdata[self._writeindex: self._writeindex + length]

    def seek_write(self, length_ahead):
        """
        seek foreward by length
        """
        self._writeindex += length_ahead
        if self._writeindex > self.get_msg_len():
            raise cup.err.AsyncMsgError(
                'You have seek_write out of the msg length'
            )

    def is_msg_already_sent(self):
        """
        is msg already sent
        """
        if self._writeindex == self.get_msg_len():
            return True
        else:
            return False


# pylint: disable=R0904
class CAckMsg(CNetMsg):
    """
    ack msg example
    """
    def __init__(self, is_postmsg=True):
        super(self.__class__, self).__init__(is_postmsg)

    def set_body(self, map_ack):
        """
        set body
        """
        body = json.dumps(map_ack)
        self._data['body'] = body

    def set_ack(self, status, msg):
        """
        :param status:
            status of the msg
        :param msg:

        """
        ack = {}
        ack['status'] = status
        ack['msg'] = msg
        self.set_body(json.dumps(ack))

    def get_ack(self):
        """
        get ack
        """
        body = json.loads(self._data['body'])
        return body

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
