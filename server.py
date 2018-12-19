# -*- coding:utf-8 -*-
'''服务器'''
import socket
import select
import queue
import sys
import database

# 服务器
class Server(object):
    '''服务器
    采用IO多路复用方法(epoll)处理客户端连接
    支持多连接
    首次启动需配置数据库，加载所需数据
    '''
    # 初始化
    def __init__(self, ip, port):
        self.__IP = ip
        self.__PORT = port
        # 地址
        self.__ADDR = (self.__IP, self.__PORT)
        # 创建套接字
        self.runServer()
        self.create_epoll()
        # 创建数据库对象
        self.dbsev = database.Database()

    # 创建服务器套接字
    def runServer(self):
        '''创建TCP/IP套接字'''
        # 创建TCP/IP套接字
        self.sockfd = socket.socket()
        # 设置地址复用
        self.sockfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 设置地址非阻塞
        self.sockfd.setblocking(False)
        # 绑定地址
        self.sockfd.bind(self.__ADDR)
        # 监听
        self.sockfd.listen(10)

    # 创建epoll
    def create_epoll(self):
        '''创建epoll对象'''
        # 超时阻塞时间
        self.TIMEOUT = 10
        # 创建epoll对象
        self.epoll = select.epoll()
        # 注册服务器
        self.epoll.register(self.sockfd.fileno(), select.EPOLLIN)
        # 用于保存客户端消息的字典
        self.messages = {}
        # 用于存放文件句柄和套接字对象的字典
        self.dict_sockfd = {self.sockfd.fileno():self.sockfd}

    # 多路复用，处理客户端连接
    def handle(self):
        '''epoll方法处理客户端连接'''
        while True:
            # 轮询连接事件
            try:
                events = self.epoll.poll(self.TIMEOUT)
            except KeyboardInterrupt:
                # 如果ctrl+c退出就调用关闭程序
                self.serverClose()
            # 如果无连接，重新轮询
            if not events:
                continue
            # 如果有，处理连接事件
            for fd, event in events:
                # 把对应句柄的套接字对象从字典中取出
                sockfd = self.dict_sockfd[fd]
                # 如果是服务器的套接字，处理新连接
                if sockfd is self.sockfd:
                    # 连接
                    self.conn, self.addr = self.sockfd.accept()
                    # 将新连接设置为非阻塞
                    self.conn.setblocking(False)
                    # 注册新连接
                    self.epoll.register(self.conn.fileno(), select.EPOLLIN)
                    # 把新连接的句柄和套接字添加到字典中
                    self.dict_sockfd[self.conn.fileno()] = self.conn
                    # 以对象为键，创建队列，保存连接信息
                    self.messages[self.conn] = queue.Queue()
                # 处理关闭事件
                elif event & select.EPOLLHUP:
                    # 注销
                    self.epoll.unregister(fd)
                    # 删除队列内的信息
                    del self.messages[self.dict_sockfd[fd]]
                    # 关闭套接字
                    self.dict_sockfd[fd].close()
                    # 删除字典信息
                    del self.dict_sockfd[fd]
                # 处理读事件
                elif event & select.EPOLLIN:
                    # 接收数据
                    data = sockfd.recv(1024)
                    # 将数据放入对应字典
                    self.messages[sockfd].put(data)
                    # 修改为写事件
                    self.epoll.modify(fd, select.EPOLLOUT)
                # 处理写事件
                elif event & select.EPOLLOUT:
                    try:
                        # 从字典中获取数据
                        msg = self.messages[sockfd].get_nowait().decode()
                    except queue.Empty:
                        # 如果无数据可获取，就修改为读事件
                        self.epoll.modify(fd, select.EPOLLIN)
                    else:
                        # 处理数据
                        # 登录
                        if msg == '':
                            self.epoll.modify(fd, select.EPOLLHUP)
                        elif msg[0] == 'L':
                            self.login(sockfd, msg)
                        # 注册
                        elif msg[0] == 'R':
                            self.register(sockfd, msg)
                        # 查询
                        elif msg[0] == 'C':
                            self.check(sockfd, msg)
                        elif msg[0] == 'A':
                            # 客户端连接后会直接发送'A’到服务器
                            # 服务器发送股票推送数据
                            msg = self.dbsev.send_stockinfo_to_client()
                            sockfd.send(msg.encode())

    # 登录
    def login(self, sockfd, msg):
        '''登录
        接收套接字和信息
        到数据库中查询用户名和密码是否匹配
        '''
        lst = msg.split(' ')
        name = lst[1]
        passwd = lst[2]
        # 从数据库查询用户是否存在
        self.dbsev.select_userinfo_table(name, passwd)
        if self.dbsev.fetch_data():
            sockfd.send(b'OK')
        else:
            sockfd.send(b'FAIL')

    # 注册
    def register(self, sockfd, msg):
        '''注册
        接收套接字和信息
        注册成功将用户名和密码写入数据库userinfo
        '''
        lst = msg.split(' ')
        name = lst[1]
        passwd = lst[2]
        # 判断用户是否存在
        self.dbsev.select_userinfo_table(name, passwd)
        if self.dbsev.fetch_data():
            sockfd.send(b'EXISTS')
            return
        else:
            try:
                self.dbsev.insert_userinfo_table(name, passwd)
            except Exception:
                sockfd.send(b'FAIL')
            else:
                sockfd.send(b'OK')

    # 查询
    def check(self, sockfd, msg):
        '''查询
        接收套接字和信息
        第一次发送用户查询股票的分析信息
        第二次发送该股票的k线数据
        '''
        lst = msg.split(' ')
        code = lst[1]
        self.dbsev.select_stockinfo_table(code)
        data = self.dbsev.fetch_data()
        # 发送推送查询数据
        if data:
            data = str(data[0][0])
            sockfd.send(data.encode())
        else:
            sockfd.send(b'FAIL')
            return
        # 发送k线数据
        data = self.dbsev.select_stock_table_for_k(code)
        data = self.handle_k_data_to_string(data)
        sockfd.send(data.encode())
    
    # 将k线数据处理成字符串
    def handle_k_data_to_string(self, data):
        '''将k线数据处理成字符串
        接收k线数据
        返回可用于发送的字符串
        '''
        msg = ''
        for x in data:
            msg += '%s,%s,%s,%s,%s ' % (x[0], str(x[1]), 
            str(x[2]), str(x[3]), str(x[4]))
        return msg

    # 关闭服务器
    def serverClose(self):
        '''关闭服务器'''
        # 注销
        self.epoll.unregister(self.sockfd.fileno())
        # 关闭epoll
        self.epoll.close()
        # 关闭服务端套接字
        self.sockfd.close()
        # 关闭进程
        sys.exit(0)

if __name__ == "__main__":
    s = Server('0.0.0.0', 8000)
    s.handle()
    
