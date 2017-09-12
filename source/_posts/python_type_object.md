---

title: python 类、属性和方法
date: 2017/6/22 09:00:00

---

## 继承

调用基类的方法时，需要加上基类的类名，并且带上self参数。 
```python 
class Parent:
    def foo(self): 
        print 'Parent'

class Child(Parent):
    def foo(self): 
        print 'Child' 
    def parent_foo(self): 
        Parent.foo(self)
```

### Super
Super是一个类，Super(cls, obj)是根据类和其对象返回一个对象，可以通过Super来调用父类属性
```python  
class Child(Parent):
    def foo(self):
        Super(Child, self).foo()
        #do other things
        pass
```

### 新类旧类 

从object继承的是新类，否则为旧类。python 3中所有类都为新类，隐式继承自object。  

|  |type(类)|type(实例)|
|----------|-----------|-------------|
|旧类 |type 'classobj' | type 'instance' |
|新类 |type 'type' | class 'ClassName' |  

新类本身也是一个对象。

## 私有属性

**\_\_private\_attrs** 以双下划线开头的属性为private属性。   
**\_protected\_attrs** 以单下划线开头的属性为protected属性。

外部访问私有属性时会报错，但是可以通过类名 \_ClassName\_\_var 来进行访问。 
```python 
class CC:
    def __init__(self, name):
        self.__name =  name

c = CC("dog")
# err
# print c.__name

# ok 
print c._CC__name
```

## 元类 

元类是用于创建类的类，一般类的元类是type。   

作用：
1. 拦截类的创建；
2. 修改类；
3. 返回修改后的类。 

在python中，\_\_metaclass\_\_属性用于指明该类创建时使用的元类。 如果没有该属性,则使用type来创建。  
搜索元类的顺序: 当前类 => 祖先类 => 模块 => type。
  
可以用type创建类。
 

概念上是 
```python 
#概念上是
MyClass = MetaClass()
MyObject = MyClass()

type(ClassName, ParentList, AttrDict)
```

### \_\_class\_\_ 

python中所有东西都是对象，并且也都是从类中生成的。例如整数对象是由类int生成的，字符串对象是由str生成的，而类是由元类生成的。  
对象的 \_\_class\_\_ 属性表示生成该对象的类。 

```python 
age = 10 
print age.__class__     #<type 'int'>
name = "bob" 
print name.__class__    #<type 'str'>

print age.__class__.__class__    #<type 'type'>  生成类的类，元类type
print name.__class__.__class__   #<type 'type'>
```

## types vs objects

生成对象的两种方法：
1. 通过已有类继承生成新的类(\_\_bases\_\_);
2. 通过已有类实例化对象(\_\_class\_\_)；

### 重要准则

1. Everything is an object  
所有东西都是object。

2. Class is type is class  
class和type的意义是一样的。

3. Type or non-type test rule    
判断一个对象是否是一个类，判断它是否 instance of type。 
 
Object是一切类(自身除外)的父类，type是生成所有类的类。

### 对象关系图

[关系图](/image/types_map.png)


## Attributes

### \_\_dict\_\_
用户自定义的属性。 

属性查找顺序(访问obj.attr)：
1. attr是python提供的特殊属性时，返回； 
2. 在它的类 \_\_dict\_\_中寻找，如果找到，且是一个data descriptor，则返回 descriptor result；
3. 在该对象的 \_\_dict\_\_中寻找，找到返回；如果该对象也是一个类，则在它的祖先的 \_\_dict\_\_ 中也找。如果找到的是 descriptor， 则返回descriptor result；
4. 在它的类 \_\_dict\_\_中寻找，如果找到，则若是非描述符，则返回；否则应该为non-data descriptor，则返回 descriptor result;
5. 触发异常。

总结：python内置属性 => 类\_\_dict\_\_中的data descriptor => 对象中的 \_\_dict\_\_ => 类中的 \_\_dict\_\_ 中的非描述符或non-data descriptor
 
一些build in类型是没有\_\_dict\_\_的，如list，tuple等，所以用户设置list对象的属性时会报错。

## Method

### 绑定(Bound)/非绑定(UnBound)
类中定义的方法，类名 + . + 方法名是非绑定， 对象 + . + 是绑定。
```python 
class Foo(object):
    def foo():
        pass  

Foo.foo()       #未绑定  
Foo().foo()     #绑定，会报错
```

obj.f是绑定方法，cls.\_\_dict\_\_["f"]是未绑定方法，可以通过 cls.\_\_dict\_\_["f"].\_\_get\_\_(obj, cls) 来获得。

### Descriptor

可以把带有\_\_get\_\_方法的object放到类的\_\_dict\_\_中，这些object称为descriptor。 

descriptor包含三个方法：
1. \_\_get\_\_   
obj.attr或cls.attr来调用
2. \_\_set\_\_  (可选)
obj.attr = .. 时调用
3. \_\_delete\_\_ (可选)
删除属性时调用

Descriptor只有绑到类上时才会起作用，绑到一个非class的实例上，不会起任何作用。
当d为类C的描述符时，实例 c.d 访问到的都是类C中的对象，要想定义使用自己的d，只能 c.\_\_dict\_\_["d"]的形式

访问描述符时，类改变描述符时会生效，但实例则不会。

|   |\_\_get\_\_|\_\_set\_\_|\_\_delete\_\_| 
|---|---|---|---|
|实例| 调用 | 调用 | 调用 |
|类| 调用 | 不调用|不调用|

只包含\_\_get\_\_的描述符称为non-data descriptor。
对于data descriptor，对象无法隐藏类的描述符；类修改d = .. 后，则会把描述符替换成其他对象了，并且不会调用\_\_delete\_\_。 
对于non-data descriptor，对象可以隐藏类的描述符。 

```python
class Desc(object):
    def __get__(self, obj, cls=None):
        pass 
    def __set__(self, obj, val):
        pass
    def __delete__(self, obj):
        pass
```

### 类方法/静态方法  

类方法既可以使用类来调用，也可以使用对象来调用。类方法有两个条件
1. 使用classmethod描述；
2. 传入的第一个参数是cls；(注意：用self时，只能被实例调用)。

```python 
class Foo(object):
    @classmethod
    def foo(cls): #第一个参数只能是cls
        pass

Foo.foo() #ok
Foo().foo() #ok
```

静态方法可以被类和对象调用，静态方法用staticmethod修饰器。
```python  
class Foo(object):
    @staticmethod  
    def foo(): #不带self和cls
        pass

Foo.foo() #ok
Foo().foo() #ok
```
----
## References

1. python types and objects [1]。
2. python attributes and methods [2]。

[1]: http://www.cafepy.com/article/python_types_and_objects/python_types_and_objects.html
[2]: http://www.cafepy.com/article/python_attributes_and_methods/python_attributes_and_methods.html
