import pymysql
import re
from time import sleep
from multiprocessing import Queue
from multiprocessing import Process
import os

"""
FTP使用的数据表

1.操作记录表 Operate_record 字段(待建立)
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

"""
协议

 %E% 用户名 %E% 密码
处理方式
返回值
 %R% 用户名 %R% 密码
处理方式
返回值
 %D% 用户名 %D% 文件名
处理方式
返回值
 %U% 用户名 %U% 密码
 %U% 文件名 %U% 文件名
 %U% 文件内容 %U% 文件内容
处理方式
返回值


每次发送完处理结果附带发送%T%
标示处理过程完结使TS_TCP不再阻塞于监听ftp_r获得处理结果
"""


# 记录所有的文件操作等待调取
class FileOperate:
    def __init__(self, serve_path: str = 'ftp_store/'):
        self.serve_path = serve_path

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
        except FileNotFoundError:
            return b'%N% %N%'

    def do_update(self, data):
        pass


class DBSFtp(Process):
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

    def process_log(self, data):
        user = data[1]
        passwd = data[3]
        try:
            sql = f"select  user,passwd from Manage_info as mi where user = '{user}' and passwd = '{passwd}';"
            self.cur.execute(sql)
            select_res = self.cur.fetchall()
            if select_res:
                return '%Y%'
            else:
                return "%N%"
        except Exception as e:
            print(e)
            self.ftp_r.put(b"E:access_deny")
            self.ftp_r.put(b'%T%')
            self.db.rollback()
            return

            # 登陆用

    def process_examine(self):
        result = self.fo.do_examine()
        self.ftp_r.put(result)  # 返回二进制形式的结果
        self.ftp_r.put(b'%T%')  # 标示传输终点

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
        if self.process_log(data) == '%Y%':
            self.ftp_r.put(b'%Y%')
            self.ftp_r.put(b'%T%')
            # 拦截给DBS_FTP的输入
            list_file = []
            while True:
                data = self.ftp_s.get()  # 获得了一个消息
                print('DBS获得了推送')
                if data == b'%T%':
                    print(f'accept term')
                    break
                print(f'DBS_FTP Processing')
                if data[0:4:] == b"%U%":
                    list_file.append(data[4:1024:])
                    list_file.append(data[1028:2048:])
                self.ftp_r.put(b"%Y%")
                self.ftp_r.put(b"%S%")  # 标示一次处理的完结
            print("文件接收完毕")
            # 对文件进行处理
            self.ftp_r.put(b"%T%")
            return
        else:
            self.ftp_r.put(b'%N%')
            self.ftp_r.put(b'%T%')

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
    def process_data(self, data: bytes):
        # 对接收的消息进行处理
        # 并根据处理的结果转发到对应的消息队列
        # %E% 用户名 %E% 密码
        # %R% 用户名 %R% 密码
        # %D% 用户名 %D% 文件名
        # %U% 用户名 %U% 文件名
        # 返回格式 %Y% data
        # 返回格式 %N% %N%
        # 返回结束时%T%
        data = data.decode()
        re_res = re.search(r'(\S{3}) (\w+) (\S{3}) (.+)', data).groups()
        data = []
        for item in re_res:  # 对输入结果的处理
            data.append(item)
        # 对输入分类处理
        if data[0] == '%E%':
            print(f'Examine request 查看请求')
            self.process_examine()
        elif data[0] == '%R%':
            print(f'Registration request 注册请求')
            pass
        elif data[0] == '%D%':
            print(f'Down request 下载请求')
            self.process_down(data)
        elif data[0] == '%U%':
            print(f'UpData request 上传请求')
            self.process_update(data)
        else:
            self.ftp_r.put(["E:啥也不是非法输入"])
