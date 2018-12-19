# -*- coding:utf-8 -*-
'''数据库操作'''
import pymysql
import os, sys
import stock
import time

class Database(object):
    # 初始化
    def __init__(self, host='localhost', user='root', 
    password='123456', database='stock', port=3306, charset='utf8'):
        self.DB_HOST = host
        self.DB_USER = user
        self.DB_PORT = port
        self.DB_PASSWD = password
        self.DB_NAME = database
        self.DB_CHARSET = charset
        self.DATE = str(time.strftime('%Y-%m-%d',time.localtime()))
        # 建立游标对象
        self.cur = self.get_cur()

    # 获取数据库游标
    def get_cur(self):
        '''建立数据库游标对象
        返回游标对象
        '''
        # 建立数据连接
        self.db = pymysql.connect(
            host = self.DB_HOST,
            user = self.DB_USER,
            password = self.DB_PASSWD,
            database = self.DB_NAME,
            charset = self.DB_CHARSET,
            port = self.DB_PORT)
        # 返回数据库游标对象
        return self.db.cursor()

    # 数据库交互
    def commit_to_database(self, sql):
        '''提交操作到数据库
        调用pymysql的execute()和commit()
        参数:mysql支持的sql语句
        无返回值
        '''
        try:
            self.cur.execute(sql)
            self.db.commit()
        except Exception as e:
            print(e)
            self.db.rollback()

    # 关闭数据库
    def close_database(self):
        '''关闭数据库'''
        self.db.close()
    
    # 建立股票表data_day
    def create_stock_table(self):
        '''创建股票表
        表名为data_day
        id: int primary key auto_increment
        date: varchar(11) not null
        code: varchar(11) not null
        open: float(7,2) not null
        close: float(7,2) not null
        hign: float(7,2) not null
        low: float(7,2) not null
        ma5: float(7,2) not null
        ma10: float(7,2) not null
        ma20: float(7,2) not null
        engine: innodb
        charset: utf8
        '''
        sql = '''create table data_day(
              id int primary key auto_increment,
              date varchar(11) not null,
              code varchar(11) not null,
              open float(7,2) not null,
              close float(7,2) not null,
              hign float(7,2) not null,
              low float(7,2) not null,
              ma5 float(7,2) not null,
              ma10 float(7,2) not null,
              ma20 float(7,2) not null
              )engine=innodb, charset=utf8'''
        self.commit_to_database(sql)
    
    # 插入股票数据data_day
    def insert_stock_table(self, *args):
        '''向stock_table表中插入数据'''
        sql = 'insert into data_day values(0, %r, %r, %f, %f, %f, %f, %f, %f, %f)' % args[0]
        self.commit_to_database(sql)

    # 给股票数据添加索引(code)
    def set_index_on_stock(self):
        '''给data_day的code列增加索引'''
        sql = "create index code_index on data_day(code)"
        self.commit_to_database(sql)

    # 从股票数据库中查询数据
    def select_stock_table(self, code, tablename, *args):
        '''根据参数查询数据
        code:股票编号，字符串
        tablename:数据表名称，字符串
        *args:字符串元祖或列表，元素为要查询的数据
        例：
        select_stock_table('600660', 'data_day', ('code', 'open', 'close'))
        如果查询错误，返回-1
        '''
        s = ','.join(args[0])   
        sql = "select %s from %s where code=%r" % (s, tablename, code)
        return self.cur_execute(sql)
    
    # 读取数据库查询数据
    def fetch_data(self):
        '''读取数据库数据
        内部封装了fetchall()方法
        返回fetchall()查询结果
        若查到是一个大元组((数据),...)
        若未查到返回''
        '''
        return self.cur.fetchall()

    # 封装游标的execute()方法
    def cur_execute(self, sql):
        '''封装了数据库execute()方法'''
        try:
            self.cur.execute(sql)
        except Exception:
            return -1

    # 将所有股票数据导入数据库data_day
    def write_all_stock_data(self, start='2010-01-01', end=str(time.strftime('%Y-%m-%d',time.localtime()))):
        '''导入股票到data_day数据库'''
        # 创建股票对象
        s = stock.Stock()
        # 获取所有正常交易的股票列表
        code_lst = s.getStockList()
        for code in code_lst:
            try:
                # 获取股票的所有日线数据
                lst = s.getStockHistData(code, start, end)
            except Exception as e:
                # 如果加载不成功，继续向后加载
                print(e)
                continue
            for x in lst:
                # 将数据写入数据库
                self.insert_stock_table(x)
            print(code)
        return 1
    
    # 创建用户信息表userinfo
    def create_userinfo_table(self):
        '''创建userinfo表，用于存放用户信息
        id:int not null primary key auto_increment
        name: varchar(30) not null unique
        password: varchar(15) not null
        engine: innodb
        charset: utf8
        '''
        sql = '''create table userinfo(
              id int not null primary key auto_increment,
              name varchar(30) not null,
              password varchar(15) not null,
              unique(name))engine=innodb, charset=utf8'''
        self.commit_to_database(sql)

    # 向用户信息表userinfo中插入数据
    def insert_userinfo_table(self, name, password):
        '''向userinfo表插入数据'''
        sql = "insert into userinfo values(0, %r, %r)" % (name, password)
        self.commit_to_database(sql)

    # 查询用户信息表userinfo的数据
    def select_userinfo_table(self, name, password):
        '''查询userinfo表的用户信息
        参数：
        name: 用户名，字符串
        password: 密码，字符串
        返回查询对象(发现并没有什么卵用)
        '''
        sql = "select name,password from userinfo where name=%r and password=%r" % (name, password)
        return self.cur_execute(sql)

    # 创建推送信息表stockinfo
    def create_stockinfo_table(self):
        '''创建stockinfo推送信息表
        id: int not null primary key auto_increment
        date: varchar(11) not null
        code: varchar(11) not null
        up_count: float(7,2) not null
        ten_count: float(7,2) not null
        ratio: float(7,2) not null
        days: int not null
        content: text not null
        engine: innodb
        charset: utf8
        '''
        sql = '''create table stockinfo(
              id int not null primary key auto_increment,
              date varchar(11) not null,
              code varchar(11) not null,
              up_count float(7,2) not null,
              ten_count float(7,2) not null,
              ratio float(7,2) not null,
              days int not null,
              content text not null
              )engine=innodb, charset=utf8'''
        self.commit_to_database(sql)
    
    # 向推送信息表stockinfo中插入数据
    def insert_stockinfo_table(self, *args):
        '''在推送信息表stockinfo中插入数据
        接收列表或元祖
        '''
        sql = "insert into stockinfo values(0, %r, %r, %f, %f, %f, %d, %r)" % args[0]
        self.commit_to_database(sql)

    # 查询stockinfo中的数据
    def select_stockinfo_table(self, code):
        '''查询股票推送信息
        code:股票编码，字符串
        查询失败返回-1，成功返回查询对象(一直没用，希望后面用到)
        '''
        sql = "select content from stockinfo where code=%r and date=%r" % (code, self.DATE)
        return self.cur_execute(sql)
    
    # 查询stockinfo中满足ratio>=0.8,days<=3的股票
    def select_stockinfo_for_case_perfect(self):
        '''查询stockinfo中满足ratio>=0.8,days<=3的股票'''
        sql = '''select code,ratio from stockinfo where ratio>=0.8 and days<=3 and date=%r
              order by ratio DESC limit 5''' % self.DATE
        return self.cur_execute(sql)

    # 查询stockinfo中满足ratio>=0.8的股票
    def select_stockinfo_for_case_good(self):
        '''查询stockinfo中满足ratio>=0.8的股票'''
        sql = '''select code,ratio from stockinfo where ratio>=0.8 and date=%r
              order by ratio DESC limit 5''' % self.DATE
        return self.cur_execute(sql)
    
    # 查询stockinfo中满足ratio>=0.6,days<=5的股票
    def select_stockinfo_for_case_soso(self):
        '''查询stockinfo中满足ratio>=0.6,days<=5的股票'''
        sql = '''select code,ratio from stockinfo where ratio>=0.6 and ratio<0.8 and days<=5 and date=%r
              order by ratio DESC limit 5''' % self.DATE
        return self.cur_execute(sql)

    # 查询k线数据
    def select_stock_table_for_k(self, code):
        '''查k线数据
        参数:
        code:股票代码，字符串
        返回值：k线数据
        ((date, open, hign, low, close),)
        date: 字符串，其它是float类型
        '''
        # 从数据库中查询数据
        msg = self.select_stock_table(code, 'data_day', (
        'date', 'open', 'hign', 'low', 'close'))
        if msg == -1:
            print('获取数据失败')
            return -1
        data_k = self.fetch_data()
        # 返回后120条数据
        l = 120
        if len(data_k) <= l:
            l = len(data_k)
        return data_k[-l:]
        
    # 服务器启动后推送消息
    def send_stockinfo_to_client(self):
        '''拼接服务器启动后推送的消息
        返回拼接好的消息
        '''
        self.select_stockinfo_for_case_perfect()
        data = self.fetch_data()
        reason = '上述股票近期有走强的趋势，建议买入。'
        if not data:
            self.select_stockinfo_for_case_good()
            data = self.fetch_data()
            reason = '暂无推荐买入股票，上述股票可暂时观望。'
            if not data: 
                self.select_stockinfo_for_case_soso()
                data = self.fetch_data()
                reason = '无好股推荐，若你实在手痒，可买入玩玩。'
        msg = '今日推送的股票编号有：'
        for s in data:
            msg += '%s，' % s[0]
        msg += '指导意见：\n'
        msg += reason
        return msg
    
    # 删除用户
    def delete_user(self, name):
        '''删除用户信息'''
        sql = "delete from userinfo where name=%r" % name
        self.cur_execute(sql)

if __name__ == "__main__":
    d = Database()
    # sql = d.create_stock_table()
    # s = stock.Stock()
    # lst = s.getStockHistData()
    # for x in lst:
    #     d.insert_stock_table(x)
    # print('提交成功')
    # d.set_index_on_stock()
    # d.select_stock_table('600660', 'data_day', ('code', 'open', 'close'))
    # print(d.fetch_data())
    # code_lst = s.getStockList()
    # for code in code_lst:
    #     try:
    #         lst = s.getStockHistData(code)
    #     except Exception:
    #         print(code, '未成功加载')
    #         continue
    #     for x in lst:
    #         d.insert_stock_table(x)
    #     print(code)
    # d.create_userinfo_table()
    # d.create_stockinfo_table()
    # d.close_database()
    # print(d.send_stockinfo_to_client())
    # d.select_stockinfo_for_case_good()
    # data = d.fetch_data()
    # d.select_stockinfo_for_case_perfect()
    # data = d.fetch_data()
    # d.select_stockinfo_for_case_soso()
    # data = d.fetch_data()
    # print(data)
    # data = d.select_stock_table_for_k('600660')
    # d.select_stockinfo_table('600660')
    # data = str(d.fetch_data()[0][0])
    # print(data)
    # s = ''
    # for x in data:
    #     s += '%s,%s,%s,%s,%s ' % (x[0], str(x[1]), str(x[2]), str(x[3]), str(x[4]))
    # # print(s)

    # lst = s.split()
    # # print(lst)
    # lst_temp = []
    # for i in lst:
    #     t = i.split(',')
    #     lst_temp.append((t[0], float(t[1]), float(t[2])
    #     , float(t[3]), float(t[4])))
    # print(lst_temp)
    # print(len(data))
    # msg = d.send_stockinfo_to_client()
    d.select_stockinfo_for_case_perfect()
    s = d.fetch_data()
    print(s)