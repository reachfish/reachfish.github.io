---

title: scala基本学习
date: 2017/6/28 09:00:00

---

# 零碎知识
### 命名
类名第一个字母要大写，方法名第一个字母要小写。

### 定义包
```scala
//法一
package com.reach
class HelloWorld

//法二
package com.reach {
    class HelloWorld
}
```

### 引入
```scala
import java.awt.Color //引入Color
import java.awt._   //引入所有成员
import java.awt.{Color, Font} //引入Color, Font
import java.util.{HashMap => JavaHashMap}  //引入并重命名为JavaHashMap
import java.util.{HashMap => _, _} //引入util中的所有成员，但是HashMap被隐藏了
```

### 数据类型
Unit: 同void， 用作不返还任何结果的方法的结果类型；
Null: null或空引用(null是对象，Null是类型)
Nothing: 任何其他类型的子类型
Any: 所有其他类的超类
AnyRef: 所有引用类的基类

scala没有Java中的原生类型，任何值都是一个对象，方法也是对象。

### 符号字面量
'<标识符>，如'x是scala.Symbol("x")的简写。

### 多行字符串
"""..."""

### 变量
var声明变量， val声明常量，声明格式：
```scala
//声明类型
var VariableName : DataType [=  InitialValue]

//不声明类型，但需要指定初值，会自动推断类型的
var VariableName = InitialValue

val xmax, ymax = 100  // xmax, ymax都声明为100
val (myVar1: Int, myVar2: String) = Pair(40, "Foo")
val (myVar1, myVar2) = Pair(40, "Foo")
```

### 循环
```scala
for ( i <- 1 to 10)
for (arg <- args)
```

### 访问修饰符
Scala 中的 private 限定符，比 Java 更严格，在嵌套类情况下，外层类不能访问被嵌套类的私有成员。但是内层类可以访问外层类的私有成员。
```scala
class Outer{
    class Inner{
    private def f(){println("f")}
    class InnerMost{
        f() // 正确
        }
    }
    (new Inner).f() //错误
}
```

在 scala 中，对保护（Protected）成员的访问比 java 更严格一些。因为它只允许保护成员在定义了该成员的的类的子类中被访问。而在java中，用protected关键字修饰的成员，除了定义了该成员的类的子类可以访问，同一个包里的其他类也可以进行访问。
```scala
package p{
class Super{
    protected def f() {println("f")}
    }
	class Sub extends Super{
	    f()
	}
	class Other{
		(new Super).f() //错误
	}
}
```

### 函数
函数可以内嵌。

传值调用（call-by-value）：先计算参数表达式的值，再应用到函数内部
传名调用（call-by-name）：将未计算的参数表达式直接应用到函数内部， 函数参数加上 =>
```scala
def fun(t:Long)  //传值调用
def fun(t: => Long) //传名调用
```

调用时可以指定参数名，从而可以不按顺序输入参数
```scala
def fun(a:Int, b:Int) = {}

fun(b=10, a=20) //指定参数名
```

通过*来指明可变参数
```scala
def fun(args: String*) //args为多个String
```

匿名函数
```scala
var inc = (x:Int) => x + 1
```

偏应用函数
偏应用函数是一种表达式，你不需要提供函数需要的所有参数，只需要提供部分，或不提供所需参数。
```scala
def log(date : Date, msg : String) 

def myLog() = {
    val date = New Date
    var logWithDate = log(date, _ : String)
    logWithDate("HelloWorld");
}
```

函数柯里化
柯里化(Currying)指的是将原来接受两个参数的函数变成新的接受一个参数的函数的过程。新的函数返回一个以原有第二个参数为参数的函数。

```scala
def addOld(x:Int,y:Int)=x+y //调用 addOld(x, y)

def add(x:Int)(y:Int) = x + y //调用 add(x)(y)

//相当于演化成  def add(x:Int) = (y:Int) = x + y

var add_1 = add(1)
var result = add_1(2)

//下面的都是等价的
def f(arg1,arg2,...,argn) = E
def f(arg1)(arg2)...(argn) = E
def f(arg1)(arg2)...(argn-1) = { def g(argn) = E; g }
def f(arg1)(arg2)...(argn-1) = argn => E
def f = arg1 => arg2 => ... => argn => E
val f = arg1 => arg2 => ... => argn => E
```

### 闭包
闭包通常来讲可以简单的认为是可以访问一个函数里面局部变量的另外一个函数。
```scala
//multiplier访问了函数外的变量factor
var factor = 3  
val multiplier = (i:Int) => i * factor  
```

### 数组
一维数组用Array，多维数组用ofDim。

```scala 
//一维数组
var a = Array[String](3)
//多维数组
var b = ofDim[Int](3,3)
```

### 集合

表List。
```scala 
val empty : List[Nothing] = List() //空表

//可以用::和Nil来构造列表，Nil表示空列表
var ls = 1::(2::(3::Nil))

//+: 在列表头添加单个元素, :+ 在列表尾添加元素，这两个操作本身不会改变操作的列表 
2 +: ls
ls :+ 3

//head表示第一个元素，tail表示除第一个元素外的剩余元素
ls.head 
ls.tail

//可以使用::: 或 List:::(ls2) 或 List.concat(...) 来链接多个链表
var ls1 = List(1,2,3,4)
var ls2 = List(1,2,3,4)
ls1:::ls2
ls1.:::(ls2)
List.concat(ls1, ls2)

```

元组可以通过t._k来访问第k个元素。
```scala
var t = (3,2,1)
var s = t._1 + t._2 + t._3
```

Option
Option[T] 是一个类型为 T 的可选值的容器： 如果值存在， Option[T] 就是一个 Some[T] ，如果不存在， Option[T] 就是对象 None 。
```scala
val myMap: Map[String, String] = Map("key1" -> "value")
val value1: Option[String] = myMap.get("key1")
val value2: Option[String] = myMap.get("key2")
```

可以使用 getOrElse() 方法来获取元组中存在的元素或者使用其默认的值，类似lua中的or
```scala
val a:Option[Int] = None 
var b = a.getOrElse(10)  //10
```

### 迭代器
用于访问集合中的元素
基本操作有next和hasNext

### 继承
重写非抽象方法时要加关键字override

### 单例对象
在 Scala 中，是没有 static 这个东西的，但是它也为我们提供了单例模式的实现方法，那就是使用关键字 object。
Scala 中使用单例模式时，除了定义的类之外，还要定义一个同名的 object 对象，它和类的区别是，object对象不能带参数。
必须在同一个源文件里定义类和它的伴生对象。
类和它的伴生对象可以互相访问其私有成员。

### Trait 特征
类似于Java中的接口。
调用超类的构造器；
特征构造器在超类构造器之后、类构造器之前执行；
特质由左到右被构造；
每个特征当中，父特质先被构造；
如果多个特征共有一个父特质，父特质不会被重复构造
所有特征被构造完毕，子类被构造。

### 模式匹配

```scala
   def matchTest(x: Any): Any = x match {
      case 1 => "one"
      case "two" => 2
      case y: Int => "scala.Int"
      case _ => "many"
   }
```

### 尾递归
尾递归在函数后面可以直接跳到函数的开头，并且改写函数的参数，从而不需要额外的空间。

```scala 
    //是尾递归
    //gcd(32,24) = gcd(24, 8) = gcd(8, 0) = 8
    def gcd(a:Int, b:Int): Int = if(b==0) a 
            else gcd(b, a%b)    

    //不是尾递归
    //factor(5) = 5 * factor(4) = 5 * (4 * factor(3)) = 5 * (4 * (3 * factor(2))) = ... = 5*(4*(3*(2*(1*1)))) = 120
    def factor(a: Int): Int = if (n==0) 1 else n * factor(n-1)

    //改成尾递归
    def factor(n: Int):Int = {
        def Iter(x:Int, result:Int):Int = if(x==0) result else Iter(x-1, result*x)
        Iter(n, 1)
    }
```
### other
赋值语句
```scala 
    val y = 0
    val x = y = 10  //y=10, x = Unit, 说明 y=10 是一个赋值语句，赋值语句类型是Unit
```

while   
while是scala内置的，但是可以用函数来实现while。
```scala 
    def while(p: => Boolean)(s: => Unit) = {
        if(p) {
            s 
            while(p)(s)
        }
    }
```

def x = e 
在定义时不会计算表达式e的值，而是在每次使用x的值时，都会计算e值。

