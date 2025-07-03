# MainProject/app/services/travel_post_service.py

from MainProject.dbhelper.SQLHelper import SQLHelper
from MainProject.dbhelper.MONGOHelper import MongoHelper
import datetime


class TravelPostService:
    def __init__(self):
        self.db = SQLHelper()
        self.mongo = MongoHelper()

    def create_post(self, user_id, title, content, location_name=None,
                    location_coordinates=None, privacy_level='public', tags=None, media_files=None):
        """创建新的旅行动态"""
        # 插入基本动态信息到MySQL
        post_sql = """
                   INSERT INTO TravelPosts
                   (user_id, title, content, location_name, location_coordinates, privacy_level)
                   VALUES (%s, %s, %s, %s, %s, %s) \
                   """
        try:
            self.db.execute(post_sql, (
                user_id, title, content, location_name,
                location_coordinates, privacy_level
            ))
            post_id = self.db.cursor.lastrowid

            # 处理标签
            if tags:
                tag_sql = "INSERT INTO PostTags (post_id, tag_name) VALUES (%s, %s)"
                tag_params = [(post_id, tag) for tag in tags]
                self.db.executemany(tag_sql, tag_params)

            # 处理媒体文件
            if media_files:
                media_sql = """
                            INSERT INTO PostMedia
                                (post_id, media_type, media_url, thumbnail_url)
                            VALUES (%s, %s, %s, %s) \
                            """
                media_params = [
                    (post_id, file['type'], file['url'], file.get('thumbnail_url'))
                    for file in media_files
                ]
                self.db.executemany(media_sql, media_params)

            # 存储详细内容到MongoDB（包括富文本和其他复杂数据）
            self.mongo.db.travel_post_details.insert_one({
                'post_id': post_id,
                'user_id': user_id,
                'title': title,
                'content': content,
                'rich_content': content,  # 可以存储HTML或Markdown格式的富文本
                'location': {
                    'name': location_name,
                    'coordinates': location_coordinates
                },
                'privacy_level': privacy_level,
                'tags': tags or [],
                'media_files': media_files or [],
                'created_at': datetime.datetime.now(),
                'updated_at': datetime.datetime.now()
            })

            return True, post_id
        except Exception as e:
            return False, f"创建动态失败: {str(e)}"

    def get_post(self, post_id, user_id=None):
        """获取单个动态详情"""
        # 基本信息从MySQL获取
        sql = """
              SELECT p.*, \
                     u.username, \
                     u.nickname, \
                     u.avatar,
                     COUNT(DISTINCT pi_like.id)                  as like_count,
                     COUNT(DISTINCT pi_comment.id)               as comment_count,
                     EXISTS(SELECT 1 \
                            FROM PostInteractions
                            WHERE post_id = p.id \
                              AND user_id = %s \
                              AND interaction_type = 'like')     as user_liked,
                     EXISTS(SELECT 1 \
                            FROM PostInteractions
                            WHERE post_id = p.id \
                              AND user_id = %s \
                              AND interaction_type = 'favorite') as user_favorited
              FROM TravelPosts p
                       JOIN Users u ON p.user_id = u.id
                       LEFT JOIN PostInteractions pi_like \
                                 ON p.id = pi_like.post_id AND pi_like.interaction_type = 'like'
                       LEFT JOIN PostInteractions pi_comment \
                                 ON p.id = pi_comment.post_id AND pi_comment.interaction_type = 'comment'
              WHERE p.id = %s
              GROUP BY p.id \
              """
        post = self.db.fetchone(sql, (user_id or 0, user_id or 0, post_id))

        if not post:
            return None

        # 检查隐私设置
        if user_id != post['user_id'] and post['privacy_level'] != 'public':
            if post['privacy_level'] == 'private':
                return None
            elif post['privacy_level'] == 'friends':
                # 检查是否是好友
                friendship_sql = """
                                 SELECT id \
                                 FROM Friendships
                                 WHERE user_id = %s \
                                   AND friend_id = %s \
                                   AND status = 'accepted' \
                                 """
                friendship = self.db.fetchone(friendship_sql, (post['user_id'], user_id))
                if not friendship:
                    return None

        # 获取标签
        tags_sql = "SELECT tag_name FROM PostTags WHERE post_id = %s"
        tags = self.db.query(tags_sql, (post_id,))
        post['tags'] = [tag['tag_name'] for tag in tags]

        # 获取媒体文件
        media_sql = "SELECT * FROM PostMedia WHERE post_id = %s"
        post['media'] = self.db.query(media_sql, (post_id,))

        # 从MongoDB获取详细内容
        details = self.mongo.db.travel_post_details.find_one({'post_id': int(post_id)})
        if details:
            post['rich_content'] = details.get('rich_content', post['content'])

        # 增加浏览次数
        if user_id and user_id != post['user_id']:
            self.db.execute("UPDATE TravelPosts SET view_count = view_count + 1 WHERE id = %s", (post_id,))

        return post

        # services/travel_post_service.py (续)

    def get_posts(self, user_id=None, page=1, page_size=10, tag=None, location=None, friend_only=False):
        """获取动态列表（支持分页和筛选）"""
        offset = (page - 1) * page_size

        # 构建基本查询
        sql = """
              SELECT p.*, \
                     u.username, \
                     u.nickname, \
                     u.avatar,
                     COUNT(DISTINCT pi_like.id)    as like_count,
                     COUNT(DISTINCT pi_comment.id) as comment_count
              FROM TravelPosts p
                       JOIN Users u ON p.user_id = u.id
                       LEFT JOIN PostInteractions pi_like \
                                 ON p.id = pi_like.post_id AND pi_like.interaction_type = 'like'
                       LEFT JOIN PostInteractions pi_comment \
                                 ON p.id = pi_comment.post_id AND pi_comment.interaction_type = 'comment' \
              """

        # 构建WHERE条件
        conditions = []
        params = []

        # 隐私过滤
        if user_id:
            # 用户可以看到自己的所有动态、好友的friends级别动态和所有public动态
            if friend_only:
                conditions.append("""
                (p.user_id IN (
                    SELECT friend_id FROM Friendships 
                    WHERE user_id = %s AND status = 'accepted'
                ) OR p.user_id = %s)
                """)
                params.extend([user_id, user_id])
            else:
                conditions.append("""
                (p.privacy_level = 'public' 
                OR p.user_id = %s 
                OR (p.privacy_level = 'friends' AND p.user_id IN (
                    SELECT friend_id FROM Friendships 
                    WHERE user_id = %s AND status = 'accepted'
                )))
                """)
                params.extend([user_id, user_id])
        else:
            # 未登录用户只能看到public动态
            conditions.append("p.privacy_level = 'public'")

        # 标签过滤
        if tag:
            sql += "JOIN PostTags pt ON p.id = pt.post_id "
            conditions.append("pt.tag_name = %s")
            params.append(tag)

        # 位置过滤
        if location:
            conditions.append("p.location_name LIKE %s")
            params.append(f"%{location}%")

        # 组合WHERE条件
        if conditions:
            sql += "WHERE " + " AND ".join(conditions)

        # 分组和排序
        sql += " GROUP BY p.id ORDER BY p.created_at DESC LIMIT %s OFFSET %s"
        params.extend([page_size, offset])

        # 执行查询
        posts = self.db.query(sql, tuple(params))

        # 获取每个动态的标签
        for post in posts:
            tags_sql = "SELECT tag_name FROM PostTags WHERE post_id = %s"
            tags = self.db.query(tags_sql, (post['id'],))
            post['tags'] = [tag['tag_name'] for tag in tags]

            # 获取第一张媒体作为预览
            media_sql = "SELECT * FROM PostMedia WHERE post_id = %s LIMIT 1"
            media = self.db.query(media_sql, (post['id'],))
            post['preview_media'] = media[0] if media else None

            # 如果是登录用户，检查是否已点赞/收藏
            if user_id:
                interaction_sql = """
                                  SELECT interaction_type
                                  FROM PostInteractions
                                  WHERE post_id = %s \
                                    AND user_id = %s \
                                    AND interaction_type IN ('like', 'favorite') \
                                  """
                interactions = self.db.query(interaction_sql, (post['id'], user_id))
                post['user_liked'] = any(i['interaction_type'] == 'like' for i in interactions)
                post['user_favorited'] = any(i['interaction_type'] == 'favorite' for i in interactions)

        # 获取总记录数
        count_sql = "SELECT COUNT(DISTINCT p.id) as total FROM TravelPosts p "
        if tag:
            count_sql += "JOIN PostTags pt ON p.id = pt.post_id "

        if conditions:
            count_sql += "WHERE " + " AND ".join(conditions)

        count_result = self.db.fetchone(count_sql, tuple(params[:-2]))  # 移除LIMIT参数
        total = count_result['total'] if count_result else 0

        return {
            'posts': posts,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }

    def like_post(self, post_id, user_id):
        """点赞动态"""
        # 检查动态是否存在且用户有权限查看
        post = self.get_post(post_id, user_id)
        if not post:
            return False, "动态不存在或无权访问"

        # 检查是否已点赞
        check_sql = """
                    SELECT id \
                    FROM PostInteractions
                    WHERE post_id = %s \
                      AND user_id = %s \
                      AND interaction_type = 'like' \
                    """
        existing = self.db.fetchone(check_sql, (post_id, user_id))

        if existing:
            # 取消点赞
            delete_sql = "DELETE FROM PostInteractions WHERE id = %s"
            self.db.execute(delete_sql, (existing['id'],))
            return True, "已取消点赞"
        else:
            # 添加点赞
            insert_sql = """
                         INSERT INTO PostInteractions (post_id, user_id, interaction_type)
                         VALUES (%s, %s, 'like') \
                         """
            self.db.execute(insert_sql, (post_id, user_id))

            # 添加通知
            if post['user_id'] != user_id:
                self.mongo.db.notifications.insert_one({
                    'user_id': post['user_id'],
                    'actor_id': user_id,
                    'action': 'like',
                    'content_id': post_id,
                    'content_type': 'post',
                    'is_read': False,
                    'created_at': datetime.datetime.now()
                })

            return True, "已点赞"

    def favorite_post(self, post_id, user_id):
        """收藏动态"""
        # 检查动态是否存在且用户有权限查看
        post = self.get_post(post_id, user_id)
        if not post:
            return False, "动态不存在或无权访问"

        # 检查是否已收藏
        check_sql = """
                    SELECT id \
                    FROM PostInteractions
                    WHERE post_id = %s \
                      AND user_id = %s \
                      AND interaction_type = 'favorite' \
                    """
        existing = self.db.fetchone(check_sql, (post_id, user_id))

        if existing:
            # 取消收藏
            delete_sql = "DELETE FROM PostInteractions WHERE id = %s"
            self.db.execute(delete_sql, (existing['id'],))

            # 同时从UserFavorites表中删除
            delete_fav_sql = """
                             DELETE \
                             FROM UserFavorites
                             WHERE user_id = %s \
                               AND content_id = %s \
                               AND content_type = 'post' \
                             """
            self.db.execute(delete_fav_sql, (user_id, post_id))

            return True, "已取消收藏"
        else:
            # 添加收藏
            insert_sql = """
                         INSERT INTO PostInteractions (post_id, user_id, interaction_type)
                         VALUES (%s, %s, 'favorite') \
                         """
            self.db.execute(insert_sql, (post_id, user_id))

            # 同时添加到UserFavorites表
            insert_fav_sql = """
                             INSERT INTO UserFavorites (user_id, content_id, content_type)
                             VALUES (%s, %s, 'post') \
                             """
            self.db.execute(insert_fav_sql, (user_id, post_id))

            return True, "已收藏"

    def comment_post(self, post_id, user_id, content):
        """评论动态"""
        # 检查动态是否存在且用户有权限查看
        post = self.get_post(post_id, user_id)
        if not post:
            return False, "动态不存在或无权访问"

        if not content or len(content.strip()) == 0:
            return False, "评论内容不能为空"

        # 添加评论
        insert_sql = """
                     INSERT INTO PostInteractions (post_id, user_id, interaction_type, comment_content)
                     VALUES (%s, %s, 'comment', %s) \
                     """
        try:
            self.db.execute(insert_sql, (post_id, user_id, content))
            comment_id = self.db.cursor.lastrowid

            # 添加通知
            if post['user_id'] != user_id:
                self.mongo.db.notifications.insert_one({
                    'user_id': post['user_id'],
                    'actor_id': user_id,
                    'action': 'comment',
                    'content_id': post_id,
                    'content_type': 'post',
                    'comment_id': comment_id,
                    'comment_content': content,
                    'is_read': False,
                    'created_at': datetime.datetime.now()
                })

            return True, comment_id
        except Exception as e:
            return False, f"评论失败: {str(e)}"

    def get_comments(self, post_id, page=1, page_size=20):
        """获取动态评论"""
        offset = (page - 1) * page_size

        sql = """
              SELECT pi.id, \
                     pi.user_id, \
                     pi.comment_content, \
                     pi.created_at,
                     u.username, \
                     u.nickname, \
                     u.avatar
              FROM PostInteractions pi
                       JOIN Users u ON pi.user_id = u.id
              WHERE pi.post_id = %s \
                AND pi.interaction_type = 'comment'
              ORDER BY pi.created_at DESC
                  LIMIT %s \
              OFFSET %s \
              """

        comments = self.db.query(sql, (post_id, page_size, offset))

        # 获取总评论数
        count_sql = """
                    SELECT COUNT(*) as total
                    FROM PostInteractions
                    WHERE post_id = %s \
                      AND interaction_type = 'comment' \
                    """
        count_result = self.db.fetchone(count_sql, (post_id,))
        total = count_result['total'] if count_result else 0

        return {
            'comments': comments,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }

    def delete_post(self, post_id, user_id):
        """删除动态"""
        # 检查动态是否存在且是否为作者
        check_sql = "SELECT user_id FROM TravelPosts WHERE id = %s"
        post = self.db.fetchone(check_sql, (post_id,))

        if not post:
            return False, "动态不存在"

        if post['user_id'] != user_id:
            # 检查是否为管理员
            user_sql = "SELECT role_id FROM Users WHERE id = %s"
            user = self.db.fetchone(user_sql, (user_id,))
            if not user or user['role_id'] > 2:  # 假设1=root, 2=admin
                return False, "无权删除此动态"

        try:
            # 删除动态（外键约束会自动删除相关的标签、媒体和互动记录）
            delete_sql = "DELETE FROM TravelPosts WHERE id = %s"
            self.db.execute(delete_sql, (post_id,))

            # 删除MongoDB中的详细内容
            self.mongo.db.travel_post_details.delete_one({'post_id': int(post_id)})

            # 删除相关的收藏记录
            delete_fav_sql = "DELETE FROM UserFavorites WHERE content_id = %s AND content_type = 'post'"
            self.db.execute(delete_fav_sql, (post_id,))

            # 删除相关的通知
            self.mongo.db.notifications.delete_many({
                'content_id': int(post_id),
                'content_type': 'post'
            })

            return True, "动态已删除"
        except Exception as e:
            return False, f"删除动态失败: {str(e)}"

    def get_popular_tags(self, limit=10):
        """获取热门标签"""
        sql = """
              SELECT tag_name, COUNT(*) as count
              FROM PostTags
              GROUP BY tag_name
              ORDER BY count DESC
                  LIMIT %s \
              """
        return self.db.query(sql, (limit,))

    def get_user_posts(self, user_id, viewer_id=None, page=1, page_size=10):
        """获取指定用户发布的动态列表"""
        offset = (page - 1) * page_size

        # 构建基础查询
        sql = """
              SELECT p.*, \
                     u.username, \
                     u.nickname, \
                     u.avatar,
                     COUNT(DISTINCT pi_like.id)    as like_count,
                     COUNT(DISTINCT pi_comment.id) as comment_count
              FROM TravelPosts p
                       JOIN Users u ON p.user_id = u.id
                       LEFT JOIN PostInteractions pi_like \
                                 ON p.id = pi_like.post_id AND pi_like.interaction_type = 'like'
                       LEFT JOIN PostInteractions pi_comment \
                                 ON p.id = pi_comment.post_id AND pi_comment.interaction_type = 'comment'
              WHERE p.user_id = %s \
              """

        params = [user_id]

        # 隐私过滤
        if viewer_id != user_id:
            sql += " AND (p.privacy_level = 'public' "
            if viewer_id:
                sql += """
                       OR (p.privacy_level = 'friends' AND EXISTS (
                           SELECT 1 FROM Friendships 
                           WHERE (user_id = %s AND friend_id = %s) 
                              OR (user_id = %s AND friend_id = %s)
                           AND status = 'accepted'
                       ))
                       """
                params.extend([user_id, viewer_id, viewer_id, user_id])
            sql += ")"

        # 完成SQL
        sql += " GROUP BY p.id ORDER BY p.created_at DESC LIMIT %s OFFSET %s"
        params.extend([page_size, offset])

        # 执行查询
        posts = self.db.query(sql, tuple(params))

        # 获取每个动态的标签和预览媒体
        for post in posts:
            tags_sql = "SELECT tag_name FROM PostTags WHERE post_id = %s"
            tags = self.db.query(tags_sql, (post['id'],))
            post['tags'] = [tag['tag_name'] for tag in tags]

            media_sql = "SELECT * FROM PostMedia WHERE post_id = %s LIMIT 1"
            media = self.db.query(media_sql, (post['id'],))
            post['preview_media'] = media[0] if media else None

            # 检查是否已点赞/收藏
            if viewer_id:
                interaction_sql = """
                                  SELECT interaction_type
                                  FROM PostInteractions
                                  WHERE post_id = %s \
                                    AND user_id = %s \
                                    AND interaction_type IN ('like', 'favorite') \
                                  """
                interactions = self.db.query(interaction_sql, (post['id'], viewer_id))
                post['user_liked'] = any(i['interaction_type'] == 'like' for i in interactions)
                post['user_favorited'] = any(i['interaction_type'] == 'favorite' for i in interactions)

        # 获取总记录数
        count_sql = "SELECT COUNT(*) as total FROM TravelPosts WHERE user_id = %s"
        count_params = [user_id]

        if viewer_id != user_id:
            count_sql += " AND (privacy_level = 'public'"
            if viewer_id:
                count_sql += """
                             OR (privacy_level = 'friends' AND EXISTS (
                                 SELECT 1 FROM Friendships 
                                 WHERE (user_id = %s AND friend_id = %s) 
                                    OR (user_id = %s AND friend_id = %s)
                                 AND status = 'accepted'
                             ))
                             """
                count_params.extend([user_id, viewer_id, viewer_id, user_id])
            count_sql += ")"

        count_result = self.db.fetchone(count_sql, tuple(count_params))
        total = count_result['total'] if count_result else 0

        return {
            'posts': posts,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
