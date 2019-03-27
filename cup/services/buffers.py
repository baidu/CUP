#!/usr/bin/env python
# -*- coding: utf-8 -*
# Copyright: [CUP] - See LICENSE for details.
# Authors: Guannan Ma (@mythmgn),
"""
:description:
    buffer pool
"""
import threading

SMALL_BLOCK_SIZE =  4096 # kb
MEDIUM_BLOCK_SIZE = (128 + 4) * 1024   # 8K
LARGE_BLOCK_SIZE = 1 * 1024 * 1024 + SMALL_BLOCK_SIZE  # 1M

SMALL_BLOCK = 0
MEDIUM_BLOCK = 1
LARGE_BLOCK = 2


class Buffer(object):
    """
    Buffer object which you get from BufferPool.allocate(num)
    """
    def __init__(self, items, block_size, uniqid):
        self._items = items
        self._block_size = block_size
        self._num = len(items)
        self._length = -1
        self._uniqid = uniqid

    def set(self, content):
        """
        return (True, None) if succeed.

        return (False, error_msg) otherwise

        """
        length = len(content)
        ind = 0
        item_ind = 0
        if length > self._block_size * self._num:
            return (False, 'content size > Buffer size')
        while ind < length:
            if ind + self._block_size <= length - 1:
                loop_size = self._block_size
            else:
                loop_size = length - ind
            self._items[item_ind].extend(content[ind: loop_size])
            item_ind += 1
            ind += loop_size
        self._length = length
        return (True, None)

    def get(self):
        """
        return (True, (content, block_size, total_length)) if succeed

        Otherwise, return (False, err_msg, None)
        """
        rev = None
        if self._length != -1:
            rev = (True, (self._items, self._block_size, self._length))
        else:
            rev = (False, ('not initialized yet', self._block_size, None))
        return rev

    def get_uniq_id(self):
        """
        return the uniqid for this object
        """
        return self._uniqid

    def get_byte_arrays(self):
        """
        get byte arrays in the buffer
        """
        return self._items


# pylint: disable=R0902
class BufferPool(object):
    """
    buffer pool class which will ease memory fragment
    """
    def __init__(
        self, pool_size, block_size=MEDIUM_BLOCK_SIZE, extendable=False
    ):
        if block_size not in (
            SMALL_BLOCK_SIZE, MEDIUM_BLOCK_SIZE, LARGE_BLOCK_SIZE
        ):
            raise ValueError('block_size should be buffers.SMALL_BLOCK_SIZE'
                ' or buffers.MEDIUM_BLOCK_SIZE or buffers.LARGE_BLOCK_SIZE'
            )
        # TODO If extendable, we should expand the pool
        self._extendable = extendable
        self._lock = threading.Lock()
        self._free_list = []
        self._used_dict = {}
        self._pool_size = pool_size
        self._used_num = 0
        self._free_num = self._pool_size - self._used_num
        self._block_size = block_size
        self._uniqid = 0

        self._block_size = block_size
        for _ in range(0, self._pool_size):
            self._free_list.append(bytearray(self._block_size))

    def allocate(self, num):
        """
        acclocate buff with num * block_size

        :return:
            (True, Buffer object)

            (False, str_error_msg)
        """
        ret = None
        self._lock.acquire()
        if num > self._free_num:
            ret = (False, 'not enough free buffer available')
        else:
            uniqid = threading.current_thread().ident
            ind = self._free_num - num
            buff = Buffer(
                self._free_list[ind: self._free_num],
                self._block_size,
                uniqid
            )
            ret = (True, buff)
            self._used_dict[uniqid] = ret[1]
            del self._free_list[ind: self._free_num]
            self._free_num -= num
            self._used_num += num
        self._lock.release()
        return ret

    def deallocate(self, buff):
        """
        return the acclocated buff back to the pool
        """
        if buff is None:
            return False
        self._lock.acquire()
        uniqid = buff.get_uniq_id()
        if uniqid not in self._used_dict:
            raise ValueError('this buff is not in the pool!!!')
        byte_arrays = buff.get_byte_arrays()
        length = len(byte_arrays)
        self._free_list.extend(byte_arrays)
        del self._used_dict[uniqid]
        del buff
        self._used_num -= length
        self._free_num += length
        self._lock.release()
        return True

# vi:set tw=0 ts=4 sw=4 nowrap fdm=indent
