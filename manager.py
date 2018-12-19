# -*- coding:utf-8 -*-
'''管理员
写代码写到吐啊，萌萌老师说要写个对象啊，那就整个对象吧，啊哈哈
要先启动数据库啊！ :$ mysql -uroot -p123456
'''
import analysis
import database
import stock
import server
import time, datetime

class Manger(object):
    '''管理员
    大名鼎鼎的root用户
    '''
    # 初始化
    def __init__(self):
        # 创建分析对象
        self.ana = analysis.Analysis()
        # 创建数据库对象
        self.dbm = self.ana.dba
        # 获取使用日期
        self.DATE = str(time.strftime('%Y-%m-%d',time.localtime()))

    # 管理方法
    def mange(self):
        '''管理流程'''
        while True:
            print('''
            ************主人，你想干点啥************
            ----------------------------------------
            1. 创建data_day表，存放股票数据
            2. 创建userinfo表，存放用户信息
            3. 创建stockinfo表，存放分析数据
            4. 将股票数据写入data_day表(洞房时用)
            5. 将分析数据写入stockinfo表(同上，你懂得)
            6. 更新data_day表中的数据
            7. 更新stockinfo中的数据
            8. 看谁不爽，让谁消失
            9. 嘿咻嘿咻
            ----------------------------------------
            ''')
            # 命令
            com = input('主人请吩咐：')
            lst = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
            if com not in lst:
                print('主人，睁大眼睛好好瞅瞅！')
                continue
            # 创建data_day表
            elif com == '1':
                if self.cheak_table_exists('data_day'):
                    print('主人, 表已存在，蒙圈了吧！')
                else:
                    self.dbm.create_stock_table()
                    print('创建完毕！')
            # 创建userinfo表
            elif com == '2':
                if self.cheak_table_exists('userinfo'):
                    print('主人, 表已存在，蒙圈了吧！')
                else:
                    self.dbm.create_userinfo_table()
                    print('创建完毕！')
            # 创建stockinfo表
            elif com == '3':
                if self.cheak_table_exists('stockinfo'):
                    print('主人, 表已存在，蒙圈了吧！')
                else:
                    self.dbm.create_stockinfo_table()
                    print('创建完毕！')
            # 将股票数据写入data_day表, 同时如果userinfo表还未创建也进行创建
            elif com == '4':
                if not self.cheak_table_exists('data_day'):
                    self.dbm.create_stock_table()
                if not self.check_update_time('data_day'):
                    print('数据已经存在啦！')
                    continue
                self.dbm.write_all_stock_data()
                self.write_to_diary('data_day')
                if not self.cheak_table_exists('userinfo'):
                    self.dbm.create_userinfo_table()
                self.dbm.set_index_on_stock()
                print('写入完毕！')
            # 将分析数据写入stockinfo表
            elif com == '5':
                if not self.cheak_table_exists('stockinfo'):
                    self.dbm.create_stock_table()
                if not self.check_update_time('stockinfo'):
                    print('数据已经存在啦')
                    continue
                self.ana.write_analysis_info()
                self.write_to_diary('stockinfo')
                print('写入完毕！')
            # 更新data_day表
            elif com == '6':
                old = self.check_update_time('data_day')
                now = self.DATE
                if not old:
                    print('数据无需更新')
                    continue
                self.dbm.write_all_stock_data(start=old, end=now)
                self.write_to_diary('data_day') 
                print('更新完毕！')
            # 更新stockinfo表
            elif com == '7':
                old = self.check_update_time('stockinfo')
                now = self.DATE
                if not old:
                    print('数据无需更新')
                    continue
                self.ana.write_analysis_info()
                self.write_to_diary('stockinfo')
                print('更新完毕！')
            # 删除用户
            elif com == '8':
                name = input('主人要拿谁开刀？')
                self.dbm.delete_user(name)
                print('%s，不见啦！' % name)
            # 退出
            elif com == '9':
                print('人家可是纯爷们，不理你了！')
                return

    # 判断数据库是否存在
    def cheak_table_exists(self, tablename):
        '''判断数据表是否存在
        接收表名, 字符串
        存在返回True, 不存在返回False
        '''
        sql = 'use %s' % tablename
        self.dbm.cur_execute(sql)
        sql = 'show tables'
        self.dbm.cur_execute(sql)
        data = self.dbm.fetch_data()
        lst = []
        for x in data:
            lst.append(x[0])
        if tablename in lst:
            return True
        else:
            return False

    # 将更新日期写入文件
    def write_to_diary(self, tablename):
        '''将更新的日期写入日志文件
        参数为表名，字符串
        '''
        # 读取数据
        with open('diary.txt', 'r') as file:
            # 存放文件数据
            lst = []
            while True:
                line = file.readline()
                if not line:
                    break
                lst.append(line.strip().split(','))
            # print(lst)
        # 修改时间
        for x in lst:
            if tablename == x[0]:
                x[1] = self.DATE
                break
        # print(lst)
        # 将数据格式化为字符串
        line = ''
        for x in lst:
            line += ','.join(x)
            line += '\n'
        # print(line)
        # 写入数据
        with open('diary.txt', 'w') as file:
            file.write(line)
    
    # 读取表上一次更新的时间，需要更新返回日期，无需更新返回0
    def check_update_time(self, tablename):
        '''判断日期是否要更新
        参数为表名，字符串
        如果需要更新返回日期
        无需更新返回0
        '''
        # 读取数据
        with open('diary.txt', 'r') as file:
            # 存放文件数据
            lst = []
            while True:
                line = file.readline()
                if not line:
                    break
                lst.append(line.strip().split(','))
            # print(lst)
        # 修改时间
        # 存放时间
        old = ''
        for x in lst:
            if tablename == x[0]:
                old = x[1]
                break
        # print(old)
        # 转换为时间格式
        old_date = datetime.datetime.strptime(old, '%Y-%m-%d')
        now = datetime.datetime.strptime(self.DATE, '%Y-%m-%d')
        # 多加一天
        date = old_date + datetime.timedelta(days=1)
        if date <= now:
            return date.strftime('%Y-%m-%d')
        else:
            return 0

if __name__ == "__main__":
    m = Manger()
    m.mange()
    # m.mange()
    # m.cheak_table_not_exists('stockinfo')
    # print(m.check_update_time('data_day'))
    # m.write_to_diary('stockinfo')
