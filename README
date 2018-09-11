

## Quick Start
### 1. Download
    - git clone CUP

### 2. Installation
    - run `python setup.py install`

### 3. Usage
Visit Wiki to see more details: https://github.com/Baidu/CUP/wiki

```python
# Examples:
# 1. Get system info 
import cup
# count cpu usage in interval, by default 60 seconds
from cup.res import linux
cpuinfo = linux.get_cpu_usage(intvl_in_sec=60)
print cpuinfo.usr

# total, available, percent, used, free, active, inactive, buffers, cached
from cup.res import linux
meminfo = linux.get_meminfo()
print meminfo.total
print meminfo.available
```


## Tests
    - Install python-nose before running the tests
    - run `cd ./cup_tests; nosetests -s`

## Contribute To CUP
    - Commit code to GITHUB, https://github.com/baidu/CUP
    - Need to check pep8 and pylint rules before you start a pull request

## Discussion
    - Github Issues
    
## Reference
      * Pexpect http://pexpect.sourceforge.net/ (under MIT license)
      * Httplib2 http://code.google.com/p/httplib2/ (under MIT license)
      * requests https://github.com/kennethreitz/requests (under Apache V2 license)
      * pymysql https://github.com/PyMySQL/PyMySQL (under MIT license)

## WIKI
https://github.com/Baidu/CUP/wiki

## 基础库代码结构说明:

```text
cup
|-- cache.py                模块|module             缓存相关
|-- decorators.py           module                  通用修饰符
|-- err.py                  module                  CUP内部Exception处理
|-- __init__.py             module                  CUP import处理模块  
|-- log.py                  module                  CUP logging
|-- mail.py                 module                  CUP Email 发送模块
|-- net                     目录|package            网络操作、资源、异步通信框架
|-- oper.py                 模块|module             各类混杂操作opertions
|-- platforms.py            模块|module             跨平台相关保留module
|-- res                     目录|package            机器资源信息获取、进程信息获取、监控等
|-- shell                   目录|package            shell操作、跨机执行、跨机数据传输等
|-- services                目录|package            心跳机制  
|-- thirdp                  目录|package            第三方库： pexpect、httplib2、
|-- timeplus.py             模块|module             时间操作函数
|-- unittest.py             模块|module             UT测试相关、assert、noseClass
|-- util                    目录|package            线程池、可打断线程、Public/Configure配置文件python实现、数据生成器
|-- version.py              模块|module             CUP版本号管理
```



