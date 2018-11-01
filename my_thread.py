import threading

"""
自定义线程类
"""
#继承threading.Thread类，自定义线程类
class MyThread(threading.Thread):
    #构造函数
    def __init__(self, func):
        # 调用父类的构造函数
        super(MyThread, self).__init__()
        # 传入线程函数
        self.func = func

    #run方法
    def run(self):
        # 运行传入的线程函数
        try:
            self.func()
        except:
            pass