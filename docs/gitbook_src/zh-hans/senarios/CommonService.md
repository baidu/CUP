<!-- MDTOC maxdepth:6 firsth1:1 numbering:0 flatten:0 bullets:1 updateOnSave:1 -->

- [1. 通用Service](#1-通用service)   
   - [1.1 Thread/Threadpool 线程池](#11-threadthreadpool-线程池)   
   - [1.2 Interruptible Thread 可打断线程 / 读写锁RWLock](#12-interruptible-thread-可打断线程-读写锁rwlock)   
   - [1.3 线程池的衍生物, 执行器](#13-线程池的衍生物-执行器)   
   - [1.4 Autowaits 事件驱动等待](#14-autowaits-事件驱动等待)   
   - [1.5 BufferPool 内存缓冲区](#15-bufferpool-内存缓冲区)   
   - [1.6 Generator 生成器](#16-generator)   
   - [1.7 Serializer Meta持久化](#17-serializer-meta持久化)   
   - [1.8 HeartBeat 心跳服务](#18-heartbeat-心跳服务)   

<!-- /MDTOC -->

# 1. 通用Service

## 1.1 Thread/Threadpool 线程池
`cup.services.threadpool`支持丰富的线程池场景, 可以:
- 典型的作业模型
- 支持执行后回调函数处理
- 支持热调整工作线程数
- 支持阻塞(stop)/非阻塞(try_stop)停止方式

```python
# 以使用线程池多线程scp分发文件为例
class CRemote(object):
    """
    handle remote things
    """
    def __init__(self, username, password, retry=0):
        self._username =  username
        self._passwd = password
        self._wget_retry = retry
        self._thdpool = threadpool.ThreadPool(minthreads=2, maxthreads=4)
        self._generator = generator.CGeneratorMan()

    # pylint: disable=R0913
    def _thread_scp_dir_by_tarfile(self,
            hostname, dst, tarpath, ret_list, timeout
        ):
        """
        do sth in a thread。 执行该scp命令的实际线程. 执行scp
        """
        if os.path.normpath(dst) == '/':
            raise IOError('You CANNOT delete root /')
        tarfile_name = os.path.basename(tarpath)
        log.info('to mkdir in case it does not exists:{0}'.format(dst))
        cmd = 'mkdir -p {0};'.format(dst, dst)
        ret = self.remote(hostname, cmd, 10)
        ret['hostname'] = hostname
        if ret['exitstatus'] != 0 or ret['remote_exitstatus'] != 0:
            log.critical('mkdir dst failed, error info:{0}'.format(ret))
            ret_list.append(ret)
            return
        log.info('scp_dir_by_tarfile, src tarfile:{0} dst:{1}'.format(
            tarpath, dst)
        )
        ret = self.lscp(tarpath, hostname, dst)
        ret['hostname'] = hostname
        if ret['exitstatus'] != 0 or ret['remote_exitstatus'] != 0:
            log.critical('lscp failed, error info:{0}'.format(ret))
            ret_list.append(ret)
        else:
            cmd = 'cd {0}; tar zxf {1}; rm -f {2}'.format(
                dst, tarfile_name, tarfile_name
            )
            ret = self.remote(hostname, cmd, timeout=timeout)
            ret['hostname'] = hostname
            ret_list.append(ret)
            log.info('succeed to scp dir, hostname:{0}'.format(hostname))
        return

    def scp_hosts_dir_by_tarfile(self,
        src, hosts, dst, tempfolder, tarfile_name=None, timeout=600
    ):
        """
        scp a folder to multiple hosts
        使用线程池，多线程并发的scp拷贝本地目录到远程机器目录

        :hosts:
            hosts that will be scped
        :tempfolder:
            temp folder which will store tar file temporarily.
        """
        src = os.path.normpath(src)
        if tarfile_name is None:
            tarfile_name = '{0}.{1}.tar.gz'.format(
                net.get_local_hostname(), time.time()
            )
        src_folder_name = os.path.basename(src)
        name = '{0}/{1}'.format(tempfolder, tarfile_name)
        log.info('to compress folder into tarfile:{0}'.format(name))
        with tarfile.open(tempfolder + '/' + tarfile_name, 'w:gz') as tar:
            tar.add(src, src_folder_name)

        ret_list = []
        # 启动线程池
        self._thdpool.start()
        for hostname in hosts:
            # 像线程池扔作业
            self._thdpool.add_1job(
                self._thread_scp_dir_by_tarfile,
                hostname,
                dst,
                name,
                ret_list,
                timeout
            )
        time.sleep(2)
        # 完成后，等待线程池关闭
        self._thdpool.stop()  # 注意，线程池也提供try_stop接口，具体可以看文档
        # if not ret:
        #     errmsg = 'failed to stop threadpool while dispath files'
        #     content = errmsg
        #     petaqa.peta.lib.common.send_mail(errmsg, content)
        #     log.error(errmsg)
        #     log.error(content)
        os.unlink(name)
        return ret_list
```

## 1.2 Interruptible Thread 可打断线程 / 读写锁RWLock

python原生线程实现, 在运行过程中无法进行干涉. 这对于实时处理任务中需要立刻停止的场景不适用.
`cup.thread`提供了两类服务

> * 可打断线程CupThread
> * RWLock 读写锁

可打断线程继承自threading.Thread, 除了原生的函数外拥有三个新特性:

1. raise_exc, 像线程发送exception并打断她的执行状态, to send a raise-exception signal to the thread,
    TRY to let the thread raise an exception.
2.  get_my_tid, get thread id
3. terminate, 停止该线程, 拥有重试机制

读写锁示例:

```python
# 读写锁支持
# for RWLock unittest
def test_rw_rw_lock():
    # 写锁有且仅有一个被获取
    lock = thread.RWLock()
    lock.acquire_writelock(None)
    try:
        lock.acquire_writelock(1)
    except RuntimeError as error:
        pass
    try:
        lock.acquire_readlock(1)
    except RuntimeError as error:
        pass
    lock.release_writelock()


def test_rd_rw_lock():
    lock = thread.RWLock()
    # 1. 先获取读锁, 读锁在没有写的情况下可以任意数量获取
    lock.acquire_readlock(None)   # None means wait until get the lock
    lock.acquire_readlock(wait_time=1)  # will return if timeouts without the lock
    lock.acquire_readlock(2)

    # 2. 此时获取写锁会失败, 抛出RuntimeError异常
    try:
        lock.acquire_writelock(1)
    except RuntimeError as error:
        pass
    # 3. 释放所有读锁
    lock.release_readlock()
    lock.release_readlock()
    lock.release_readlock()
    # 4. 获取写锁, 这个时候可以获取成功
    try:
        lock.acquire_writelock(1)
    except RuntimeError as error:
        assert False
    lock.release_writelock()

```

## 1.3 线程池的衍生物, 执行器
cup.services.executor, 线程池 based 执行器, 支持:
- delay_exec 延迟xx秒执行
- queue_exec 排队执行
    - `def delay_exec(self,delay_time_insec, function, urgency, *args, **kwargs)`

延迟执行代码示例:
```python
# 谁没有延迟个XX秒，或者周期性XX秒后执行某件事情的需求呢?

from cup import log
from cup.services import executor

class TestMyCase(unittest.CUTCase):
    """
    test class for cup
    """
    def __init__(self):
        super(self.__class__, self).__init__(
            './test.log', log.DEBUG
        )
        log.info('Start to run ' + str(__file__))
        self._executor = executor.ExecutionService(
        )

    def setup(self):
        """
        setup
        """
        self._executor.run()
        self._info = time.time()

    def _change_data(self, data=None):
        self._info = time.time() + 100

    def test_run(self):
        """
        @author: maguannan
        """
        self._executor.delay_exec(5, self._change_data, 1)  # 延迟5秒执行某个函数， 同时支持函数参数传递
        time.sleep(2)
        assert time.time() > self._info
        time.sleep(5)
        assert time.time() < self._info

    def teardown(self):
        """
        teardown
        """
        cup.log.info('End running ' + str(__file__))
        self._executor.stop()

if __name__ == '__main__':
    cup.unittest.CCaseExecutor().runcase(TestMyCase())
```
## 1.4 Autowaits 事件驱动等待
```python

# 等待某个条件达成否则阻塞直到超时。 （再也不用while for循环sleep啊 亲们）

# 等待文件存在直到超时
cup.services.autowait.wait_until_file_exist(dst_path, file_name, max_wait_sec=10, interval_sec=2,recursive=False)

# 等待正则字符串在文件存在直到超时,如果读取失败，raise IOError
cup.services.autowait.wait_until_reg_str_exist(dst_file_path, reg_str, max_wait_sec=10,interval_sec=0.5)[source]

# 等待特定路径的进程不存在直到超时
cup.services.autowait.wait_until_process_not_exist(process_path, max_wait_sec=10,interval_sec=0.5)[source]

```

## 1.5 BufferPool 内存缓冲区

```python
# 1. Buffer内存缓冲以及Bufferpool内存缓冲池
# http://cupdoc.iobusy.com/cup.services/#module-cup.services.buffers
# 由于Python内存管理的特点，在比如网络通信以及频繁（稍大）内存的申请释放时候会退化为malloc/free。 具体可见两篇比较好的解释文章：
#  (a). stackflow的关于什么时候可以用bytearray
# http://stackoverflow.com/questions/9099145/where-are-python-bytearrays-used

#  (b). Python的内存管理

#  http://leyafo.logdown.com/posts/159345-python-memory-management

# 这个时候直接使用str来存储效率低下，但好消息是python原生提供了bytearray这样的数据结构。利用她mutable可变的特性做成Buffer，进一步组成Bufferpool内存缓存池，非常适配频繁申请释放较大内存的场景。
import os
import sys
import logging

from cup.services import buffers
from cup import unittest

class CTestServiceBuffer(unittest.CUTCase):
    """
    service buffer
    """
    def __init__(self):
        super(self.__class__, self).__init__()
        self._buffpool = buffers.BufferPool(
            buffers.MEDIUM_BLOCK_SIZE,
            102400,
        )

    def test_run(self):
        """test_run"""
        ret, buff = self._buffpool.allocate(102401)  # 回返的是Buffer数据结构
        unittest.assert_eq(ret, False)

        ret, buff = self._buffpool.allocate(10)
        unittest.assert_eq(ret, True)
        # pylint: disable=W0212
        unittest.assert_eq(self._buffpool._used_num, 10)
        unittest.assert_eq(self._buffpool._free_num, 102390)
        ret = buff.set('a' * 10 * buffers.MEDIUM_BLOCK_SIZE)  # Buffer数据结构支持set语义
        unittest.assert_eq(ret[0], True)
        ret = buff.set('a' * (10 * buffers.MEDIUM_BLOCK_SIZE + 1))
        unittest.assert_ne(ret[0], True)
        self._buffpool.deallocate(buff)     # 归还buffer到线程池
        # pylint: disable=W0212
        unittest.assert_eq(self._buffpool._used_num, 0)
        unittest.assert_eq(self._buffpool._free_num, 102400)
        unittest.assert_eq(len(self._buffpool._free_list), 102400)
        unittest.assert_eq(len(self._buffpool._used_dict), 0)
```

## 1.6 Generator

a. 用来生成各类唯一数，字符集，线程安全的自增uint的类。 目前生成函数较少， 欢迎大家贡献ci. Singleton类。
```python
# 初始化需要传入一个用来生成字符集的string.
# 初始化函数:
__init__(self, str_prefix=get_local_hostname()) # 默认传入当前自己的hostname

# 成员函数:
get_uniqname()   # 获得一个以传入的初始化string为base, 加上pid, threadid等组合的host级别的 unique
get_next_uniq_num() # 获得当前进程唯一的自增非负整数。线程安全.

```
b. CycleIDGenerator 128bit循环id线程安全自增ID生成器
```python
next_id() # 支持获取循环且线程安全的next id
```

## 1.7 Serializer Meta持久化

示例制作中

## 1.8 HeartBeat 心跳服务

示例制作中
