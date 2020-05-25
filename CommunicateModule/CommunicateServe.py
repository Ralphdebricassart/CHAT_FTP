"""
功能划分
chat_serv
    建立通信进程
    建立DBserv进程
    
    外层 CommunicateServ进程
        Tcp_serv给DBserv监听的{创建消息队列}发送用户名
        创建Tcp进程
        
协议 $ user $ content 以用户名发送消息 清屏后服务端返回最近十条信息
    $% user $% passwd 登入指定用户名
    返回值Y 登录成功 调用修改本文件的函数 返回值N 登录失败,用户名或密码错误
    $# user $# passwd 发送用户名和密码 未注册则判定 并注册
    返回值 Y 注册成功 N注册失败,用户名已存在
    @#$ 填充值
"""
from CommunicateModule.TS_CHAT import TSChat
from CommunicateModule.TS_FTP import TSFtp
from multiprocessing import Process, Queue
from signal import *
import time

signal(SIGCHLD, SIG_IGN)

"""于此创建所有的TCP UDP服务
"""


class CommunicateServe(Process):

    def __init__(self, msg_q: Queue, recv_q: Queue, ftp_s: Queue, ftp_r: Queue):
        super().__init__()
        self.TSChat = TSChat
        self.TSFtp = TSFtp
        self.msg_q = msg_q
        self.recv_q = recv_q
        self.ftp_s = ftp_s
        self.ftp_r = ftp_r

    def start_tcp(self):
        ts_chat = self.TSChat(self.msg_q, self.recv_q)
        ts_ftp = self.TSFtp(self.ftp_s, self.ftp_r)
        ts_ftp.start()
        time.sleep(0.1)
        ts_chat.start()
        ts_chat.join()
        ts_ftp.join()

    def run(self):
        self.start_tcp()


if __name__ == '__main__':
    pass
