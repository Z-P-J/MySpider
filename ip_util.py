import queue
import time
from my_thread import MyThread
import requests
import random
from bs4 import BeautifulSoup

# 构造一个不限制大小的的队列
SHARE_Q = queue.Queue()
# 设置线程数
_WORKER_THREAD_NUM = 128

"""
代理IP工具类，爬取某网站上免费的代理IP，检测有效性并保存, 随机获取IP操作
"""
class IPUtil:
    #构造函数
    def __init__(self, ua_util):
        self.ua_util = ua_util
        # 用一个列表保存爬取的所有代理ip
        self.ips = []
        # 用一个列表保存有效的代理ip
        self.valid_ips = []
        #爬取网页获取代理ip
        self.get_ips()

    # 爬取http://www.xicidaili.com/ 网站获取免费高匿代理ip
    def get_ips(self):
        #高匿ip和普通ip各爬取前20页
        for i in range(2):
            short_link = "http://www.xicidaili.com/nn/"
            if i == 1:
                short_link = "http://www.xicidaili.com/nt/"
            for i in range(0, 20):
                # 设置请求链接和请求头
                #异常处理
                try:
                    #get请求获取网页
                    response = requests.get(short_link + str(i + 1),
                                            headers={'User-Agent': self.ua_util.random(), 'Connection': 'close'})
                except:
                    print("连接失败")
                    continue

                # 获取网页源码
                html = BeautifulSoup(response.text, "html.parser")
                ip_list = html.find("table", {"id": "ip_list"})
                trs = ip_list.find_all("tr")
                for tr in trs[1:]:
                    # 过滤掉响应速度和连接时间大于1秒的ip地址
                    bars = tr.find_all("div", {"class": "bar"})
                    flag = False
                    for bar in bars:
                        if not str(bar.attrs["title"]).startswith("0"):
                            flag = True
                            break
                    if flag:
                        continue

                    # 将ip地址和端口组合在一起
                    tds = tr.find_all("td")
                    addr = tds[1].get_text() + ":" + tds[2].get_text()
                    ip = {
                        'http': 'http://' + addr,
                        'https': 'https://' + addr
                    }
                    self.ips.append(ip)
        self.test_ip(self.ips)

    def test_ip(self, ips):
        #检查代理ip可用性
        print("检查代理ip可用性...共有" + str(len(ips)) + "个ip待检查")
        global SHARE_Q
        threads = []
        # 向队列中放入任务, 真正使用时, 应该设置为可持续的放入任务
        for task in range(0, len(ips)):
            SHARE_Q.put(ips[task])
        # 开启_WORKER_THREAD_NUM个线程
        for i in range(_WORKER_THREAD_NUM):
            thread = MyThread(self.worker)
            thread.start()  # 线程开始处理任务
            threads.append(thread)
        for thread in threads:
            thread.join()
        # 等待所有任务完成
        SHARE_Q.join()
        print("可用代理ip:" + str(self.valid_ips))

    def do_something(self, item):
        #运行逻辑
        print("检查第" + str(self.ips.index(item) + 1) + "个ip")
        #初步检查代理IP可用性
        # 异常处理
        try:
            requests.get("http://icanhazip.com", headers={'User-Agent': self.ua_util.random()},
                         proxies=item, timeout=2)
            self.valid_ips.append(item)
        except:
            #代理IP失效
            pass

    def worker(self):
        """
        主要用来写工作逻辑, 只要队列不空持续处理
        队列为空时, 检查队列, 由于Queue中已经包含了wait,
        notify和锁, 所以不需要在取任务或者放任务的时候加锁解锁
        """
        global SHARE_Q
        running = True
        while running:
            if not SHARE_Q.empty():
                #获得任务
                item = SHARE_Q.get()
                #检查ip可用性
                self.do_something(item)
                time.sleep(1)
                SHARE_Q.task_done()
            else:
                running = False


    def random(self):
        #随机获取ip
        return random.choice(self.valid_ips)

    def remove_ip(self, ip):
        #移除无效ip
        self.valid_ips.remove(ip)