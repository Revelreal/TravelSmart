# MainProject/app/services/user_stats_service.py

from MainProject.dbhelper.SQLHelper import SQLHelper
from MainProject.dbhelper.MONGOHelper import MongoHelper


def get_default_statistics():
    """获取默认的统计数据（当出错时使用）

    Returns:
        dict: 包含默认值的统计数据字典
    """
    return {
        "friend_count": 0,
        "accepted_friends": 0,
        "pending_friends": 0,
        "accepted_percent": 0,
        "sent_messages": 0,
        "received_messages": 0,
        "post_count": 0,
        "public_percent": 0,
        "friends_percent": 0,
        "private_percent": 0,
        "image_count": 0,
        "video_count": 0,
        "like_count": 0,
        "comment_count": 0,
        "favorite_count": 0,
        "engagement_rate": 0,
        "avg_interactions": 0,
        "given_likes": 0,
        "given_comments": 0,
        "top_tags": [],
        "location_count": 0,
        "top_locations": []
    }


class UserStatsService:
    """用户统计信息服务，提供用户相关统计数据的获取和处理功能"""

    def __init__(self):
        self.db = SQLHelper()
        self.mongo = MongoHelper()

    def get_user_statistics(self, user_id):
        """获取用户的综合统计信息

        Args:
            user_id: 用户ID

        Returns:
            dict: 包含所有统计数据的字典
        """
        try:
            # 1. 好友统计
            friendship_stats = self.get_friendship_stats(user_id)

            # 2. 消息统计
            message_stats = self.get_message_stats(user_id)

            # 3. 动态统计
            post_stats = self.get_post_stats(user_id)

            # 4. 媒体统计
            media_stats = self.get_media_stats(user_id)

            # 5. 互动统计
            interaction_stats = self.get_interaction_stats(user_id)

            # 6. 标签统计
            tag_stats = self.get_tag_stats(user_id)

            # 7. 地点统计
            location_stats = self.get_location_stats(user_id)

            # 整合所有统计数据
            return {
                # 社交统计
                "friend_count": friendship_stats["total"],
                "accepted_friends": friendship_stats["accepted"],
                "pending_friends": friendship_stats["pending"],
                "accepted_percent": friendship_stats["accepted_percent"],
                "sent_messages": message_stats["sent"],
                "received_messages": message_stats["received"],

                # 内容统计
                "post_count": post_stats["total"],
                "public_percent": post_stats["public_percent"],
                "friends_percent": post_stats["friends_percent"],
                "private_percent": post_stats["private_percent"],
                "image_count": media_stats["image"],
                "video_count": media_stats["video"],

                # 互动统计
                "like_count": interaction_stats["received_likes"],
                "comment_count": interaction_stats["received_comments"],
                "favorite_count": interaction_stats["favorited"],
                "engagement_rate": interaction_stats["engagement_rate"],
                "avg_interactions": interaction_stats["avg_interactions"],
                "given_likes": interaction_stats["given_likes"],
                "given_comments": interaction_stats["given_comments"],

                # 标签统计
                "top_tags": tag_stats["top_tags"],

                # 地点统计
                "location_count": location_stats["total"],
                "top_locations": location_stats["top_locations"]
            }
        except Exception as e:
            print(f"Error getting user statistics: {str(e)}")
            return get_default_statistics()

    def get_friendship_stats(self, user_id):
        """获取用户的好友统计信息

        Args:
            user_id: 用户ID

        Returns:
            dict: 包含好友统计信息的字典
        """
        try:
            # 计算好友总数（包括待接受和已接受）
            total_query = """
                SELECT COUNT(*) as total FROM Friendships 
                WHERE user_id = %s OR friend_id = %s
            """
            total_result = self.db.fetchone(total_query, (user_id, user_id))
            total = total_result['total'] if total_result else 0

            # 计算已接受的好友数量
            accepted_query = """
                SELECT COUNT(*) as accepted FROM Friendships 
                WHERE (user_id = %s OR friend_id = %s) AND status = 'accepted'
            """
            accepted_result = self.db.fetchone(accepted_query, (user_id, user_id))
            accepted = accepted_result['accepted'] if accepted_result else 0

            # 计算待处理的好友请求数量
            # 作为接收者的待处理请求
            pending_received_query = """
                SELECT COUNT(*) as pending FROM Friendships 
                WHERE friend_id = %s AND status = 'pending'
            """
            pending_received_result = self.db.fetchone(pending_received_query, (user_id,))
            pending_received = pending_received_result['pending'] if pending_received_result else 0

            # 作为发送者的待处理请求
            pending_sent_query = """
                SELECT COUNT(*) as pending FROM Friendships 
                WHERE user_id = %s AND status = 'pending'
            """
            pending_sent_result = self.db.fetchone(pending_sent_query, (user_id,))
            pending_sent = pending_sent_result['pending'] if pending_sent_result else 0

            # 总的待处理请求
            pending = pending_received + pending_sent

            # 计算已屏蔽的用户数量
            # 屏蔽了别人
            blocked_others_query = """
                SELECT COUNT(*) as blocked FROM Friendships 
                WHERE user_id = %s AND status = 'blocked'
            """
            blocked_others_result = self.db.fetchone(blocked_others_query, (user_id,))
            blocked_others = blocked_others_result['blocked'] if blocked_others_result else 0

            # 被别人屏蔽
            blocked_by_others_query = """
                SELECT COUNT(*) as blocked FROM Friendships 
                WHERE friend_id = %s AND status = 'blocked'
            """
            blocked_by_others_result = self.db.fetchone(blocked_by_others_query, (user_id,))
            blocked_by_others = blocked_by_others_result['blocked'] if blocked_by_others_result else 0

            # 总的屏蔽关系
            blocked = blocked_others + blocked_by_others

            # 计算已接受好友的百分比
            accepted_percent = 0
            if total > 0:
                accepted_percent = round((accepted / total) * 100)

            return {
                "total": total,
                "accepted": accepted,
                "pending": pending,
                "pending_received": pending_received,
                "pending_sent": pending_sent,
                "blocked": blocked,
                "blocked_others": blocked_others,
                "blocked_by_others": blocked_by_others,
                "accepted_percent": accepted_percent
            }
        except Exception as e:
            print(f"Error getting friendship stats: {str(e)}")
            return {
                "total": 0,
                "accepted": 0,
                "pending": 0,
                "pending_received": 0,
                "pending_sent": 0,
                "blocked": 0,
                "blocked_others": 0,
                "blocked_by_others": 0,
                "accepted_percent": 0
            }

    def get_message_stats(self, user_id):
        """获取用户的消息统计信息

        Args:
            user_id: 用户ID

        Returns:
            dict: 包含消息统计信息的字典
        """
        try:
            # 计算发送的消息数量
            sent_query = """
                SELECT COUNT(*) as sent FROM Messages 
                WHERE sender_id = %s
            """
            sent_result = self.db.fetchone(sent_query, (user_id,))
            sent = sent_result['sent'] if sent_result else 0

            # 计算接收的消息数量
            received_query = """
                SELECT COUNT(*) as received FROM Messages 
                WHERE receiver_id = %s
            """
            received_result = self.db.fetchone(received_query, (user_id,))
            received = received_result['received'] if received_result else 0

            # 计算未读消息数量
            unread_query = """
                SELECT COUNT(*) as unread FROM Messages 
                WHERE receiver_id = %s AND is_read = FALSE
            """
            unread_result = self.db.fetchone(unread_query, (user_id,))
            unread = unread_result['unread'] if unread_result else 0

            # 按类型统计发送的消息
            type_stats_query = """
                SELECT content_type, COUNT(*) as count
                FROM Messages 
                WHERE sender_id = %s
                GROUP BY content_type
            """
            type_stats_rows = self.db.query(type_stats_query, (user_id,))

            type_stats = {
                "text": 0,
                "image": 0,
                "location": 0,
                "shared_content": 0
            }

            if type_stats_rows:
                for row in type_stats_rows:
                    content_type = row.get("content_type")
                    count = row.get("count", 0)
                    if content_type in type_stats:
                        type_stats[content_type] = count

            return {
                "sent": sent,
                "received": received,
                "total": sent + received,
                "unread": unread,
                "type_stats": type_stats
            }
        except Exception as e:
            print(f"Error getting message stats: {str(e)}")
            return {
                "sent": 0,
                "received": 0,
                "total": 0,
                "unread": 0,
                "type_stats": {
                    "text": 0,
                    "image": 0,
                    "location": 0,
                    "shared_content": 0
                }
            }

    def get_post_stats(self, user_id):
        """获取用户的动态统计信息

        Args:
            user_id: 用户ID

        Returns:
            dict: 包含动态统计信息的字典
        """
        try:
            # 计算动态总数
            total_query = """
                SELECT COUNT(*) as total FROM TravelPosts 
                WHERE user_id = %s
            """
            total_result = self.db.fetchone(total_query, (user_id,))
            total = total_result['total'] if total_result else 0

            if total == 0:
                return {
                    "total": 0,
                    "public": 0,
                    "friends": 0,
                    "private": 0,
                    "public_percent": 0,
                    "friends_percent": 0,
                    "private_percent": 0,
                    "total_views": 0,
                    "avg_views": 0
                }

            # 计算公开动态数量
            public_query = """
                SELECT COUNT(*) as public_count FROM TravelPosts 
                WHERE user_id = %s AND privacy_level = 'public'
            """
            public_result = self.db.fetchone(public_query, (user_id,))
            public_count = public_result['public_count'] if public_result else 0

            # 计算好友可见动态数量
            friends_query = """
                SELECT COUNT(*) as friends_count FROM TravelPosts 
                WHERE user_id = %s AND privacy_level = 'friends'
            """
            friends_result = self.db.fetchone(friends_query, (user_id,))
            friends_count = friends_result['friends_count'] if friends_result else 0

            # 计算私密动态数量
            private_query = """
                SELECT COUNT(*) as private_count FROM TravelPosts 
                WHERE user_id = %s AND privacy_level = 'private'
            """
            private_result = self.db.fetchone(private_query, (user_id,))
            private_count = private_result['private_count'] if private_result else 0

            # 计算总浏览量
            views_query = """
                SELECT SUM(view_count) as total_views FROM TravelPosts 
                WHERE user_id = %s
            """
            views_result = self.db.fetchone(views_query, (user_id,))
            total_views = views_result['total_views'] if views_result and views_result['total_views'] else 0

            # 计算平均浏览量
            avg_views = round(total_views / total, 1) if total > 0 else 0

            # 计算各类型的百分比
            public_percent = round((public_count / total) * 100)
            friends_percent = round((friends_count / total) * 100)
            private_percent = round((private_count / total) * 100)

            # 获取按月份统计的动态数量
            monthly_posts_query = """
                SELECT 
                    YEAR(created_at) as year,
                    MONTH(created_at) as month,
                    COUNT(*) as count
                FROM TravelPosts
                WHERE user_id = %s
                GROUP BY YEAR(created_at), MONTH(created_at)
                ORDER BY YEAR(created_at) DESC, MONTH(created_at) DESC
                LIMIT 12
            """
            monthly_posts_rows = self.db.query(monthly_posts_query, (user_id,))

            monthly_posts = []
            if monthly_posts_rows:
                for row in monthly_posts_rows:
                    monthly_posts.append({
                        "year": row.get("year"),
                        "month": row.get("month"),
                        "count": row.get("count", 0)
                    })

            return {
                "total": total,
                "public": public_count,
                "friends": friends_count,
                "private": private_count,
                "public_percent": public_percent,
                "friends_percent": friends_percent,
                "private_percent": private_percent,
                "total_views": total_views,
                "avg_views": avg_views,
                "monthly_posts": monthly_posts
            }
        except Exception as e:
            print(f"Error getting post stats: {str(e)}")
            return {
                "total": 0,
                "public": 0,
                "friends": 0,
                "private": 0,
                "public_percent": 0,
                "friends_percent": 0,
                "private_percent": 0,
                "total_views": 0,
                "avg_views": 0,
                "monthly_posts": []
            }

    def get_media_stats(self, user_id):
        """获取用户的媒体内容统计信息

        Args:
            user_id: 用户ID

        Returns:
            dict: 包含媒体统计信息的字典
        """
        try:
            # 计算图片数量
            image_query = """
                SELECT COUNT(*) as image_count FROM PostMedia 
                JOIN TravelPosts ON PostMedia.post_id = TravelPosts.id
                WHERE TravelPosts.user_id = %s AND PostMedia.media_type = 'image'
            """
            image_result = self.db.fetchone(image_query, (user_id,))
            image_count = image_result['image_count'] if image_result else 0

            # 计算视频数量
            video_query = """
                SELECT COUNT(*) as video_count FROM PostMedia 
                JOIN TravelPosts ON PostMedia.post_id = TravelPosts.id
                WHERE TravelPosts.user_id = %s AND PostMedia.media_type = 'video'
            """
            video_result = self.db.fetchone(video_query, (user_id,))
            video_count = video_result['video_count'] if video_result else 0

            # 计算平均每条动态的媒体数量
            avg_media_per_post_query = """
                SELECT AVG(media_count) as avg_count FROM (
                    SELECT TravelPosts.id, COUNT(PostMedia.id) as media_count
                    FROM TravelPosts 
                    LEFT JOIN PostMedia ON TravelPosts.id = PostMedia.post_id
                    WHERE TravelPosts.user_id = %s
                    GROUP BY TravelPosts.id
                ) as post_media_counts
            """
            avg_result = self.db.fetchone(avg_media_per_post_query, (user_id,))
            avg_media_per_post = round(avg_result['avg_count'], 1) if avg_result and avg_result['avg_count'] else 0

            return {
                "image": image_count,
                "video": video_count,
                "total": image_count + video_count,
                "avg_per_post": avg_media_per_post
            }
        except Exception as e:
            print(f"Error getting media stats: {str(e)}")
            return {
                "image": 0,
                "video": 0,
                "total": 0,
                "avg_per_post": 0
            }

    def get_interaction_stats(self, user_id):
        """获取用户的互动统计信息

        Args:
            user_id: 用户ID

        Returns:
            dict: 包含互动统计信息的字典
        """
        try:
            # 获取动态总数
            post_count_query = """
                SELECT COUNT(*) as post_count FROM TravelPosts 
                WHERE user_id = %s
            """
            post_count_result = self.db.fetchone(post_count_query, (user_id,))
            post_count = post_count_result['post_count'] if post_count_result else 0

            # 计算收到的点赞数
            likes_query = """
                SELECT COUNT(*) as likes FROM PostInteractions
                JOIN TravelPosts ON PostInteractions.post_id = TravelPosts.id
                WHERE TravelPosts.user_id = %s AND PostInteractions.interaction_type = 'like'
            """
            likes_result = self.db.fetchone(likes_query, (user_id,))
            received_likes = likes_result['likes'] if likes_result else 0

            # 计算收到的评论数
            comments_query = """
                SELECT COUNT(*) as comments FROM PostInteractions
                JOIN TravelPosts ON PostInteractions.post_id = TravelPosts.id
                WHERE TravelPosts.user_id = %s AND PostInteractions.interaction_type = 'comment'
            """
            comments_result = self.db.fetchone(comments_query, (user_id,))
            received_comments = comments_result['comments'] if comments_result else 0

            # 计算被收藏数
            favorites_query = """
                SELECT COUNT(*) as favorites FROM UserFavorites
                JOIN TravelPosts ON UserFavorites.content_id = TravelPosts.id
                WHERE TravelPosts.user_id = %s AND UserFavorites.content_type = 'post'
            """
            favorites_result = self.db.fetchone(favorites_query, (user_id,))
            favorited = favorites_result['favorites'] if favorites_result else 0

            # 计算给出的点赞数
            given_likes_query = """
                SELECT COUNT(*) as given_likes FROM PostInteractions
                WHERE user_id = %s AND interaction_type = 'like'
            """
            given_likes_result = self.db.fetchone(given_likes_query, (user_id,))
            given_likes = given_likes_result['given_likes'] if given_likes_result else 0

            # 计算给出的评论数
            given_comments_query = """
                SELECT COUNT(*) as given_comments FROM PostInteractions
                WHERE user_id = %s AND interaction_type = 'comment'
            """
            given_comments_result = self.db.fetchone(given_comments_query, (user_id,))
            given_comments = given_comments_result['given_comments'] if given_comments_result else 0

            # 计算平均每条动态的互动数
            total_interactions = received_likes + received_comments + favorited
            avg_interactions = round(total_interactions / post_count, 1) if post_count > 0 else 0

            # 计算互动率
            engagement_rate = 0
            if post_count > 0:
                # 假设每条动态平均能被100人看到
                avg_reach = 100
                engagement_rate = round((total_interactions / (post_count * avg_reach)) * 100, 1)

                # 确保互动率不超过100%
                engagement_rate = min(engagement_rate, 100)

            # 获取点赞最多的动态
            top_liked_post_query = """
                SELECT TravelPosts.id, TravelPosts.title, COUNT(*) as like_count
                FROM PostInteractions
                JOIN TravelPosts ON PostInteractions.post_id = TravelPosts.id
                WHERE TravelPosts.user_id = %s AND PostInteractions.interaction_type = 'like'
                GROUP BY TravelPosts.id, TravelPosts.title
                ORDER BY like_count DESC
                LIMIT 1
            """
            top_liked_post_result = self.db.fetchone(top_liked_post_query, (user_id,))
            top_liked_post = None
            if top_liked_post_result:
                top_liked_post = {
                    "id": top_liked_post_result.get("id"),
                    "title": top_liked_post_result.get("title"),
                    "like_count": top_liked_post_result.get("like_count")
                }

            return {
                "received_likes": received_likes,
                "received_comments": received_comments,
                "favorited": favorited,
                "given_likes": given_likes,
                "given_comments": given_comments,
                "total_interactions": total_interactions,
                "avg_interactions": avg_interactions,
                "engagement_rate": engagement_rate,
                "top_liked_post": top_liked_post
            }
        except Exception as e:
            print(f"Error getting interaction stats: {str(e)}")
            return {
                "received_likes": 0,
                "received_comments": 0,
                "favorited": 0,
                "given_likes": 0,
                "given_comments": 0,
                "total_interactions": 0,
                "avg_interactions": 0,
                "engagement_rate": 0,
                "top_liked_post": None
            }

    def get_tag_stats(self, user_id):
        """获取用户的标签统计信息

        Args:
            user_id: 用户ID

        Returns:
            dict: 包含标签统计信息的字典
        """
        try:
            # 获取用户使用最多的标签
            top_tags_query = """
                SELECT tag_name, COUNT(*) as count
                FROM PostTags
                JOIN TravelPosts ON PostTags.post_id = TravelPosts.id
                WHERE TravelPosts.user_id = %s
                GROUP BY tag_name
                ORDER BY count DESC
                LIMIT 10
            """
            top_tags_rows = self.db.query(top_tags_query, (user_id,))

            top_tags = []
            if top_tags_rows:
                for row in top_tags_rows:
                    top_tags.append({
                        "name": row.get("tag_name"),
                        "count": row.get("count", 0)
                    })

            # 计算使用标签的动态百分比
            total_posts_query = """
                SELECT COUNT(*) as total FROM TravelPosts 
                WHERE user_id = %s
            """
            total_posts_result = self.db.fetchone(total_posts_query, (user_id,))
            total_posts = total_posts_result['total'] if total_posts_result else 0

            posts_with_tags_query = """
                SELECT COUNT(DISTINCT TravelPosts.id) as count
                FROM TravelPosts
                JOIN PostTags ON TravelPosts.id = PostTags.post_id
                WHERE TravelPosts.user_id = %s
            """
            posts_with_tags_result = self.db.fetchone(posts_with_tags_query, (user_id,))
            posts_with_tags = posts_with_tags_result['count'] if posts_with_tags_result else 0

            tags_usage_percent = round((posts_with_tags / total_posts) * 100) if total_posts > 0 else 0

            return {
                "top_tags": top_tags,
                "total_unique_tags": len(top_tags),
                "posts_with_tags": posts_with_tags,
                "tags_usage_percent": tags_usage_percent
            }
        except Exception as e:
            print(f"Error getting tag stats: {str(e)}")
            return {
                "top_tags": [],
                "total_unique_tags": 0,
                "posts_with_tags": 0,
                "tags_usage_percent": 0
            }

    def get_location_stats(self, user_id):
        """获取用户的地点统计信息

        Args:
            user_id: 用户ID

        Returns:
            dict: 包含地点统计信息的字典
        """
        try:
            # 计算记录过的总地点数量
            total_locations_query = """
                SELECT COUNT(DISTINCT location_name) as total
                FROM TravelPosts
                WHERE user_id = %s AND location_name IS NOT NULL AND location_name != ''
            """
            total_result = self.db.fetchone(total_locations_query, (user_id,))
            total_locations = total_result['total'] if total_result else 0

            # 获取最常去的地点
            top_locations_query = """
                SELECT location_name as name, COUNT(*) as count
                FROM TravelPosts
                WHERE user_id = %s AND location_name IS NOT NULL AND location_name != ''
                GROUP BY location_name
                ORDER BY count DESC
                LIMIT 5
            """
            top_locations_rows = self.db.query(top_locations_query, (user_id,))

            top_locations = []
            if top_locations_rows:
                for row in top_locations_rows:
                    top_locations.append({
                        "name": row.get("name"),
                        "count": row.get("count", 0)
                    })

            # 计算带地点信息的动态百分比
            total_posts_query = """
                SELECT COUNT(*) as total FROM TravelPosts 
                WHERE user_id = %s
            """
            total_posts_result = self.db.fetchone(total_posts_query, (user_id,))
            total_posts = total_posts_result['total'] if total_posts_result else 0

            posts_with_location_query = """
                SELECT COUNT(*) as count
                FROM TravelPosts
                WHERE user_id = %s AND location_name IS NOT NULL AND location_name != ''
            """
            posts_with_location_result = self.db.fetchone(posts_with_location_query, (user_id,))
            posts_with_location = posts_with_location_result['count'] if posts_with_location_result else 0

            location_usage_percent = round((posts_with_location / total_posts) * 100) if total_posts > 0 else 0

            return {
                "total": total_locations,
                "top_locations": top_locations,
                "posts_with_location": posts_with_location,
                "location_usage_percent": location_usage_percent
            }
        except Exception as e:
            print(f"Error getting location stats: {str(e)}")
            return {
                "total": 0,
                "top_locations": [],
                "posts_with_location": 0,
                "location_usage_percent": 0
            }

    def generate_statistics_html(self, user_id):
        """为用户生成统计信息的HTML表示

        Args:
            user_id: 用户ID

        Returns:
            str: 包含用户统计信息的HTML代码
        """
        try:
            # 获取统计数据
            stats = self.get_user_statistics(user_id)

            # 构建标签云HTML
            tag_cloud_html = ""
            for tag in stats.get("top_tags", [])[:8]:
                tag_cloud_html += f'<span class="stats-tag">#{tag["name"]} ({tag["count"]})</span>'

            if not tag_cloud_html:
                tag_cloud_html = "<span class='stats-label'>暂无标签数据</span>"

            # 构建地点列表HTML
            locations_list_html = ""
            for loc in stats.get("top_locations", [])[:5]:
                locations_list_html += f'''<div class="stats-location-item">
                    <span class="stats-location-name">{loc["name"]}</span>
                    <span class="stats-location-count">{loc["count"]}次</span>
                </div>'''

            if not locations_list_html:
                locations_list_html = "<div class='stats-label'>暂无地点数据</div>"

            # 构建HTML内容
            html = f"""
            <style>
                .stats-container {{
                    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }}
                .stats-row {{
                    display: flex;
                    gap: 15px;
                    margin-bottom: 15px;
                    flex-wrap: wrap;
                }}
                .stats-card {{
                    border-radius: 10px;
                    padding: 18px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    flex: 1;
                    min-width: 200px;
                }}
                .stats-section-title {{
                    font-size: 16px;
                    font-weight: 600;
                    margin-bottom: 15px;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 12px;
                }}
                .stats-item {{
                    text-align: center;
                    padding: 10px;
                    border-radius: 8px;
                }}
                .stats-value {{
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 4px;
                }}
                .stats-label {{
                    font-size: 12px;
                }}
                .stats-tag-cloud {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                    margin-top: 10px;
                }}
                .stats-tag {{
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                }}
                .stats-location-item {{
                    display: flex;
                    justify-content: space-between;
                    padding: 8px 0;
                    border-bottom: 1px solid #eee;
                }}
                .stats-location-name {{
                    font-size: 14px;
                }}
                .stats-location-count {{
                    font-weight: 500;
                }}
                .stats-progress {{
                    height: 6px;
                    background: #ecf0f1;
                    border-radius: 3px;
                    margin-top: 8px;
                }}
                .stats-progress-bar {{
                    height: 100%;
                    border-radius: 3px;
                }}
            </style>

            <div class="stats-container">
                <!-- 社交统计 -->
                <div class="stats-row">
                    <div class="stats-card">
                        <div class="stats-section-title">社交概览</div>
                        <div class="stats-grid">
                            <div class="stats-item">
                                <div class="stats-value">{stats["friend_count"]}</div>
                                <div class="stats-label">好友总数</div>
                            </div>
                            <div class="stats-item">
                                <div class="stats-value">{stats["accepted_friends"]}</div>
                                <div class="stats-label">已接受好友</div>
                            </div>
                            <div class="stats-item">
                                <div class="stats-value">{stats["sent_messages"]}</div>
                                <div class="stats-label">发送消息</div>
                            </div>
                            <div class="stats-item">
                                <div class="stats-value">{stats["received_messages"]}</div>
                                <div class="stats-label">接收消息</div>
                            </div>
                        </div>
                    </div>

                    <!-- 内容统计 -->
                    <div class="stats-card">
                        <div class="stats-section-title">内容概览</div>
                        <div class="stats-grid">
                            <div class="stats-item">
                                <div class="stats-value">{stats["post_count"]}</div>
                                <div class="stats-label">发布动态</div>
                            </div>
                            <div class="stats-item">
                                <div class="stats-value">{stats["image_count"]}</div>
                                <div class="stats-label">分享图片</div>
                            </div>
                            <div class="stats-item">
                                <div class="stats-value">{stats["video_count"]}</div>
                                <div class="stats-label">分享视频</div>
                            </div>
                            <div class="stats-item">
                                <div class="stats-value">{stats["location_count"]}</div>
                                <div class="stats-label">标记地点</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 互动统计 -->
                <div class="stats-row">
                    <div class="stats-card">
                        <div class="stats-section-title">互动概览</div>
                        <div class="stats-grid">
                            <div class="stats-item">
                                <div class="stats-value">{stats["like_count"]}</div>
                                <div class="stats-label">收到点赞</div>
                            </div>
                            <div class="stats-item">
                                <div class="stats-value">{stats["comment_count"]}</div>
                                <div class="stats-label">收到评论</div>
                            </div>
                            <div class="stats-item">
                                <div class="stats-value">{stats["given_likes"]}</div>
                                <div class="stats-label">给出点赞</div>
                            </div>
                            <div class="stats-item">
                                <div class="stats-value">{stats["given_comments"]}</div>
                                <div class="stats-label">给出评论</div>
                            </div>
                        </div>
                    </div>

                    <!-- 内容隐私 -->
                    <div class="stats-card">
                        <div class="stats-section-title">内容隐私</div>
                        <div style="margin-bottom: 15px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                                <div class="stats-label">公开</div>
                                <div class="stats-label">{stats["public_percent"]}%</div>
                            </div>
                            <div class="stats-progress">
                                <div class="stats-progress-bar" style="width: {stats["public_percent"]}%; background: #2ecc71;"></div>
                            </div>
                        </div>
                        <div style="margin-bottom: 15px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                                <div class="stats-label">好友可见</div>
                                <div class="stats-label">{stats["friends_percent"]}%</div>
                            </div>
                            <div class="stats-progress">
                                <div class="stats-progress-bar" style="width: {stats["friends_percent"]}%; background: #f39c12;"></div>
                            </div>
                        </div>
                        <div>
                            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                                <div class="stats-label">私密</div>
                                <div class="stats-label">{stats["private_percent"]}%</div>
                            </div>
                            <div class="stats-progress">
                                <div class="stats-progress-bar" style="width: {stats["private_percent"]}%; background: #e74c3c;"></div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 标签和地点 -->
                <div class="stats-row">
                    <div class="stats-card">
                        <div class="stats-section-title">常用标签</div>
                        <div class="stats-tag-cloud">
                            {tag_cloud_html}
                        </div>
                    </div>

                    <div class="stats-card">
                        <div class="stats-section-title">常去地点</div>
                        {locations_list_html}
                    </div>
                </div>
            </div>
            """

            return html
        except Exception as e:
            print(f"Error generating statistics HTML: {str(e)}")
            return f"<div style='color:red'>加载统计数据失败: {str(e)}</div>"

    def get_simple_user_statistics(self, user_id):
        """获取简化版的用户统计信息

        Args:
            user_id: 用户ID

        Returns:
            str: 包含简化用户统计信息的HTML代码
        """
        try:
            # 使用直接的SQL查询获取基本统计信息

            # 1. 动态数量
            post_count_query = "SELECT COUNT(*) as count FROM TravelPosts WHERE user_id = %s"
            post_count_result = self.db.fetchone(post_count_query, (user_id,))
            post_count = post_count_result['count'] if post_count_result else 0

            # 2. 好友数量
            friend_count_query = """
                SELECT COUNT(*) as count FROM Friendships 
                WHERE (user_id = %s OR friend_id = %s) AND status = 'accepted'
            """
            friend_count_result = self.db.fetchone(friend_count_query, (user_id, user_id))
            friend_count = friend_count_result['count'] if friend_count_result else 0

            # 3. 收到的点赞数
            like_count_query = """
                SELECT COUNT(*) as count FROM PostInteractions
                JOIN TravelPosts ON PostInteractions.post_id = TravelPosts.id
                WHERE TravelPosts.user_id = %s AND PostInteractions.interaction_type = 'like'
            """
            like_count_result = self.db.fetchone(like_count_query, (user_id,))
            like_count = like_count_result['count'] if like_count_result else 0

            # 4. 收到的评论数
            comment_count_query = """
                SELECT COUNT(*) as count FROM PostInteractions
                JOIN TravelPosts ON PostInteractions.post_id = TravelPosts.id
                WHERE TravelPosts.user_id = %s AND PostInteractions.interaction_type = 'comment'
            """
            comment_count_result = self.db.fetchone(comment_count_query, (user_id,))
            comment_count = comment_count_result['count'] if comment_count_result else 0

            # 5. 上传的媒体数量
            media_count_query = """
                SELECT COUNT(*) as count FROM PostMedia
                JOIN TravelPosts ON PostMedia.post_id = TravelPosts.id
                WHERE TravelPosts.user_id = %s
            """
            media_count_result = self.db.fetchone(media_count_query, (user_id,))
            media_count = media_count_result['count'] if media_count_result else 0

            # 生成简单的HTML展示
            html = f"""
            <style>
            .simple-stats {{
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                margin: 20px 0;
            }}
            .stat-card {{
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                text-align: center;
                flex: 1;
                min-width: 150px;
                transition: transform 0.2s;
            }}
            .stat-card:hover {{
                transform: translateY(-5px);
            }}
            .stat-value {{
                font-size: 36px;
                font-weight: bold;
                color: #3498db;
                margin: 10px 0;
            }}
            .stat-label {{
                color: #7f8c8d;
                font-size: 14px;
            }}
            </style>

            <div class="simple-stats">
                <div class="stat-card">
                    <div class="stat-value">{post_count}</div>
                    <div class="stat-label">发布动态</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{friend_count}</div>
                    <div class="stat-label">好友数量</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{like_count}</div>
                    <div class="stat-label">获得点赞</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{comment_count}</div>
                    <div class="stat-label">收到评论</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{media_count}</div>
                    <div class="stat-label">媒体内容</div>
                </div>
            </div>
            """

            return html
        except Exception as e:
            return f"<div style='color:red'>加载统计数据失败: {str(e)}</div>"
