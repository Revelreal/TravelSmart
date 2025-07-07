# MainProject/app/services/user_profile_service.py
from MainProject.dbhelper.SQLHelper import SQLHelper
from MainProject.dbhelper.MONGOHelper import MongoHelper


class UserProfileService:
    def __init__(self):
        self.db = SQLHelper()
        self.mongo = MongoHelper()

    def get_user_profile(self, user_id, viewer_id=None):
        """获取用户个人资料"""
        sql = """
              SELECT u.id, \
                     u.username, \
                     u.nickname, \
                     u.avatar, \
                     u.city, \
                     u.create_time,
                     (SELECT COUNT(*) \
                      FROM Friendships \
                      WHERE user_id = u.id AND status = 'accepted')          as friend_count,
                     (SELECT COUNT(*) FROM TravelPosts WHERE user_id = u.id) as post_count,
                     ups.profile_visibility, \
                     ups.show_online_status
              FROM Users u
                       LEFT JOIN UserPrivacySettings ups ON u.id = ups.user_id
              WHERE u.id = %s \
              """
        profile = self.db.fetchone(sql, (user_id,))

        if not profile:
            return None

        # 检查隐私设置
        if viewer_id != user_id and profile.get('profile_visibility') != 'public':
            if profile.get('profile_visibility') == 'private':
                return {'id': user_id, 'privacy': 'private'}
            elif profile.get('profile_visibility') == 'friends':
                # 检查是否是好友
                friendship_sql = """
                                 SELECT id \
                                 FROM Friendships
                                 WHERE user_id = %s \
                                   AND friend_id = %s \
                                   AND status = 'accepted' \
                                 """
                friendship = self.db.fetchone(friendship_sql, (user_id, viewer_id))
                if not friendship:
                    return {'id': user_id, 'privacy': 'friends_only'}

        # 如果是查看自己的资料或有权限查看，返回完整资料
        return profile

    def update_user_profile(self, user_id, profile_data):
        """更新用户个人资料"""
        allowed_fields = ['nickname', 'avatar', 'city']
        update_fields = []
        params = []

        for field in allowed_fields:
            if field in profile_data:
                update_fields.append(f"{field} = %s")
                params.append(profile_data[field])

        if not update_fields:
            return False, "没有提供要更新的字段"

        sql = f"UPDATE Users SET {', '.join(update_fields)} WHERE id = %s"
        params.append(user_id)

        try:
            self.db.execute(sql, tuple(params))
            return True, "个人资料已更新"
        except Exception as e:
            return False, f"更新个人资料失败: {str(e)}"

    def get_user_favorites(self, user_id, content_type=None, page=1, page_size=6):
        """获取用户收藏内容"""
        if not user_id:
            return {
                'favorites': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0
            }

        offset = (page - 1) * page_size

        # 构建基本查询
        sql = """
              SELECT uf.id, uf.content_id, uf.content_type, uf.created_at
              FROM UserFavorites uf
              WHERE uf.user_id = %s \
              """
        params = [user_id]

        # 按内容类型筛选
        if content_type:
            sql += " AND uf.content_type = %s"
            params.append(content_type)

        # 添加排序和分页
        sql += " ORDER BY uf.created_at DESC LIMIT %s OFFSET %s"
        params.extend([page_size, offset])

        try:
            favorites = self.db.query(sql, tuple(params))

            # 详细日志输出，帮助调试
            print(f"获取到 {len(favorites)} 条收藏记录")

            # 获取每个收藏项的详细信息
            for fav in favorites:
                if fav['content_type'] == 'post':
                    # 获取动态信息
                    post_sql = """
                           SELECT p.id, p.title, p.content, p.created_at, p.location_name,
                                  p.user_id, u.username, u.nickname, u.avatar
                           FROM TravelPosts p
                                    JOIN Users u ON p.user_id = u.id
                           WHERE p.id = %s \
                           """
                    post = self.db.fetchone(post_sql, (fav['content_id'],))
                    if post:
                        fav['details'] = post

                        # 获取标签
                        tags_sql = "SELECT tag_name FROM PostTags WHERE post_id = %s"
                        tags = self.db.query(tags_sql, (fav['content_id'],))
                        fav['details']['tags'] = [tag['tag_name'] for tag in tags]

                        # 获取动态第一张媒体作为预览
                        media_sql = "SELECT * FROM PostMedia WHERE post_id = %s"
                        media = self.db.query(media_sql, (fav['content_id'],))
                        fav['media'] = media if media else []
                        fav['preview_media'] = media[0] if media else None
                    else:
                        print(f"收藏的动态 {fav['content_id']} 不存在")

            # 获取总收藏数
            count_sql = "SELECT COUNT(*) as total FROM UserFavorites WHERE user_id = %s"
            count_params = [user_id]

            if content_type:
                count_sql += " AND content_type = %s"
                count_params.append(content_type)

            count_result = self.db.fetchone(count_sql, tuple(count_params))
            total = count_result['total'] if count_result else 0

            return {
                'favorites': favorites,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
        except Exception as e:
            print(f"获取收藏失败: {str(e)}")
            # 返回空结果而不是抛出异常
            return {
                'favorites': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0,
                'error': str(e)
            }

    def remove_favorite(self, favorite_id, user_id):
        """删除收藏"""
        if not favorite_id or not user_id:
            print("移除收藏失败：无效的收藏ID或用户ID")
            return False, "收藏ID或用户ID无效"

        # 检查收藏是否存在且属于该用户
        check_sql = "SELECT id, content_id, content_type FROM UserFavorites WHERE id = %s AND user_id = %s"
        favorite = self.db.fetchone(check_sql, (favorite_id, user_id))

        if not favorite:
            print(f"移除收藏失败：收藏 {favorite_id} 不存在或不属于用户 {user_id}")
            return False, "收藏不存在或无权操作"

        try:
            print(f"开始移除收藏: ID={favorite_id}, 用户ID={user_id}")
            # 开始事务
            self.db.execute("START TRANSACTION")

            # 删除收藏
            delete_sql = "DELETE FROM UserFavorites WHERE id = %s"
            self.db.execute(delete_sql, (favorite_id,))

            # 如果是动态，同时删除交互记录
            if favorite['content_type'] == 'post':
                content_id = favorite['content_id']
                print(f"同时删除动态交互记录: 动态ID={content_id}, 用户ID={user_id}")
                delete_interaction_sql = """
                    DELETE FROM PostInteractions 
                    WHERE post_id = %s AND user_id = %s AND interaction_type = 'favorite'
                """
                self.db.execute(delete_interaction_sql, (content_id, user_id))

            # 提交事务
            self.db.execute("COMMIT")
            print(f"成功移除收藏: ID={favorite_id}")
            return True, "已取消收藏"
        except Exception as e:
            # 回滚事务
            self.db.execute("ROLLBACK")
            print(f"移除收藏失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, f"取消收藏失败: {str(e)}"

    def get_self_posts(self, user_id, privacy_level=None, page=1, page_size=6):
        """用户获取自己发布的动态

        Args:
            user_id: 用户ID
            privacy_level: 动态的隐私级别 ('public', 'friends', 'private' 或 None 表示全部)
            page: 页码
            page_size: 每页大小

        Returns:
            包含动态列表及分页信息的字典
        """
        # 构建基础查询 - 只获取自己发布的动态
        conditions = ["p.user_id = %s"]
        params = [user_id]

        # 如果指定了隐私级别，添加过滤条件
        if privacy_level in ['public', 'friends', 'private']:
            conditions.append("p.privacy_level = %s")
            params.append(privacy_level)

        # 构建SQL查询
        sql = """
        SELECT p.*, u.username, u.nickname, u.avatar,
               COUNT(DISTINCT pi_like.id) as like_count,
               COUNT(DISTINCT pi_comment.id) as comment_count
        FROM TravelPosts p
        JOIN Users u ON p.user_id = u.id
        LEFT JOIN PostInteractions pi_like ON p.id = pi_like.post_id AND pi_like.interaction_type = 'like'
        LEFT JOIN PostInteractions pi_comment ON p.id = pi_comment.post_id AND pi_comment.interaction_type = 'comment'
        WHERE """ + " AND ".join(conditions) + """
        GROUP BY p.id
        ORDER BY p.created_at DESC
        LIMIT %s OFFSET %s
        """

        offset = (page - 1) * page_size
        params.extend([page_size, offset])

        posts = self.db.query(sql, tuple(params))

        # 获取每个动态的标签和预览媒体
        for post in posts:
            tags_sql = "SELECT tag_name FROM PostTags WHERE post_id = %s"
            tags = self.db.query(tags_sql, (post['id'],))
            post['tags'] = [tag['tag_name'] for tag in tags]

            media_sql = "SELECT * FROM PostMedia WHERE post_id = %s LIMIT 1"
            media = self.db.query(media_sql, (post['id'],))
            post['preview_media'] = media[0] if media else None

            # 检查用户是否已点赞/收藏自己的动态
            interaction_sql = """
                              SELECT interaction_type
                              FROM PostInteractions
                              WHERE post_id = %s 
                                AND user_id = %s 
                                AND interaction_type IN ('like', 'favorite')
                              """
            interactions = self.db.query(interaction_sql, (post['id'], user_id))
            post['user_liked'] = any(i['interaction_type'] == 'like' for i in interactions)
            post['user_favorited'] = any(i['interaction_type'] == 'favorite' for i in interactions)

        # 获取总记录数
        count_sql = """
                    SELECT COUNT(*) as total
                    FROM TravelPosts p
                    WHERE """ + " AND ".join(conditions)

        count_result = self.db.fetchone(count_sql, tuple(params[:-2]))  # 移除LIMIT参数
        total = count_result['total'] if count_result else 0

        return {
            'posts': posts,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }

    def get_user_notifications(self, user_id, is_read=None, page=1, page_size=20):
        """获取用户通知"""
        # 构建查询条件
        query = {'user_id': user_id}
        if is_read is not None:
            query['is_read'] = is_read

        # 分页
        skip = (page - 1) * page_size

        # 查询通知
        notifications = list(self.mongo.db.notifications.find(
            query,
            sort=[('created_at', -1)],
            skip=skip,
            limit=page_size
        ))

        # 获取通知中涉及的用户信息
        actor_ids = [n['actor_id'] for n in notifications if 'actor_id' in n]
        if actor_ids:
            users_sql = """
            SELECT id, username, nickname, avatar 
            FROM Users 
            WHERE id IN (%s)
            """ % ','.join(['%s'] * len(actor_ids))

            users = self.db.query(users_sql, tuple(actor_ids))
            users_dict = {user['id']: user for user in users}

            # 将用户信息添加到通知中
            for notification in notifications:
                if 'actor_id' in notification and notification['actor_id'] in users_dict:
                    notification['actor'] = users_dict[notification['actor_id']]

        # 获取总通知数
        total = self.mongo.db.notifications.count_documents(query)

        return {
            'notifications': notifications,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size,
            'unread_count': self.mongo.db.notifications.count_documents({'user_id': user_id, 'is_read': False})
        }

    def mark_notifications_read(self, user_id, notification_ids=None):
        """将通知标记为已读"""
        query = {'user_id': user_id}
        if notification_ids:
            query['_id'] = {'$in': notification_ids}

        try:
            result = self.mongo.db.notifications.update_many(
                query,
                {'$set': {'is_read': True}}
            )
            return True, f"已将{result.modified_count}条通知标记为已读"
        except Exception as e:
            return False, f"标记通知失败: {str(e)}"

    def get_privacy_settings(self, user_id):
        """获取用户隐私设置"""
        sql = "SELECT * FROM UserPrivacySettings WHERE user_id = %s"
        settings = self.db.fetchone(sql, (user_id,))

        if not settings:
            # 如果没有设置记录，创建默认设置
            default_settings = {
                'profile_visibility': 'public',
                'post_default_privacy': 'public',
                'allow_friend_requests': True,
                'show_online_status': True
            }

            insert_sql = """
                         INSERT INTO UserPrivacySettings
                         (user_id, profile_visibility, post_default_privacy, allow_friend_requests, \
                          show_online_status)
                         VALUES (%s, %s, %s, %s, %s) \
                         """
            self.db.execute(insert_sql, (
                user_id,
                default_settings['profile_visibility'],
                default_settings['post_default_privacy'],
                default_settings['allow_friend_requests'],
                default_settings['show_online_status']
            ))
            return default_settings

        return settings

    def update_privacy_settings(self, user_id, settings):
        """更新用户隐私设置"""
        allowed_fields = [
            'profile_visibility',
            'post_default_privacy',
            'allow_friend_requests',
            'show_online_status'
        ]

        # 构建更新语句
        update_fields = []
        params = []

        for field in allowed_fields:
            if field in settings:
                update_fields.append(f"{field} = %s")
                params.append(settings[field])

        if not update_fields:
            return False, "没有提供要更新的设置"

        sql = f"UPDATE UserPrivacySettings SET {', '.join(update_fields)} WHERE user_id = %s"
        params.append(user_id)

        try:
            self.db.execute(sql, tuple(params))
            return True, "隐私设置已更新"
        except Exception as e:
            return False, f"更新隐私设置失败: {str(e)}"

    def get_user_interactions(self, user_id, interaction_type=None, page=1, page_size=20):
        """获取用户互动历史"""
        offset = (page - 1) * page_size

        # 构建基本查询
        sql = """
              SELECT pi.id, \
                     pi.post_id, \
                     pi.interaction_type, \
                     pi.comment_content, \
                     pi.created_at,
                     p.title, \
                     p.content, \
                     p.user_id  as post_author_id,
                     u.username as author_username, \
                     u.nickname as author_nickname
              FROM PostInteractions pi
                       JOIN TravelPosts p ON pi.post_id = p.id
                       JOIN Users u ON p.user_id = u.id
              WHERE pi.user_id = %s \
              """
        params = [user_id]

        # 按互动类型筛选
        if interaction_type:
            sql += " AND pi.interaction_type = %s"
            params.append(interaction_type)

        # 添加排序和分页
        sql += " ORDER BY pi.created_at DESC LIMIT %s OFFSET %s"
        params.extend([page_size, offset])

        interactions = self.db.query(sql, tuple(params))

        # 获取总记录数
        count_sql = "SELECT COUNT(*) as total FROM PostInteractions WHERE user_id = %s"
        count_params = [user_id]

        if interaction_type:
            count_sql += " AND interaction_type = %s"
            count_params.append(interaction_type)

        count_result = self.db.fetchone(count_sql, tuple(count_params))
        total = count_result['total'] if count_result else 0

        return {
            'interactions': interactions,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }

    def get_favorite_id_by_content(self, content_id, user_id, content_type="post"):
        """通过内容ID获取收藏ID"""
        if not content_id or not user_id:
            print("获取收藏ID失败: 内容ID或用户ID为空")
            return None

        try:
            # 查询该用户是否收藏了这个内容
            query = """
                SELECT id 
                FROM UserFavorites 
                WHERE user_id = %s AND content_id = %s AND content_type = %s
                LIMIT 1
            """
            result = self.db.fetchone(query, (user_id, content_id, content_type))

            if result:
                print(f"成功获取收藏ID: {result['id']} (内容ID={content_id}, 用户ID={user_id})")
                return result['id']
            else:
                print(f"未找到收藏记录: 内容ID={content_id}, 用户ID={user_id}")
                return None
        except Exception as e:
            print(f"查询收藏ID失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

