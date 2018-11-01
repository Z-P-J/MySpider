
import pymysql

"""
Mysql工具类，初始化数据库，建表和插入数据操作
"""
#自定义的mysql工具类，不具有通用性，仅本项目可用
class MysqlUtil:
    def __init__(self):
        #初始化连接并创建一张名为app_list表
        # 创建连接
        self.conn = pymysql.connect(
            host="localhost",       #本地服务器
            user="root",             #root用户
            password="zpj19990509", #数据库密码
            port=3306,                #默认端口
            charset="utf8",          #设置字符集
            db="my_spider"          #数据库名
        )

        # 使用cursor()方法获取操作游标
        cursor = self.conn.cursor()
        # 在my_spider数据库中创建一张名为app_list的表，用来存放数据
        sql = """create table if not exists app_list(
            id INT AUTO_INCREMENT PRIMARY KEY NOT NULL, 
            app_name VARCHAR(150), package_name VARCHAR(150), 
            version_name VARCHAR(50), app_size VARCHAR(50), 
            app_description VARCHAR(256), app_classification VARCHAR(30), 
            app_type VARCHAR(20), download_page_url VARCHAR(150),  
            icon_link VARCHAR(150))"""
        # 异常处理
        try:
            # 执行SQL语句
            cursor.execute(sql)
            pass
        except Exception as e:
            #打印错误信息
            print("建表失败！" + str(e))
        # 关闭操作游标
        cursor.close()

    def write_to_sql(self, list):
        # 打开数据库连接
        db = self.conn
        # 使用cursor()方法获取操作游标
        cursor = db.cursor()
        for i in range(0, len(list)):
            map = list[i]
            # SQL 插入语句
            sql = """INSERT INTO app_list(app_name, package_name, version_name, 
                    app_size, app_description, app_classification, app_type, download_page_url, icon_link)
                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            # 异常处理
            try:
                # 每次运行sql之前，ping一次，检查与数据库的连接是否断开，如果连接断开就重连。
                db.ping(reconnect=True)
                # 执行sql语句
                cursor.execute(
                    sql,
                    (
                        map["title"],
                        map["packge_name"],
                        map["version_name"],
                        map["size"],
                        map["description"],
                        map["classification"],
                        map["type"],
                        map["download_page_url"],
                        map["icon_link"]
                     )
                )
                # 提交到数据库执行
                db.commit()
                print('插入成功')
            except Exception as e:
                #插入出错时，数据库回滚，恢复数据到修改之前
                print("插入失败：" + str(e))
                db.rollback()
        #关闭操作游标
        cursor.close()

    def close_mysql(self):
        # 关闭数据库连接
        self.conn.close()