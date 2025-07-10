# MainProject/app/ui/common_components.py
import gradio as gr
from MainProject.app.services.mongo_file_service import mongo_file_service

def create_styled_likes_display(likes_data, total_count):
    """创建样式化的点赞用户显示（带头像）- 完善版"""
    if not likes_data or total_count == 0:
        return f"""
        <div class='likes-container'>
            <div class='likes-header'>❤️ 暂无点赞</div>
            <div class='likes-empty'>成为第一个点赞的人吧！</div>
        </div>
        """

    html = f"""
        <style>
        .likes-container {{
            padding: 15px;
            border-radius: 12px;
            margin: 10px 0;
            border: 1px solid;
        }}
        .likes-header {{
            font-weight: 600;
            margin-bottom: 12px;
            font-size: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .likes-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 10px;
        }}
        .like-user {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 12px;
            border-radius: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            border: 1px solid;
            cursor: pointer;
        }}
        .like-user:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }}
        .like-avatar {{
            width: 28px;
            height: 28px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid;
        }}
        .like-username {{
            font-size: 13px;
            font-weight: 500;
            max-width: 80px;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .likes-more {{
            font-size: 12px;
            text-align: center;
            padding: 8px;
            border-radius: 8px;
            margin-top: 8px;
        }}
        .likes-empty {{
            text-align: center;
            font-style: italic;
            padding: 20px;
        }}
        .like-time {{
            font-size: 11px;
            margin-top: 2px;
        }}
        </style>
        <div class='likes-container'>
            <div class='likes-header'>
                <span>❤️ {total_count} 人点赞</span>
            </div>
            <div class='likes-list'>
        """

    # 显示点赞用户（最多显示12个）
    displayed_count = 0
    for like in likes_data[:12]:
        try:
            # 获取用户头像 - 使用完善的错误处理
            avatar_key = like.get('avatar')
            try:
                avatar_url = mongo_file_service.get_avatar_data_url(avatar_key)
            except Exception as e:
                print(f"获取点赞用户头像失败: {e}")
                # 使用默认头像
                avatar_url = mongo_file_service.get_avatar_data_url(None)

            # 获取用户名 - 优先显示昵称
            username = like.get('nickname') or like.get('username', '用户')

            # 格式化点赞时间
            like_time = like.get('created_at', '')
            if hasattr(like_time, 'strftime'):
                like_time_str = like_time.strftime('%m-%d %H:%M')
            else:
                like_time_str = '刚刚'

            html += f"""
            <div class='like-user' title='{username} 在 {like_time_str} 点赞'>
                <img src='{avatar_url}' class='like-avatar' alt='{username}的头像' 
                     onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjgiIGhlaWdodD0iMjgiIHZpZXdCb3g9IjAgMCAyOCAyOCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIxNCIgY3k9IjE0IiByPSIxNCIgZmlsbD0iI2Y4ZjlmYSIvPjxjaXJjbGUgY3g9IjE0IiBjeT0iMTAiIHI9IjQiIGZpbGw9IiNkZWUyZTYiLz48cGF0aCBkPSJNNiAyMmMwLTQgNC04IDgtOHM4IDQgOCA4IiBmaWxsPSIjZGVlMmU2Ii8+PC9zdmc+'" />
                <div>
                    <div class='like-username'>{username}</div>
                    <div class='like-time'>{like_time_str}</div>
                </div>
            </div>
            """
            displayed_count += 1
        except Exception as e:
            print(f"处理点赞用户数据失败: {e}")
            continue

    html += "</div>"

    # 如果还有更多点赞用户
    if total_count > displayed_count:
        html += f"<div class='likes-more'>还有 {total_count - displayed_count} 人点赞了这条动态</div>"

    html += "</div>"

    return html


def create_styled_comments_display(comments_data, total_count):
    """创建样式化的评论显示（带头像）- 完善版"""
    if not comments_data or total_count == 0:
        return f"""
        <div class='comments-container'>
            <div class='comments-header'>💬 暂无评论</div>
            <div class='comments-empty'>快来发表第一条评论吧！</div>
        </div>
        """

    html = f"""
        <style>
        .comments-container {{
            padding: 15px;
            border-radius: 12px;
            margin: 10px 0;
            border: 1px solid;
        }}
        .comments-header {{
            font-weight: 600;
            margin-bottom: 15px;
            font-size: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
            padding-bottom: 10px;
            border-bottom: 1px solid;
        }}
        .comment-item {{
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
            padding: 12px;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
            border: 1px solid;
            transition: all 0.3s ease;
        }}
        .comment-item:hover {{
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
            transform: translateY(-1px);
        }}
        .comment-item:last-child {{
            margin-bottom: 0;
        }}
        .comment-avatar {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid;
            flex-shrink: 0;
            cursor: pointer;
            transition: border-color 0.3s ease;
        }}
        .comment-content {{
            flex: 1;
            min-width: 0;
        }}
        .comment-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 6px;
            flex-wrap: wrap;
        }}
        .comment-username {{
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            transition: color 0.3s ease;
        }}
        .comment-time {{
            font-size: 12px;
            padding: 2px 6px;
            border-radius: 4px;
        }}
        .comment-text {{
            font-size: 14px;
            line-height: 1.5;
            word-wrap: break-word;
            word-break: break-word;
        }}
        .comment-actions {{
            display: flex;
            gap: 15px;
            margin-top: 8px;
            align-items: center;
        }}
        .comment-action {{
            font-size: 12px;
            cursor: pointer;
            transition: color 0.3s ease;
            display: flex;
            align-items: center;
            gap: 4px;
        }}
        .comments-more {{
            text-align: center;
            font-size: 13px;
            margin-top: 15px;
            padding: 10px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        .comments-empty {{
            text-align: center;
            font-style: italic;
            padding: 30px;
            border-radius: 8px;
            margin-top: 10px;
        }}
        .comment-mention {{
            font-weight: 500;
            text-decoration: none;
        }}
        .comment-mention:hover {{
            text-decoration: underline;
        }}
        </style>
        <div class='comments-container'>
            <div class='comments-header'>
                <span>💬 {total_count} 条评论</span>
            </div>
        """

    # 显示评论（最多显示8条）
    displayed_count = 0
    for comment in comments_data[:8]:
        try:
            # 获取评论者头像 - 使用完善的错误处理
            avatar_key = comment.get('avatar')
            try:
                avatar_url = mongo_file_service.get_avatar_data_url(avatar_key)
            except Exception as e:
                print(f"获取评论者头像失败: {e}")
                # 使用默认头像
                avatar_url = mongo_file_service.get_avatar_data_url(None)

            # 获取用户名 - 优先显示昵称
            username = comment.get('nickname') or comment.get('username', '用户')

            # 获取评论内容
            content = comment.get('comment_content') or comment.get('content', '')

            # 处理@提及 - 将@username转换为可点击的链接
            content = _process_mentions_in_content(content)

            # 格式化评论时间
            comment_time = comment.get('created_at', '')
            if hasattr(comment_time, 'strftime'):
                comment_time_str = comment_time.strftime('%m-%d %H:%M')
            elif isinstance(comment_time, str) and comment_time:
                try:
                    from datetime import datetime
                    # 尝试解析ISO格式的时间
                    dt = datetime.fromisoformat(comment_time.replace('Z', '+00:00'))
                    comment_time_str = dt.strftime('%m-%d %H:%M')
                except:
                    # 如果解析失败，截取前16个字符
                    comment_time_str = comment_time[:16] if len(comment_time) > 16 else comment_time
            else:
                comment_time_str = '刚刚'

            # 获取评论ID用于操作
            comment_id = comment.get('id', '')

            html += f"""
            <div class='comment-item' data-comment-id='{comment_id}'>
                <img src='{avatar_url}' class='comment-avatar' alt='{username}的头像' 
                     title='查看 {username} 的资料'
                     onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIyMCIgY3k9IjIwIiByPSIyMCIgZmlsbD0iI2Y4ZjlmYSIvPjxjaXJjbGUgY3g9IjIwIiBjeT0iMTUiIHI9IjYiIGZpbGw9IiNkZWUyZTYiLz48cGF0aCBkPSJNOCAzMmMwLTYgNi0xMiAxMi0xMnMxMiA2IDEyIDEyIiBmaWxsPSIjZGVlMmU2Ii8+PC9zdmc+'" />
                <div class='comment-content'>
                    <div class='comment-header'>
                        <span class='comment-username' title='查看 {username} 的资料'>{username}</span>
                        <span class='comment-time'>{comment_time_str}</span>
                    </div>
                    <div class='comment-text'>{content}</div>
                    <div class='comment-actions'>
                        <span class='comment-action' title='回复评论'>
                            <span>💬</span> 回复
                        </span>
                        <span class='comment-action' title='点赞评论'>
                            <span>👍</span> 点赞
                        </span>
                    </div>
                </div>
            </div>
            """
            displayed_count += 1
        except Exception as e:
            print(f"处理评论数据失败: {e}")
            continue

    # 如果还有更多评论
    if total_count > displayed_count:
        html += f"""
        <div class='comments-more' onclick='loadMoreComments()'>
            <span>📖</span> 查看更多评论 ({total_count - displayed_count} 条)
        </div>
        """

    html += "</div>"

    return html


def _process_mentions_in_content(content):
    """处理评论内容中的@提及，转换为可点击的链接"""
    import re

    def replace_mention(match):
        username = match.group(1)
        return f'<span class="comment-mention" title="查看 @{username} 的资料">@{username}</span>'

    # 匹配@username格式
    content = re.sub(r'@(\w+)', replace_mention, content)
    return content


def create_post_detail_view(container, is_from_favorites=False):
    """创建通用的动态详情视图 - 完善版"""
    with container:
        with gr.Group(visible=False) as detail_view:
            with gr.Row():
                back_btn = gr.Button("⬅️ 返回", elem_classes="back-button")

            with gr.Group(elem_classes="detail-container"):
                post_title = gr.Markdown("### 标题")
                post_meta = gr.Markdown("*发布信息*")
                post_privacy = gr.Markdown("*可见性*")
                post_tags = gr.Markdown("*标签*")
                post_location = gr.Markdown("*位置*")
                post_content = gr.Markdown("*内容*")
                post_media = gr.Gallery(label="媒体内容", show_label=False, elem_classes="post-media")

                with gr.Row():
                    post_stats = gr.Markdown("*统计数据*")
                    if is_from_favorites:
                        unfav_btn = gr.Button("❌ 取消收藏", variant="secondary")
                    else:
                        fav_btn = gr.Button("⭐ 收藏", variant="secondary")
                        like_btn = gr.Button("👍 点赞", variant="secondary")

            # 点赞用户列表 - 使用完善的显示组件
            with gr.Group(elem_classes="likes-section"):
                gr.Markdown("### 点赞用户")
                post_likes = gr.HTML("*加载中...*")

                # 添加加载更多点赞的按钮
                load_more_likes_btn = gr.Button("查看更多点赞", visible=False, elem_classes="load-more-btn")

            # 评论区 - 使用完善的显示组件
            with gr.Group(elem_classes="comments-section"):
                gr.Markdown("### 评论区")
                post_comments = gr.HTML("*加载中...*")

                # 添加加载更多评论的按钮
                load_more_comments_btn = gr.Button("查看更多评论", visible=False, elem_classes="load-more-btn")

                # 评论输入框 - 增强版
                with gr.Group(elem_classes="comment-input-section"):
                    gr.Markdown("#### 发表评论")
                    with gr.Row():
                        comment_input = gr.Textbox(
                            label="",
                            placeholder="写下你的评论... (支持@提及用户)",
                            lines=3,
                            elem_classes="comment-input"
                        )
                    with gr.Row():
                        emoji_btn = gr.Button("😊", elem_classes="emoji-btn")
                        mention_btn = gr.Button("@", elem_classes="mention-btn")
                        submit_comment_btn = gr.Button("发送评论", variant="primary")

            # 存储状态
            post_id_state = gr.State(None)
            fav_status = gr.State(False)
            fav_id_state = gr.State(None)

            # 分页状态
            likes_page_state = gr.State(1)
            comments_page_state = gr.State(1)

    # 返回组件字典
    components = {
        "view": detail_view,
        "back_btn": back_btn,
        "title": post_title,
        "meta": post_meta,
        "privacy": post_privacy,
        "tags": post_tags,
        "location": post_location,
        "content": post_content,
        "media": post_media,
        "stats": post_stats,
        "likes": post_likes,
        "comments": post_comments,
        "comment_input": comment_input,
        "submit_comment": submit_comment_btn,
        "post_id": post_id_state,
        "fav_status": fav_status,
        "fav_id": fav_id_state,
        "load_more_likes": load_more_likes_btn,
        "load_more_comments": load_more_comments_btn,
        "likes_page": likes_page_state,
        "comments_page": comments_page_state,
        "emoji_btn": emoji_btn,
        "mention_btn": mention_btn
    }

    if is_from_favorites:
        components["unfav_btn"] = unfav_btn
    else:
        components["fav_btn"] = fav_btn
        components["like_btn"] = like_btn

    return components




