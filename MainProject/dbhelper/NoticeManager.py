import toml
import os
import pymysql
from pymysql import connect, cursors
from datetime import datetime, timedelta


class NoticeManager:
    def __init__(self, config_path="../../config.toml"):
        """
        初始化公告管理器

        Args:
            config_path: 配置文件路径
        """
        # 加载数据库配置
        self.config_path = config_path
        self._connect_db()

        # 确保相关表存在
        self._ensure_tables_exist()

    def _load_db_config(self):
        """加载数据库配置"""
        abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), self.config_path))
        config = toml.load(abs_path)
        return config["mysql"]

    def _connect_db(self):
        """连接到数据库"""
        db_conf = self._load_db_config()
        self.conn = connect(
            host=db_conf.get("host"),
            port=db_conf.get("port"),
            user=db_conf.get("user"),
            password=db_conf.get("password"),
            database=db_conf.get("database"),
            charset=db_conf.get("charset", "utf8mb4"),
            autocommit=True
        )
        self.cursor = self.conn.cursor(cursors.DictCursor)

    def _ensure_tables_exist(self):
        """确保公告相关的表存在，如果不存在则创建"""
        # 公告表
        create_notices_table = """
                               CREATE TABLE IF NOT EXISTS notices \
                               ( \
                                   id \
                                   INT \
                                   AUTO_INCREMENT \
                                   PRIMARY \
                                   KEY, \
                                   title \
                                   VARCHAR \
                               ( \
                                   255 \
                               ) NOT NULL,
                                   content TEXT NOT NULL,
                                   type VARCHAR \
                               ( \
                                   50 \
                               ) DEFAULT 'info',
                                   priority INT DEFAULT 0,
                                   start_time DATETIME NOT NULL,
                                   end_time DATETIME NOT NULL,
                                   created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                   updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                   created_by VARCHAR \
                               ( \
                                   100 \
                               ),
                                   is_active BOOLEAN DEFAULT TRUE,
                                   target_audience VARCHAR \
                               ( \
                                   50 \
                               ) DEFAULT 'all',
                                   view_count INT DEFAULT 0,
                                   like_count INT DEFAULT 0,
                                   dislike_count INT DEFAULT 0
                                   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; \
                               """

        # 公告阅读记录表
        create_notice_views_table = """
                                    CREATE TABLE IF NOT EXISTS notice_views \
                                    ( \
                                        id \
                                        INT \
                                        AUTO_INCREMENT \
                                        PRIMARY \
                                        KEY, \
                                        notice_id \
                                        INT \
                                        NOT \
                                        NULL, \
                                        user_id \
                                        VARCHAR \
                                    ( \
                                        100 \
                                    ) NOT NULL,
                                        viewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                        UNIQUE KEY unique_view \
                                    ( \
                                        notice_id, \
                                        user_id \
                                    ),
                                        FOREIGN KEY \
                                    ( \
                                        notice_id \
                                    ) REFERENCES notices \
                                    ( \
                                        id \
                                    ) ON DELETE CASCADE
                                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; \
                                    """

        # 公告反馈表（点赞/踩）
        create_notice_reactions_table = """
                                        CREATE TABLE IF NOT EXISTS notice_reactions \
                                        ( \
                                            id \
                                            INT \
                                            AUTO_INCREMENT \
                                            PRIMARY \
                                            KEY, \
                                            notice_id \
                                            INT \
                                            NOT \
                                            NULL, \
                                            user_id \
                                            VARCHAR \
                                        ( \
                                            100 \
                                        ) NOT NULL,
                                            reaction_type ENUM \
                                        ( \
                                            'like', \
                                            'dislike' \
                                        ) NOT NULL,
                                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                                            UNIQUE KEY unique_reaction \
                                        ( \
                                            notice_id, \
                                            user_id \
                                        ),
                                            FOREIGN KEY \
                                        ( \
                                            notice_id \
                                        ) REFERENCES notices \
                                        ( \
                                            id \
                                        ) ON DELETE CASCADE
                                            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; \
                                        """

        self.cursor.execute(create_notices_table)
        self.cursor.execute(create_notice_views_table)
        self.cursor.execute(create_notice_reactions_table)

    def add_notice(self, title, content, notice_type="info", priority=0,
                   start_time=None, end_time=None, created_by=None,
                   is_active=True, target_audience="all"):
        """
        添加新公告

        Args:
            title: 公告标题
            content: 公告内容
            notice_type: 公告类型 (info, warning, error, success)
            priority: 优先级 (数字越大优先级越高)
            start_time: 开始展示时间，格式为 'YYYY-MM-DD HH:MM:SS'
            end_time: 结束展示时间，格式为 'YYYY-MM-DD HH:MM:SS'
            created_by: 创建者
            is_active: 是否激活
            target_audience: 目标受众 (all, user, admin)

        Returns:
            新公告的ID
        """
        # 处理时间
        if start_time is None:
            start_time = datetime.now()
        elif isinstance(start_time, str):
            start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')

        if end_time is None:
            end_time = datetime.now() + timedelta(days=30)  # 默认一个月
        elif isinstance(end_time, str):
            end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')

        sql = """
              INSERT INTO notices
              (title, content, type, priority, start_time, end_time, created_by, is_active, target_audience)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) \
              """

        self.cursor.execute(sql, (
            title, content, notice_type, priority,
            start_time, end_time, created_by, is_active, target_audience
        ))

        return self.cursor.lastrowid

    def update_notice(self, notice_id, **kwargs):
        """
        更新公告

        Args:
            notice_id: 公告ID
            **kwargs: 要更新的字段和值

        Returns:
            更新的行数
        """
        allowed_fields = {
            'title', 'content', 'type', 'priority',
            'start_time', 'end_time', 'is_active', 'target_audience'
        }

        # 过滤不允许的字段
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not update_fields:
            return 0

        # 处理日期字段
        for field in ['start_time', 'end_time']:
            if field in update_fields and isinstance(update_fields[field], str):
                update_fields[field] = datetime.strptime(update_fields[field], '%Y-%m-%d %H:%M:%S')

        # 构建SET子句
        set_clause = ", ".join([f"{field} = %s" for field in update_fields])
        values = list(update_fields.values())
        values.append(notice_id)

        sql = f"UPDATE notices SET {set_clause} WHERE id = %s"
        self.cursor.execute(sql, values)

        return self.cursor.rowcount

    def delete_notice(self, notice_id):
        """
        删除公告

        Args:
            notice_id: 公告ID

        Returns:
            删除的行数
        """
        sql = "DELETE FROM notices WHERE id = %s"
        self.cursor.execute(sql, (notice_id,))

        return self.cursor.rowcount

    def get_notice(self, notice_id, user_id=None):
        """
        获取单个公告详情，如果提供user_id，会记录阅读

        Args:
            notice_id: 公告ID
            user_id: 用户ID，如果提供则记录阅读

        Returns:
            公告详情字典，如果不存在则返回None
        """
        sql = "SELECT * FROM notices WHERE id = %s"
        self.cursor.execute(sql, (notice_id,))
        notice = self.cursor.fetchone()

        if notice and user_id:
            self.record_view(notice_id, user_id)

        return notice

    def get_active_notices(self, audience="all", limit=5):
        """
        获取当前有效的公告

        Args:
            audience: 目标受众 (all, user, admin)
            limit: 返回的最大公告数量

        Returns:
            公告列表
        """
        sql = """
              SELECT * \
              FROM notices
              WHERE is_active = TRUE
                AND start_time <= NOW()
                AND end_time >= NOW()
                AND (target_audience = %s OR target_audience = 'all')
              ORDER BY priority DESC, start_time DESC
                  LIMIT %s \
              """
        self.cursor.execute(sql, (audience, limit))

        return self.cursor.fetchall()

    def get_all_notices(self, page=1, page_size=20):
        """
        获取所有公告（分页）

        Args:
            page: 页码，从1开始
            page_size: 每页数量

        Returns:
            (公告列表, 总数)
        """
        # 计算总数
        self.cursor.execute("SELECT COUNT(*) as total FROM notices")
        total = self.cursor.fetchone()['total']

        # 获取分页数据
        offset = (page - 1) * page_size
        sql = """
              SELECT * \
              FROM notices
              ORDER BY created_at DESC
                  LIMIT %s \
              OFFSET %s \
              """
        self.cursor.execute(sql, (page_size, offset))
        notices = self.cursor.fetchall()

        return notices, total

    def search_notices(self, keyword, page=1, page_size=20):
        """
        搜索公告

        Args:
            keyword: 搜索关键词
            page: 页码，从1开始
            page_size: 每页数量

        Returns:
            (公告列表, 总数)
        """
        search_param = f"%{keyword}%"

        # 计算总数
        count_sql = """
                    SELECT COUNT(*) as total \
                    FROM notices
                    WHERE title LIKE %s \
                       OR content LIKE %s \
                    """
        self.cursor.execute(count_sql, (search_param, search_param))
        total = self.cursor.fetchone()['total']

        # 获取分页数据
        offset = (page - 1) * page_size
        search_sql = """
                     SELECT * \
                     FROM notices
                     WHERE title LIKE %s \
                        OR content LIKE %s
                     ORDER BY created_at DESC
                         LIMIT %s \
                     OFFSET %s \
                     """
        self.cursor.execute(search_sql, (search_param, search_param, page_size, offset))
        notices = self.cursor.fetchall()

        return notices, total

    def toggle_notice_status(self, notice_id):
        """
        切换公告的激活状态

        Args:
            notice_id: 公告ID

        Returns:
            新的激活状态 (True/False)
        """
        # 先获取当前状态
        self.cursor.execute(
            "SELECT is_active FROM notices WHERE id = %s",
            (notice_id,)
        )
        result = self.cursor.fetchone()

        if not result:
            return None

        new_status = not result['is_active']

        # 更新状态
        self.cursor.execute(
            "UPDATE notices SET is_active = %s WHERE id = %s",
            (new_status, notice_id)
        )

        return new_status

    # ===== 新增功能：阅读统计、点赞和踩 =====

    def record_view(self, notice_id, user_id):
        """
        记录用户查看公告

        Args:
            notice_id: 公告ID
            user_id: 用户ID

        Returns:
            是否为新的查看记录
        """
        try:
            # 尝试插入查看记录
            sql = """
                  INSERT INTO notice_views (notice_id, user_id)
                  VALUES (%s, %s) \
                  """
            self.cursor.execute(sql, (notice_id, user_id))

            # 更新公告的查看计数
            update_sql = """
                         UPDATE notices
                         SET view_count = (SELECT COUNT(*) FROM notice_views WHERE notice_id = %s)
                         WHERE id = %s \
                         """
            self.cursor.execute(update_sql, (notice_id, notice_id))

            return True
        except pymysql.err.IntegrityError:
            # 如果记录已存在（唯一键约束违反），则不是新的查看
            return False

    def add_reaction(self, notice_id, user_id, reaction_type):
        """
        添加或更新用户对公告的反应（点赞/踩）

        Args:
            notice_id: 公告ID
            user_id: 用户ID
            reaction_type: 反应类型 ('like' 或 'dislike')

        Returns:
            操作结果 ('added', 'updated', 'removed', 'error')
        """
        if reaction_type not in ('like', 'dislike'):
            return 'error'

        try:
            # 检查用户是否已有反应
            check_sql = """
                        SELECT reaction_type \
                        FROM notice_reactions
                        WHERE notice_id = %s \
                          AND user_id = %s \
                        """
            self.cursor.execute(check_sql, (notice_id, user_id))
            existing = self.cursor.fetchone()

            result = None

            if existing:
                # 如果已有相同反应，则删除（取消反应）
                if existing['reaction_type'] == reaction_type:
                    delete_sql = """
                                 DELETE \
                                 FROM notice_reactions
                                 WHERE notice_id = %s \
                                   AND user_id = %s \
                                 """
                    self.cursor.execute(delete_sql, (notice_id, user_id))
                    result = 'removed'
                else:
                    # 如果有不同反应，则更新
                    update_sql = """
                                 UPDATE notice_reactions
                                 SET reaction_type = %s
                                 WHERE notice_id = %s \
                                   AND user_id = %s \
                                 """
                    self.cursor.execute(update_sql, (reaction_type, notice_id, user_id))
                    result = 'updated'
            else:
                # 如果没有反应，则添加
                insert_sql = """
                             INSERT INTO notice_reactions (notice_id, user_id, reaction_type)
                             VALUES (%s, %s, %s) \
                             """
                self.cursor.execute(insert_sql, (notice_id, user_id, reaction_type))
                result = 'added'

            # 更新公告的点赞/踩计数
            # 更新公告的点赞和踩计数
            update_counts_sql = """
                                UPDATE notices
                                SET like_count    = (SELECT COUNT(*) \
                                                     FROM notice_reactions \
                                                     WHERE notice_id = %s AND reaction_type = 'like'),
                                    dislike_count = (SELECT COUNT(*) \
                                                     FROM notice_reactions \
                                                     WHERE notice_id = %s AND reaction_type = 'dislike')
                                WHERE id = %s \
                                """
            self.cursor.execute(update_counts_sql, (notice_id, notice_id, notice_id))

            return result

        except Exception as e:
            print(f"Error adding reaction: {e}")
            return 'error'

    def get_user_reaction(self, notice_id, user_id):
        """
        获取用户对特定公告的反应

        Args:
            notice_id: 公告ID
            user_id: 用户ID

        Returns:
            用户的反应类型 ('like', 'dislike' 或 None)
        """
        sql = """
              SELECT reaction_type \
              FROM notice_reactions
              WHERE notice_id = %s \
                AND user_id = %s \
              """
        self.cursor.execute(sql, (notice_id, user_id))
        result = self.cursor.fetchone()

        return result['reaction_type'] if result else None

    def get_notice_stats(self, notice_id):
        """
        获取公告的统计信息

        Args:
            notice_id: 公告ID

        Returns:
            包含查看次数、点赞数和踩数的字典
        """
        sql = """
              SELECT view_count, like_count, dislike_count
              FROM notices
              WHERE id = %s \
              """
        self.cursor.execute(sql, (notice_id,))
        result = self.cursor.fetchone()

        if not result:
            return {'view_count': 0, 'like_count': 0, 'dislike_count': 0}

        return result

    def get_notice_viewers(self, notice_id, page=1, page_size=20):
        """
        获取查看过公告的用户列表

        Args:
            notice_id: 公告ID
            page: 页码，从1开始
            page_size: 每页数量

        Returns:
            (查看记录列表, 总数)
        """
        # 计算总数
        count_sql = """
                    SELECT COUNT(*) as total \
                    FROM notice_views
                    WHERE notice_id = %s \
                    """
        self.cursor.execute(count_sql, (notice_id,))
        total = self.cursor.fetchone()['total']

        # 获取分页数据
        offset = (page - 1) * page_size
        sql = """
              SELECT user_id, viewed_at
              FROM notice_views
              WHERE notice_id = %s
              ORDER BY viewed_at DESC
              LIMIT %s OFFSET %s \
              """
        self.cursor.execute(sql, (notice_id, page_size, offset))
        viewers = self.cursor.fetchall()

        return viewers, total

    def get_popular_notices(self, days=7, limit=5):
        """
        获取最受欢迎的公告（基于查看次数和点赞数）

        Args:
            days: 最近几天
            limit: 返回的最大公告数量

        Returns:
            公告列表
        """
        sql = """
              SELECT * \
              FROM notices
              WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
              ORDER BY (view_count + like_count * 2 - dislike_count) DESC
              LIMIT %s \
              """
        self.cursor.execute(sql, (days, limit))

        return self.cursor.fetchall()

    def get_reaction_stats(self, notice_id):
        """
        获取公告的详细反应统计

        Args:
            notice_id: 公告ID

        Returns:
            包含点赞和踩详细信息的字典
        """
        # 获取点赞用户
        like_sql = """
                   SELECT user_id, created_at
                   FROM notice_reactions
                   WHERE notice_id = %s \
                     AND reaction_type = 'like'
                   ORDER BY created_at DESC \
                   """
        self.cursor.execute(like_sql, (notice_id,))
        likes = self.cursor.fetchall()

        # 获取踩用户
        dislike_sql = """
                      SELECT user_id, created_at
                      FROM notice_reactions
                      WHERE notice_id = %s \
                        AND reaction_type = 'dislike'
                      ORDER BY created_at DESC \
                      """
        self.cursor.execute(dislike_sql, (notice_id,))
        dislikes = self.cursor.fetchall()

        return {
            'likes': likes,
            'dislikes': dislikes,
            'like_count': len(likes),
            'dislike_count': len(dislikes)
        }

    def get_user_viewed_notices(self, user_id, page=1, page_size=20):
        """
        获取用户查看过的公告

        Args:
            user_id: 用户ID
            page: 页码，从1开始
            page_size: 每页数量

        Returns:
            (公告列表, 总数)
        """
        # 计算总数
        count_sql = """
                    SELECT COUNT(*) as total \
                    FROM notice_views
                    WHERE user_id = %s \
                    """
        self.cursor.execute(count_sql, (user_id,))
        total = self.cursor.fetchone()['total']

        # 获取分页数据
        offset = (page - 1) * page_size
        sql = """
              SELECT n.*, nv.viewed_at
              FROM notices n
                       JOIN notice_views nv ON n.id = nv.notice_id
              WHERE nv.user_id = %s
              ORDER BY nv.viewed_at DESC
              LIMIT %s OFFSET %s \
              """
        self.cursor.execute(sql, (user_id, page_size, offset))
        notices = self.cursor.fetchall()

        return notices, total

    def close(self):
        """关闭数据库连接"""
        if hasattr(self, 'conn') and self.conn is not None:
            self.cursor.close()
            self.conn.close()


# 使用示例
if __name__ == "__main__":
    # 创建NoticeManager实例
    notice_manager = NoticeManager()

    try:
        # 添加一条公告
        notice_id = notice_manager.add_notice(
            title="系统维护通知",
            content="系统将于2024年5月1日凌晨2:00-4:00进行维护升级，期间服务可能不可用。",
            notice_type="warning",
            priority=10,
            created_by="admin"
        )
        print(f"添加公告成功，ID: {notice_id}")

        # 模拟用户查看公告
        notice_manager.record_view(notice_id, "user1")
        notice_manager.record_view(notice_id, "user2")
        notice_manager.record_view(notice_id, "user3")

        # 模拟用户点赞/踩
        notice_manager.add_reaction(notice_id, "user1", "like")
        notice_manager.add_reaction(notice_id, "user2", "like")
        notice_manager.add_reaction(notice_id, "user3", "dislike")

        # 获取公告统计信息
        stats = notice_manager.get_notice_stats(notice_id)
        print(f"公告统计: 查看次数={stats['view_count']}, 点赞={stats['like_count']}, 踩={stats['dislike_count']}")

        # 获取查看过公告的用户
        viewers, total = notice_manager.get_notice_viewers(notice_id)
        print(f"查看用户总数: {total}")
        for viewer in viewers:
            print(f"- 用户 {viewer['user_id']} 在 {viewer['viewed_at']} 查看了公告")

        # 获取公告的详细反应统计
        reaction_stats = notice_manager.get_reaction_stats(notice_id)
        print(f"点赞用户: {', '.join([like['user_id'] for like in reaction_stats['likes']])}")
        print(f"踩用户: {', '.join([dislike['user_id'] for dislike in reaction_stats['dislikes']])}")

    finally:
        # 关闭连接
        notice_manager.close()
