---
title: C++知识点学习
---

## 函数
### 内联函数
内联函数需要在.h中定义，一旦内联函数发生修改，所有包含其头文件的文件都需要编译。
在类中定义的函数自动成为内敛函数。

### 重载函数
非指针、非引用的const形参和非const形参是等价的，所以const和非const的函数不是重载，会报错。
```c
    int f1(const A)
    int f1(A)      //error,重定义

    int f2(const A&)
    int f2(A&)     //ok,是重载

    int f3(const A*)
    int f3(A* )    //ok, 是重载
```

typedef, define 只是提供别名，类型本身不变，基于typedef的函数不能重载，会报错。
```c
    typedef A B;

    int f(A);
    int f(B); //error, 重定义
```

每一个版本的重载函数都应该在同一个作用域中声明。如果局部地声明一个函数，则该函数将屏蔽而不是重载在外层作用域中声明的同名函数。

## 类
### mutable 
mutable 声明的成员变量允许在const的成员函数中被修改。

### explicit
可以在类的构造函数声明前加上explicit，防止在调用其构造函数中对参数进行隐式类型转换。
```c 
class A{
    public:
            A(string &);
            bool isEq(const A&);
};

A a;

//进行隐式转换，生成临时对象A("Hello")进行传参，如果将其构造函数加上explicit，就不能进行类型转换了，这时就会报错。
a.isEq("Hello"); 
```

### 访问控制
struct的成员默认是public的，class的成员默认是private的。

### 初始化列表
包含以下条件的成员，必须在构造函数的初始化列表中进行初始化。
1. 没有默认构造函数的成员
2. const 成员
3. 引用类型成员

成员被初始化的次序是根据定义成员的次序。

### 构造函数
如果一个类定义了至少一个构造函数，则编译器再也不会为其生成默认构造函数。  
默认构造函数中，只会对具有类类型的成员通过运行各自的默认构造函数来进行初始化。内置和复合类型的成员，如指针和数组，只对定义在全局作用域中的对象才进行初始化。  
类通常都应该定义一个默认构造函数。  

### {...} 显式初始化
对于没有定义构造函数，且所有成员都是public的类，可以用{}进行显式初始化。
```c
class A{
    public:
            string name;
            int age;
            string sex;
};

A a = { "Jack", 20, "Male" };
```

### 复制构造函数
A(const A&)  
如果定义了复制构造函数，则必须也定义默认构造函数。  

在继承类的复制构造函数和赋值函数中，如果要调用父类的复制构造函数和赋值函数，需要显式调用。
```c
class Parent{
    ...
};

class Child : public Parent{
    public:
        Child(const Child& rh) : Parent(rh) { ... }

        Child& operator=(const Child& rh) 
        {
            if(this != &rh){
                Parent::operator=(rh);
            }

            return *this;
        }
};
```

### 析构函数
析构函数和构造函数不一样：
1. 析构函数只能有一种方式且是无参数的；
2. 即使定义了用户的析构函数，默认析构函数依然会被调用，在默认析构函数中，会调用各成员各自的析构函数。
3. 在需要释放资源时，析构函数最好定义成虚函数，这样在调用一个基类指针的析构函数时，知道应该调用哪个正确的函数。

需要定义析构函数的地方，一般也需要定义拷贝构造函数和赋值函数，这称为三原则。

### 继承
构造函数和复制构造函数不能被继承。

### 友元
```c
friend class A;  //友元类
friend int B::foo(void); //友元成员函数
friend int test(void); //友元普通函数
```

### 重载操作符
重载下标操作符[]时，一般需要重载两个版本：一个非const成员的返回和一个const成员的返回
```c
class A{
    public:
            const int& operator[](int idx) const { return data[idx]; }
            int& operator[](int idx) { return data[idx]; }
    private:
            vector<int> data;
};
```

重载自增/自减操作符
```c
class A{
    public:
            //前缀自增， ++A
            A& operator++()
            {
                cur++;

                return *this;
            }

            //后缀自增，A++
            //这里增加参数int，是为了和前缀自增进行区别
            A operator++(int)
            {
                A ret = *this;
                ++*this;

                return ret;
            }

    private:
            int cur;
};
```

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
