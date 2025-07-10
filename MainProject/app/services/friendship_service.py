# MainProject/app/services/friendship_service.py
import logging

from MainProject.dbhelper.SQLHelper import SQLHelper


class FriendshipService:
    def __init__(self):
        self.db = SQLHelper()

    def get_friends(self, user_id, status='accepted'):
        """获取用户的好友列表"""
        sql = """
              SELECT f.id, \
                     f.friend_id, \
                     f.status, \
                     f.created_at,
                     u.username, \
                     u.nickname, \
                     u.avatar
              FROM Friendships f
                       JOIN Users u ON f.friend_id = u.id
              WHERE f.user_id = %s \
                AND f.status = %s
              ORDER BY u.username \
              """
        return self.db.query(sql, (user_id, status))

    def get_friend_requests(self, user_id):
        """获取用户收到的好友请求"""
        sql = """
              SELECT f.id, \
                     f.user_id as sender_id, \
                     f.created_at,
                     u.username, \
                     u.nickname, \
                     u.avatar
              FROM Friendships f
                       JOIN Users u ON f.user_id = u.id
              WHERE f.friend_id = %s \
                AND f.status = 'pending'
              ORDER BY f.created_at DESC \
              """
        return self.db.query(sql, (user_id,))

    def send_friend_request(self, user_id, friend_id):
        """发送好友请求"""
        # 检查是否已经是好友或已发送请求
        check_sql = """
                    SELECT id, status \
                    FROM Friendships
                    WHERE (user_id = %s AND friend_id = %s) \
                       OR (user_id = %s AND friend_id = %s) \
                    """
        existing = self.db.query(check_sql, (user_id, friend_id, friend_id, user_id))

        if existing:
            for record in existing:
                if record['status'] == 'accepted':
                    return False, "已经是好友关系"
                elif record['status'] == 'pending':
                    return False, "已发送过好友请求"
                elif record['status'] == 'blocked':
                    return False, "无法添加该用户为好友"

        # 发送好友请求
        sql = "INSERT INTO Friendships (user_id, friend_id) VALUES (%s, %s)"
        try:
            self.db.execute(sql, (user_id, friend_id))
            return True, "好友请求已发送"
        except Exception as e:
            return False, f"发送好友请求失败: {str(e)}"

    def accept_friend_request(self, request_id, user_id):
        """接受好友请求"""
        # 验证请求是否存在且发送给了当前用户
        check_sql = "SELECT user_id FROM Friendships WHERE id = %s AND friend_id = %s AND status = 'pending'"
        request = self.db.fetchone(check_sql, (request_id, user_id))

        if not request:
            return False, "好友请求不存在或已处理"

        # 更新请求状态为已接受
        update_sql = "UPDATE Friendships SET status = 'accepted' WHERE id = %s"

        # 创建反向好友关系
        sender_id = request['user_id']
        insert_sql = "INSERT INTO Friendships (user_id, friend_id, status) VALUES (%s, %s, 'accepted')"

        try:
            self.db.execute(update_sql, (request_id,))
            self.db.execute(insert_sql, (user_id, sender_id))
            return True, "已接受好友请求"
        except Exception as e:
            return False, f"处理好友请求失败: {str(e)}"

    def reject_friend_request(self, request_id, user_id):
        """拒绝好友请求"""
        # 验证请求是否存在且发送给了当前用户
        check_sql = "SELECT id FROM Friendships WHERE id = %s AND friend_id = %s AND status = 'pending'"
        request = self.db.fetchone(check_sql, (request_id, user_id))

        if not request:
            return False, "好友请求不存在或已处理"

        # 删除请求
        delete_sql = "DELETE FROM Friendships WHERE id = %s"

        try:
            self.db.execute(delete_sql, (request_id,))
            return True, "已拒绝好友请求"
        except Exception as e:
            return False, f"处理好友请求失败: {str(e)}"

    def remove_friend(self, user_id, friend_id):
        """删除好友关系"""
        sql = """
              DELETE \
              FROM Friendships
              WHERE (user_id = %s AND friend_id = %s) \
                 OR (user_id = %s AND friend_id = %s) \
              """
        try:
            self.db.execute(sql, (user_id, friend_id, friend_id, user_id))
            return True, "已删除好友关系"
        except Exception as e:
            return False, f"删除好友关系失败: {str(e)}"

    def block_user(self, user_id, blocked_user_id):
        """屏蔽用户"""
        # 先删除现有的任何关系
        self.remove_friend(user_id, blocked_user_id)

        # 添加屏蔽关系
        sql = "INSERT INTO Friendships (user_id, friend_id, status) VALUES (%s, %s, 'blocked')"
        try:
            self.db.execute(sql, (user_id, blocked_user_id))
            return True, "已屏蔽该用户"
        except Exception as e:
            return False, f"屏蔽用户失败: {str(e)}"

    def unblock_user(self, user_id, blocked_user_id):
        """解除屏蔽"""
        sql = "DELETE FROM Friendships WHERE user_id = %s AND friend_id = %s AND status = 'blocked'"
        try:
            self.db.execute(sql, (user_id, blocked_user_id))
            return True, "已解除屏蔽"
        except Exception as e:
            return False, f"解除屏蔽失败: {str(e)}"

    def get_blocked_users(self, user_id):
        """获取已屏蔽的用户列表"""
        sql = """
              SELECT f.id, \
                     f.friend_id, \
                     f.created_at,
                     u.username, \
                     u.nickname, \
                     u.avatar
              FROM Friendships f
                       JOIN Users u ON f.friend_id = u.id
              WHERE f.user_id = %s \
                AND f.status = 'blocked'
              ORDER BY f.created_at DESC \
              """
        return self.db.query(sql, (user_id,))

    def check_friendship_status(self, user_id, other_user_id):
        """检查两个用户之间的关系状态"""
        sql = """
              SELECT status \
              FROM Friendships
              WHERE user_id = %s \
                AND friend_id = %s \
              """
        result = self.db.fetchone(sql, (user_id, other_user_id))
        if result:
            return result['status']

        # 检查反向关系
        result = self.db.fetchone(sql, (other_user_id, user_id))
        if result and result['status'] == 'pending':
            return 'request_received'

        return 'none'

    def get_user_id_by_username(self, username):
        """根据用户名获取用户ID"""
        try:
            sql = "SELECT id FROM Users WHERE username = %s"
            result = self.db.fetchone(sql, (username,))
            return result[0] if result else None
        except Exception as e:
            logging.error(f"获取用户ID失败: {str(e)}")
            return None
