import pymysql
import re
from time import sleep
from multiprocessing import Queue
from threading import Thread
import os

"""
FTP使用的数据表

1.操作记录表 Operate_record 字段
主键
user  M_to_O(外键联系管理表) 
操作行为 behavior
目标文件 target
操作时间 datetime "YYYY-MM-DD HH:MM:SS" now()


共用
1.管理信息表Manage_info 字段 
主键
user 建立 unique索引
passwd 类型CHAR(20)建立 mul索引
注册时间 datetime ："YYYY-MM-DD HH:MM:SS" now() 返回服务器当前日期时间,格式对应datetime类型
最后登录时间 datetime ："YYYY-MM-DD HH:MM:SS" now() 返回服务器当前日期时间,格式对应datetime类型



"""


# 记录所有的文件操作等待调取
class FileOperate:
    def __init__(self, serve_path: str = 'ftp/', client_path: str = 'ftp/'):
        self.serve_path = serve_path
        self.client_path = client_path

    def do_examine(self):
        # 判断文件库是否为空
        file_list = os.listdir(self.serve_path)
        # 给客户端反馈
        if not file_list:
            return b'%N% %N%'
        else:
            sleep(0.1)
            # 发送文件列表  %#%作为消息边界防止粘包
            files = '\n'.join(file_list)
            return files.encode()

    def do_download(self, file_name):
        download_path = f"{self.serve_path}{file_name}"
        try:
            f = open(download_path, 'rb')
            list_read = []
            while True:
                data = f.read(102400)
                if not data:
                    break
                list_read.append(data)
            if list_read:
                return list_read
            else:
                return b'%N% %N%'
        except:
            return b'%N% %N%'

    def do_update(self, data):
        pass


class DBSFtp(Thread):
    def __init__(self, ftp_s: Queue, ftp_r: Queue):
        super().__init__()
        self.fo = FileOperate()
        self.db = pymysql.connect(host='127.0.0.1',
                                  port=3306,
                                  user='root',
                                  password='123456',
                                  database='chatroom',
                                  charset='utf8')
        self.cur = self.db.cursor()
        self.ftp_s = ftp_s
        self.ftp_r = ftp_r

    def process_examine(self):
        result = self.fo.do_examine()
        self.ftp_r.put(result)  # 返回二进制形式的结果
        self.ftp_r.put(b'%T%')  # 标示传输终点

    def process_reg(self, data):
        pass

    def process_down(self, data):
        file_name = data[3]
        res_list = self.fo.do_download(file_name)
        if res_list == b'%N% %N%':
            self.ftp_r.put(b'%N% %N%')
            self.ftp_r.put(b'%T%')
            return
        else:
            for item in res_list:
                self.ftp_r.put(item)
            self.ftp_r.put(b'%T%')

    def process_update(self, data):
        pass

    def run(self) -> None:
        print('DBS_FTP服务就绪')
        print("Serve------------------------Start")
        self.get_msg_Q()

    def get_msg_Q(self):
        while True:
            try:
                data = self.ftp_s.get()  # 获得了一个消息
                print(f'DBS_FTP Processing')
                if data:
                    self.process_data(data)
            except Exception as e:
                print(e)

                # 获得消息 阻塞

    # 对请求进行分发
    def process_data(self, data):
        # 对接收的消息进行处理
        # 并根据处理的结果转发到对应的消息队列
        # %E% 用户名 %E% 密码
        # %R% 用户名 %R% 密码
        # %D% 用户名 %D% 文件名
        # %U% 用户名 %U% 文件名
        # 返回格式 %Y% data
        # 返回格式 %N% %N%
        # 返回结束时%T%
        re_res = re.search(r'(\S{3}) (\w+) (\S{3}) (\S+)', data).groups()
        data = []
        for item in re_res:  # 对输入结果的处理
            data.append(item)
        # 对输入分类处理
        print(data)
        if data[0] == '%E%':
            print(f'Examine request 查看请求')
            self.process_examine()
        elif data[0] == '%R%':
            print(f'Registration request 注册请求')
            self.process_reg(data)
        elif data[0] == '%D%':
            print(f'Down request 下载请求')
            self.process_down(data)
        elif data[0] == '%U%':
            print(f'UpData request 上传请求')
            self.process_update(data)
        else:
            self.ftp_r.put(["E:啥也不是非法输入"])
