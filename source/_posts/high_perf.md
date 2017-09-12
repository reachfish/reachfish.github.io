---

title: 高性能优化
date: 2017/7/18 09:00:00

---

# Fast UNIX Servers文章
设计原则：
1. __利用带宽__
避免阻塞IO和不必要的cache，但是使用合适的cache(对处理器cache和其他层级的cache都适用)。
利用好多处理器。对齐数据，避免出现cache alias。
2. __不要重复工作__
避免不必要的拷贝、上下文切换、系统调用和signal。使用双缓存double buffer和ringbuffers，使用像slice那样的调用。
双缓冲一般是由于生产者和消费者供需速度不一致所造成的，比如图像显示和CPU两者速度差别比较大，就使用了双缓存。
3. __再三测量__
使用系统性能测量工具进行性能测量，如Oprofile, dtrace, ktrace。

# The C10k Problem

表示的是Client 10k 问题。

IO策略:
1. 处理单线程中的多IO调用
考虑使用多线程/多进程。
使用非阻塞IO(只对网络IO适用，对disk IO不适用);
使用异步IO(对网络IO和disk IO都适用)。

2. 如何处理每个client
1)每个进程处理一个用户；
2)一个OS-level线程处理多个client，每个client又可以被控制：
  i)一个 user-level thread(如 GNU state thread, 或者 Java中的 green thread)；
  ii) 一个状态机
  iii) a continuation
3)一个os-level thread处理一个client 
4)一个os-level thread处理一个active client(如NT completion ports， 线程池等)；
3. 使用标准的OS service，或者在kernel代码中添加代码。




## Four Pool Performance 

1. Data copies
2. Context switches
3. Memory allocation 
4. Lock contention 

## Data copies

## 补充说明

* os-level thread vs user-level thread 

os-level thread 指的是操作系统本身提供的，很多语言都支持，如c中通过pthread_create的就是os-level thread，开发人员需要100%负责问题的产生，在没加锁的情况下，即使是native data structure(如dict等)都可能会出问题。

green thread 则是由编程语言本身来管理的，如c中的coroutine和go中的goroutine，这种thread只存在于编程语言中，不存在OS中。green thread编程通常比较简单，但是不能利用多核。通常的方式是开一个os level thread，然后在上面允许很多green thread。

## 网络编程模型

### 单线程

* __reactor__

例子 libevent/libev

* __proactor__

linux下实现不好，可以使用boost::asio，windows下实现较好。

### 多线程

* __每个请求创建一个线程，阻塞io__

* __线程池，阻塞io__

写法：

```c
queue<std::function<void()>> taskQue;

void worker_thread(){
	while(!quit){
		std::function<void()> task = taskQue.take(); //阻塞

		task();
	}
}

//添加任务
std::function<void()> task = std::bind(func, ...);
taskQue.post(task);
```

* __每个线程io多路复用，非阻塞io__

每个线程是一个loop的多路复用模型。方便在线程间调配负载。让哪个线程干活，把其注册到对应线程的timer上即可。

数据量大的connection可以单独占一个线程。

* __Leader/Follower__

```c
static pthread_mutex_t mutex;

void worker_thread(){
	while(true){
		wait_be_leader(); //阻塞, pthread_mutex_lock(&mutex);

		reactor();  //epoll

		promote_new_leader(); //提升其他follower为leader, pthread_mutex_unlock(&mutex)

		do_task();
	}
}
```

* __半同步半异步__

同步模式下编程容易，但io利用率低；而异步编程编程复杂，但io使用率高。

在该模型中，高层中同步io模型简化编程，而底层用异步io模型高效执行。

实现方案：

```c
同步任务层(调用时会被阻塞,应用层)
---
队列层
---
异步任务层(调用时不会被阻塞)
```

实现代码：

```c
//队列层
class TaskQue{
public:
	void append(const TaskItem& item){
		pthread_mutex_lock(&_mutex);
		_que.push(item);
		pthread_mutex_unlock(&_mutex);
	}

	bool pop(TaskItem& item){
		bool ret;
		pthread_mutex_lock(&_mutex);
		if(_que.empty()){
			ret = false;
		}
		else{
			item = _que.front();
			_que.pop();
		}
		pthread_mutex_unlock(&_mutex);

		return ret;
	}

private:
	queue<TaskItem> _que;
	pthread_mutex_t _mutex;
};

//异步任务层
class AioProcess{
public:
	void start(int count){
		if(!_isStarted){
			_isStarted = true;
			for(int  i=0;i<count;++i){
				pthread_t tid;
				pthread_create(&tid, NULL, process, this);
				_tids.push_back(tid);
			}
		}
	}

	void shutdown(){
		if(_isStarted){
			_isStarted = false;
			for(auto tid : _tids){
				pthread_join(tid, NULL);
			}
		}
	}
	
private:
	void process(void* param){
		AioProcess* processor = (AioProcess*) param;
		while(processor._isStarted){
			TaskItem item;
			if(_pQue->pop(&item)){
				pread(...);
				sem_post(...);
			}
			else{
				usleep(10);
			}
		}
	}

	bool _isStarted;
	TaskQue* _pQue;
	vector<phread_t> _tids;
};


//同步应用层
class Read{
public:
	void read(){
		//init task item
		_pQue.push(item);

		seg_wait(...);

		//do other things
	}

private:
	taskQue* _pQue;
};
```

----

## References

1. High-Performance Request-Handling Programs [1]。
2. Fast Unix Servers [2]。
3. The C10k Problem [3]。
4. Network Algorithmics: An Interdisciplinary Approach to Designing Fast Networked Devices。

[1]: http://pl.atyp.us/content/tech/servers.html
[2]: https://nick-black.com/dankwiki/index.php/Fast_UNIX_Servers
[3]: http://www.kegel.com/c10k.html#related

