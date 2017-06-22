---
title: python小知识
---

# 魔法方法
## 构造和析构函数
\_\_new\_\_是构造函数，在\_\_init\_\_函数之前调用，只使用参数cls，其余参数传给\_\_init\_\_。


\_\_del\_\_是析构函数，并不是语句del x的实现。

```python
class FileObject:
    def __init__(self, filepath):
        self.file = open(filepath, 'r')

    def __del__(self):
        self.file.close()
        del self.file
```

## 访问控制
\_\_getattr\_\_ 当用户试图访问不存在的属性时，会被调用。
\_\_setattr\_\_ 当用户试图设置属性时，不管改属性是否存在，会被调用。
\_\_delattr\_\_ 当用户试图删除属性时，不管改属性是否存在，会被调用。

## 自定义序列
1. 不可变容器
   需要实现 \_\_len\_\_ 和\_\_getitem\_\_ 方法。
2. 可变容器
   除了1，还要实现 \_\_setitem\_\_ 和 \_\_delitem\_\_ 方法。

为了使容器支持迭代，还需要实现\_\_iter\_\_接口。

## 上下文管理器

with .. as xx: 做清理时使用，
需要定义 \_\_enter\_\_(self) 和 \_\_exit\_\_(self, exception_type, exception_value, traceback)。

