---

title: libevent源码阅读1

---

## 状态转换 

### EVCON_DISCONNECTED 

* 创建连接时，evhttp_connection_new
* 重置 evhttp_connection_reset 
* 重连开始时 evhttp_connection_retry 
* request之后读回调函数中判断连接已断开

### EVCON_CONNECTING 

* 连接 evhttp_connection_connect

### EVCON_IDLE 

* 在连接成功后 evhttp_connectioncb 
* 在处理一个出request成功后

### EVCON_WRITING 

* 在连接成功后，evhttp_request_dispatch开始处理request

### EVCON_READING_FIRSTLINE 

读内部状态。

在发送第一个request之后，注册读事件event_read，进入读状态，监听读。

### EVCON_READING_HEADERS 

读内部状态。

### EVCON_READING_BODY 

读内部状态。

### EVCON_READING_TRAILER

读内部状态。

## 函数

### evhttp_connection_new(const char* address, unsigned int port)

初始化timeout, retry_cnt, input_buffer, output_buffer, request队列， state(EVCON_DISCONNECTED)。

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

### evhttp_make_request(evcon, req, type, uri)

请求资源。

将req加入到请求队列中，如果当前未完成连接，先建立连接。若已经建立连接，则直接处理请求(evhttp_request_dispatch)。

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

### evhttp_write_connectioncb(*evcon, *arg)

刚刚把request队列中的第一个request给发出去时调用。

__步骤：__

1. 把队列中的第一个request类型改为 EVHTTP_RESPONSE.

2. 开始注册读事件 evhttp_start_read(evcon)

### evhttp_connection_done(*evcon)

如果是入连接，说明刚刚处理一个request，如果是出连接，说明刚刚处理一个response。


* 如果是出连接 

说明刚刚处理一个response，清掉该req， evcon状态变为EVCON_IDLE

如果后面还有request，若当前仍连接，则直接 evhttp_request_dispatch，否则再次连接 evhttp_connection_connect。

如果该连接是persistent的，则不能关闭该连接，并且开启close检测：evhttp_connection_start_detectclose。

执行回调函数。

* 如果是入连接 

说明刚处理完一个request, 把状态变为 EVCON_WRITIN，接着执行回调函数。

### evhttp_start_read(evcon)

在发送request之后，注册读事件。

__步骤:__

1. 注册读回调事件 evhttp_read，加入超时 HTTP_READ_TIMEOUT.

2. 状态变为 EVCON_READING_FIRSTLINE

### evhttp_handle_chunked_read(struct evhttp_request* req, struct evbuffer* buf)

把buf中的数据不断读到req->input_buffer中去。一个一个chunk的读。 数据格式为 len\r\n + data + len\r\n + ... + 0，最后的长度0表示传输完毕。

读的状态有三种：

* DATA_CORRUPTED 

数据格式错误。

* MORE_DATA_EXPECTED 

若缓冲区的长度小于req->ntoread留待下次再读，否则只读req->ntoread，读后把req->ntoread改成-1表示需要再读进其长度。

* ALL_DATA_READ 

遇到最后面的长度0.

### evhttp_read_firstline(* evcon, * req)

读第一行，然后进入读Header状态。

对于request，第一行为 GET HTTP1.1 这样类似的。

对于response，第一行为 HTTP1.1 200 这样类似的。

成功读完后，接着evhttp_read_header。

### evhttp_read_header(* evcon, * req)

读头部。

读完成后，如果req是request或 正常的response，则进入evhttp_read_body， 如果是非正常正常状态的response，则进入evhttp_connection_done。

### evhttp_read_body(evcon, req)

区分分块传输"Transfer-Encoding: chunked"，则把chunked置为1，并且挨个块进行读取。

如果不是分块(chunked=0)，则要读取body的长度，查看Content-Length，并把长度赋给req->ntoread。

读body，直到读完成，否则继续添加 evhttp_read + HTTP_READ_TIMEOUT 读事件。

### evhttp_read_trailer(* evcon, * req)

安装读header的格式先读取，读取完成后，进入 evhttp_connection_done中。

### evhttp_read(int fd, short what, void *arg)

发送request之后的读回调函数。

__步骤：__

1. 如果是超时，则触发 evhttp_connection_fail(evcon, HTTP_READ_TIMEOUT)

2. 把数据从evcon->input_buffer中读出来。

3. 如果读出来的长度为0，表示连接已经断开，则关闭连接，设置状态为 EVCON_DISCONNECTED, 执行 evhttp_connection_done。

### evhttp_send(req, buf)

发送请求。

__步骤:__

把buf中的数据给req，req在后续再传给evcon。

发送完后调用 evhttp_send_done。

__相关函数：__  evhttp_send_reply, evhttp_send_reply_start, evhttp_send_reply_end，都是属于服务器端的。

### evhttp_send_done(evcon, arg)

先删除可能的close event: evhttp_connection_stop_detectclose，注意：close_ev 会重置该connection的。

### evhttp_handle_request(evcon, arg)

服务端处理request。

__步骤：__

判断当前连接是否正常，如果连接断开或uri有异常，则返回错误。

处理回调 evhttp_dispatch_callback，注意客户端可能是发多个request的，所以这里callback也是多个。

如果其中有一个uri是成功的，则返回，否则调用通用回调函数，如果其状态不行，则返还page not found。
