#服务端(基础功能框子写好了V0.35,服务端还没能储存上传的文件)

##1.运行的进程

###1.1进程 CommunicateServe

####1.1.1子进程TS_CHAT

负责与所有CHAT客户端的通信

将所有客户端请求推送到msg_q队列
阻塞在recv_q接收处理结果并回复给客户端


####1.1.2子进程TS_FTP
负责与所有FTP客户端的通信

将所有客户端请求推送到Ftp_s队列
阻塞在Ftp_r接收处理结果并回复给客户端


###1.2进程 DBS_CHAT
监听msg_q和recv_q
从msg接收 处理完 推送到recv_q

###1.3进程 DBS_FTP

监听msg_q和recv_q
从msg接收 处理完 推送到recv_q

