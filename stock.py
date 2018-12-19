# -*- coding:utf-8 -*-
'''股票'''
import tushare
import pymysql
import database
import datetime
import matplotlib
import matplotlib.dates
import matplotlib.pyplot
import matplotlib.finance
import time

class Stock(object):
    # 初始化
    def __init__(self):
        pass

    # 获取个股历史数据
    def getStockHistData(self, code, start='2010-01-01', end=str(time.strftime('%Y-%m-%d',time.localtime()))):
        '''获取股票历史数据
        调用tushare的get_hist_data()方法获取数据
        返回值：
        date:日期
        code:股票代码
        open:开盘价
        hign:最高价
        close:收盘价
        low:最低价
        ma5:5日均价
        ma10:10日均价
        ma20:20日均价
        '''
        # 从tushare平台获取数据
        data = tushare.get_hist_data(code, start, end)
        # 建立存储数据的列表
        self.stock_list = []
        # 组合所需元素(日期-股票代码-开盘价-收盘价-最高价-最低价-5日线－10日线-20日线)
        temp = zip(data.index, [code for x in range(len(data.index))],data.open,
        data.close, data.high, data.low, data.ma5, data.ma10, data.ma20)
        for i in temp:
            self.stock_list.append(i)
        return self.stock_list[::-1]

    # 获取正常交易股票列表
    def getStockList(self):
        # 查询当前所有正常上市交易的股票列表
        self.data = tushare.get_stock_basics()
        return self.data.index
    
    # 从数据库中获取k线数据(用于测试)
    def get_data_for_k(self, code='600660'):
        '''获取k线数据(数据库)
        参数：股票代码，字符串
        返回：fetchall()方法的大元组
        ((date, open, hign, low, close),)
        注：数据库表中hign(high)写错了，就错下去吧，懒得改了
        '''
        # 从数据库中查询数据
        # 创建数据库对象
        self.dbs = database.Database()
        # 查询k线数据
        msg = self.dbs.select_stock_table(code, 'data_day', (
        'date', 'open', 'hign', 'low', 'close'))
        if msg == -1:
            print('获取数据失败')
            return -1
        self.data_k = self.dbs.fetch_data()
        if not self.data_k:
            return self.data_k
    
    # 处理k线数据
    def handle_data_for_k(self):
        '''处理k线数据
        返回列表：[[date, open, hign, low, close],]
        date:处理成matplotlib时间格式
        open,hign,low,close为float类型
        '''
        # 创建k线数据列表
        self.lst_k = []
        for x in self.data_k:
            self.lst_k.append([
                self.handle_time_date(x[0]),
                x[1],x[2],x[3],x[4]
            ])
        return self.lst_k

    # 处理时间
    def handle_time_date(self, date):
        '''将时间字符串处理为matplotlib时间格式
        接收时间字符串，返回matplotlib格式时间
        '''
        t = date.split('-')
        y, m, d = t[0:3]
        # 将字符串转化为时间格式
        d = datetime.date(int(y), int(m), int(d))
        # 将时间转化为matplotlib时间格式
        date = matplotlib.dates.date2num(d)
        return date

    # 画k线
    def draw_k(self, code):
        '''画k线
        code为股票编码，字符串
        将k线保存在当前目录下，名称为k.png
        '''
        # 获取k线数据
        self.get_data_for_k(code)
        # 处理k线数据(转换日期)
        self.handle_data_for_k()
        # 绘制k线
        # figsize=(a,b)，调节窗口宽,高
        fig, ax = matplotlib.pyplot.subplots(figsize=(12,6))
        fig.subplots_adjust(bottom=0.2)
        matplotlib.finance.candlestick_ohlc(ax, self.lst_k, width=0.4, colorup='r', colordown='g')
        matplotlib.pyplot.grid(False)
        ax.xaxis_date()
        ax.autoscale_view()
        matplotlib.pyplot.setp(matplotlib.pyplot.gca().get_xticklabels(), rotation=30)
        # 保存k线
        matplotlib.pyplot.savefig('k.png')
        # 展示k线
        matplotlib.pyplot.show()
    

if __name__ == "__main__":
    s = Stock()
    # s.get_data_for_k('600660')
    # s.handle_data_for_k()
    # a = s.handle_time_date('2018-12-12')
    # s.draw_k('600660')
    data = s.getStockHistData('600660','2018-10-12')
    print(data)
