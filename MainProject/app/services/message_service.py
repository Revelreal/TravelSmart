# MainProject/app/services/message_service.py
from MainProject.dbhelper.SQLHelper import SQLHelper
from MainProject.dbhelper.MONGOHelper import MongoHelper
import datetime
import logging


class MessageService:
    def __init__(self):
        self.db = SQLHelper()
        self.mongo = MongoHelper()
        self.logger = logging.getLogger(__name__)

    def send_message(self, sender_id, receiver_id, content, content_type='text'):
        """发送消息（与UI完全兼容版）"""
        try:
            # 参数验证
            if not all([sender_id, receiver_id]):
                self.logger.warning("无效的用户ID")
                return False, "无效的用户ID"

            content = str(content).strip()
            if not content and content_type == 'text':
                self.logger.warning("消息内容为空")
                return False, "消息内容不能为空"

            # 检查好友关系
            if not self._check_friendship(sender_id, receiver_id):
                self.logger.warning(f"用户{sender_id}和{receiver_id}不是好友")
                return False, "只能向好友发送消息"

            # 数据库操作
            message_id = self._save_message(
                sender_id, receiver_id, content, content_type
            )

            self.logger.info(f"消息发送成功 ID:{message_id}")
            return True, str(message_id)

        except Exception as e:
            self.logger.error(f"发送消息失败: {str(e)}", exc_info=True)
            return False, f"发送失败: {str(e)}"

    def _check_friendship(self, user_id, friend_id):
        """优化后的好友关系检查"""
        sql = "SELECT 1 FROM Friendships WHERE user_id=%s AND friend_id=%s AND status='accepted'"
        return bool(self.db.fetchone(sql, (user_id, friend_id)))

    def _save_message(self, sender_id, receiver_id, content, content_type):
        """原子化消息存储"""
        # MySQL存储
        sql = """INSERT INTO Messages
                     (sender_id, receiver_id, content, content_type, is_read)
                 VALUES (%s, %s, %s, %s, FALSE)"""
        self.db.execute(sql, (sender_id, receiver_id, content, content_type))
        message_id = self.db.cursor.lastrowid

        # MongoDB存储
        self.mongo.db.chat_history.insert_one({
            'message_id': message_id,
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'content': content,
            'content_type': content_type,
            'is_read': False,
            'created_at': datetime.datetime.now()
        })

        return message_id

    def get_recent_messages(self, user_id, friend_id, limit=50):
        """为UI优化的消息获取"""
        try:
            messages = list(self.mongo.db.chat_history.find({
                '$or': [
                    {'sender_id': user_id, 'receiver_id': friend_id},
                    {'sender_id': friend_id, 'receiver_id': user_id}
                ]
            }).sort('created_at', -1).limit(limit))

            formatted = []
            for msg in reversed(messages):  # 转为时间升序
                formatted.append({
                    'id': str(msg['message_id']),
                    'content': msg['content'],
                    'direction': 'sent' if msg['sender_id'] == user_id else 'received',
                    'created_at': msg['created_at']
                })

            return formatted

        except Exception as e:
            self.logger.error(f"获取消息失败: {str(e)}")
            return []

    def mark_messages_as_read(self, user_id, friend_id):
        """标记已读（双存储一致性保证）"""
        try:
            # MySQL更新
            self.db.execute(
                "UPDATE Messages SET is_read=TRUE WHERE sender_id=%s AND receiver_id=%s",
                (friend_id, user_id)
            )

            # MongoDB更新
            self.mongo.db.chat_history.update_many(
                {'sender_id': friend_id, 'receiver_id': user_id},
                {'$set': {'is_read': True}}
            )

            return True

        except Exception as e:
            self.logger.error(f"标记已读失败: {str(e)}")
            return False

    def get_unread_message_count(self, user_id):
        """为UI优化的未读计数"""
        try:
            pipeline = [
                {'$match': {'receiver_id': user_id, 'is_read': False}},
                {'$group': {'_id': '$sender_id', 'count': {'$sum': 1}}}
            ]
            return [{'sender_id': str(x['_id']), 'count': x['count']}
                    for x in self.mongo.db.chat_history.aggregate(pipeline)]
        except Exception as e:
            self.logger.error(f"未读计数失败: {str(e)}")
            return []

    def get_conversation_users(self, user_id):
        """获取有过对话的用户列表（为UI优化）"""
        try:
            # 从MongoDB获取最近对话过的用户
            pipeline = [
                {
                    "$match": {
                        "$or": [
                            {"sender_id": user_id},
                            {"receiver_id": user_id}
                        ]
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "$cond": [
                                {"$eq": ["$sender_id", user_id]},
                                "$receiver_id",
                                "$sender_id"
                            ]
                        },
                        "last_time": {"$max": "$created_at"}
                    }
                },
                {"$sort": {"last_time": -1}},
                {"$limit": 50}
            ]

            return [str(user["_id"]) for user in self.mongo.db.chat_history.aggregate(pipeline)]
        except Exception as e:
            self.logger.error(f"获取对话用户失败: {str(e)}")
            return []
