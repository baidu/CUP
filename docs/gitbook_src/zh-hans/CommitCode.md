# 如何贡献代码
## 1. 熟悉CUP规则
- 首先CUP使用python pep8规则, 所有新增代码必须遵守.
- Python新增代码需要进行规范化代码注释, 和原生python的sphinx规则保持一致

```python
def lock(self, msg, blocking=True):                                                                     
    """                                                                                            
    lock the file 

    :param msg:
        Msg that will be logged.                                                                                            
    :param blocking:                                                                            
        If blocking is True, will block there until cup gets the lock.                          
        True by default.                                                                        

    :return:                                                                                    
        return False if locking fails                                                           

    :raise Exception:                                                                              
        raise cup.err.LockFileError if blocking is False and                                       
        the lock action failed                                                                     
    """                                                                                            
    flags = 0x1               
```

## 2. 撰写代码

## 3. 发起评审和代码Merge操作

* Commit All Changes
* Request for comments and Start a pull Request
