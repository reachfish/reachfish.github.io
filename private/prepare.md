
## https回调函数

```c
脚本逻辑
https.request(url, callback)
------- 
引擎
read_cb:把数据读出来
error_cb:调用callback
------- 
libevent: 
bufferevent_readcb
evbuffer_read => read = 0(关闭),<0 error_cb(fd, what=EVBUFFER_EOF|EVBUFFER_ERROR)，>0时，read_cb
------- 
epoll:  EPOLLIN, EPOLLOUT, EPOLLHUP, EPOLLERR
EPOLLIN | EPOLLHUP | EPOLLERR => active_event
-------
```

## http处理

```c
if(chunked){
	while(read_data){
		finish_read_tail || read == 0 => done(callback)
	}
}
else{
	read content-lenght content || read == 0 => done(callback)
}
```

## main && write

```bash
       main							      write
   request_queue	=> m2w_que  =>  write_process_queue
									       ||
main_process_queue	<= w2m_que  <=	   result_queue
```

