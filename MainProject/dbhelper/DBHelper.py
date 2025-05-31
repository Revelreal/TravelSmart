import toml
from pymysql import cursors, connect


def load_db_config(filename="db_config.toml"):
    config = toml.load(filename)
    return config["database"]


class DBHelper:
    def __init__(self, config_path="../../db_config.toml"):
        db_conf = load_db_config(config_path)
        host = db_conf.get("host")
        port = db_conf.get("port")
        user = db_conf.get("user")
        password = db_conf.get("password")
        database = db_conf.get("database")
        charset = db_conf.get("charset", "utf8mb4")

        # 先连不带database参数，检查/创建数据库
        temp_conn = connect(
            host=host,
            port=port,
            user=user,
            password=password,
            charset=charset,
            autocommit=True
        )
        temp_cursor = temp_conn.cursor()
        temp_cursor.execute("SHOW DATABASES LIKE %s;", (database,))
        result = temp_cursor.fetchone()
        if not result:
            temp_cursor.execute(f"CREATE DATABASE {database} DEFAULT CHARSET {charset};")
            print(f"已创建数据库 {database}")
        temp_cursor.close()
        temp_conn.close()

        # 再连新数据库
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

    # 以下方法与你之前的定义一致...

    def query(self, sql, params=None):
        self.cursor.execute(sql, params or ())
        return self.cursor.fetchall()

    def execute(self, sql, params=None):
        result = self.cursor.execute(sql, params or ())
        self.conn.commit()
        return result

    def executemany(self, sql, param_list):
        result = self.cursor.executemany(sql, param_list)
        self.conn.commit()
        return result

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def fetchone(self, sql, params=None):
        self.cursor.execute(sql, params or ())
        return self.cursor.fetchone()

    # 注册用户
    def create_user(self, username, password, nickname=None, avatar=None, phone=None, email=None, city=None):
        # 查询用户是否已存在
        exists_sql = "SELECT id FROM Users WHERE username=%s;"
        if self.fetchone(exists_sql, (username,)):
            return False, "用户已存在"
        insert_sql = '''
                     INSERT INTO Users (username, password, nickname, avatar, phone, email, city)
                     VALUES (%s, %s, %s, %s, %s, %s, %s) \
                     '''
        self.execute(insert_sql, (username, password, nickname, avatar, phone, email, city))
        return True, "注册成功"

        # 校验用户

    def verify_user(self, username, password):
        check_sql = "SELECT id FROM Users WHERE username=%s AND password=%s;"
        result = self.fetchone(check_sql, (username, password))
        if not result:
            # 判断具体失败原因
            sql = "SELECT id FROM Users WHERE username=%s;"
            if not self.fetchone(sql, (username,)):
                return False, "用户不存在"
            else:
                return False, "密码错误"
        return True, "登录成功"


# 以下为创建表的函数，可根据需要调用
def create_spots_table(m_db):
    create_sql = '''
    CREATE TABLE IF NOT EXISTS Spots (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        address VARCHAR(255),
        longitude DECIMAL(10,6),
        latitude DECIMAL(10,6),
        type VARCHAR(50),
        images JSON,
        open_time VARCHAR(100),
        city VARCHAR(50),
        recommend_level INT DEFAULT 0
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    '''
    m_db.execute(create_sql)
    print("Spots表创建完成")


def create_foods_table(m_db):
    create_sql = '''
    CREATE TABLE IF NOT EXISTS Foods (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        address VARCHAR(255),
        longitude DECIMAL(10,6),
        latitude DECIMAL(10,6),
        type VARCHAR(50),
        images JSON,
        city VARCHAR(50),
        recommend_level INT DEFAULT 0
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    '''
    m_db.execute(create_sql)
    print("Foods表创建完成")


def create_routes_table(m_db):
    create_sql = '''
    CREATE TABLE IF NOT EXISTS Routes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        start_spot_id INT,
        end_spot_id INT,
        waypoints JSON,
        distance FLOAT,
        duration INT,
        route_type VARCHAR(50),
        ai_feature JSON,
        INDEX idx_start_spot (start_spot_id),
        INDEX idx_end_spot (end_spot_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    '''
    m_db.execute(create_sql)
    print("Routes表创建完成")


def create_users_table(m_db):
    create_sql = '''
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
        online_status TINYINT DEFAULT 0 COMMENT '0离线 1在线',
        last_active_time DATETIME DEFAULT NULL COMMENT '最近活动时间'
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    '''
    m_db.execute(create_sql)
    print("Users表创建完成")


def create_comments_table(m_db):
    create_sql = '''
    CREATE TABLE IF NOT EXISTS Comments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        target_id INT NOT NULL,
        target_type VARCHAR(20) NOT NULL,
        content TEXT,
        rating INT,
        create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_user_id (user_id),
        INDEX idx_target (target_id, target_type)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    '''
    m_db.execute(create_sql)
    print("Comments表创建完成")


if __name__ == "__main__":
     db = DBHelper()
#     create_spots_table(db)
#     create_foods_table(db)
#     create_routes_table(db)
#     create_users_table(db)
#     create_comments_table(db)
#     print(db.query("SHOW TABLES;"))
     db.query("SELECT * FROM Users;")
     db.close()
