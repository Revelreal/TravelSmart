# MainProject/app/ui/travel_post_ui.py
import gradio as gr
from MainProject.app.services.travel_post_service import TravelPostService


def create_travel_post_ui(user_info_state):
    """创建旅行动态UI组件"""
    travel_post_service = TravelPostService()

    with gr.TabItem("旅行动态"):
        gr.Markdown("## 旅行动态")

        with gr.Tabs():
            # 动态列表标签页
            with gr.TabItem("动态列表"):
                with gr.Row():
                    with gr.Column(scale=3):
                        with gr.Group():
                            gr.Markdown("### 旅行动态")

                            with gr.Row():
                                search_tag = gr.Textbox(label="标签", placeholder="输入标签筛选")
                                search_location = gr.Textbox(label="位置", placeholder="输入位置筛选")
                                friend_only = gr.Checkbox(label="仅显示好友动态")
                                search_btn = gr.Button("搜索")

                            posts_display = gr.HTML("")  # 改为使用HTML组件显示帖子
                            page_info = gr.Markdown("第 1 页，共 1 页")

                            with gr.Row():
                                prev_page = gr.Button("上一页")
                                next_page = gr.Button("下一页")
                                refresh_btn = gr.Button("刷新")

                            current_page = gr.State(1)
                            total_pages = gr.State(1)
                            post_ids = gr.State([])

                    with gr.Column(scale=1):
                        with gr.Group():
                            gr.Markdown("### 热门标签")
                            tags_container = gr.HTML("加载中...")
                            refresh_tags_btn = gr.Button("刷新标签")

                # 加载按钮
                initial_load_btn = gr.Button("加载动态", visible=True)

            # 发布动态标签页
            with gr.TabItem("发布动态"):
                with gr.Group():
                    gr.Markdown("### 发布新动态")

                    post_title = gr.Textbox(label="标题", placeholder="输入动态标题")
                    post_content = gr.Textbox(label="内容", placeholder="分享你的旅行故事...", lines=5)
                    post_location = gr.Textbox(label="位置", placeholder="输入位置名称（可选）")
                    post_tags = gr.Textbox(label="标签", placeholder="输入标签，用逗号分隔")
                    post_privacy = gr.Radio(
                        ["public", "friends", "private"],
                        label="隐私设置",
                        value="public",
                        info="公开、仅好友可见或私密"
                    )
                    post_media = gr.File(label="上传图片/视频", file_count="multiple")

                    submit_post = gr.Button("发布")
                    post_result = gr.Markdown("")

            # 动态详情标签页
            with gr.TabItem("动态详情"):
                post_id_input = gr.Number(label="动态ID", precision=0)
                load_post_btn = gr.Button("加载动态")

                post_detail = gr.HTML("请输入动态ID并点击加载")
                comments_container = gr.HTML("")

                with gr.Group():
                    comment_input = gr.Textbox(label="发表评论", placeholder="写下你的评论...", lines=2)
                    submit_comment = gr.Button("提交评论")
                    comment_result = gr.Markdown("")

                # 隐藏的交互按钮
                like_btn = gr.Button("点赞", visible=False)
                fav_btn = gr.Button("收藏", visible=False)

    # 定义所有交互函数
    def load_posts(page, tag, location, friend_only, user_data):
        if not user_data and friend_only:
            return "", page, 1, f"请先登录后查看好友动态", []

        try:
            user_id = user_data["user_id"] if user_data else None
            result = travel_post_service.get_posts(
                user_id=user_id,
                page=page,
                page_size=5,
                tag=tag if tag else None,
                location=location if location else None,
                friend_only=friend_only
            )

            posts = result.get("posts", [])
            total = result.get("total", 0)
            total_pages_val = result.get("total_pages", 1)
            current_post_ids = [post["id"] for post in posts]

            if not posts:
                return "<div class='no-posts'>没有找到符合条件的动态</div>", page, total_pages_val, f"第 {page} 页，共 {total_pages_val} 页，总计 {total} 条动态", current_post_ids

            # 构建HTML内容
            html_content = "<div class='posts-container'>"
            for post in posts:
                user = f"{post.get('nickname') or post.get('username')}"
                title = post.get("title", "")
                content = post.get("content", "")
                location = f"📍 {post.get('location_name')}" if post.get("location_name") else ""
                time = post.get("created_at", "")
                likes = post.get("like_count", 0)
                comments_count = post.get("comment_count", 0)
                tags = post.get("tags", [])

                html_content += f"""
                <div class='post' data-post-id='{post["id"]}'>
                    <div class='post-header'>
                        <h3 class='post-title'>{title}</h3>
                        <div class='post-meta'>
                            <span class='post-author'>{user}</span>
                            <span class='post-time'>{time}</span>
                        </div>
                    </div>
                    <div class='post-content'>{content}</div>
                    {f"<div class='post-location'>{location}</div>" if location else ""}
                    {f"<div class='post-tags'>{' '.join([f'<span class="tag">#{tag}</span>' for tag in tags])}</div>" if tags else ""}
                    <div class='post-stats'>
                        <span class='likes'>❤️ {likes}</span>
                        <span class='comments'>💬 {comments_count}</span>
                    </div>
                    <div class='post-actions'>
                        <button class='like-btn' onclick='handleLike("{post["id"]}")'>点赞</button>
                        <button class='view-btn' onclick='handleView("{post["id"]}")'>查看详情</button>
                    </div>
                </div>
                """

            html_content += "</div>"
            return html_content, page, total_pages_val, f"第 {page} 页，共 {total_pages_val} 页，总计 {total} 条动态", current_post_ids
        except Exception as e:
            return f"<div class='error'>错误: {str(e)}</div>", page, 1, "加载错误", []

    def load_popular_tags():
        try:
            tags = travel_post_service.get_popular_tags(limit=10)
            html = "<div class='popular-tags'>"
            for tag in tags:
                name = tag.get("tag_name", "")
                count = tag.get("count", 0)
                html += f"<div class='tag-item' onclick='document.querySelector(\"#search_tag input\").value=\"{name}\"; document.querySelector(\"#search_btn\").click();'><span class='tag-name'>#{name}</span><span class='tag-count'>{count}</span></div>"
            html += "</div>"
            return html
        except Exception as e:
            return f"<div class='error'>错误: {str(e)}</div>"

    def create_post(title, content, location, tags, privacy, files, user_data):
        if not user_data:
            return "请先登录后发布动态"
        if not title or not content:
            return "标题和内容不能为空"

        try:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

            media_files = None
            if files:
                media_files = [{'type': 'image', 'url': file.name} for file in files]

            success, result = travel_post_service.create_post(
                user_id=user_data["user_id"],
                title=title,
                content=content,
                location_name=location,
                privacy_level=privacy,
                tags=tag_list,
                media_files=media_files
            )

            return f"动态发布成功！[查看动态](#/post/{result})" if success else f"发布失败: {result}"
        except Exception as e:
            return f"错误: {str(e)}"

    def load_post_detail(post_id, user_data):
        if not post_id:
            return "请输入有效的动态ID", ""

        try:
            user_id = user_data["user_id"] if user_data else None
            post = travel_post_service.get_post(post_id, user_id)

            if not post:
                return f"<div class='error'>动态不存在或无权访问</div>", ""

            # 构建HTML显示
            user = f"{post.get('nickname') or post.get('username')}"
            title = post.get("title", "")
            content = post.get("content", "").replace("\n", "<br>")
            location = f"📍 {post.get('location_name')}" if post.get("location_name") else ""
            time = post.get("created_at", "")
            likes = post.get("like_count", 0)
            comments_count = post.get("comment_count", 0)
            tags = post.get("tags", [])
            tags_html = "".join([f"<span class='tag'>#{tag}</span>" for tag in tags])

            # 媒体文件
            media_html = ""
            if post.get("media"):
                media_html = "<div class='post-media'>"
                for media in post.get("media"):
                    if media.get("media_type") == "image":
                        media_html += f"<img src='{media.get('media_url')}' class='post-image' />"
                    elif media.get("media_type") == "video":
                        media_html += f"<video controls src='{media.get('media_url')}' class='post-video'></video>"
                media_html += "</div>"

            html = f"""
            <div class='post-detail'>
                <div class='post-header'>
                    <div class='post-user-info'>
                        <img src='{post.get('avatar') or "/static/img/default-avatar.png"}' class='user-avatar' />
                        <span class='post-user'>{user}</span>
                    </div>
                    <span class='post-time'>{time}</span>
                </div>
                <h2 class='post-title'>{title}</h2>
                <div class='post-content'>{content}</div>
                {media_html}
                <div class='post-footer'>
                    <span class='post-location'>{location}</span>
                    <div class='post-tags'>{tags_html}</div>
                    <div class='post-stats'>
                        <span>❤️ {likes}</span>
                        <span>💬 {comments_count}</span>
                    </div>
                </div>
            </div>
            """

            # 加载评论
            comments_data = travel_post_service.get_comments(post_id)
            comments_html = "<div class='comments-section'><h3>评论</h3>"

            comments = comments_data.get("comments", [])
            if not comments:
                comments_html += "<p>暂无评论</p>"
            else:
                for comment in comments:
                    comment_user = comment.get("username") or "用户"
                    comment_content = comment.get("comment_content", "")
                    comment_time = comment.get("created_at", "")

                    comments_html += f"""
                    <div class='comment-item'>
                        <div class='comment-header'>
                            <span class='comment-user'>{comment_user}</span>
                            <span class='comment-time'>{comment_time}</span>
                        </div>
                        <div class='comment-content'>{comment_content}</div>
                    </div>
                    """

            comments_html += "</div>"

            return html, comments_html
        except Exception as e:
            return f"<div class='error'>错误: {str(e)}</div>", ""

    def submit_post_comment(post_id, comment, user_data):
        if not user_data:
            return "请先登录后评论"
        if not post_id:
            return "无效的动态ID"
        if not comment or comment.strip() == "":
            return "评论内容不能为空"

        try:
            success, result = travel_post_service.comment_post(
                post_id=int(post_id),
                user_id=user_data["user_id"],
                content=comment
            )
            return "评论发表成功！" if success else f"评论失败: {result}"
        except Exception as e:
            return f"错误: {str(e)}"

    def like_post_action(post_id, user_data):
        if not user_data:
            return gr.Info("请先登录")
        try:
            success, message = travel_post_service.like_post(
                post_id=int(post_id),
                user_id=user_data["user_id"]
            )
            return gr.Info(message)
        except Exception as e:
            return gr.Info(f"操作失败: {str(e)}")

    def favorite_post_action(post_id, user_data):
        if not user_data:
            return gr.Info("请先登录")
        try:
            success, message = travel_post_service.favorite_post(
                post_id=int(post_id),
                user_id=user_data["user_id"]
            )
            return gr.Info(message)
        except Exception as e:
            return gr.Info(f"操作失败: {str(e)}")

    # 绑定交互事件
    search_btn.click(
        lambda tag, loc, friend, user: load_posts(1, tag, loc, friend, user),
        inputs=[search_tag, search_location, friend_only, user_info_state],
        outputs=[posts_display, current_page, total_pages, page_info, post_ids]
    )

    refresh_btn.click(
        lambda page, tag, loc, friend, user: load_posts(page, tag, loc, friend, user),
        inputs=[current_page, search_tag, search_location, friend_only, user_info_state],
        outputs=[posts_display, current_page, total_pages, page_info, post_ids]
    )

    prev_page.click(
        lambda page, total, tag, loc, friend, user: load_posts(max(1, page - 1), tag, loc, friend, user),
        inputs=[current_page, total_pages, search_tag, search_location, friend_only, user_info_state],
        outputs=[posts_display, current_page, total_pages, page_info, post_ids]
    )

    next_page.click(
        lambda page, total, tag, loc, friend, user: load_posts(min(total, page + 1), tag, loc, friend, user),
        inputs=[current_page, total_pages, search_tag, search_location, friend_only, user_info_state],
        outputs=[posts_display, current_page, total_pages, page_info, post_ids]
    )

    refresh_tags_btn.click(load_popular_tags, outputs=tags_container)

    submit_post.click(
        create_post,
        inputs=[post_title, post_content, post_location, post_tags, post_privacy, post_media, user_info_state],
        outputs=post_result
    )

    load_post_btn.click(
        load_post_detail,
        inputs=[post_id_input, user_info_state],
        outputs=[post_detail, comments_container]
    )

    submit_comment.click(
        submit_post_comment,
        inputs=[post_id_input, comment_input, user_info_state],
        outputs=comment_result
    )

    like_btn.click(
        like_post_action,
        inputs=[post_id_input, user_info_state]
    )

    fav_btn.click(
        favorite_post_action,
        inputs=[post_id_input, user_info_state]
    )

    # 初始加载
    initial_load_btn.click(
        lambda user: load_posts(1, "", "", False, user),
        inputs=[user_info_state],
        outputs=[posts_display, current_page, total_pages, page_info, post_ids]
    )

    return {
        "posts_display": posts_display,
        "post_detail": post_detail,
        "tags_container": tags_container
    }