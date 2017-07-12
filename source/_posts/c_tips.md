---
title: C++小知识
---

## 知识
* sizeof是一个运算符，而不是函数
```c
struct c{
	int a;
	static int b;
};

sizeof(struct c); //4, 静态变量存放在全局数据区，sizeof只计算栈中分配的大小。
```
sizeof(空类) = 1, sizeof(空类+虚指针) = 4

* 三目条件运算符编译器生成的代码会优于if...else...
* 函数参数的计算顺序是从右往左
* switch中判断的表达式只能为整型或字符型
* 数组中地址
```c
	//a, &a[0] 首元素地址；&a 数组首地址

	a == &a[0]; //true
	a != &a; //err, a和&a是两个不同类型，不能比较的
```
* 三数取中间数
```c
	min(max(a,b), max(b,c), max(c,a))
```

* 构造和析构函数执行顺序
构造函数：基类 -> 成员 -> 派生类
析构函数：派生类 -> 成员 -> 基类

注意，即使类定义了自己的析构函数，依然会执行成员和基类的析构函数。

* 临时变量可以作参数的定义为 const A& 或 A
```c
class A{
}; 

void f1(A a);
void f2(A& a);
void f3(const A& a);

f1(A()); //ok
f2(A()); //err
f3(A()); //ok
```
