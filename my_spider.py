import time
from mysql_util import MysqlUtil
from ua_util import UAUtil
from ip_util import IPUtil
from my_spider_helper import MySpiderHelper


"""
(主程序)
"""
#获取运行时的时间
temp_time = time.time()
#获取UAUtil对象
ua_util = UAUtil()
#获取IPUtil对象
ip_util = IPUtil(ua_util)
#获取MysqlUtil对象
mysql_util = MysqlUtil()
#获取MySpiderHelper对象
my_spider_helper = MySpiderHelper(ua_util, ip_util, mysql_util)
#启动爬虫
my_spider_helper.start_spider()
#获取程序结束时的时间
current_time = time.time()
print("爬取完成, 共花费时间：" + str(current_time - temp_time))