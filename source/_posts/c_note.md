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

### sizeof是一个运算符，而不是函数

```c
struct c{
	int a;
	static int b;
};

sizeof(struct c); //4, 静态变量存放在全局数据区，sizeof只计算栈中分配的大小。
```
sizeof(空类) = 1, sizeof(空类+虚指针) = 4

### 三目条件运算符编译器生成的代码会优于if...else...

### 函数参数的计算顺序是从右往左

### switch中判断的表达式只能为整型或字符型

### 数组中地址

```c
	//a, &a[0] 首元素地址；&a 数组首地址

	a == &a[0]; //true
	a != &a; //err, a和&a是两个不同类型，不能比较的
```
### 三数取中间数

```c
	min(max(a,b), max(b,c), max(c,a))
```

### 构造和析构函数执行顺序

构造函数：基类 -> 成员 -> 派生类
析构函数：派生类 -> 成员 -> 基类

注意，即使类定义了自己的析构函数，依然会执行成员和基类的析构函数。

析构函数定义为虚函数： 基类指针指向派生类对象，且delete该指针时。

### 临时变量可以作参数的定义为 const A& 或 A

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

### ++i 和 i++ 哪个运行快

```c
//++i 的实现
int & operator++(){
	*this += 1;

	return *this;
}

//i++的实现
int operator++(int){
	int tmp = *this;
	++(*this);

	return tmp;
}
```

所以++i的效率会更高点，但是实际上编译器会进行优化，两者的效率几乎没差别。

### 析构函数为什么用虚函数

基类指针指向派生类对象，delete 该基类指针。

### 在模板template中，如何声明嵌套从属类型

```c
template<typename C>
void func(const C& c){
	C::iterator it1(c.begin());  //err, 编译遇到C::iterator时，并不会假设它为一个类型，只有加上typename声明它是一个类型时才可以使用；

	typename C::iterator it2(c.begin()); //ok
}
```

编译器遇到一个未知类型时，并不会假设它就是一个类型，需要显式使用typename告知编译器：这是一个类型。

### 类的const static 成员初始化

整型(char,int,long,bool)的const static 可以在类内中初始化，其他的类型必须在类外初始化（包括整型数组）。

### public, protected, private 继承

|继承方式   |父public成员   |父protected成员|父private成员|
|-----------|---------------|---------------|-------------|
|public     |子public成员   |子protected成员|-            |
|protected  |子protected成员|子protected成员|-            |
|private    |子private成员  |子private成员  |-            |

### 如何避免用户的复制对象行为

将复制构造函数声明为private

### 位拷贝（浅拷贝） vs 值拷贝(深拷贝)

如果一个类拥有资源，当这个类的对象发生复制过程的时候，资源重新分配，这个过程就是深拷贝，反之，没有重新分配资源，就是浅拷贝。

### 赋值函数需要注意什么

赋值函数一般定义为:

```c
A& operator=(const & other){
	if(this == &other){
		return *this;
	}

	//do sth.

	return *this;
}
```

说明，上面中 this==&other 很重要，防止被自复制。

### 运算符重载

```c++
class A{

public:

	//成员函数格式
	A operator+();  //单目
	A operator+(const A&); //双目
	A& operator+=(const A&); 

	//友元函数格式
	friend A operator+(const A&, const A&);

	//特殊运算符重载，且只能以成员函数格式
	A& operator=(const A&); //复制
	int operator[](int i); //取下标
	int* operator()();  //仿函数
	T operator->();

	//流操作只能以友元函数重载
	friend inline ostream& operator<<(ostream& os, const A&);
	friend inline istream& operator>>(istream& is, A&);
};
```

一般情况下，单目运算符重载为成员函数；双目运算符重载为友元函数；
需要修改成员的运算符一般重载为成员函数；
(), [], ->, = 只能重载为成员函数；
流操作只能以友元函数重载；


### 如何实现单例模式

构造函数、析构函数、复制构造函数、赋值函数都声明为私有，通常的单例模式实现为：

```c
class Singleton{
	public:
		static Singleton* getInstance();

	protected:
		Singleton();

	private:
		static Singleton* instance;
};

Singleton::Singleton(){
}

Singleton* Singleton::instance = nullptr;

Singleton* Singleton::getInstance(){
	if(instance == nullptr){
		instance = new Singleton();
	}

	return instance;
}
```

### 如何实现线程安全的单例模式

上面中的getInstance不是线程安全的，因为在静态成员初始化时存在竞争关系。

```c
Singleton* Singleton::getInstance(){
	if(instance != nullptr){
		return instance;
	}

	pthread_lock(&lock);
	if(instance == nullptr){
		instance = new Singleton();
	}
	pthread_unlock(&lock);

	return instance;
}
```

### 相等和等级的区别？哪些容器使用相等或等价？

相等(equality)是以operator==为判断，如果x==y，则x和y成为相等。

等价(equalvalence)是以operator< 为判断，如果 !(x < y) && !(x > y)，则称为x和y为等价。

顺序容器一般使用“相等”，关联容器一般使用“等价”。

### STL中的vector增删元素对迭代器的影响

对于连续内存容器，如vector,deque，增删元素均会使得当前元素之后的所有迭代器失效。

对于非连续内存容器，如set，map，增删元素只对当前元素的迭代器失效。

```c
vector<int> v;

while(it != v.end()){
	if(...){
		it = v.erase(it); //it后面的都无效了
	}
	else{
		it++;
	}
}

map<int, int> m;
while(it != m.end()){
	if(...){
		m.erase(it++); //it+1之后仍然有效
		//也可以写成 it = m.erase(it);
	}
	else{
		it++;
	}
}
```

### delete 和 delete[]

delete 对应的是 new， 针对的是单个对象。 delete[] 对应的是new[]，针对的是数组对象。对数组，使用delete[] 时，会对每个对象都调用析构函数，而delete只会对第一个对象调用析构函数。

但是，因为基本类型是没有析构函数的，所以对基本类型数组，delete和delete[] 效果是一样的。

### STL中sort的实现是什么

当数组中数据量比较大时调用quicksort，当分段后的数量小于一定值时，则使用insert sort，当递归的层次过深时，会使用heapsort。

### 虚继承

虚继承主要是为了解决多重继承的问题。此时派生类中除了派生类本身的空间外，还要加上父类空间+一个虚类指针。

### 重载、覆盖和隐藏

|     |作用范围          |参数|virtual          |
|---  |---               |--- |---              |
|重载 |相同(同一个类中)  |不同|可有可无         |
|覆盖 |不同(父类和子类中)|相同|基类函数带virtual|
|隐藏 |不同(父类和子类中)|不同，或者相同且基类无virtual|


### static\_cast 和 dynamic\_cast

static\_cast< type >(c++形式的)和 c中的(type)转换是具有一样意义的。

dynamic\_cast 是将基类的指针或引用指向派生类的指针或引用，当转换失败时，返回一个空指针或抛出异常（引用），其只能应用在包含虚函数的类上。

### 构造函数可以为虚函数吗？语法和语义上能通过吗？

不可以。在语法上可以通过，语义上通不过。

### 实现一个不能在堆分配的类

是通过new在堆上分配的类的，所以可以重载new操作符，并声明为private。

```c
class A{
	private:

	void* operator new(size_t){
	}
};
```

### 实现一个不能被继承的类

使用c++11中的final

```c

class A final{
};
```

### STL中vector, list, map, set 实现 

* __map__

使用平衡二叉树实现，查找某个数时间为log(n)，插入一个元素时需要重新调整为一棵二叉树，对于未指明位置复杂度为log(n)，指明位置时的平摊复杂度为O(1)。

* __vector__

在堆中分配内存,元素连续存放,有保留内存,如果减少大小后，内存也不会释放.如果新值>当前大小时才会再分配内存。

* __list__

list就是双向链表,元素也是在堆中存放,每个元素都是放在一块内存中,它的内存空间可以是不连续的。

* __deque__

deque就是双向队列，也是在堆中存放，deque中会包含多个堆，堆和堆之间有指针相连，看起来是list和vector的结合。

deque在开始和最后添加元素都一样快,并提供了随机访问方法,像vector一样使用[]访问任意元素,但是随机访问速度比不上vector快,因为它要内部处理堆跳转。

deque也有保留空间。另外,由于deque不要求连续空间,所以可以保存的元素比vector更大。

### 智能指针 

* __auto\_ptr__

auto\_ptr 是一个类，参数模板是对象。但是C++11已经弃用auto\_ptr了。

```c
class A{
	void show() { cout<<"A"<<endl; }
};

auto_ptr<A> ap(new A());

ap->show();
ap.get();  //返回原始指针， &A

//判断一个智能指针是否为空
if(ap.get()==NULL) {
	...
}
```

执行智能指针赋值 ap2 = ap1 时, ap2会接管ap1的内存管理权：
1. ap1 变为空指针；
2. 如果ap2不为空，先释放原来的资源，再接管ap1的资源。


* __unique\_ptr__

用于取代auto\_ptr。

unique\_ptr无法进行复制构造，无法进行复制赋值操作。即无法使两个unique\_ptr指向同一个对象。但是可以进行移动构造和移动赋值操作。
即不能使用 up2 = up1，但是可以使用 up2 = move(up1)。可以使用 up == NULL 的判断。

* __share\_ptr__

使用计数机制来表明资源被几个指针共享。可以通过成员函数use_count()来查看资源的所有者个数。

当我们调用release()时，当前指针会释放资源所有权，计数减一。当计数等于0时，资源会被释放。

### 用一台4G内存的机器对100G数据进行排序[摘自陈硕博客]

使用内存排序(如快排)对100G数据进行分块排序，每块排序后的数据输出到一个文件中，接着使用堆排序对这些已经排好序的文件进行多路归并排序。
IO读数据只有两遍。

### 有 a、 b 两个文件，大小各是 100G 左右，每行长度不超过 1k，这两个文件有少量（几百个）重复的行，要求用一台 4G 内存的机器找出这些重复行[摘自陈硕博客]

将a, b 两个文件按行hash到几百个小文件中，再对小文件(a1, b1), (a2, b2) 进行求交集

