# MainProject/app/ui/common_components.py
import datetime
import gradio as gr

def create_styled_likes_display(likes, like_count):
    """创建带有内联样式的点赞用户列表展示

    Args:
        likes: 点赞用户列表
        like_count: 总点赞数

    Returns:
        str: 格式化的HTML代码
    """
    likes_html = """
    <div class='likes-list'>
    <style>
    .likes-list .user-avatars {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 10px;
    }
    .likes-list .user-avatar-item {
        width: 40px;
        height: 40px;
        position: relative;
    }
    .likes-list .avatar-img {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #fff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .likes-list .more-likes {
        font-size: 0.9em;
        color: #666;
        margin-top: 5px;
    }
    </style>
    """

    if not likes:
        likes_html += "<p>暂无点赞</p>"
    else:
        likes_html += "<div class='user-avatars'>"
        for user in likes:
            user_name = user.get("nickname") or user.get("username", "用户")
            user_avatar = user.get("avatar", "/default-avatar.png")
            likes_html += f"""
            <div class="user-avatar-item" title="{user_name}">
                <img src="{user_avatar}" class="avatar-img">
            </div>
            """
        likes_html += "</div>"

        # 如果点赞数超过显示的用户数
        if like_count > len(likes):
            likes_html += f"<p class='more-likes'>共{like_count}人点赞</p>"

    likes_html += "</div>"
    return likes_html


def create_styled_comments_display(comments, comment_count):
    """创建带有内联样式的评论列表展示

    Args:
        comments: 评论列表
        comment_count: 总评论数

    Returns:
        str: 格式化的HTML代码
    """
    comments_html = """
    <div class='comments-list'>
    <style>
    .comments-list .comment-item {
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 1px solid #eee;
    }
    .comments-list .comment-header {
        display: flex;
        align-items: center;
        margin-bottom: 5px;
    }
    .comments-list .comment-avatar {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        margin-right: 10px;
        object-fit: cover;
    }
    .comments-list .comment-meta {
        display: flex;
        flex-direction: column;
    }
    .comments-list .comment-author {
        font-weight: bold;
        font-size: 0.95em;
    }
    .comments-list .comment-time {
        font-size: 0.8em;
        color: #888;
    }
    .comments-list .comment-content {
        margin-left: 40px;
        line-height: 1.4;
    }
    .comments-list .more-comments {
        color: #1a73e8;
        cursor: pointer;
        font-size: 0.9em;
        margin-top: 10px;
    }
    </style>
    """

    if not comments:
        comments_html += "<p>暂无评论，来发表第一条评论吧！</p>"
    else:
        for comment in comments:
            commenter = comment.get("nickname") or comment.get("username", "用户")
            comment_avatar = comment.get("avatar", "/default-avatar.png")
            comment_content = comment.get("comment_content", "")

            # 格式化时间
            comment_time = comment.get("created_at", "")
            if isinstance(comment_time, datetime.datetime):
                comment_time = comment_time.strftime("%Y-%m-%d %H:%M")

            comments_html += f"""
            <div class="comment-item">
                <div class="comment-header">
                    <img src="{comment_avatar}" class="comment-avatar">
                    <div class="comment-meta">
                        <span class="comment-author">{commenter}</span>
                        <span class="comment-time">{comment_time}</span>
                    </div>
                </div>
                <div class="comment-content">{comment_content}</div>
            </div>
            """

        # 如果评论数超过显示的评论数
        if comment_count > len(comments):
            comments_html += f"<p class='more-comments'>查看全部{comment_count}条评论</p>"

    comments_html += "</div>"
    return comments_html


def create_post_detail_view(container, is_from_favorites=False):
    """创建通用的动态详情视图"""
    with container:
        with gr.Group(visible=False) as detail_view:
            with gr.Row():
                back_btn = gr.Button("⬅️ 返回")

            with gr.Group(elem_classes="detail-container"):
                post_title = gr.Markdown("### 标题")
                post_meta = gr.Markdown("*发布信息*")
                post_privacy = gr.Markdown("*可见性*")
                post_tags = gr.Markdown("*标签*")
                post_location = gr.Markdown("*位置*")
                post_content = gr.Markdown("*内容*")
                post_media = gr.Gallery(label="媒体内容")

                with gr.Row():
                    post_stats = gr.Markdown("*统计数据*")
                    if is_from_favorites:
                        unfav_btn = gr.Button("❌ 取消收藏", variant="secondary")
                    else:
                        fav_btn = gr.Button("⭐ 收藏", variant="secondary")
                        like_btn = gr.Button("👍 点赞", variant="secondary")

            # 点赞用户列表
            with gr.Group(elem_classes="likes-section"):
                gr.Markdown("### 点赞用户")
                post_likes = gr.HTML("*加载中...*")

            # 评论区
            with gr.Group(elem_classes="comments-section"):
                gr.Markdown("### 评论区")
                post_comments = gr.HTML("*加载中...*")

                # 添加评论输入框
                with gr.Row():
                    comment_input = gr.Textbox(
                        label="发表评论",
                        placeholder="写下你的评论...",
                        lines=2
                    )
                    submit_comment_btn = gr.Button("发送")

            # 存储当前查看的动态ID
            post_id_state = gr.State(None)

            # 收藏状态
            fav_status = gr.State(False)

            # 收藏ID状态组件
            fav_id_state = gr.State(None)

    # 返回组件字典，方便后续引用
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
        "fav_id": fav_id_state
    }

    if is_from_favorites:
        components["unfav_btn"] = unfav_btn
    else:
        components["fav_btn"] = fav_btn
        components["like_btn"] = like_btn

    return components




