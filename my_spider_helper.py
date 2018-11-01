import requests
import time
import queue
from my_thread import MyThread
from bs4 import BeautifulSoup

# 构造一个不限制大小的的队列
SHARE_Q = queue.Queue()
# 设置线程数
_WORKER_THREAD_NUM = 32

"""
爬虫工具类，运行爬取网页逻辑，多线程爬取数据
"""
class MySpiderHelper:
    #构造函数
    def __init__(self, ua_util, ip_util, mysql_util):
        self.ua_util = ua_util
        self.ip_util = ip_util
        self.mysql_util = mysql_util

    # 获取网页源码
    def get_html(self, url):
        # 随机设置代理IP
        ip = self.ip_util.random()
        print("代理IP:" + str(ip))
        # 设置请求头
        header = {
            'User-Agent': self.ua_util.random(),    #设置随机ua
            'Referer': 'https://www.apkhere.com/',  #设置Referer
            'Accept': "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8", #接受的数据类型
            'Accept-Language': 'zh-CN, zh;q=0.9',   #接收的语言类型
            'Cache-Control': 'max-age=0',
            'Connection': 'close'   #设置Connection为close
        }
        # 异常处理
        try:
            #get请求获取网页
            response = requests.get(url, headers=header, proxies=ip, timeout=10)
            return BeautifulSoup(response.text, "html.parser")
        except Exception as ee:
            #代理ip爬取失败， 尝试不用代理去爬取网站
            print("使用本机IP爬取网页:" + str(ee))
            if str(ee).find("Caused by ProxyError") != -1:
                self.ip_util.remove_ip(ip)
                print("移除无效ip")
            try:
                #发送get请求
                response = requests.get(url, headers=header)
                # 获取网页源码
                return BeautifulSoup(response.text, "html.parser")
            except  Exception as e:
                print("获取失败:" + str(e))
                return None

    #爬取网页数据
    def get_apps_info(self, url, classification, type):
        main_html = self.get_html(url)
        if main_html == None:
            print(url + "爬取失败!")
            return
        # 获取当前分类下的总页数
        pageList_div = main_html.find("div", {"class": "pagelist", "id": "pagelist"})
        pageList = pageList_div.find_all("a")
        #当前软件分类下的总页数
        all_pages = int(pageList[len(pageList) - 2].get_text())

        # 全局变量
        global SHARE_Q
        threads = []
        # 向队列中放入任务, 真正使用时, 应该设置为可持续的放入任务
        for i in range(0, all_pages):
            current_url = url + "/" + str(i + 1)
            SHARE_Q.put(current_url)
        # 开启_WORKER_THREAD_NUM个线程
        for i in range(_WORKER_THREAD_NUM):
            thread = MyThread(self.worker(classification, type))
            # 线程开始处理任务
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        # 等待所有任务完成
        SHARE_Q.join()

    #线程工作逻辑, 只要队列不空持续处理
    def worker(self, classification, type):
        global SHARE_Q
        running = True
        while running:
            #判断任务队列是否为空
            if not SHARE_Q.empty():
                # 获得任务
                link = SHARE_Q.get()
                #爬取网页数据
                self.do_something(link, classification, type)
                #睡眠1秒
                time.sleep(1)
                SHARE_Q.task_done()
            else:
                #设置running为False，表示当前线程执行的任务结束
                running = False

    def do_something(self, link, classification, type):
        #运行逻辑, 爬取网页
        print("-----------------------------分割线-------------------------------")
        print("爬取" + classification + "第" + str(link).split("/")[-1] + "页")
        #创建一个列表保存
        list = []
        html = self.get_html(link)
        if html == None:
            return
        table = html.find("table", {"class": "apkList"})
        for tr in table.find_all("tr"):
            # 获取软件标题
            span = tr.find("span", {"class": "title"})
            title = span.find("a").get_text()

            # 获取安卓应用包名和应用下载页网址
            td_down = tr.find("td", {"class": "down"})
            down = td_down.find("a", attrs={'href': True}).attrs["href"]
            pos = str(down).rfind("/") + 1
            packge_name = str(down)[pos:]
            download_page_url = "https://www.apkhere.com" + down

            # 获取软件版本号
            version_name = tr.find("em", {"class": "ver"}).get_text()

            # 获取软件大小
            size = tr.find("em", {"class": "size"}).get_text()

            # 获取软件描述
            des = tr.find("p").get_text()

            # 获取应用图标图片地址
            td_icon = tr.find("td", {"class": "icon"})
            icon = td_icon.find("img", attrs={'src': True}).attrs["src"]

            # 将爬取的每一项结果保存到字典
            map = {}
            map["title"] = title    #软件名字
            map["packge_name"] = packge_name    #软件包名
            map["version_name"] = version_name  #软件版本号
            map["size"] = size  #软件大小
            map["description"] = des    #软件简介
            map["classification"] = classification  #软件分类
            map["download_page_url"] = download_page_url    #软件下载页链接
            map["icon_link"] = icon     #软件图标链接
            map["type"] = type          #软件类型
            # 将保存数据的字典保存到列表
            list.append(map)

        #将爬取的数据写入到数据库
        self.mysql_util.write_to_sql(list)

    #运行爬虫
    def start_spider(self):
        url = 'https://www.apkhere.com/apk'
        html = self.get_html(url)
        # 获取所有的软件分类及相应的网址
        mainSide = html.find_all("dt")

        for dt in mainSide:
            short_link = str(dt.find("a", attrs={'href': True}).attrs["href"]).strip()
            #判断软件类型，应用或者游戏
            type = "应用"
            if short_link.startswith("/game/"):
                type = "游戏"
            #获取软件分类
            classification = dt.find('a').get_text()
            #获取该分类的完整的网址
            link = "https://www.apkhere.com" + short_link
            #爬取该分类网页中的数据
            self.get_apps_info(link, classification, type)
            #每爬取一个分类就睡眠10秒
            time.sleep(10)

        #爬取完毕，关闭数据库连接
        self.mysql_util.close_mysql()