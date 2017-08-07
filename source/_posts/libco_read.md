---

title: libco的阅读

---

## 函数

### 结构体

```c
struct stStackMem_t{
	stCoRoutine_t* occupy_co; //标明该栈当前被谁占有
	int stack_size;
	char* stack_bp; //stack_buffer + stack_size
	char* stack_buffer;
};

//共享栈是把stack_array挨个进行分配
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
struct stCoRoutineEnv_t
{
	stCoRoutine_t *pCallStack[128]; //每个线程的嵌套协程最大深度128
	int iCallStackSize;
	stCoEpoll_t *pEpoll;  //该线程中关联协程的epoll结构，遇到send,recv等时会自动切换协程，pEpoll就是检测里面遇到的各个fd事件
	//struct stCoEpoll_t
	//{
	//	int iEpollFd;				   //epoll_create返回的套接字
	//	static const int _EPOLL_SIZE = 1024 * 10;
	//	struct stTimeout_t *pTimeout;   //60秒超时
	//	struct stTimeoutItemLink_t *pstTimeoutList;
	//	struct stTimeoutItemLink_t *pstActiveList;
	//	co_epoll_res *result; 
	//};

	//for copy stack log lastco and nextco
	stCoRoutine_t* pending_co; //即将切换的协程
	stCoRoutine_t* occupy_co;  //标明谁的栈被pending_co给抢占了
};

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

	unsigned long long ullStart;  //开始时间
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

对线程所属的CoEpoll进行loop循环，当协程超时或者触发事件时，则会恢复协程。循环会一直执行，知道pfn(arg)返回-1才跳出循环。

### co_poll_inner(stCoEpoll_t* ctx, struct pollfd fds[], nfds_t nfds, int timeout, poll_pfn_t pollfunc) 


### coctx_swap(cur, pending)

刚进入coctx_swap汇编函数中栈结构为：

rbp: 帧地址
.
.
.
第二个参数：pending 
第一个参数：cur 
rsp：返回地址

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

```asm
leaq 8(%rsp),%rax 
leaq 112(%rdi),%rsp  //rdi指向第一个参数cur，指向regs[13]

pushq %rax        //把cur的返回地址放到cur->regs[13]中

//接下来保存个寄存器的值
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

movq %rsi, %rsp
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
ret
```

### CoRoutineFunc(co, *)

所有协程的入口调用函数。

__步骤：__

执行co->pfn(co->arg)函数。
co->env切换协程co_yield_env(栈顶协程退出，并且切换到栈顶的下一个协程)。

### AddTimeout(apTimeout, apItem, allNow)

将apItem加入到apTimeout中。
