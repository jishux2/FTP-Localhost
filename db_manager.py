# db_manager.py
# 这是一个管理数据库的类，使用sqlite3模块，可以创建和操作一个本地的数据库文件
import sqlite3

# 定义一个常量，用于存储数据库文件的名称
DB_NAME = "ftp_users.db"

# 定义一个常量，用于存储用户表的名称
TABLE_NAME = "users"

# 定义一个常量，用于存储用户表的字段
FIELDS = ["username", "password"]

# 定义一个管理数据库的类
class DBManager:

    # 初始化方法，创建或打开数据库文件，创建或检查用户表
    def __init__(self):
        # 创建或打开数据库文件
        self.conn = sqlite3.connect(DB_NAME)
        # 创建一个游标对象，用于执行SQL语句
        self.cursor = self.conn.cursor()
        # 创建或检查用户表
        self.create_table()

    # 创建或检查用户表的方法
    def create_table(self):
        # 拼接一个创建用户表的SQL语句
        sql = f"CREATE TABLE IF NOT EXISTS {TABLE_NAME} ("
        for field in FIELDS:
            sql += f"{field} TEXT NOT NULL, "
        sql = sql[:-2] + ")"
        # 执行SQL语句
        self.cursor.execute(sql)
        # 提交事务
        self.conn.commit()

    # 关闭数据库连接的方法
    def close(self):
        # 关闭游标对象
        self.cursor.close()
        # 关闭连接对象
        self.conn.close()

    # 查询用户是否存在的方法，接受用户名和密码作为参数，返回一个布尔值
    def query_user(self, username, password):
        # 拼接一个查询用户的SQL语句
        sql = f"SELECT * FROM {TABLE_NAME} WHERE username = ? AND password = ?"
        # 执行SQL语句，传入参数
        self.cursor.execute(sql, (username, password))
        # 获取查询结果
        result = self.cursor.fetchone()
        # 如果结果不为空，表示用户存在，返回True
        if result:
            return True
        # 否则，表示用户不存在，返回False
        else:
            return False

    # 插入用户的方法，接受用户名和密码作为参数，返回一个布尔值，表示是否插入成功
    def insert_user(self, username, password):
        # 拼接一个查询用户名是否存在的SQL语句
        sql = f"SELECT * FROM {TABLE_NAME} WHERE username = ?"
        # 执行SQL语句，传入参数
        self.cursor.execute(sql, (username,))
        # 获取查询结果
        result = self.cursor.fetchone()
        # 如果结果不为空，表示用户名已存在，返回False，表示插入失败
        if result:
            return False
        # 否则，表示用户名不存在，可以插入
        # 拼接一个插入用户的SQL语句
        sql = f"INSERT INTO {TABLE_NAME} ("
        for field in FIELDS:
            sql += f"{field}, "
        sql = sql[:-2] + ") VALUES ("
        for field in FIELDS:
            sql += "?, "
        sql = sql[:-2] + ")"
        # 尝试执行SQL语句，传入参数
        try:
            self.cursor.execute(sql, (username, password))
            # 提交事务
            self.conn.commit()
            # 返回True，表示插入成功
            return True
        # 如果发生异常，回滚事务
        except Exception as e:
            self.conn.rollback()
            # 返回False，表示插入失败
            return False