import toml
from pymongo import MongoClient
import os


def load_mongodb_config(filename="../../db_config.toml"):
    abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), filename))
    config = toml.load(abs_path)
    return config["mongodb"]


class MongoHelper:
    def __init__(self, config_path="../../db_config.toml"):
        conf = load_mongodb_config(config_path)
        host = conf["host"]
        port = conf["port"]
        username = conf.get("username", "")
        password = conf.get("password", "")
        db_name = conf.get("database", "test")
        if username and password:
            uri = f"mongodb://{username}:{password}@{host}:{port}"
        else:
            uri = f"mongodb://{host}:{port}"
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def get_collection(self, name):
        return self.db[name]

    def create_collection_with_indexes(self, name, indexes=None):
        # collection不会重复创建；可创建所需索引
        if name not in self.db.list_collection_names():
            self.db.create_collection(name)
            print(f"集合 {name} 已创建")
        else:
            print(f"集合 {name} 已存在")
        if indexes:
            col = self.get_collection(name)
            for idx in indexes:
                col.create_index(idx)
            print(f"集合 {name} 索引已建立：{indexes}")

    def drop_collection(self, name):
        self.db.drop_collection(name)
        print(f"集合 {name} 已删除")

    def insert_test(self, col_name, doc):
        col = self.get_collection(col_name)
        col.insert_one(doc)
        print(f"向 {col_name} 插入了测试文档")

    def close(self):
        self.client.close()


# ----- 各表/集合的“建表”和“删表”函数 -----

def create_spots_collection(mh: MongoHelper):
    indexes = [
        [("city", 1)],
        [("name", 1)]
    ]
    mh.create_collection_with_indexes("Spots", indexes)


def drop_spots_collection(mh: MongoHelper):
    mh.drop_collection("Spots")


def create_foods_collection(mh: MongoHelper):
    indexes = [
        [("city", 1)],
        [("name", 1)]
    ]
    mh.create_collection_with_indexes("Foods", indexes)


def drop_foods_collection(mh: MongoHelper):
    mh.drop_collection("Foods")


def create_routes_collection(mh: MongoHelper):
    indexes = [
        [("name", 1)],
        [("start_spot_id", 1)],
        [("end_spot_id", 1)]
    ]
    mh.create_collection_with_indexes("Routes", indexes)


def drop_routes_collection(mh: MongoHelper):
    mh.drop_collection("Routes")


def create_comments_collection(mh: MongoHelper):
    indexes = [
        [("user_id", 1)],
        [("target_id", 1), ("target_type", 1)]
    ]
    mh.create_collection_with_indexes("Comments", indexes)


def drop_comments_collection(mh: MongoHelper):
    mh.drop_collection("Comments")


if __name__ == "__main__":
    mh = MongoHelper()
    # 建表：
    create_spots_collection(mh)
    create_foods_collection(mh)
    create_routes_collection(mh)
    create_comments_collection(mh)
    # 插入一条测试数据（任选一表演示）
    mh.insert_test("Spots", {
        "name": "外滩",
        "description": "上海著名地标",
        "address": "上海市黄浦区中山东一路",
        "longitude": 121.490317,
        "latitude": 31.241701,
        "type": "地标",
        "images": [],
        "open_time": "全天",
        "city": "上海",
        "recommend_level": 5
    })
    # 读取数据
    create_routes_collection(mh)
    col = mh.get_collection("Spots")
    for doc in col.find():
        print(doc)
    # 删表示例（启用请解除注释）
    # drop_spots_collection(mh)
    # drop_foods_collection(mh)
    # drop_routes_collection(mh)
    # drop_comments_collection(mh)
    mh.close()
