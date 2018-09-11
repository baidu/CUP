

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

## code directory tree:

```text
cup
    |-- cache.py                module              Memory cache related module                                       
    |-- decorators.py           module              Decorators of python                                       
    |-- err.py                  module              Exception classes for CUP                              
    |-- __init__.py             module              Default __init__.py                                 
    |-- log.py                  module              CUP logging                                        
    |-- mail.py                 module              CUP Email module (send emails)                               
    |-- net                     package             Network operations, such as net handler parameter tuning         
    |-- oper.py                 module              Mixin operations                              
    |-- platforms.py            module              Cross-platform operations                              
    |-- res                     package             Resource usage queries (in /proc)、Prcoess query、etc            
    |-- shell                   package             Shell Operations、cross-hosts execution              
    |-- services                package             Heartbeat、Threadpool based executors、file service、etc                 
    |-- thirdp                  package             Third-party modules： pexpect、httplib2                   
    |-- timeplus.py             module              Time related module                                       
    |-- unittest.py             module              Unittest、assert、noseClass                      
    |-- util                    package             ThreadPool、Interruptable-Thread、Rich configuration、etc
    |-- version.py              module              CUP Version  
```
