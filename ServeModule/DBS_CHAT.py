import pymysql
import re
import time
from multiprocessing import Queue, Process

"""
chat使用的数据表

1.聊天记录表 Chat_record字段 
主键 
user M_to_C(外键联系管理表) 
content varchar(144)
send_date date ："YYYY-MM-DD" curdate() 返回当前日期，格式对应date类型
time_depart time ："HH:MM:SS" curtime() 返回当前时间，格式对应time类型


2.运行日志表 字段 
主键  
发生时间 
内容

3.管理信息表Manage_info 字段 
主键
user 建立 unique索引
passwd 类型CHAR(20)建立 mul索引
注册时间 datetime ："YYYY-MM-DD HH:MM:SS" now() 返回服务器当前日期时间,格式对应datetime类型
最后登录时间 datetime ："YYYY-MM-DD HH:MM:SS" now() 返回服务器当前日期时间,格式对应datetime类型


"""


class DBSChat(Process):

    def __init__(self, msg_q: Queue, recv_q: Queue):
        # 连接数据库
        super().__init__()
        self.db = pymysql.connect(host='127.0.0.1',
                                  port=3306,
                                  user='root',
                                  password='123456',
                                  database='chatroom',
                                  charset='utf8')
        self.cur = self.db.cursor()
        self.msg_Q = msg_q
        self.recv_Q = recv_q

    @staticmethod
    def join_chat_record(user: str, content: str, date_depart: str, time_depart: str):
        list_record = [user, content, date_depart, time_depart]
        return list_record

    @staticmethod
    def gen_date_time():
        time_str = time.strftime("%y-%m-%d %H:%M:%S", time.localtime(time.time()))
        list_time = time_str.split(" ")
        return list_time[0], list_time[1]

    @staticmethod
    def format_read(select_res):
        list_res = []
        for item in select_res:
            list_res.append(str(item))
        return list_res

    def gen_id(self, user: str):
        """
        将用户名转化成mi表中的id
        :param user:
        :return:
        """
        sql_user = f"select id from Manage_info where user = '{user}';"
        self.cur.execute(sql_user)
        M_to_C = self.cur.fetchall()
        M_to_C = re.search(r"([1-9]+)", str(M_to_C)).groups()
        for item in M_to_C:
            return item

    def read_chat_record(self, read_num: int = 15):
        try:
            sql = f"select  mi.user,cr.time_depart,cr.content from Chat_record as cr left join Manage_info as mi on mi.id = cr.M_to_C order by cr.id desc limit {read_num};"
            self.cur.execute(sql)
            select_res = self.cur.fetchall()
            if select_res:
                select_res = self.format_read(select_res)
                return select_res
            else:
                return
        except Exception as e:
            print(e)
            self.db.rollback()

    def write_chat_record(self, data: list):
        """
        将单条信息存进chat_record
        :param data: 用户名,内容,发送日期,发送时间组成的列表 转化成 id,内容,发送日期,发送时间存储进 chat_record
        :return:
        """
        chat_record = data
        user = chat_record[1]
        content = chat_record[3]
        (date_depart, time_depart) = DBSChat.gen_date_time()
        try:
            M_to_C = self.gen_id(user)
            sql = f"insert into Chat_record (M_to_C,content,date_depart,time_depart) values({M_to_C},'{content}','{date_depart}','{time_depart}');"
            self.cur.execute(sql)
            self.db.commit()
        except Exception as e:
            print(e)
            self.db.rollback()

    def read_log(self, data: str):
        pass

    def write_log(self, data: str):
        pass

    def run(self):
        print('DBS_CHAT服务就绪')
        print("Serve------------------------Start")
        self.get_msg_Q()

    # 运行get_msg_Q

    def get_msg_Q(self):
        while True:
            try:
                data = self.msg_Q.get()  # 获得了一个消息
                print(f'DBS_CHAT Processing')
                if data:
                    self.process_data(data)
            except Exception as e:
                print(e)

                # 获得消息 阻塞

    def process_func(self, data):
        func = data[1]
        if func == 'flush':
            result = self.read_chat_record()
            self.recv_Q.put(result)
        if func == 'quit':
            self.recv_Q.put("E:服务端退出")
            exit()
        else:
            self.recv_Q.put(["E:功能非法输入"])

    def process_log(self, data):
        user = data[1]
        passwd = data[3]
        try:
            sql = f"select  user,passwd from Manage_info as mi where user = '{user}' and passwd = '{passwd}';"
            self.cur.execute(sql)
            select_res = self.cur.fetchall()
            if select_res:
                self.recv_Q.put(["$%Y"])
            else:
                self.recv_Q.put(["$%N"])
        except Exception as e:
            print(e)
            self.recv_Q.put(["E:登录信息非法输入"])
            self.db.rollback()
            return

            # 登陆用

    def process_reg(self, data):
        user = data[1]
        passwd = data[3]
        try:
            sql = f"select  user,passwd from Manage_info as mi where user = '{user}' and passwd = '{passwd}';"
            self.cur.execute(sql)
            select_res = self.cur.fetchall()
            if select_res:
                self.recv_Q.put(["$%N"])
            else:
                sql = f"insert into Manage_info (user,passwd) values ('{user}',{passwd});"
                self.cur.execute(sql)
                self.recv_Q.put(["$%Y"])
        except Exception as e:
            print(e)
            self.recv_Q.put(["E:注册信息非法输入"])
            self.db.rollback()
            return

            # 注册用

    def process_msg(self, data):
        try:
            self.write_chat_record(data)
            result = self.read_chat_record()
            self.recv_Q.put(result)
        except Exception as e:
            self.recv_Q.put(["E:聊天信息非法输入"])
            print(e)

    def process_data(self, data):
        # 对接收的消息进行处理
        # 并根据处理的结果转发到对应的消息队列
        re_res = re.search(r'(\S{2}) (\w+) (\S{2}) (.+)', data).groups()
        data = []
        for item in re_res:  # 对输入结果的处理
            data.append(item)
        # 对输入分类处理
        if data[0] == '$L':
            print(f'Login request 登入请求')
            self.process_log(data)  # $% user $% content
        elif data[0] == '$R':
            print(f'Registration request 注册请求')
            self.process_reg(data)  # $# user $# passwd
        elif data[0] == '$M':
            print(f'Message request 消息请求')
            self.process_msg(data)  # $ user $ passwd
        elif data[0] == '$F':
            print(f'Function request 功能请求')
            self.process_func(data)  # $@ func $@ func
        else:
            self.recv_Q.put(["E:啥也不是非法输入"])

# 协议 $M user $ content 以用户名发送消息 清屏后服务端返回最近十条信息
#     $L user $% passwd 登入指定用户名
#     返回值Y 登录成功 调用修改本文件的函数 返回值N 登录失败,用户名或密码错误
#     $R user $# passwd 发送用户名和密码 判定未注册 并注册
#     返回值 Y 注册成功 N注册失败,用户名已存在
#     $F flush  等等                功能参数
#     $#$ 填充用
