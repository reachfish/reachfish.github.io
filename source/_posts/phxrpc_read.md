---

title: phxrpc源码阅读
date: 2017/8/11 09:00:00

---

phxrpc是微信开源的rpc框架。

# rpc框架

## rpc/http_caller

### HttpCaller

代码

```c
    BaseTcpStream & socket_;
    ClientMonitor & client_monitor_;
    int cmdid_;

    HttpRequest request_;
    HttpResponse response_;

	//连接
	//相当于客户端发起连接
	//request -> post -> rsponse
	int HttpCaller::Call(const google::protobuf::MessageLite & request, google::protobuf::MessageLite * response)

	void SetURI(const char * uri, int cmdid );
    void SetKeepAlive(const bool keep_alive );
```

说明：http客户端建立连接部分。

## rpc/hsha_server

### 半同步半异步模式

一种服务器网络框架模式：使用线程池，这些线程负责执行服务端所有代码的执行。一部分负责IO，一部分负责业务逻辑。两者是独立的，互相不需要管对方做什么，它们是生产者/消费者的关系。

hsha就是网络io部分为非阻塞异步模式，而业务逻辑为同步模式。

同步和异步部分采用一个作业队列(jobQueue)来实现结合。io回调函数中的on_accept, on_recv, on_send, on_close等会把相关任务和上下文放到作业队列，而负责执行作业的线程会被唤醒，取出这些作业并继续执行。

该模式的原文为：http://www.cs.wustl.edu/~schmidt/PDF/HS-HA.pdf . 

开源的spserver就是包含了这种模式。

### DataFlow 

代码

```c
    ThdQueue<std::pair<QueueExtData, HttpRequest *> > in_queue_;
    ThdQueue<std::pair<QueueExtData, HttpResponse *> > out_queue_;

    void PushRequest(void * args, HttpRequest * request);
    int PluckRequest(void *& args, HttpRequest *& request);
    int PickRequest(void *& args, HttpRequest *& request);

    void PushResponse(void * args, HttpResponse * response);
    int PluckResponse(void *& args, HttpResponse *& response);
    bool CanPushRequest(const int max_queue_length);
    bool CanPluckResponse();

    void BreakOut();
```

### HshaServerQos

代码

```c
    const HshaServerConfig * config_;
    HshaServerStat * hsha_server_stat_;
    std::mutex mutex_;
    std::condition_variable cv_;
    std::thread thread_;
    bool break_out_;
    int enqueue_reject_rate_; //入队被拒绝概率
    int inqueue_avg_wait_time_costs_per_second_cal_last_seq_;  //这变量名服了

    void CalFunc();
    bool CanAccept(); //跟最大连接数相关
    bool CanEnqueue(); //满足随机数大于入队被拒绝概率即可
```

### Worker

代码

```c
    WorkerPool * pool_; //线程池
    int uthread_count_; //协程数
    int utherad_stack_size_;
    bool shut_down_;
    UThreadEpollScheduler * worker_scheduler_;  //协程模式中的调度器
    std::thread thread_;

	//根据协程数是否为0选择线程或协程
    void Func(); 

	//data_flow_->shut_down_
    void Shutdown();

	//线程模式
	//步骤：
	//空闲线程数+1
	//阻塞等待请求 data_flow_->PluckRequest
	//空闲线程数-1
	//处理业务逻辑WorkerLogic(request)
    void ThreadMode();

	//协程模式
	//步骤：
	//若当前任务未满，则等待请求 data_flow_->PickRequest
	//调度器添加执行该任务
    void UThreadMode();

	//设置处理request的响应，实际就是交给调度器执行任务
    void HandlerNewRequestFunc();

	//协程处理函数，里面就是允许业务逻辑函数 WorkerLogic
    void UThreadFunc(void * args, HttpRequest * request, int queue_wait_time_ms);

	//业务处理逻辑 
	//步骤：
	//线程池的处理函数来处理得到的请求 pool->dispatch_ 
	//把结果返回给data_flow_中 data_flow_->PushResponse
	//线程池通知epoll
    void WorkerLogic(void * args, HttpRequest * request, int queue_wait_time_ms);

	//线程池通知epoll
    void Notify();
```

### WorkerPool 

代码

```c
    friend class Worker;
    UThreadEpollScheduler * scheduler_;
    DataFlow * data_flow_;
    HshaServerStat * hsha_server_stat_;
    Dispatch_t dispatch_;
    void * args_;
    std::vector<Worker *> worker_list_;
    size_t last_notify_idx_;
    std::mutex mutex_;
```

### HshaServerIO

代码

```c
    int idx_;
    UThreadEpollScheduler * scheduler_;
    const HshaServerConfig * config_;
    DataFlow * data_flow_;
    int listen_fd_;
    HshaServerStat * hsha_server_stat_;
    HshaServerQos * hsha_server_qos_;
    WorkerPool * worker_pool_;

    std::queue<int> accepted_fd_list_; //accept fd 
    std::mutex queue_mutex_;

    void RunForever();

	//fd入队列，并且进行通告NotifyEpoll
    bool AddAcceptedFd(int accepted_fd);

	//调度器将accept队列里的fd进行添加任务 scheduler_->AddTask，处理的入口函数是 IOFunc
    void HandlerAcceptedFd();

	//while(1){
	//	 从accept_fd中接收request，并且把request push到data_flow_中
	//   协程挂起等待调度器执行完毕，返回response，并且把response返回去
	//   如果出错或者不是keep alive的，则停止循环
	//}
    void IOFunc(int accept_fd);

	//把data_flow_中的response给返回去
    UThreadSocket_t * ActiveSocketFunc();

```

### HshaServerUnit 

单个服务器

代码 

```c
    HshaServer * hsha_server_;
    UThreadEpollScheduler scheduler_;
    DataFlow data_flow_;
    WorkerPool worker_pool_;
    HshaServerIO hsha_server_io_;
    std::thread thread_;


	//hsha_server_io_.RunForever
    void RunFunc();

	//hsha_server_io_.AddAcceptedFd
    bool AddAcceptedFd(int accepted_fd);

```

### HshaServerAcceptor

代码 

```c
    HshaServer * hsha_server_;
    size_t idx_;

	//专门listen连接，连接accept后，就抛给io线程侦听
    void LoopAccept(const char * bind_ip, const int port);
```

### HshaServer 

代码

```c
    const HshaServerConfig * config_;
    ServerMonitorPtr hsha_server_monitor_;
    HshaServerStat hsha_server_stat_;
    HshaServerQos hsha_server_qos_;
    HshaServerAcceptor hsha_server_acceptor_;

    std::vector<HshaServerUnit *> server_unit_list_;

	//while(1) {
	// acceptor 一直保持listen
	//}
    void RunForever();
```

### 小结

HshaServer包含:

* 多个执行单元HshaServerUnit， 每个执行单元中包含一个data_flow，一个io处理和一个业务逻辑处理池 WorkerPool，一个io可以处理多个accept fd。 

* 一个acceptor，专门用于listen收发上来的accept fd，当建立以一个连接连接后，按Round Robin算法分配到一个执行单元 HshaServerUnit 上。 HshaServer的主函数就是一直运行acceptor的Loop Listen逻辑。

* 质量保证 HshaServerQos。

* 统计工具 HshaServerStat。

## rpc/thread_queue

### ThdQueue

多线程环境下的加锁队列

代码 

```c
	//压入队列
    void push(const T & value);

	//出队列，如果队列为空，则阻塞等待
    bool pluck(T & value);

	//出队列，如果为空，则返回false
    bool pick(T & value);

	//关闭 
    void break_out();
```

# network框架

## 协程实现 

数据结构

```c
typedef struct ucontext {  
	struct ucontext *uc_link;   //当前上下文终止时，将会恢复的上下文
	sigset_t         uc_sigmask; //该上下文中阻塞信号的信号 
	stack_t          uc_stack;   //该上下文使用的栈 
	mcontext_t       uc_mcontext; //特定的机器表示，包括线程使用的特定寄存器 
	...  
} ucontext_t;
```

### int getcontext(ucontext_t *ucp);

将当前上下文保存到 ucp 中。

### int setcontext(const ucontext_t *ucp);

切换到ucp表示的上下文中
1. 如果ucp是getcontext取得的，则会继续继续这个调用
2. 如果ucp是是通过调用makecontext取得,程序会调用makecontext函数的第二个参数指向的函数，如果func函数返回,则恢复makecontext第一个参数指向的上下文第一个参数指向的上下文context_t中指向的uc_link. 如果uc_link为NULL,则线程退出。

### void makecontext(ucontext_t *ucp, void (*func)(), int argc, ...);

makecontext修改通过getcontext取得的上下文ucp(这意味着调用makecontext前必须先调用getcontext)。然后给该上下文指定一个栈空间ucp->stack，设置后继的上下文ucp->uc_link.

当上下文通过setcontext或者swapcontext激活后，执行func函数，argc为func的参数个数，后面是func的参数序列。当func执行返回后，继承的上下文被激活，如果继承上下文为NULL时，线程退出。

### int swapcontext(ucontext_t *oucp, ucontext_t *ucp);

保存当前上下文到oucp结构体中，然后激活upc上下文。 

## 利用 ucontext 实现的一个简单协程

```c
scheduler{
	ucontext_t main;
	vector<co_t> vco;
};

//创建一个co结构，设置其栈，其后继协程uc_link，设置其入口函数makecontext
co_create(scheduler, func, arg)

//swapcontext(&main, co)
co_resume(co)

//swapcontext(co, &main)
co_yield(co)
```

## network/uthread_context_base

### UThreadContext

协程context

代码 

```c
    static ContextCreateFunc_t context_create_func_;

	//使用工厂模式
	//使用函数 context_create_func_ 来创建context
    static UThreadContext * Create(size_t stack_size, 
            UThreadFunc_t func, void * args, 
            UThreadDoneCallback_t callback, const bool need_stack_protect);
    static void SetContextCreateFunc(ContextCreateFunc_t context_create_func);
    static ContextCreateFunc_t GetContextCreateFunc();

    virtual void Make(UThreadFunc_t func, void * args) = 0;
    virtual bool Resume() = 0;
    virtual bool Yield() = 0;
```

## network/uthread_context_system

### UThreadContextSystem 

从UThreadContext中继承

代码 

```c
    ucontext_t context_;
    UThreadFunc_t func_;
    void * args_;
    UThreadStackMemory stack_;   //自己维护一个栈
    UThreadDoneCallback_t callback_;


	//工厂模式
	//生成一个实例
    static UThreadContext * DoCreate(size_t stack_size, 
            UThreadFunc_t func, void * args, UThreadDoneCallback_t callback,
            const bool need_stack_protect);

	//makecontext -> (func -> UThreadFuncWrapper)
    void Make(UThreadFunc_t func, void * args) override;
    bool Resume() override;  //swapcontext(main, context)
    bool Yield() override;   //swapcontext(context, main)

    ucontext_t * GetMainContext();   //使用静态变量保存一个 main context

	//wrap用户自定义的函数，
    static void UThreadFuncWrapper(uint32_t low32, uint32_t high32);  
```

## network/uthread_epoll

### EpollNotifier

结构 

```c
    UThreadEpollScheduler * scheduler_;
    int pipe_fds_[2];  //用于通知scheduler，通知时往[1]写"a"，scheduler_侦听[0]，将会触发读事件

	//scheduler_->AddTask( this->Fun )
    void Run();


	//while(true){
	//  UThreadPoll
	//} 
	void Func();

	//想管道中写a，触发读通知
    void Notify();
```

### UThreadEpollScheduler

结构 

```c
    UThreadRuntime runtime_;
    int max_task_;  //最大任务个数
    TaskQueue todo_list_;
    int epoll_fd_;   //epoll_create返回的结构

    Timer timer_;
    bool closed_;
    bool run_forever_;

    UThreadActiveSocket_t active_socket_func_;
    UThreadHandlerAcceptedFdFunc_t handler_accepted_fd_func_;
    UThreadHandlerNewRequest_t handler_new_request_func_;

    int epoll_wait_events_; //在统计1s过程中保存的事件个数
    int epoll_wait_events_per_second_; //每秒处理的事件个数
    uint64_t epoll_wait_events_last_cal_time_; //更新每秒事件个数的时间

    EpollNotifier epoll_wake_up_;


	//获取static的静态单例
    static UThreadEpollScheduler * Instance();

	//runtime_未完成的任务 + todo_list_ 的个数少于 max_task_
    bool IsTaskFull();

	//放到todo_list_中
    void AddTask(UThreadFunc_t func, void * args);

    UThreadSocket_t * CreateSocket(int fd, int socket_timeout_ms = 5000, 
            int connect_timeout_ms = 200, bool no_delay = true);

	//active_socket_func_
    void SetActiveSocketFunc(UThreadActiveSocket_t active_socket_func);

	//handler_accepted_fd_func_
    void SetHandlerAcceptedFdFunc(UThreadHandlerAcceptedFdFunc_t handler_accepted_fd_func);

	//handler_new_request_func_
    void SetHandlerNewRequestFunc(UThreadHandlerNewRequest_t handler_new_request_func);

	//runtime_.yield()
    bool YieldTask();

	//ConsumeTodoList
	//while(run_forever_ || runtime_ 的任务未处理完之前){
	// epoll_wait
	// runtime_ 恢复协程
	// 继续ConsumeTodoList
	//}
    bool Run();

	//执行自己的Run 和 NotifyEpoll 的Run
    void RunForever();

    void Close();
    
    void NotifyEpoll();

	//runtime_.GetCurrUThread()
    int GetCurrUThread();

	//给该socket添加超时
    void AddTimer(UThreadSocket_t * socket, int timeout_ms);
    void RemoveTimer(const size_t timer_id);

	//runtime_恢复timeout的协程
    void DealwithTimeout(int & next_timeout);

	//runtime_ 创建、resume todo_list_ 中所有的任务
    void ConsumeTodoList();

	//runtime_ resume socketlist 中所有的任务
    void ResumeAll(int flag);

	//统计每秒的事件个数
    void StatEpollwaitEvents(const int event_count);
```

### int UThreadPoll(UThreadSocket_t & socket, int events, int * revents, int timeout_ms) 

socket对应的协程添加event事件和timeout超时，接着协程被挂起。

### int UThreadPoll(UThreadSocket_t * list[], int count, int timeout_ms) 

socketlist对应的协程添加event和timeout事件，接着协程被挂起

### int UThreadConnect(UThreadSocket_t & socket, const struct sockaddr *addr, socklen_t addrlen) 

socket建立连接

### int UThreadAccept(UThreadSocket_t & socket, struct sockaddr *addr, socklen_t *addrlen) 

socket accept


## network/uthread_runtime

### UThreadRuntime

结构体中

```c
    struct ContextSlot {
        ContextSlot() {
            context = nullptr;
            next_done_item = -1;
        }
        UThreadContext * context;
        int next_done_item;  //已完成任务通过这个字段构成一个已完成任务协程链（空闲协程链）
        int status; //创建时为 UTHREAD_SUSPEND，完成任务时为UTHREAD_DONE, resume协程时为UTHREAD_RUNNING
    };

    size_t stack_size_;
    std::vector<ContextSlot> context_list_;   //协程数组中的上下文会重复使用
    int first_done_item_;  //空闲协程，通过 next_done_item 来组成一个空闲协程链
    int current_uthread_;  //当前运行的协程下标
    int unfinished_item_count_;
    bool need_stack_protect_;

	//如果context_list_有已经完成任务的协程，则把任务分给它，否则创建新的协程，并加入到context_list_中
    int Create(UThreadFunc_t func, void * args);

	//current_uthread_
    int GetCurrUThread();
    bool Yield();
    bool Resume(size_t index);  //恢复协程

	//判断 unfinished_item_count_ 是否为0
    bool IsAllDone();
    int GetUnfinishedItemCount() const;

	//协程完成的回调，主要是协程标记为空闲，并且未完成任务数-1
    void UThreadDoneCallback();
```

## network/timer

超时任务，使用堆来维护

# http

## http/http_proto

### HttpProto

http request/response 解析。 类似libevent中http的解析，包括解析头部、body等。

## http/http_msg

http消息，基类是HttpMessage，派生出HttpRequest和HttpResponse。

## http/http_dispatcher

貌似没调用到的地方。

## http/http_client

HttpClient实现GET和POST方法。调用HttpProto中的SendReq，然后对Response再调用HttpProto进行解析。 
