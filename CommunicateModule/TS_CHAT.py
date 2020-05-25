from socket import *
from multiprocessing import Process, Queue
from signal import *
from select import select

signal(SIGCHLD, SIG_IGN)
"""于此创建所有的CHAT TCP服务
io 处理
阻塞点 intial中 self.tcp_socket.accept()
  connfd_func中  self.conn_fd.recv(1024)  # 阻塞 不同的进程阻塞位置不同
                 self.recv_Q.get()  # 阻塞 获得的回复是列表中多个元祖 
"""


class TSChat(Process):
    # 创建套接字
    tcp_socket = socket(AF_INET, SOCK_STREAM)
    # 绑定地址
    server_addr = ("0.0.0.0", 6665)
    tcp_socket.bind(server_addr)
    tcp_socket.listen(8)
    # io多路复用与之配合
    tcp_socket.setblocking(False)
    # 设置套接字为监听套接字   (设置后表示tcp_socket可以被客户端连接)
    r_list = [tcp_socket]
    w_list = []
    x_list = []

    def __init__(self, msg_q: Queue, recv_q: Queue):
        super().__init__()
        self.msg_q = msg_q
        self.recv_q = recv_q

    def inital(self):
        print("Link----------------------Start")
        while True:
            rs, ws, xs = select(TSChat.r_list, TSChat.w_list, TSChat.x_list)
            # 被动处理 wlist主动处理
            # 捕获等待就绪的io
            for r in rs:
                # io用来创建Tcp连接
                if r is TSChat.tcp_socket:
                    conn_fd, addr = TSChat.tcp_socket.accept()  # io行为
                    print("TS CHAT Connect from", addr)
                    # io多路复用与之配合 防止接收信息有延迟
                    conn_fd.setblocking(False)
                    TSChat.r_list.append(conn_fd)  # 每当有一个客户端链接，就将这个链接套接字加入监控
                # io用来等待接收与回复 recv_q这个队列似乎是io对象
                else:
                    print("TS CHAT recv from", addr)
                    data = r.recv(1024)  # 阻塞io行为
                    data = data.decode()
                    if not data:
                        print("TS CHAT break from", addr)
                        TSChat.r_list.remove(r)
                        r.close()  # 客户端收到服务端的tcp_socket.close()选择退出
                        continue
                    self.msg_q.put(data)

                    list_res = self.recv_q.get()  # 阻塞 获得的回复是列表中多个元祖
                    print("TS CHAT result for", addr)
                    result = '$#$'.join(list_res)
                    if result:
                        r.send(result.encode())

    def run(self):
        print("CHAT_TCP服务就绪")
        self.inital()
