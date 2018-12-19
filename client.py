# -*- coding:utf-8 -*-
'''客户端'''
import socket
import sys
import getpass
import re
import stock_single

class Client(object):
    # 初始化
    def __init__(self, ip, port):
        self.__IP = ip
        self.__PORT = port
        # 地址
        self.__ADDR = (self.__IP, self.__PORT)
        # 连接服务器
        self.runClient()
        self.sockfd.send(b'A')
        # 接收服务器推送消息
        self.TMSG = self.sockfd.recv(4096)
        # 显示推送消息
        print('股票信息：', self.TMSG.decode())
    
    # 创建TCP/IP套接字
    def runClient(self):
        # 创建套接字
        self.sockfd = socket.socket()
        # 连接服务器
        self.sockfd.connect(self.__ADDR)

    # 操作
    def operation(self):
        while True:
            print('1.登录  2.注册  q.退出')
            # 输入选项
            cmd = input('>> ')
            # 如果选项不符，重新输入
            if cmd not in ['1', '2', 'q']:
                print('不存在该选项，请重新输入：')
                continue
            # 登录
            elif cmd == '1':
                # self.sockfd.send(b'L')
                self.login()
            # 注册
            elif cmd == '2':
                # self.sockfd.send(b'R')
                self.register()
            # 退出
            elif cmd == 'q':
                self.closeClient()
    
    # 注册
    def register(self):
        while True:
            name = input('请输入姓名(8-18位)：')
            passwd_one = getpass.getpass('请输入密码(8-18位)：')
            passwd_two = getpass.getpass('再次输入密码：')
            # 判断姓名和密码是否输入正确
            regex = r'^[a-zA-Z0-9]{8,18}$'
            result = re.compile(regex)
            if passwd_one != passwd_two:
                print('两次密码输入不同')
                continue
            if result.match(name) and result.match(passwd_one):
                msg = 'R %s %s' % (name, passwd_one)
                # 发送请求
                self.sockfd.send(msg.encode())
                # 等待回复
                data = self.sockfd.recv(128).decode()
                if data == 'OK':
                    print('注册成功')
                elif data == 'EXISTS':
                    print('该用户已存在，请重新输入！')
                    continue
                else:
                    print('注册失败！')
            else:
                print('用户名或密码输入格式不符')
                continue
            return

    # 登录
    def login(self):
        name = input('请输入用户名：')
        passwd = getpass.getpass('请输入密码：')
        # 判断姓名和密码是否输入正确
        regex = r'^[a-zA-Z0-9]{8,18}$'
        result = re.compile(regex)
        # 如果正确进行登录验证，否则退回上一级界面
        if result.match(name) and result.match(passwd):
            msg = 'L %s %s' % (name, passwd)
            # 发送请求
            self.sockfd.send(msg.encode())
            # 接收消息
            data = self.sockfd.recv(128).decode()
            if data == 'OK':
                print('登录成功')
                self.check()
            else:
                print('登录失败')
        else:
            print('用户名密码格式不符！')

    # 查询
    def check(self):
        while True:
            code = input('请输入要查询的股票代码(q返回)：')
            if code == 'q':
                return
            regex = r'^[0-9]{6}$'
            result = re.compile(regex)
            # 判断输入是否有误
            if not result.match(code):
                print('代码输入错误！')
                continue
            msg = 'C %s' % code
            # 发送信息给服务器
            self.sockfd.send(msg.encode())
            # 接收服务器数据
            data = self.sockfd.recv(1024)
            if data.decode() == 'FAIL':
                print('无可查数据，请重新输入查询：')
                continue
            print(data.decode())
            # 接收k线数据
            data = self.sockfd.recv(1024*8)
            data = self.decode_k_data(data.decode())
            # print(data)
            ss = stock_single.StockSingle(code, data)
            ss.draw_k(code)
            # print(data)
    
    # 解析k线数据
    def decode_k_data(self, data):
        lst = data.split()
        lst_temp = []
        for i in lst:
            t = i.split(',')
            lst_temp.append((t[0], float(t[1]), float(t[2]), 
            float(t[3]), float(t[4])))
        return lst_temp

    # 关闭客户端
    def closeClient(self):
        # 关闭套接字
        self.sockfd.close()
        # 关闭进程
        sys.exit(0)

if __name__ == "__main__":
    c = Client('localhost', 8000)
    c.operation()