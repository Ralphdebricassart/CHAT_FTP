"""
tcp客户端
"""
from socket import *
import os
from time import sleep
from signal import *
import re

signal(SIGCHLD, SIG_IGN)


class ChatRoomServe:
    def __init__(self):
        self.server_addr = ("127.0.0.1", 6665)
        # 创建套接字119.45.140.40
        self.tcp_socket = socket()
        # 发起连接
        self.tcp_socket.connect(self.server_addr)  # 填充accept阻塞
        print('聊天服务器已连接')
        self.list_log = ['游客', '123']

    @staticmethod
    def get_option():
        while True:
            try:
                print("=================CHAT====================")
                print("*****          I登入                  *****")
                print("*****          R修改用户名             *****")
                print("*****          Q退出                  *****")
                print("*****          F刷新                  *****")
                print("==========================================")
                opt = input(">>")
                if opt == 'I':
                    return 'chat'
                if opt == 'R':
                    return 'reg'
                if opt == 'Q':
                    return 'quit'
                if opt == 'F':
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
            option = ChatRoomServe.get_option()
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


class FtpServe:
    def __init__(self):
        self.server_addr = ("127.0.0.1", 6666)
        # 创建套接字119.45.140.40
        self.tcp_socket = socket()
        # 发起连接
        self.tcp_socket.connect(self.server_addr)  # 填充accept阻塞
        print('Ftp服务器已连接')
        self.list_log = ['游客', '123']
        self.dir_path = ""

    def get_file(self, file_name):
        file_path = f"{self.dir_path}{file_name}"
        try:
            f = open(file_path, 'rb')
            list_read = []
            while True:  # print(len(b"%U% ")) 4个长度
                data = f.read(1020)
                if not data:
                    break
                list_read.append(data)
            return list_read  # 二进制单位长度为1020的列表
        except FileNotFoundError:
            return

    def do_download(self):
        file_name = FtpServe.do_input()
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

    def do_update(self):
        # 发送请求
        msg = f"%U% {self.list_log[0]} %U% {self.list_log[1]}"
        self.tcp_socket.send(msg.encode())
        # 获得肯定后 循环读取发送文件
        while True:
            data = self.tcp_socket.recv(1024)
            if data == b"%Y%":
                data = self.tcp_socket.recv(1024)
                if data == b"%T%":
                    os.system("clear")
                    print('身份验证成功,可以上传')
                    file_name = FtpServe.do_input()
                    result = self.get_file(file_name)
                    if result:
                        print("开始上传")
                        # 循环推送文件 长度2048的两段式
                        while True:
                            sleep(0.05)
                            if len(result) % 2 == 0:
                                for item in range(0, len(result), 2):
                                    print(f'第{item}次发送')
                                    msg = b"%U% " + result[item] + b"%U% " + result[item + 1]
                                    self.tcp_socket.send(msg)
                                    res = self.tcp_socket.recv(4)
                                    if res == b'%Y%':
                                        print("标示以接收")
                                    else:
                                        print("E:上传失败")
                                        sleep(2)
                                        return
                            if len(result) % 2 == 1:
                                for item in range(0, len(result), 2):
                                    print(f'第{item}次发送')
                                    if item == len(result) - 1:
                                        msg = b"%U% " + result[item] + b"%U% " + result[item]
                                    else:
                                        msg = b"%U% " + result[item] + b"%U% " + result[item + 1]
                                    self.tcp_socket.send(msg)
                                    res = self.tcp_socket.recv(4)
                                    if res == b'%Y%':
                                        print("标示以接收")
                                    else:
                                        print("E:上传失败")
                                        sleep(2)
                                        return
                            self.tcp_socket.send(b"%T%")
                            print("上传结束")
                            response = self.tcp_socket.recv(4)
                            if response == b"%T%":
                                print('传输正常结束')
                            else:
                                print("E:传输异常结束")
                            return

                else:
                    print("E:警告!文件不存在")
                    msg = b'%T%'
                    self.tcp_socket.send(msg)
                    data = self.tcp_socket.recv(1024)
                    print()
                    return

            if data == b'%N%':
                os.system("clear")
                print('身份验证失败')
            if data == b'%T%':
                break

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
    def do_input():
        while True:
            try:
                name = input(">>请输入需要下载或上传的文件名")
                return name

            except ValueError:
                print("输入错误重新输入")

    @staticmethod
    def get_option():
        while True:
            try:
                print("=================FTP====================")
                print("*****          R登入                 *****")
                print("*****          E请求文件列表          *****")
                print("*****          D下载请求              *****")
                print("*****          U上传请求              *****")
                print("*****          Q离开                  *****")
                print("=========================================")
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
            option = FtpServe.get_option()
            if option == 'Reg':
                pass
            if option == 'Exa':
                self.do_examine()
            if option == 'Down':
                self.do_download()
            if option == 'UpData':
                self.do_update()
            if option == 'Quit':
                break
        self.tcp_socket.close()

    # %E% 用户名 %E% 密码
    # %R% 用户名 %R% 密码
    # %D% 用户名 %D% 文件名
    # %U% 用户名 %U% 文件名


class ServeStart:
    def __init__(self):
        self.FtpServe = FtpServe()
        self.ChatRoomServe = ChatRoomServe()

    @staticmethod
    def get_option():
        while True:
            try:
                print("=================命令选项====================")
                print("*****          C进入聊天室              *****")
                print("*****          F进入文件系统            *****")
                print("*****          Q离开                   *****")
                print("============================================")
                opt = input('<<')
                if opt == 'C':
                    return 'Chat'
                if opt == 'F':
                    return 'Ftp'
                if opt == 'Q':
                    return 'Quit'
                else:
                    raise ValueError
            except ValueError:
                print("输入错误重新输入")

    def main_interface(self):
        while True:
            option = ServeStart.get_option()
            if option == 'Chat':
                self.ChatRoomServe.main_interface()
            if option == 'Ftp':
                self.FtpServe.main_interface()
            if option == 'Quit':
                break


a = ServeStart()
a.main_interface()
