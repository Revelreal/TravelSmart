# MainProject/dbhelper/MONGOHelper.py
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

import pymongo
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

    # ====================== 新增方法 ======================
    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> Optional[str]:
        """插入单个文档"""
        try:
            collection = self.get_collection(collection_name)
            result = collection.insert_one(document)
            return str(result.inserted_id) if result.inserted_id else None
        except Exception as e:
            print(f"插入文档失败: {e}")
            return None

    def find_one(self, collection_name: str, filter_dict: Dict[str, Any],
                 projection: Optional[Dict[str, int]] = None) -> Optional[Dict[str, Any]]:
        """查找单个文档"""
        try:
            collection = self.get_collection(collection_name)
            return collection.find_one(filter_dict, projection)
        except Exception as e:
            print(f"查找文档失败: {e}")
            return None

    def update_one(self, collection_name: str, filter_dict: Dict[str, Any],
                   update_dict: Dict[str, Any], upsert: bool = False) -> bool:
        """更新单个文档"""
        try:
            collection = self.get_collection(collection_name)
            result = collection.update_one(filter_dict, {"$set": update_dict}, upsert=upsert)
            return result.modified_count > 0 or (upsert and result.upserted_id is not None)
        except Exception as e:
            print(f"更新文档失败: {e}")
            return False

    def update_many(self, collection_name: str, filter_dict: Dict[str, Any],
                    update_dict: Dict[str, Any]) -> int:
        """更新多个文档"""
        try:
            collection = self.get_collection(collection_name)
            result = collection.update_many(filter_dict, {"$set": update_dict})
            return result.modified_count
        except Exception as e:
            print(f"批量更新文档失败: {e}")
            return 0

    def delete_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> bool:
        """删除单个文档"""
        try:
            collection = self.get_collection(collection_name)
            result = collection.delete_one(filter_dict)
            return result.deleted_count > 0
        except Exception as e:
            print(f"删除文档失败: {e}")
            return False

    def delete_many(self, collection_name: str, filter_dict: Dict[str, Any]) -> int:
        """删除多个文档"""
        try:
            collection = self.get_collection(collection_name)
            result = collection.delete_many(filter_dict)
            return result.deleted_count
        except Exception as e:
            print(f"批量删除文档失败: {e}")
            return 0

    def count_documents(self, collection_name: str, filter_dict: Dict[str, Any] = None) -> int:
        """统计文档数量"""
        try:
            collection = self.get_collection(collection_name)
            return collection.count_documents(filter_dict or {})
        except Exception as e:
            print(f"统计文档数量失败: {e}")
            return 0

    def aggregate(self, collection_name: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """聚合查询"""
        try:
            collection = self.get_collection(collection_name)
            return list(collection.aggregate(pipeline))
        except Exception as e:
            print(f"聚合查询失败: {e}")
            return []

    def create_index(self, collection_name: str,
                     keys: Union[str, List[tuple], List[str]],
                     **kwargs) -> Optional[str]:
        """
        创建索引

        Args:
            collection_name: 集合名称
            keys: 索引键，可以是：
                - 字符串: "field_name" (单字段升序)
                - 字符串列表: ["field1", "field2"] (多字段升序)
                - 元组列表: [("field1", 1), ("field2", -1)] (指定排序方向)
            **kwargs: 其他索引选项

        Returns:
            索引名称或None
        """
        try:
            collection = self.get_collection(collection_name)

            # 处理不同类型的keys参数
            if isinstance(keys, str):
                # 单个字段名，默认升序
                index_spec = keys
            elif isinstance(keys, list):
                if len(keys) == 0:
                    print("索引键列表不能为空")
                    return None

                # 检查列表中的元素类型
                if isinstance(keys[0], str):
                    # 字符串列表，转换为升序索引
                    index_spec = [(key, 1) for key in keys]
                elif isinstance(keys[0], tuple):
                    # 元组列表，直接使用
                    index_spec = keys
                else:
                    print(f"不支持的索引键类型: {type(keys[0])}")
                    return None
            else:
                print(f"不支持的索引键类型: {type(keys)}")
                return None

            # 创建索引
            result = collection.create_index(index_spec, **kwargs)
            print(f"索引创建成功: {result}")
            return result

        except Exception as e:
            print(f"创建索引失败: {e}")
            return None

    def drop_index(self, collection_name: str, index_name: str) -> bool:
        """删除索引"""
        try:
            collection = self.get_collection(collection_name)
            collection.drop_index(index_name)
            return True
        except Exception as e:
            print(f"删除索引失败: {e}")
            return False

    def get_current_time(self) -> datetime:
        """获取当前时间"""
        return datetime.now()


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
