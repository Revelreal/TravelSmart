import toml
import os
from pymysql import connect, cursors


def load_db_config(filename="../../db_config.toml"):
    abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), filename))
    config = toml.load(abs_path)
    return config["mysql"]


class SQLHelper:
    def __init__(self, config_path="../../db_config.toml"):
        db_conf = load_db_config(config_path)
        host = db_conf.get("host")
        port = db_conf.get("port")
        user = db_conf.get("user")
        password = db_conf.get("password")
        database = db_conf.get("database")
        charset = db_conf.get("charset", "utf8mb4")
        self.conn = connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset=charset,
            autocommit=True
        )
        self.cursor = self.conn.cursor(cursors.DictCursor)

    def execute(self, sql, params=None):
        self.cursor.execute(sql, params or ())
        self.conn.commit()

    def executemany(self, sql, param_list):
        self.cursor.executemany(sql, param_list)
        self.conn.commit()

    def query(self, sql, params=None):
        self.cursor.execute(sql, params or ())
        return self.cursor.fetchall()

    def fetchone(self, sql, params=None):
        self.cursor.execute(sql, params or ())
        return self.cursor.fetchone()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def verify_user(self, username, password):
        """
        验证用户名密码
        返回：(bool, 信息/字典)
        - 成功：True, 用户信息字典（含role_name/status_name等）
        - 失败：False, 错误字符串
        """
        # 联表查出用户所有关心信息
        user = self.fetchone(
            '''
            SELECT u.id, u.username, u.nickname, r.role_name, s.status_name, u.password
            FROM Users u
                     LEFT JOIN Roles r ON u.role_id = r.id
                     LEFT JOIN UserStatus s ON u.status_id = s.id
            WHERE u.username = %s
            ''', (username,)
        )
        if not user:
            return False, "用户不存在"
        # 账户状态判断
        if user.get("status_name") == "封禁":
            return False, "用户已被封禁，如有疑问请联系管理员"
        if user.get("status_name") == "禁言":
            # 禁言通常只是限制发言，可允许登录
            pass
        # 密码判断
        if user["password"] != password:
            return False, "密码错误"
        # 登录成功，返回所有关键信息（去掉密码字段）
        user_info = user.copy()
        user_info.pop("password", None)
        return True, user_info

    # --------- 建表与删表相关 ---------
    def drop_all_tables(self):
        tables = ["Users", "UserStatus", "Roles"]
        for tbl in tables:
            try:
                self.execute(f"DROP TABLE IF EXISTS {tbl};")
                print(f"已删除表 {tbl}")
            except Exception as e:
                print(f"删除表 {tbl} 时异常: {e}")

    def create_userstatus_table(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS UserStatus (
            id INT AUTO_INCREMENT PRIMARY KEY,
            status_name VARCHAR(30) NOT NULL UNIQUE,
            description VARCHAR(255)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        '''
        self.execute(sql)
        print("UserStatus表创建完成")
        sql2 = "INSERT IGNORE INTO UserStatus (id, status_name, description) VALUES (1,'正常','正常用户'), (2,'禁言','无法发言'), (3,'封禁','禁用与踢出')"
        self.execute(sql2)
        print("UserStatus表初始化完成")

    def create_role_table(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS Roles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            role_name VARCHAR(30) NOT NULL UNIQUE,
            description VARCHAR(255)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        '''
        self.execute(sql)
        print("Roles表创建完成")
        sql2 = "INSERT IGNORE INTO Roles (id, role_name, description) VALUES (1,'root','最高权限'), (2,'admin','管理员'), (3,'user','普通用户')"
        self.execute(sql2)
        print("Roles表初始化完成")

    def create_users_table(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS Users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(128) NOT NULL,
            nickname VARCHAR(50),
            avatar VARCHAR(255),
            phone VARCHAR(20),
            email VARCHAR(100),
            city VARCHAR(50),
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_active_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            status_id INT DEFAULT 1,
            role_id INT DEFAULT 3,
            FOREIGN KEY(status_id) REFERENCES UserStatus(id) ON DELETE SET NULL ON UPDATE CASCADE,
            FOREIGN KEY(role_id) REFERENCES Roles(id)      ON DELETE SET NULL ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        '''
        self.execute(sql)
        print("Users表创建完成")

    # --- 用户插入与演示查询 ---
    def create_user(self, username, password, nickname="", phone=None, email=None, city=None, status_id=1, role_id=3):
        try:
            sql = '''
                  INSERT INTO Users (username, password, nickname, phone, email, city, status_id, role_id)
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s) \
                  '''
            self.execute(sql, (username, password, nickname, phone, email, city, status_id, role_id))
            print(f"添加用户 {username} 成功")
            return True, "添加成功"
        except Exception as e:
            print(f"添加用户 {username} 失败: {e}")
            return False, f"添加失败: {e}"

    def show_users(self):
        rows = self.query('''
            SELECT u.id, u.username, u.nickname, r.role_name, s.status_name, u.last_active_time
            FROM Users u
            LEFT JOIN Roles r ON u.role_id = r.id
            LEFT JOIN UserStatus s ON u.status_id = s.id
        ''')
        print("当前用户：")
        for row in rows:
            print(row)


if __name__ == "__main__":
    db = SQLHelper()
    # db.drop_all_tables()
    # db.create_userstatus_table()
    # db.create_role_table()
    # db.create_users_table()
    # 测试插入3种不同身份和状态的用户
    db.create_user("rootuser",  "pwroot",  "超级管理员", status_id=1, role_id=1)
    # db.create_user("admin001",  "pwadmin", "普通管理员", status_id=2, role_id=2)
    # db.create_user("tommy",     "pwuser",  "小明",       status_id=1, role_id=3)
    db.show_users()
    db.close()
