---

title: phxrpc源码阅读
date: 2017/8/11 09:00:00

---

phxrpc是微信开源的rpc框架。

# 类

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

