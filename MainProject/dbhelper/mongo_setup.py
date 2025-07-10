# MainProject/dbhelper/mongo_setup.py
from MainProject.dbhelper.MONGOHelper import MongoHelper


class MongoSetup:
    def __init__(self):
        self.mongo = MongoHelper()

    def setup_collections(self):
        """设置MongoDB集合"""
        # 创建聊天历史集合（用于存储大量聊天记录）
        self.mongo.db.create_collection("chat_history")

        # 创建旅行动态详情集合（用于存储富文本和复杂媒体内容）
        self.mongo.db.create_collection("travel_post_details")

        # 创建用户活动日志集合
        self.mongo.db.create_collection("user_activity_logs")

        # 创建通知集合
        self.mongo.db.create_collection("notifications")

        # 为相关字段创建索引
        self.mongo.db.chat_history.create_index([("sender_id", 1), ("receiver_id", 1)])
        self.mongo.db.chat_history.create_index([("created_at", -1)])
        self.mongo.db.travel_post_details.create_index([("post_id", 1)], unique=True)
        self.mongo.db.user_activity_logs.create_index([("user_id", 1)])
        self.mongo.db.notifications.create_index([("user_id", 1), ("is_read", 1)])

        print("MongoDB集合设置完成")

if __name__ == '__main__':
    mongo = MongoSetup()
    mongo.setup_collections()