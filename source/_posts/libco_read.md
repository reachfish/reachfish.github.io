---

title: libco的阅读
date: 2017/8/9 09:00:00

---

## 函数

### 结构体

```c
struct stStackMem_t{
	stCoRoutine_t* occupy_co; //标明该栈当前被谁占有，共享栈时才可能会被占用
	int stack_size;
	char* stack_bp; //stack_buffer + stack_size
	char* stack_buffer;
};

//共享栈是把stack_array挨个进行分配
//共享栈使用Round Robin算法进行分配，当两个协程使用同一块内存时，轮到谁执行时谁就会抢占
struct stShareStack_t
{
	unsigned int alloc_idx;
	int stack_size;
	int count;
	stStackMem_t** stack_array;  //count个stack_size的stStackMem_t
};

struct stCoRoutineAttr_t{
	int stack_size; //128*1024 ~ 8*1024*1024，且是0x1000的倍数
	stShareStack_t*  share_stack; //是否使用共享栈
};

struct stCoRoutine_t
{
	stCoRoutineEnv_t *env;
	pfn_co_routine_t pfn;
	void *arg;
	coctx_t ctx; //里面的指针指向stack_mem

	char cStart;
	char cEnd;
	char cIsMain;
	char cEnableSysHook;
	char cIsShareStack;

	void *pvEnv;

	//char sRunStack[ 1024 * 128 ];
	stStackMem_t* stack_mem;


	//save satck buffer while confilct on same stack_buffer;
	char* stack_sp; 
	unsigned int save_size;
	char* save_buffer;

	stCoSpec_t aSpec[1024];
};

//每个线程对应一个协程栈
//创建一个线程的co env时，需要先创建一个入口协程、pEpoll数据结构。
struct stCoRoutineEnv_t
{
	stCoRoutine_t *pCallStack[128]; //每个线程的嵌套协程最大深度128
	int iCallStackSize;
	stCoEpoll_t *pEpoll;  //该线程中关联协程的epoll结构，遇到send,recv等时会自动切换协程，pEpoll就是检测里面遇到的各个fd事件
	//struct stCoEpoll_t
	//{
	//	int iEpollFd;				   //epoll_create返回的套接字
	//	static const int _EPOLL_SIZE = 1024 * 10;
	//	struct stTimeout_t *pTimeout;   //维护60s长度的队列
	//	struct stTimeoutItemLink_t *pstTimeoutList;
	//	struct stTimeoutItemLink_t *pstActiveList;
	//	co_epoll_res *result; 
	//};

	//for copy stack log lastco and nextco
	stCoRoutine_t* pending_co; //即将切换的协程
	stCoRoutine_t* occupy_co;  //标明谁的栈被pending_co给抢占了
};

g_arrCoEnvPerThread;  //所有线程对应的co env数组

```

```c
struct stTimeoutItem_t
{

	enum
	{
		eMaxTimeout = 40 * 1000 //40s
	};

	//以下三项是链表结构
	stTimeoutItem_t *pPrev;
	stTimeoutItem_t *pNext;
	stTimeoutItemLink_t *pLink; //所指向的链表，结构如下：
	//struct stTimeoutItemLink_t
	//{
	//	stTimeoutItem_t *head;
	//	stTimeoutItem_t *tail;
	//};

	unsigned long long ullExpireTime;

	OnPreparePfn_t pfnPrepare;  //从原队列中删除，并将其加入active队列中
	OnProcessPfn_t pfnProcess;  //事件回调函数，实际调用时是恢复协程的执行co_resume(pArg)

	void *pArg; // routine 
	bool bTimeout; //表明是否是Timeout了
};

struct stTimeout_t
{
	stTimeoutItemLink_t *pItems; //pItems[i]表示一个链表链表，里面的元素的超时时间-ullStart=i
	int iItemSize;

	//设上次timeout的时间为t1, 结束index为 idx1
	//那么当经过时间t后，处理的范围为[idx1, idx1 + t]
	//然后更新idx2 = idx1 + t, t2 = t1 + t
	//也是一个圈循环处理
	unsigned long long ullStart;  
	long long llStartIdx;
};

struct stPollItem_t : stTimeoutItem_t 
{
	struct pollfd *pSelf;
	stPoll_t *pPoll;

	struct epoll_event stEvent;
};

struct stPoll_t : stTimeoutItem_t 
{
	struct pollfd *fds;
	nfds_t nfds; // typedef unsigned long int nfds_t;

	stPollItem_t *pPollItems;

	int iAllEventDetach;
	int iEpollFd;
	int iRaiseCnt;
}

```

```c
struct coctx_param_t{
	const void *s1;
	const void *s2;
};

struct coctx_t{
	void *regs[14];
	size_t ss_size;
	char *ss_sp;
};
```

### co_swap(curr, pending_co)

协程切换

__步骤：__

1. 获取当前线程的env，设置其pending_co(抢占别的栈的协程)和occupy_co(栈被抢的协程)。如果传入参数pending_co为共享栈的，则它们都为空，否则:
更新env->pending_co和env->occupy_co。并且把occupy_co的栈给保存起来(把sp到bp之间的数据拷贝到save_buffer中)。

2. 进行上下文切换coctx_swap，切换之后可能会换了上下文

3. 重新获取cur_env和它的pending_co,occupy_co，如果这两者不同并且pending_co的save_buffer不为空，则把save_buffer中的内容重新拷到它的栈中去。

### co_alloc_stackmem(stack_size)

分配一个copy栈。

### co_alloc_sharestack(count, stack_size)

分配共享栈，包含了count个栈，每个栈的大小为stack_size。

### co_eventloop(stCoEpoll_t* ctx, pfn, arg)

操作为：

while(true){
	事件终端 + 1ms 超时检测，内部调用co_poll_wait。
}

对线程所属的CoEpoll进行loop循环，当协程超时或者触发事件时，则会恢复协程。循环会一直执行，直到pfn(arg)返回-1才跳出循环。

### co_poll_inner(stCoEpoll_t* ctx, struct pollfd fds[], nfds_t nfds, int timeout, poll_pfn_t pollfunc) 

当前协程添加epoll事件，添加timeout，添加完成后当前线程进行协程切换。

### co_resume(co)

恢复协程的执行。
将当前协程压入栈顶，将栈顶下一个协程切换到当前的协程。

何时调用：
1. OnPollProcessEvent: 遇到epoll事件时。
2. OnSignalProcessEvent
3. OnCoroutineEvent: 代码中没碰到这种情况。


### CoRoutineFunc(co, *)

所有协程的入口调用函数。

__步骤：__

执行co->pfn(co->arg)函数。
co->env切换协程co_yield_env(栈顶协程退出，并且切换到栈顶的下一个协程)。

### AddTimeout(apTimeout, apItem, allNow)

将apItem加入到apTimeout中。

满足的条件为：

```c

timeoutList.ullStart < allNow < apItem.ullExpireTime

```

## 同步

同步唤醒就是把协程添加到 pstActiveList 中，然后在其响应函数 OnSignalProcessEvent 中恢复协程。

### int co_cond_signal( stCoCond_t *si )

唤醒Cond List的头部。

### int co_cond_broadcast( stCoCond_t *si )

唤醒Cond List中的所有元素。

### int co_cond_timedwait( stCoCond_t *link,int ms )

等待条件满足。
如果超时，则添加超时事件，添加完毕之后，进行协程切换，等待其他条件满足时，再唤醒。

### example_cond 

协程间的同步，改例子是生产者和消费者之间的协作。

```c
void* Producer(void* args)
{
	co_enable_hook_sys();
	stEnv_t* env=  (stEnv_t*)args;
	int id = 0;
	while (true)
	{
		stTask_t* task = (stTask_t*)calloc(1, sizeof(stTask_t));
		task->id = id++;
		env->task_queue.push(task);
		printf("%s:%d produce task %d\n", __func__, __LINE__, task->id);
		co_cond_signal(env->cond);  //唤醒消费者
		poll(NULL, 0, 1000);
	}
	return NULL;
}

void* Consumer(void* args)
{
	co_enable_hook_sys();
	stEnv_t* env = (stEnv_t*)args;
	while (true)
	{
		if (env->task_queue.empty())
		{
			co_cond_timedwait(env->cond, -1);  //等待被唤醒
			continue; //增强检查，被唤醒后，是继续从这句话开始执行的，之后继续判断队列是否为空，增强代码的健壮性。
		}
		stTask_t* task = env->task_queue.front();
		env->task_queue.pop();
		printf("%s:%d consume task %d\n", __func__, __LINE__, task->id);
		free(task);
	}
	return NULL;
}
```

## 汇编部分学习

### C函数调用和栈帧分析

每个函数对应一个stack frame。

stack frame 的机构为：
1. ebp，储存调用者的stack frame的帧指针。ebp寄存器指向此地址。
2. 保存的寄存器、局部变量以及临时值。
3. 被调函数的 argn, argn-1, ..., arg1
4. 返回地址，call语句之后返回的地址。

所以，ebp是frame指针，而esp是栈指针，数据的存储与丢弃是esp负责的，而数据的访问则是ebp来负责的。

每个stack frame存储了调用它的ebp，它所调用函数的参数。假设A调用B，B调用C，则在B的帧中保存了A的ebp，C的参数，以及B的局部变量，B的返回地址。

Call语句：把返回地址入栈，把当前寄存器的ebp入栈，接着寄存器的ebp更新为当前esp的值。

Ret语句：弹出栈顶ebp元素到ebp中，接着调到返回地址中继续执行。

若返回值是一个整数或指针，按惯例由eax返回。

寄存器eax, edx, ecx由调用者负责保存。
寄存器ebx, esi, edi由被调用者负责保存。

分析调用函数的汇编

```c
int f1{
...
int e = f2(a, b)
...
}
```

在f1调用f2时，负责传递参数、返回地址

```x86asm
//保存参数
mov b $rdi
mov a $rsi   

//将rip的地址入栈，接着更新rip的值为f2的地址
call f2
```

在f2函数的入口，负责建立自己的栈帧

```x86asm  
push  $rbp
mov   $rsp  $rbp
```

在f2调用结束时，负责恢复f1的栈帧、执行地址

```x86asm 
leaveq  //相当于 mov rbp rsp; pop rbp，是入口地方建立栈的反操作

retq  //此时栈顶指向返回地址，retq相当于将栈顶的地址出栈赋给rip 
```

### 协程切换coctx_swap(cur, pending)

__操作__：

存旧：保存原来协程寄存器的值、保存返回地址
换新：恢复原来的值到寄存器中、修改栈顶指针esp，恢复返回地址到栈顶，通过ret指令跳到栈顶的地址在开始执行。

函数调用时，参数少于7个时，把参数保存到寄存器中：rdi, rsi, rdx, rcx, r8, r9

刚进入coctx_swap汇编函数中栈结构为：

rbp: 帧地址
...
rsp：返回地址

第一个参数：cur，保存在rsi中
第二个参数：pending，保存在rdi中 

```c
//low | regs[0]: r15 |
//    | regs[1]: r14 |
//    | regs[2]: r13 |
//    | regs[3]: r12 |
//    | regs[4]: r9  |
//    | regs[5]: r8  | 
//    | regs[6]: rbp |
//    | regs[7]: rdi |
//    | regs[8]: rsi |
//    | regs[9]: ret |  //ret func addr
//    | regs[10]: rdx |
//    | regs[11]: rcx | 
//    | regs[12]: rbx |
//hig | regs[13]: rsp |

struct coctx_t
{
	void *regs[14];
	size_t ss_size;
	char *ss_sp;
};
```

```x86asm
/*
rax ->
返回地址  
*/
leaq 8(%rsp),%rax    //刚进入被调函数时，返回地址在栈顶
leaq 112(%rdi),%rsp  //rdi指向第一个参数cur，指向regs[13]的尾部

//接下来保存第一个协程的各个寄存器的值
pushq %rax        //把rsp放到cur->regs[13]中
pushq %rbx
pushq %rcx
pushq %rdx
pushq -8(%rax) //ret func addr
pushq %rsi
pushq %rdi
pushq %rbp
pushq %r8
pushq %r9
pushq %r12
pushq %r13
pushq %r14
pushq %r15

//恢复第二个协程各个寄存器的值
movq %rsi, %rsp   //为什么不是 leaq 104(%rsi), %rsp ?? 
popq %r15
popq %r14
popq %r13
popq %r12
popq %r9
popq %r8
popq %rbp
popq %rdi
popq %rsi
popq %rax //ret func addr
popq %rdx
popq %rcx
popq %rbx
popq %rsp

pushq %rax
xorl %eax, %eax
ret   //ret 表示当前栈顶元素为一个执行地址，把改地址出栈并且修改eip值
```

## Hook

重载阻塞函数，使得函数原来的阻塞挂起变成阻塞切换协程。

以send为例子：send -> poll-> co_poll_inner -> 添加epoll事件 -> 切换协程。
在epoll事件后，触发该协程被激活-> 协程切换 -> 继续执行原来代码 -> 执行系统原来的send函数。

系统原来的send函数，通过打开动态库dlsym(RTLD_NEXT, "send")来获得。


## 总结

### libco如何实现协程间的平级调用，而普通的C语言为什么不能创建协程

C语言通过栈来保存自身的数据，传统的函数调用都是一栈接着一栈，从而导致函数间不能同级调用，只能上下调用。而libco把所有协程自己负责栈的创建和维护，在堆中创建栈，并且通过使用汇编语言把sp指向自定义栈。从而使得函数间的调用具有平级效果。

### libco协程的优缺点

协程比线程具有的好处：切换开销小，共享数据不需要加锁。
对于独立并发的任务，还是使用多线程才能高效率，而对于加锁或同步问题，可以考虑使用这种协程。

### 协程保存恢复

协程的状态包括：

1. 寄存器的值（保存到上下文结构coctx）中
2. 当前执行地址（保存到上下文结构coctx）中
3. 普通私有变量，保存到自己的栈帧中

所以协程的保存对着三者保存即可，协程的恢复也是对这三者恢复即可。

对于1,2使用汇编语言来访问修改寄存器，对于3,直接使用C语言可以访问修改栈帧了，但要注意对于协程的栈帧，如果是保存在C语言本身的栈中则随着程序的跳转会销毁了，所以需要把它的栈帧改放到堆中来生成，从而可以一直可以访问到。


### 阻塞超时切换协程

每个线程维护一个协程栈，一个CoEpoll结构，该结构包含一个epoll fd，以及一个超时事件队列。协程遇到阻塞被切换下一个协程，在超时、epoll事件的回调函数中被重新执行。假如某个协程一直没被阻塞，那么其他协程将没法运行。

### 同步切换协程

协程间的同步：协程间共享一个同步结构体（可以是静态数据或堆上的数据），协程通过timewait把自己挂起切换到其他协程中，其他协程则通过signal该结构体重新把挂起的协程重新加到唤醒队列中。

### 协程栈

每个线程都会在协程栈的底部创建一个Main协程，main协程没有调用函数。通过co_create创建出来的协程不会直接加到协程栈上，只有当co_resume时，才会把该协程添加到协程栈顶上。

协程栈中的自底往上的结构为： main协程 -> 协程1 -> 协程2(协程1运行过程co_resume(2)) -> 协程3(协程2运行过程中co_resume(3)) ...

除main协程外，每个协程的入口函数都是

```c
static int CoRoutineFunc( stCoRoutine_t *co,void * )
{
	if( co->pfn )
	{
		co->pfn( co->arg );    //用户真正自定义的函数，用作co_create中的参数
	}
	co->cEnd = 1;

	stCoRoutineEnv_t *env = co->env;

	co_yield_env( env );     //当前协程退栈，运行下一个栈顶的函数，以上面的例子为例，切换的情况可能为 协程3->协程2->协程1->main协程

	return 0;
}
```

### 共享栈

libco即可以使用独用栈，每个协程单独分配一个栈，也可以使用共享栈，协程从共享栈中分配获得一个栈，当协程个数超过共享栈中栈数目时，有些协程将会共享同一个栈，假如协程A和B共享一个栈stack，并且出现A协程切换到B协程时，需要先把stack中的数据保存到A的私有空间中，再把B私有空间的数据拷到栈stack中。
加入协程个数很多，使用共享栈可以降低空间需求，但是也会增加数据的copy out, copy in的时间开销。

是否使用共享栈的对策：在频繁 co_create 时因为需要创建很多协程，可以考虑使用共享栈。 但是在频繁 co_resume 时因为需要协程间频繁切换， 则可以考虑使用独占栈。

## 改进

### co_poll_wait 的效率
1. co_eventloop中在检测事件 co_poll_wait 中是每隔1ms就去检查是否判断超时，检查频繁；
2. timeout list 有缺陷， timeout list是按ms组成的数组，数组大小是60 * 1000，表示60秒，而co_poll_wait中会把 now - Start 之间的当做超时来处理了，所以该超时最多只能用在60s内的超时，对于大于60s的超时是错误的，里面有一个比较隐秘的地方，加了把大于40的超时都改成40，代码是后来添加的，猜测是他们为了fix而加上的。

__改进的思考：__
采用libevent中的思路，修改timeout list，改用最小堆队列来表示，判断时直接检查当前时间是否大于其过期时间，这样可以对大于60s的超时仍然适用；
并且按堆中最小的时间设置 co_poll_wait中的timeout参数，避免了固定1ms检查，也减少了频繁调用。

__补充：__

考虑到微信的并发任务非常大，假如每一毫秒都很可能发生事件。设总事件数为n，激活事件数为k，采用这种的timeout结构，可以在O(k)的时间内来找出所有激活的事件，而采用小根堆的复杂度为O(k*log n)。这样看来，这种timeout结构虽然不能表示大于60s的超时事件，但是在事件频繁的时候，反而可以极大提高效率，所以也不算是缺陷。

### 协程同步

用于协程同步的数据结构很简单，不能支持稍微复杂的同步，如生产m才能消费1，或者初值为m的资源。

__改进的思考：__
简单点的可以在链头结构中增加一个变量value表示初始资源，复杂点的同步结构还可以在链头结构中增加func, value。

### 用户增加协程切换类型

libco目前支持的协程切换有阻塞切换(如io阻塞)、同步等待切换，用户如何实现更加多类型的切换

用户可以实现两个函数：

```c
//自动切换的函数 
my_switch(){
	if(...){ //检查条件
		return
	}

	use_data *udata;
	udata->pfnProcess = my_wakeup
	co_yield_ct() //切换当前协程
}

//唤醒函数
my_wakeup(){
	...

	co_resume(co) //恢复协程
}
```

### 协程间唤醒是无状态的，导致协程间的数据传递能力很弱

唤唤醒协程co时，不提供其他形参，不具备向co传递参数功能。唤醒协程的定义为
```c
void co_resume(stCoRoutine_t *co)    //
```

协程挂起的定义为

```c
//协程在这里被挂起，当然被唤醒后也是在这语句之后执行，
//但是被唤醒后是无状态，没有返回值的(返回值是void)，也就没法获得一些额外的信息
void co_yield(stCoRoutine_t *co)     
```

这种无状态的唤醒、被唤醒能力会有限，使得协程间同步或传递数据能力不强。比如，它不能实现如下的需求：

```c
void produce_action(){

	randome produce one food;   //生产者随机生成一种食品

	co_resume(consumer_co,  "cake");  //生产者生产了cake，并且唤醒消费者，告知其生成了cake
}

void consumer_action(){

	food = co_yield()    //消费者等待生产者生产一种食品

	switch(food){  //根据生产的食品执行不同动作
		...
	}
}
```

__改进的思考：__

协程数据结构增加一个成员 void* pArg，用于传递数据，并且修改原来的唤醒、挂起函数：

```c
void co_resume(stCoRoutine_t *co, void *arg, size_t arg_len){
	if(co->pArg){
		free(co->pArg);
		co->pArg = NULL;
	}

	if(arg && arg_len){
		co->pArg = malloc(arg_len);
		memcpy(co->pArg, arg, arg_len);
	}

	//原来的co_resume部分
	...
}

void *co_yield(stCoRoutine_t *co){
	//原来的co_yield部分
	...

	return co->pArg;
}
```

改写成这样的结构后，就很容易在唤醒其他协程时传递参数，而在被唤醒后，也可以获得返回值了。

