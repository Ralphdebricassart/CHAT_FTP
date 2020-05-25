from ServeModule.DBS_CHAT import DBSChat
from ServeModule.DBS_FTP import DBSFtp
from CommunicateModule.CommunicateServe import CommunicateServe
from multiprocessing import Queue
from multiprocessing import Process
from time import sleep

"""
功能划分
chat_serv进程
    一个队列  msg_q公用的输入队列
    一个队列  recv_q公用的输出队列
    一个队列  ftp_s公用的输出队列
    一个队列  ftp_r公用的输出队列

    创建线程 单个DBS_CHAT服务用线程
    创建线程 单个DBS_FTP服务用线程
    创建进程 CommunicateServe进程 
        创建TS_CHAT子进程 # 阻塞于intial等待新进程的创建
        创建TS_FTP子进程 # 阻塞于intial等待新进程的创建

    线程 DBS_CHAT服务用线程
    功能 阻塞接收msg_Q中的消息 
        获得数据后处理
        处理后发送到消息队列recv_Q中等待接受
    进程 TS_CHAT
        循环使用 msg_Q recv_Q  收发消息
        服务端使用self.tcp_socket.close() 连接断开 套接字关闭       
        
    流程
    服务端
    创建ftps线程
            监听ftp_S用于接收消息 将处理结果推送到ftp_R公用的输出队列
            # ftp协议    $ user 
            #           $% user 
            #           $# 
            #           $@ flush  等等                功能参数
            #           @#$ 填充用

    创建dbs线程
            监听msg_Q用于接收消息并处理 将处理结果推送到recv_Q公用的输出队列
            # 聊天协议   $ user $ content 以用户名发送消息 清屏后服务端返回最近十条信息
            #           $% user $% passwd 登入指定用户名
            #           返回值Y 登录成功 调用修改本文件的函数 返回值N 登录失败,用户名或密码错误
            #           $# user $# passwd 发送用户名和密码 判定未注册 并注册
            #           返回值 Y 注册成功 N注册失败,用户名已存在
            #           $@ flush  等等                功能参数
            #           @#$ 填充用

    创建cs进程
          cs调用的tcp阻塞intial在while循环里的accept
          一旦有客户端连入 tcp进程对msg_Q推送消息 阻塞在recv_Q等待回复
    
"""


class ChatServe(Process):
    def __init__(self, msg_q: Queue, recv_q: Queue, ftp_s: Queue, ftp_r: Queue):
        super().__init__()
        self.CommunicateServ = CommunicateServe
        self.DBSChat = DBSChat
        self.DBSftp = DBSFtp
        self.msg_q = msg_q
        self.recv_q = recv_q
        self.ftp_s = ftp_s
        self.ftp_r = ftp_r

    def start_CS_Process_dbs_thread(self):
        dbs_chat = self.DBSChat(self.msg_q, self.recv_q)
        dbs_ftp = self.DBSftp(self.ftp_s, self.ftp_r)
        c_s = self.CommunicateServ(self.msg_q, self.recv_q, self.ftp_s, self.ftp_r)
        dbs_chat.start()
        sleep(0.1)
        dbs_ftp.start()
        sleep(0.1)
        c_s.start()
        dbs_ftp.join()
        c_s.join()
        dbs_chat.join()

    def run(self):
        self.start_CS_Process_dbs_thread()


if __name__ == '__main__':
    msg_que = Queue(6)
    rec_que = Queue(6)
    ftp_s_que = Queue(12)
    ftp_r_que = Queue(12)
    a = ChatServe(msg_que, rec_que, ftp_s_que, ftp_r_que)
    a.start()
    a.join()
