---
---title: 高性能优化
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

----
## References

1. High-Performance Request-Handling Programs [1]。
2. Fast Unix Servers [2]。
3. The C10k Problem [3]。
4. Network Algorithmics: An Interdisciplinary Approach to Designing Fast Networked Devices。

[1]: http://pl.atyp.us/content/tech/servers.html
[2]: https://nick-black.com/dankwiki/index.php/Fast_UNIX_Servers
[3]: http://www.kegel.com/c10k.html#related

