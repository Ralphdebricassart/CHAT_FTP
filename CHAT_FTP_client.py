"""
tcp客户端
"""
from socket import *
import os
from time import sleep
from signal import *
import re

signal(SIGCHLD, SIG_IGN)


# 协议 $M user $ content 以用户名发送消息 清屏后服务端返回最近十条信息
#     $L user $% passwd 登入指定用户名
#     返回值Y 登录成功 调用修改本文件的函数 返回值N 登录失败,用户名或密码错误
#     $R user $# passwd 发送用户名和密码 判定未注册 并注册
#     返回值 Y 注册成功 N注册失败,用户名已存在
#     $F flush  等等                功能参数
#     $#$ 填充用
# bug 无法准确显示客户端端口

class ChatRoomServ:
    def __init__(self):
        self.server_addr = ("127.0.0.1", 6665)
        # 创建套接字119.45.140.40
        self.tcp_socket = socket()
        # 发起连接
        self.tcp_socket.connect(self.server_addr)  # 填充accept阻塞
        print('服务器已连接')
        self.list_log = ['游客', '123']

    @staticmethod
    def get_option():
        while True:
            try:
                opt = input("""#i登入#r修改用户名#q退出#f刷新""")
                if opt == 'i':
                    return 'chat'
                if opt == 'r':
                    return 'reg'
                if opt == 'q':
                    return 'quit'
                if opt == 'f':
                    return 'flush'

            except ValueError:
                print("输入错误重新输入")

    def process_msg(self, data: str):
        result = data.split('$#$')[::-1]
        result_list = []
        for item in result:
            result_pack = []  # 封装  0发送者 1时间 2内容
            result_str = re.search(r"\(\'(\w+)\', \'(\d+:\d+:\d+)\', \'(.+)\'\)", item).groups()
            for msg in result_str:
                result_pack.append(msg)
            result_list.append(result_pack)
        return result_list

    def login(self):
        msg = f"$L {self.list_log[0]} $L {self.list_log[1]}"
        self.tcp_socket.send(msg.encode())
        print('已发送')
        data = self.tcp_socket.recv(1024)
        print('收到判定')
        result_data = data.decode()
        os.system("clear")
        result = result_data.split('@#$')
        for item in result:
            if item == "$%Y":
                print(f"登陆成功")
                return
            if item == "$%N":
                print(f"登陆失败")
                return

    def reg(self):
        while True:
            user = input(">>输入用户名")
            msg = f"$R {user} $R {self.list_log[1]}"
            self.tcp_socket.send(msg.encode())
            print('已发送')
            data = self.tcp_socket.recv(1024)
            print('收到判定')
            result_data = data.decode()
            os.system("clear")
            result = result_data.split('@#$')
            for item in result:
                if item == "$%Y":
                    self.list_log[0] = user
                    print(f"修改成功:新注册用户名")
                    return
                if item == "$%N":
                    self.list_log[0] = user
                    print(f"修改成功:已有用户登入")
                    return

    def flush_msg(self):
        msg = f"$F flush $F flush"
        self.tcp_socket.send(msg.encode())
        data = self.tcp_socket.recv(1024)
        result_data = data.decode()
        os.system("clear")
        result = self.process_msg(result_data)
        for item in result:
            print(f"{item[0]}:{item[2]}                       @{item[1]}")

        # 对获得数据的处理

    # 实现消息的更新

    def send_recv_msg(self):
        while True:
            msg = input(">>")
            if not msg:
                break
            # 收发消息
            msg = f"$M {self.list_log[0]} $M {msg}"
            self.tcp_socket.send(msg.encode())
            print('已发消息')
            data = self.tcp_socket.recv(1024)
            result_data = data.decode()
            os.system("clear")
            result = self.process_msg(result_data)
            for item in result:
                print(f"{item[0]}:{item[2]}                       @{item[1]}")
        return

        #         result = item[1:-1:].split(",")
        #         if len(result) == 3:
        #             result_str = f'{result[0][1:-1:]}:{result[2][2:-1:]}         @{result[1][2:-1:]}'
        #             print(result_str)
        #         else:
        #             print_str = ""
        #             for item in range(2, len(result)):
        #                 print_str += f",{result[item]}"
        #             result_str = f'{result[0][1:-1:]}:{print_str[3:-1:]}         @{result[1][2:-1:]}'
        #             print(result_str)
        # return

        # 聊天消息的收发

    def main_interface(self):
        while True:
            option = ChatRoomServ.get_option()
            if option == 'chat':
                self.login()
                sleep(0.2)
                self.send_recv_msg()
            if option == 'reg':
                self.reg()
                self.login()
                self.send_recv_msg()
            if option == 'quit':
                break
            if option == 'flush':
                self.flush_msg()
                self.send_recv_msg()
        self.tcp_socket.close()


class FtpServ:
    def __init__(self):
        self.server_addr = ("127.0.0.1", 6666)
        # 创建套接字119.45.140.40
        self.tcp_socket = socket()
        # 发起连接
        self.tcp_socket.connect(self.server_addr)  # 填充accept阻塞
        print('服务器已连接')
        self.list_log = ['游客', '123']


    def do_download(self):
        file_name = FtpServ.do_input()
        msg = f"%D% {self.list_log[0]} %D% {file_name}"
        self.tcp_socket.send(msg.encode())
        list_res = []
        print("开始接收")
        while True:
            data = self.tcp_socket.recv(1024 * 100)
            if data == b'%N% %N%':
                print('查无此文件')
            elif data == b'%T%':
                break
            else:
                list_res.append(data)
        print('接收完毕')
        f = open(f"{file_name}", "wb")
        for item in list_res:
            f.write(item)
        f.close()
    @staticmethod
    def do_input():
        while True:
            try:
                name = input(">>请输入需要下载或上传的文件名")
                return name

            except ValueError:
                print("输入错误重新输入")

    def do_examine(self):
        msg = f"%E% {self.list_log[0]} %E% {self.list_log[1]}"
        self.tcp_socket.send(msg.encode())
        print('已发送')
        while True:
            data = self.tcp_socket.recv(1024)
            if data == b'%T%':
                break
            print('收到判定')
            result_data = data.decode()
            os.system("clear")
            print(result_data)

    @staticmethod
    def get_option():
        while True:
            try:
                print("=================命令选项====================")
                print("*****          R登入                 *****")
                print("*****          E请求文件列表          *****")
                print("*****          D下载请求              *****")
                print("*****          U上传请求              *****")
                print("*****          Q离开                  *****")
                print("============================================")
                opt = input('<<')
                if opt == 'R':
                    return 'Reg'
                if opt == 'E':
                    return 'Exa'
                if opt == 'D':
                    return 'Down'
                if opt == 'U':
                    return 'UpData'
                if opt == 'Q':
                    return 'Quit'
                else:
                    raise ValueError
            except ValueError:
                print("输入错误重新输入")

    def main_interface(self):
        while True:
            option = FtpServ.get_option()
            if option == 'Reg':
                pass
            if option == 'Exa':
                self.do_examine()
            if option == 'Down':
                self.do_download()
            if option == 'UpData':
                pass
            if option == 'Quit':
                break
        self.tcp_socket.close()

    # %E% 用户名 %E% 密码
    # %R% 用户名 %R% 密码
    # %D% 用户名 %D% 文件名
    # %U% 用户名 %U% 文件名


a = FtpServ()
a.main_interface()
