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

    def get_favorite_status(self, post_id, user_id):
        """检查用户是否已收藏该动态"""
        if not user_id or not post_id:
            return False

        try:
            sql = """
                SELECT 1 FROM UserFavorites 
                WHERE user_id = %s AND content_id = %s AND content_type = 'post'
                LIMIT 1
            """
            result = self.db.fetchone(sql, (user_id, post_id))
            return bool(result)
        except Exception as e:
            print(f"检查收藏状态出错: {str(e)}")
            return False

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
        """
        删除动态及其相关数据

        Args:
            post_id: 要删除的动态ID
            user_id: 请求删除的用户ID

        Returns:
            (success, message): 表示操作是否成功及相关信息
        """
        # 检查动态是否存在
        check_sql = "SELECT user_id FROM TravelPosts WHERE id = %s"
        post = self.db.fetchone(check_sql, (post_id,))

        if not post:
            return False, "动态不存在"

        # 权限检查
        if post['user_id'] != user_id:
            # 检查是否为管理员
            user_sql = "SELECT role_id FROM Users WHERE id = %s"
            user = self.db.fetchone(user_sql, (user_id,))
            if not user or user['role_id'] > 2:  # 假设1=root, 2=admin
                return False, "无权删除此动态"

        try:
            # 由于没有事务支持，我们需要确保最关键的删除操作在最后执行
            # 这样即使中间步骤失败，至少不会留下悬空的主记录

            # 1. 删除PostTags表中的相关记录
            try:
                self.db.execute("DELETE FROM PostTags WHERE post_id = %s", (post_id,))
            except Exception as e:
                print(f"删除标签时出错: {str(e)}")

            # 2. 删除PostMedia表中的相关记录
            try:
                self.db.execute("DELETE FROM PostMedia WHERE post_id = %s", (post_id,))
            except Exception as e:
                print(f"删除媒体记录时出错: {str(e)}")

            # 3. 删除PostInteractions表中的相关记录
            try:
                self.db.execute("DELETE FROM PostInteractions WHERE post_id = %s", (post_id,))
            except Exception as e:
                print(f"删除互动记录时出错: {str(e)}")

            # 4. 删除UserFavorites表中的相关记录
            try:
                self.db.execute("DELETE FROM UserFavorites WHERE content_id = %s AND content_type = 'post'", (post_id,))
            except Exception as e:
                print(f"删除收藏记录时出错: {str(e)}")

            # 5. 检查并删除UserViewHistory表中的相关记录(如果表存在)
            try:
                # 检查表是否存在
                check_table_sql = """
                    SELECT COUNT(*) as count
                    FROM information_schema.tables
                    WHERE table_schema = DATABASE()
                    AND table_name = 'UserViewHistory'
                """
                result = self.db.fetchone(check_table_sql)

                if result and result.get('count', 0) > 0:
                    # 表存在，删除相关记录
                    self.db.execute("DELETE FROM UserViewHistory WHERE content_id = %s AND content_type = 'post'",
                                    (post_id,))
            except Exception as e:
                print(f"处理浏览历史时出错: {str(e)}")

            # 6. 删除MongoDB中的详细内容
            try:
                self.mongo.db.travel_post_details.delete_one({'post_id': int(post_id)})
            except Exception as e:
                print(f"删除MongoDB数据时出错: {str(e)}")

            # 7. 删除相关的通知
            try:
                self.mongo.db.notifications.delete_many({
                    'content_id': int(post_id),
                    'content_type': 'post'
                })
            except Exception as e:
                print(f"删除通知时出错: {str(e)}")

            # 8. 最后删除TravelPosts表中的主记录
            # 这是最关键的操作，放在最后执行
            self.db.execute("DELETE FROM TravelPosts WHERE id = %s", (post_id,))

            return True, "动态已删除"
        except Exception as e:
            return False, f"删除动态失败: {str(e)}"

    def update_post(self, post_id, user_id, title, content, location_name=None,
                    privacy_level='public', tags=None, media_files=None):
        """
        更新旅行动态

        Args:
            post_id: 动态ID
            user_id: 请求更新的用户ID
            title: 新标题
            content: 新内容
            location_name: 新位置名称 (可选)
            privacy_level: 新隐私级别 (可选)
            tags: 新标签列表 (可选)
            media_files: 新媒体文件列表 (可选)

        Returns:
            (success, message): 成功与否及相关信息
        """
        # 首先检查动态是否存在
        check_sql = "SELECT user_id FROM TravelPosts WHERE id = %s"
        post = self.db.fetchone(check_sql, (post_id,))

        if not post:
            return False, "动态不存在"

        # 检查用户权限 - 必须是动态作者或管理员
        has_permission = False

        if post['user_id'] == user_id:
            # 用户是动态作者
            has_permission = True
        else:
            # 检查用户是否为管理员
            user_sql = "SELECT role_id FROM Users WHERE id = %s"
            user = self.db.fetchone(user_sql, (user_id,))
            if user and user['role_id'] <= 2:  # 假设1=root, 2=admin
                has_permission = True

        if not has_permission:
            return False, "无权修改此动态"

        try:
            # 开始更新操作
            # 1. 更新基本信息
            update_sql = """
                UPDATE TravelPosts
                SET title = %s, 
                    content = %s, 
                    location_name = %s, 
                    privacy_level = %s,
                    updated_at = NOW()
                WHERE id = %s
            """
            self.db.execute(update_sql, (
                title,
                content,
                location_name,
                privacy_level,
                post_id
            ))

            # 2. 处理标签 - 删除旧标签并添加新标签
            if tags is not None:  # 仅当明确提供标签时才更新
                # 删除旧标签
                delete_tags_sql = "DELETE FROM PostTags WHERE post_id = %s"
                self.db.execute(delete_tags_sql, (post_id,))

                # 添加新标签
                if tags and len(tags) > 0:
                    tag_sql = "INSERT INTO PostTags (post_id, tag_name) VALUES (%s, %s)"
                    tag_params = [(post_id, tag) for tag in tags]
                    self.db.executemany(tag_sql, tag_params)

            # 3. 处理媒体文件 (如果提供了新的媒体文件列表)
            if media_files is not None:  # 仅当明确提供媒体文件时才更新
                # 删除旧媒体文件
                delete_media_sql = "DELETE FROM PostMedia WHERE post_id = %s"
                self.db.execute(delete_media_sql, (post_id,))

                # 添加新媒体文件
                if media_files and len(media_files) > 0:
                    media_sql = """
                        INSERT INTO PostMedia 
                            (post_id, media_type, media_url, thumbnail_url) 
                        VALUES (%s, %s, %s, %s)
                    """
                    media_params = [
                        (post_id, file['type'], file['url'], file.get('thumbnail_url'))
                        for file in media_files
                    ]
                    self.db.executemany(media_sql, media_params)

            # 4. 更新MongoDB中的详细内容
            mongo_update = {
                "$set": {
                    "title": title,
                    "content": content,
                    "rich_content": content,  # 可以存储HTML或Markdown格式的富文本
                    "privacy_level": privacy_level,
                    "updated_at": datetime.datetime.now()
                }
            }

            # 仅当提供了位置时才更新位置信息
            if location_name is not None:
                mongo_update["$set"]["location.name"] = location_name

            # 仅当提供了标签时才更新标签
            if tags is not None:
                mongo_update["$set"]["tags"] = tags or []

            # 仅当提供了媒体文件时才更新媒体文件
            if media_files is not None:
                mongo_update["$set"]["media_files"] = media_files or []

            # 记录编辑历史
            mongo_update["$push"] = {
                "edit_history": {
                    "edited_by": user_id,
                    "edited_at": datetime.datetime.now(),
                    "previous_title": post.get("title"),
                    "previous_content": post.get("content")
                }
            }

            # 执行MongoDB更新
            self.mongo.db.travel_post_details.update_one(
                {"post_id": int(post_id)},
                mongo_update
            )

            return True, "动态已成功更新"
        except Exception as e:
            return False, f"更新动态失败: {str(e)}"

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

    def get_post_detail(self, post_id, user_id=None):
        """
        获取单个动态的详细信息，包括内容、媒体、交互状态等

        Args:
            post_id: 动态ID
            user_id: 查看者ID，用于检查权限和个人交互状态

        Returns:
            包含动态详情的字典，如果没有权限或动态不存在则返回None
        """
        # 首先使用已有的get_post方法获取基本数据
        post = self.get_post(post_id, user_id)

        if not post:
            return None

        # 获取更详细的信息
        try:
            # 获取所有媒体文件
            media_sql = """
                        SELECT id, media_type, media_url, thumbnail_url, created_at
                        FROM PostMedia
                        WHERE post_id = %s
                        ORDER BY id \
                        """
            post['media'] = self.db.query(media_sql, (post_id,))

            # 获取点赞用户列表(限制数量)
            likes_sql = """
                        SELECT u.id, u.username, u.nickname, u.avatar
                        FROM PostInteractions pi
                        JOIN Users u ON pi.user_id = u.id
                        WHERE pi.post_id = %s AND pi.interaction_type = 'like'
                        ORDER BY pi.created_at DESC
                        LIMIT 10 \
                        """
            post['recent_likes'] = self.db.query(likes_sql, (post_id,))

            # 获取评论计数和最新评论
            comments_data = self.get_comments(post_id, page=1, page_size=5)
            post['recent_comments'] = comments_data['comments']
            post['comment_count'] = comments_data['total']

            # 从MongoDB获取富文本内容和其他元数据
            details = self.mongo.db.travel_post_details.find_one({'post_id': int(post_id)})
            if details:
                # 添加富文本内容
                post['rich_content'] = details.get('rich_content', post['content'])

                # 添加其他可能的元数据
                post['metadata'] = {
                    'device': details.get('device'),
                    'app_version': details.get('app_version'),
                    'draft_saved_count': details.get('draft_saved_count'),
                    'edit_history': details.get('edit_history', [])
                }

                # 如果有地理位置坐标
                if details.get('location') and details['location'].get('coordinates'):
                    post['location_coordinates'] = details['location']['coordinates']

                # 添加相关动态推荐
                if details.get('related_posts'):
                    post['related_posts'] = details['related_posts']

            # 增加用户交互状态检查
            if user_id:
                # 检查用户与发布者的关系
                is_friend_sql = """
                                SELECT 1
                                FROM Friendships
                                WHERE ((user_id = %s AND friend_id = %s) OR (user_id = %s AND friend_id = %s))
                                AND status = 'accepted'
                                LIMIT 1 \
                                """
                is_friend = self.db.fetchone(is_friend_sql, (user_id, post['user_id'], post['user_id'], user_id))
                post['is_friend_with_author'] = bool(is_friend)

                # 检查是否已收藏
                favorite_sql = """
                               SELECT 1
                               FROM PostInteractions
                               WHERE post_id = %s AND user_id = %s AND interaction_type = 'favorite'
                               LIMIT 1 \
                               """
                favorite = self.db.fetchone(favorite_sql, (post_id, user_id))
                post['user_favorited'] = bool(favorite)

                # 检查是否已点赞
                like_sql = """
                           SELECT 1
                           FROM PostInteractions
                           WHERE post_id = %s AND user_id = %s AND interaction_type = 'like'
                           LIMIT 1 \
                           """
                like = self.db.fetchone(like_sql, (post_id, user_id))
                post['user_liked'] = bool(like)

                # 记录查看历史（如果需要）
                if user_id != post['user_id']:
                    self._record_view_history(post_id, user_id)

            return post

        except Exception as e:
            print(f"获取动态详情时发生错误: {str(e)}")
            # 如果有错误，返回基本信息
            return post

    def get_post_by_favorite(self, favorite_id, user_id):
        """通过收藏ID获取动态详情"""
        if not favorite_id or not user_id:
            return None

        try:
            # 获取收藏信息
            fav_sql = """
                SELECT content_id, content_type
                FROM UserFavorites
                WHERE id = %s AND user_id = %s
            """
            favorite = self.db.fetchone(fav_sql, (favorite_id, user_id))

            if not favorite:
                return None

            # 目前只处理动态类型的收藏
            if favorite['content_type'] != 'post':
                return {
                    'id': favorite_id,
                    'content_type': favorite['content_type'],
                    'message': '暂不支持查看此类型的收藏详情'
                }

            # 获取动态详情
            return self.get_post_detail(favorite['content_id'], user_id)
        except Exception as e:
            print(f"通过收藏获取动态失败: {str(e)}")
            return None

    def _record_view_history(self, post_id, user_id):
        """记录用户查看历史"""
        try:
            # First check if the table exists
            check_table_sql = """
                SELECT COUNT(*) as count
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = 'UserViewHistory'
            """
            result = self.db.fetchone(check_table_sql)

            if not result or result.get('count', 0) == 0:
                # Table doesn't exist, so create it
                create_table_sql = """
                    CREATE TABLE IF NOT EXISTS UserViewHistory (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        content_id INT NOT NULL,
                        content_type VARCHAR(20) NOT NULL,
                        view_count INT DEFAULT 1,
                        last_viewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_user_content (user_id, content_id, content_type)
                    )
                """
                self.db.execute(create_table_sql)

            # Now proceed with the original logic
            check_sql = """
                        SELECT id, view_count
                        FROM UserViewHistory
                        WHERE user_id = %s AND content_id = %s AND content_type = 'post'
                        LIMIT 1 \
                        """
            existing = self.db.fetchone(check_sql, (user_id, post_id))

            if existing:
                # 更新现有记录
                update_sql = """
                             UPDATE UserViewHistory
                             SET view_count = view_count + 1, last_viewed_at = NOW()
                             WHERE id = %s \
                             """
                self.db.execute(update_sql, (existing['id'],))
            else:
                # 创建新记录
                insert_sql = """
                             INSERT INTO UserViewHistory 
                             (user_id, content_id, content_type, view_count, last_viewed_at)
                             VALUES (%s, %s, 'post', 1, NOW()) \
                             """
                self.db.execute(insert_sql, (user_id, post_id))

        except Exception as e:
            # 记录历史失败不应影响主流程
            print(f"记录查看历史时出错: {str(e)}")

    def add_comment(self, post_id, user_id, content):
        """
        向动态添加评论

        Args:
            post_id: 动态ID
            user_id: 评论者用户ID
            content: 评论内容

        Returns:
            成功返回评论ID，失败返回错误信息
        """
        if not content or not content.strip():
            return {"success": False, "message": "评论内容不能为空"}

        # 检查动态是否存在且用户有权限查看
        post = self.get_post(post_id, user_id)
        if not post:
            return {"success": False, "message": "动态不存在或无权访问"}

        try:
            # 添加评论
            insert_sql = """
                         INSERT INTO PostInteractions 
                         (post_id, user_id, interaction_type, comment_content, created_at)
                         VALUES (%s, %s, 'comment', %s, NOW()) \
                         """
            self.db.execute(insert_sql, (post_id, user_id, content))
            comment_id = self.db.cursor.lastrowid

            # 获取评论者信息
            user_sql = "SELECT username, nickname, avatar FROM Users WHERE id = %s"
            user_info = self.db.fetchone(user_sql, (user_id,))

            # 创建评论对象
            comment = {
                'id': comment_id,
                'post_id': post_id,
                'user_id': user_id,
                'username': user_info.get('username', ''),
                'nickname': user_info.get('nickname', ''),
                'avatar': user_info.get('avatar', ''),
                'comment_content': content,
                'created_at': datetime.datetime.now()
            }

            # 添加通知
            if post['user_id'] != user_id:
                self.mongo.db.notifications.insert_one({
                    'user_id': post['user_id'],
                    'actor_id': user_id,
                    'actor_name': user_info.get('nickname') or user_info.get('username', '用户'),
                    'actor_avatar': user_info.get('avatar', ''),
                    'action': 'comment',
                    'content_id': int(post_id),
                    'content_type': 'post',
                    'content_title': post.get('title', ''),
                    'comment_id': comment_id,
                    'comment_content': content[:100],  # 存储评论预览
                    'is_read': False,
                    'created_at': datetime.datetime.now()
                })

            # 检查评论中是否有@提及用户
            mentions = self._extract_mentions(content)
            if mentions:
                self._process_mentions(mentions, post_id, user_id, comment_id, content, post.get('title', ''))

            return {
                "success": True,
                "comment_id": comment_id,
                "comment": comment
            }

        except Exception as e:
            return {"success": False, "message": f"评论失败: {str(e)}"}

    def _extract_mentions(self, content):
        """从评论内容中提取@的用户名"""
        import re
        # 匹配@username格式的提及
        mentions = re.findall(r'@(\w+)', content)
        return mentions

    def _process_mentions(self, mentions, post_id, commenter_id, comment_id, comment_content, post_title):
        """处理评论中@提及的用户，发送通知"""
        try:
            # 获取提及的用户信息
            if not mentions:
                return

            # 获取评论者信息
            commenter_sql = "SELECT username, nickname, avatar FROM Users WHERE id = %s"
            commenter = self.db.fetchone(commenter_sql, (commenter_id,))
            commenter_name = commenter.get('nickname') or commenter.get('username', '用户')

            # 查找用户名匹配的用户
            placeholders = ', '.join(['%s'] * len(mentions))
            users_sql = f"""
                         SELECT id, username, nickname
                         FROM Users
                         WHERE username IN ({placeholders}) \
                         """
            mentioned_users = self.db.query(users_sql, tuple(mentions))

            # 为每个被提及的用户创建通知
            for user in mentioned_users:
                # 避免给自己发通知
                if user['id'] == commenter_id:
                    continue

                self.mongo.db.notifications.insert_one({
                    'user_id': user['id'],
                    'actor_id': commenter_id,
                    'actor_name': commenter_name,
                    'actor_avatar': commenter.get('avatar', ''),
                    'action': 'mention',
                    'content_id': int(post_id),
                    'content_type': 'post',
                    'content_title': post_title,
                    'comment_id': comment_id,
                    'comment_content': comment_content[:100],
                    'is_read': False,
                    'created_at': datetime.datetime.now()
                })

        except Exception as e:
            # 提及处理失败不应影响主评论流程
            print(f"处理用户提及时出错: {str(e)}")

    def get_likes(self, post_id, page=1, page_size=20):
        """获取动态点赞用户（带头像）"""
        try:
            offset = (page - 1) * page_size

            # 获取点赞用户列表，包含头像信息
            likes_sql = """
                        SELECT pi.user_id, pi.created_at, u.username, u.nickname, u.avatar
                        FROM PostInteractions pi
                                 JOIN Users u ON pi.user_id = u.id
                        WHERE pi.post_id = %s \
                          AND pi.interaction_type = 'like'
                        ORDER BY pi.created_at DESC
                        LIMIT %s OFFSET %s \
                        """

            likes = self.db.query(likes_sql, (post_id, page_size, offset))

            # 获取总点赞数
            count_sql = """
                        SELECT COUNT(*) as total
                        FROM PostInteractions
                        WHERE post_id = %s \
                          AND interaction_type = 'like' \
                        """
            count_result = self.db.fetchone(count_sql, (post_id,))
            total = count_result['total'] if count_result else 0

            return {
                'likes': likes,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }

        except Exception as e:
            print(f"获取点赞用户失败: {e}")
            return {
                'likes': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0
            }

    def get_post_detail_with_interactions(self, post_id, user_id=None):
        """
        获取动态详情，包含完整的点赞用户和评论信息
        """
        # 获取基本动态信息
        post = self.get_post_detail(post_id, user_id)
        if not post:
            return None

        try:
            # 获取完整的点赞用户列表（带头像）
            likes_data = self.get_likes_with_avatars(post_id, page=1, page_size=20)
            post['likes_data'] = likes_data

            # 获取完整的评论列表（带头像）
            comments_data = self.get_comments_with_avatars(post_id, page=1, page_size=10)
            post['comments_data'] = comments_data

            return post

        except Exception as e:
            print(f"获取动态交互信息失败: {e}")
            return post

    def get_likes_with_avatars(self, post_id, page=1, page_size=20):
        """获取点赞用户列表（包含头像信息）"""
        try:
            offset = (page - 1) * page_size

            # 获取点赞用户列表，包含完整用户信息
            likes_sql = """
                        SELECT pi.user_id, \
                               pi.created_at,
                               u.username, \
                               u.nickname, \
                               u.avatar,
                               u.id as user_id
                        FROM PostInteractions pi
                                 JOIN Users u ON pi.user_id = u.id
                        WHERE pi.post_id = %s \
                          AND pi.interaction_type = 'like'
                        ORDER BY pi.created_at DESC
                        LIMIT %s OFFSET %s \
                        """

            likes = self.db.query(likes_sql, (post_id, page_size, offset))

            # 获取总点赞数
            count_sql = """
                        SELECT COUNT(*) as total
                        FROM PostInteractions
                        WHERE post_id = %s \
                          AND interaction_type = 'like' \
                        """
            count_result = self.db.fetchone(count_sql, (post_id,))
            total = count_result['total'] if count_result else 0

            # 处理头像数据
            for like in likes:
                # 确保头像键存在
                if not like.get('avatar'):
                    like['avatar'] = None

            return {
                'likes': likes,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size,
                'has_more': total > page * page_size
            }

        except Exception as e:
            print(f"获取点赞用户失败: {e}")
            return {
                'likes': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0,
                'has_more': False
            }

    def get_comments_with_avatars(self, post_id, page=1, page_size=10):
        """获取评论列表（包含头像信息）"""
        try:
            offset = (page - 1) * page_size

            # 获取评论列表，包含完整用户信息
            comments_sql = """
                           SELECT pi.id, \
                                  pi.user_id, \
                                  pi.comment_content, \
                                  pi.created_at,
                                  u.username, \
                                  u.nickname, \
                                  u.avatar,
                                  u.id as commenter_id
                           FROM PostInteractions pi
                                    JOIN Users u ON pi.user_id = u.id
                           WHERE pi.post_id = %s \
                             AND pi.interaction_type = 'comment'
                           ORDER BY pi.created_at DESC
                           LIMIT %s OFFSET %s \
                           """

            comments = self.db.query(comments_sql, (post_id, page_size, offset))

            # 获取总评论数
            count_sql = """
                        SELECT COUNT(*) as total
                        FROM PostInteractions
                        WHERE post_id = %s \
                          AND interaction_type = 'comment' \
                        """
            count_result = self.db.fetchone(count_sql, (post_id,))
            total = count_result['total'] if count_result else 0

            # 处理头像数据和评论内容
            for comment in comments:
                # 确保头像键存在
                if not comment.get('avatar'):
                    comment['avatar'] = None

                # 处理评论内容中的换行符
                if comment.get('comment_content'):
                    comment['comment_content'] = comment['comment_content'].replace('\n', '<br>')

            return {
                'comments': comments,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size,
                'has_more': total > page * page_size
            }

        except Exception as e:
            print(f"获取评论失败: {e}")
            return {
                'comments': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0,
                'has_more': False
            }

    def load_more_likes(self, post_id, page, user_id=None):
        """加载更多点赞用户"""
        return self.get_likes_with_avatars(post_id, page=page, page_size=20)

    def load_more_comments(self, post_id, page, user_id=None):
        """加载更多评论"""
        return self.get_comments_with_avatars(post_id, page=page, page_size=10)

