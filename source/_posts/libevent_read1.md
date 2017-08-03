---

title: libevent源码阅读1

---

## 状态转换 

EVCON_DISCONNECTED(重置 evhttp_connection_reset 或重连开始时 evhttp_connection_retry)

EVCON_CONNECTING(连接 evhttp_connection_connect)

EVCON_IDLE(在连接成功后 evhttp_connectioncb, 或者在处理一个出request成功后)

EVCON_WRITING(在连接成功后，evhttp_request_dispatch开始处理request)

## 函数

### evhttp_connection_connect(struct evhttp_connection *evcon)

建立连接

先重置自己: evhttp_connection_reset(把连接状态设置为 EVCON_DISCONNECTED)

修改 flag: flag |= EVHTTP_CON_OUTGOING

使用套接字进行连接：bind_socket, socket_connect(socket得到的fd设置为非阻塞的，这里也是非阻塞connect, 并返回成功与否)

添加事件：

* EV_WRITE的回调函数 

evhttp_connectioncb(通过connect的socket，当连接成功时，其事件的状态为可写的)

* 增加超时事件：HTTP_CONNECT_TIMEOUT

修改连接状态：EVCON_CONNECTING

### evhttp_connectioncb(int fd, short what, void* arg)

连接完成或连接超时，判断：

* 连接已完成 

清零retry_cnt，状态变为 EVCON_IDLE，并开始处理request队列(evhttp_request_dispatch)。

* 超时或连接未完成 

若没有超出最大重试次数，则2^retry_cnt秒后尝试重新连接(evhttp_connection_retry)，否则重置con，并把它的request队列中的挨个删除并执行回调函数。

### evhttp_connection_retry(struct evhttp_connection* evcon)

状态标为EVCON_DISCONNECTED，并且重来 evhttp_connection_connect

### evhttp_request_dispatch(struct evhttp_connection* evcon)

先删除可能的close event: evhttp_connection_stop_detectclose，注意：close_ev 会重置该connection的。

状态变为EVCON_WRITING 

生成 header: evhttp_make_header

开始写buffer: evhttp_write_buffer, 写完成后，回调 evhttp_write_connectioncb

### evhttp_make_header(struct evhttp_connection * evcon, struct evhttp_request * req)

如果是request，则evhttp_make_header_request: Method + Uri + HTTP + version + ... 

否则是response，则evhttp_make_header_response: HTTP + version + status + ...

### evhttp_write_buffer(*evcon, cb, *arg)

evhttp_write + HTTP_WRITE_TIMEOUT 超时

在 evhttp_write(fd, what, *arg)中

如果是写超时，则会触发 evhttp_connection_fail(evcon, HTTP_WRITE_TIMEOUT)

否则把evcon->output_buffer中的数据写到fd中，并且调用cb回调。

### evhttp_connection_done(*evcon)

如果是入连接，说明刚刚处理一个request，如果是出连接，说明刚刚处理一个response。


* 如果是出连接 

说明刚刚处理一个response，清掉该req， evcon状态变为EVCON_IDLE

如果后面还有request，若当前仍连接，则直接 evhttp_request_dispatch，否则再次连接 evhttp_connection_connect。

如果该连接是persistent的，则不能关闭该连接，并且开启close检测：evhttp_connection_start_detectclose。

执行回调函数。

* 如果是入连接 

说明刚处理完一个request, 把状态变为 EVCON_WRITIN，接着执行回调函数。

