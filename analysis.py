# -*- coding:utf-8 -*-
'''数据分析
实现：
    根据日线推算出12日的平均线。统计日线上穿12日线的次数sum，
    统计日线上穿12日线10个交易日后的仍然上涨的次数sec，
    模型概率cul=sec/sum，当概率大于0.80时，即可认为可靠性较高。（股票筛选）
	在上述筛选出的股票中，如果最近一次上穿至数据更新的最新时间，
    交易日间隔小于3日，即推荐买入。按照概率高低排序，从高到低选5支股票给客户。
反馈交易指导信息：
	接受用户反馈的股票编号，对该股票进行数据分析，将分析结果反馈给用户。
    符合度超过80%，天数小于3天，建议买入，不小于３天建议观望。
    其它可理解为不建议买入。(^_^)
注：
    用函数或类封装方法，服务端启动时，循环调用方法对每只股票分析。
    用户指定股票，调用该方法对指定股票分析。
'''
import tushare
import database
import stock
import time

class Analysis(object):
    def __init__(self):
        # 创建股票对象
        self.sa = stock.Stock()
        # 获取数据库对象
        self.dba = database.Database()
        # 获取股票列表
        self.get_stock_list()

    def write_analysis_info(self):
        '''将分析后的数据写入stockinfo表'''
        # 记录符合条件的股票代码和比率
        # 记录日期
        date = str(time.strftime('%Y-%m-%d',time.localtime()))
        for code in self.stock_list:
            try:
                up, ten, days, ratio = self.analysis(code) 
            except Exception:
                print(code)
            # 如果10天后上涨的次数与总次数的比率大于0.80，筛选
            if ratio >= 0.80 and days <= 3:
                content = '股票指标符合度达到80%以上，近期有走强的趋势，建议买入。'
            elif ratio >= 0.8:
                content = '股票指标符合度较高，建议继续观望。'
            elif ratio >= 0.6 and days <= 5:
                content = '股票指标符合度一般，可少量买入。'
            elif ratio >= 0.6:
                content = '股票指标符合度一般，不建议买入。'
            else:
                content = '股票不符合指标，建议远离。'
            self.dba.insert_stockinfo_table(
                (date, code, up, ten, ratio, days, content)
            )
            print(code, content)

    # 获取股票列表
    def get_stock_list(self):
        '''查询所有已写入数据库的股票代码'''
        self.stock_list = self.sa.getStockList()

    # 分析
    def analysis(self, code):
        '''数据分析
        接收股票代码
        返回值：
        up_count: 均线上穿次数
        ten_count: 均线上穿10天后仍然上涨的次数
        up_days: 距离最近一次上穿的天数
        ratio:　指标符合度 = ten_count / up_count
        '''
        data_analysis = self.get_daydate(code)
        # print(data_analysis)
        up_count, ten_count = self.count_avg_cross_day(data_analysis)
        # print(up_count, ten_count)
        up_days = self.count_up_last_days(data_analysis)
        ratio = ten_count / up_count
        return up_count, ten_count, up_days, ratio

    # 获取日线数据，元素形式[(收盘价, 12日均价),]
    def get_daydate(self, code):
        '''获取日线数据
        接收股票代码，字符串
        返回用于分析的日线数据
        [(收盘价, 12日均价),]
        '''
        # 获取股票日线数据
        self.dba.select_stock_table(code, 'data_day', ('close',))
        close = self.dba.fetch_data()
        lst_temp = []
        for x in close:
            lst_temp.append(x[0])
        close = lst_temp
        data_12day = self.get_avgdata(close)
        # 提取数据，元素形式[(收盘价, 12日均价),]
        data_analysis = []
        for x in zip(close[13:], data_12day):
            data_analysis.append(x)
        return data_analysis

    # 12天均线
    def get_avgdata(self, data):
        '''获取12日均线
        接收日线数据，将日线数据处理成12日均线
        返回12日均线列表
        '''
        start = 0
        end = 13
        # 存放均线数据
        lst_temp = []
        while end <= len(data):
            data_sum = sum(data[start:end]) / 13
            lst_temp.append(data_sum)
            start += 1
            end += 1
        return lst_temp

    # 统计均线上穿次数和10天后股价仍高于日线的次数
    def count_avg_cross_day(self, data):
        '''统计均线上穿次数和10天后股价仍高于日线的次数
        接收[(收盘价, 12日均价),]列表
        返回值：(count, count_ten)
        count: 上穿次数
        count_ten: 10天后股价仍高于日线的次数
        '''
        # 上穿总次数
        count = 0
        # 上穿十天后仍高于日线的次数
        count_ten = 0
        # print(data)
        i = 1
        while i < len(data):
            # 均线上穿日线
            if (data[i-1][1] < data[i-1][0]) & (data[i][1] > data[i][0]):
                count += 1
                # 10天后均线仍高于日线
                if (i+10) < len(data):
                    if data[i+10][1] > data[i+10][0]:
                        count_ten += 1
            i += 1
        return (count, count_ten)

    # 统计最后一次均线上穿日线距最后交易日的天数
    def count_up_last_days(self, data):
        '''统计最后一次均线上穿日线距最后交易日的天数
        接收[(收盘价, 12日均价),]列表
        返回值：count，天数，整数
        '''
        # 记录天数
        count = 0
        i = -1
        while True:
            if i < -len(data):
                break
            # 判断是否上穿
            if (data[i-1][1] < data[i-1][0]) & (data[i][1] > data[i][0]):
                break
            count += 1
            i -= 1
        return count

if __name__ == "__main__":
    a = Analysis()
    a.write_analysis_info()