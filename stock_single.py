# -*- coding:utf-8 -*-
'''单只股票
继承Stock类
重写get_data_for_k方法
'''
import stock

class StockSingle(stock.Stock):
    # 初始化
    def __init__(self, code, data):
        # 股票代码
        self.CODE = code
        # 接收k线数据
        self.DATA = data
    
    def get_data_for_k(self, code='600660'):
        '''重写父类方法'''
        self.data_k = self.DATA

if __name__ == "__main__":
    pass