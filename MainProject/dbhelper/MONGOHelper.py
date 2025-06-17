import pymongo
from datetime import datetime
import toml
import os

from pymongo import MongoClient


def load_mongodb_config(filename="../config.toml"):
    abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), filename))
    config = toml.load(abs_path)
    return config["mongodb"]


class MongoHelper:
    def __init__(self, config_path="../../config.toml"):
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

        # 构建连接URI
        if username and password:
            uri = f"mongodb://{username}:{password}@{host}:{port}"
        else:
            uri = f"mongodb://{host}:{port}"

        self.client = pymongo.MongoClient(uri)
        self.db = self.client[db_name]
        print(f"已连接到数据库: {db_name}")

    def get_collection(self, name):
        return self.db[name]

    def create_collection_with_indexes(self, name, indexes=None):
        # 创建集合（如果不存在）
        if name not in self.db.list_collection_names():
            self.db.create_collection(name)
            print(f"集合 {name} 已创建")
        else:
            print(f"集合 {name} 已存在")

        # 创建索引
        if indexes:
            col = self.get_collection(name)
            for idx in indexes:
                col.create_index(idx)
            print(f"集合 {name} 索引已建立：{indexes}")

    def drop_collection(self, name):
        if name in self.db.list_collection_names():
            self.db.drop_collection(name)
            print(f"集合 {name} 已删除")
        else:
            print(f"集合 {name} 不存在，无需删除")

    def close(self):
        self.client.close()
        print("数据库连接已关闭")


def create_reviews_collection(mongo_helper):
    """创建评价表"""
    indexes = [
        [("user_id", 1)],
        [("target_id", 1)],
        [("target_type", 1)],
        [("created_at", -1)]
    ]
    mongo_helper.create_collection_with_indexes("Reviews", indexes)


def get_target_reviews(mongo_helper, target_id, target_type=None, limit=10, skip=0):
    """获取指定目标的评价"""
    collection = mongo_helper.get_collection("Reviews")
    query = {"target_id": target_id}
    if target_type:
        query["target_type"] = target_type

    # 按时间倒序排列
    reviews = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
    return list(reviews)


def get_user_reviews(mongo_helper, user_id, limit=10, skip=0):
    """获取用户的所有评价"""
    collection = mongo_helper.get_collection("Reviews")
    reviews = collection.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit)
    return list(reviews)


# 主程序测试
if __name__ == "__main__":
    pass
