# MainProject/app/ui/travel_post_ui.py
import datetime
import gradio as gr
from MainProject.app.services.travel_post_service import TravelPostService
from MainProject.app.ui.common_components import create_styled_likes_display


def create_travel_post_ui(user_info_state):
    """创建旅行动态UI组件，使用卡片样式展示内容"""
    travel_post_service = TravelPostService()
    PAGE_SIZE = 6  # 每页显示动态数量

    with gr.TabItem("动态广场") as travel_post_tab:
        view_state = gr.State("list")  # 可能的值: "list", "detail", "create"
        selected_post_id = gr.State(None) # 选中的动态ID

        with gr.Group(visible=True) as list_view:
            gr.Markdown("## 旅行动态")

            with gr.Row():
                with gr.Column(scale=3):
                    # 搜索区域
                    with gr.Group():
                        gr.Markdown("### 搜索与筛选")
                        search_tag = gr.Textbox(label="标签搜索", placeholder="输入标签，如：美食、风景")
                        search_location = gr.Textbox(label="地点搜索", placeholder="输入地点名称")
                        friend_only = gr.Checkbox(label="仅显示好友动态")

                        with gr.Row():
                            search_btn = gr.Button("🔍 搜索", variant="primary")
                            refresh_btn = gr.Button("🔄 刷新")

                    # 状态反馈
                    status_text = gr.Markdown("")

                    # 分页信息和控制
                    with gr.Row():
                        prev_page = gr.Button("上一页")
                        page_info = gr.Markdown("第 1 页，共 1 页")
                        next_page = gr.Button("下一页")

                    # 隐藏状态
                    page_state = gr.State(1)
                    total_pages_state = gr.State(1)

                    # 帖子容器 - 显示固定数量的帖子卡片
                    post_cards = []
                    # 创建容器来包装所有的卡片
                    with gr.Group() as posts_container:
                        for i in range(PAGE_SIZE):
                            with gr.Group(visible=False, elem_classes="post-card") as card:
                                post_title = gr.Markdown("### 标题")
                                post_meta = gr.Markdown("**发布者:** 用户 | **发布于:** 时间")
                                post_location = gr.Markdown("", elem_classes="post-location")
                                post_tags = gr.Markdown("", elem_classes="post-tags")
                                post_content = gr.Markdown("内容")

                                with gr.Row(elem_classes="action-row"):
                                    post_stats = gr.Markdown("👁️ 0 次查看", elem_classes="stats-text")
                                    view_btn = gr.Button("查看详情")
                                    like_btn = gr.Button("👍 0")
                                    fav_btn = gr.Button("⭐ 收藏")

                                # 存储帖子ID (用于操作)
                                post_id_state = gr.State(0)

                                # 将组件添加到卡片列表
                                post_cards.append({
                                    "card": card,
                                    "title": post_title,
                                    "meta": post_meta,
                                    "location": post_location,
                                    "tags": post_tags,
                                    "content": post_content,
                                    "stats": post_stats,
                                    "view_btn": view_btn,
                                    "like_btn": like_btn,
                                    "fav_btn": fav_btn,
                                    "id_state": post_id_state
                                })

                with gr.Column(scale=1):
                    # 热门标签
                    gr.Markdown("### 热门标签")
                    with gr.Row():
                        refresh_tags_btn = gr.Button("🔄 刷新标签", scale=0)

                    tags_display = gr.Markdown("*加载中...*", elem_classes="tag-cloud")

                    # 新建动态按钮
                    create_post_btn = gr.Button("✏️ 发布新动态", variant="primary")
        # 详情页面标签页
        with gr.Group(visible=False) as detail_view:
            gr.Markdown("## 动态详情")

            # 返回按钮
            with gr.Row():
                back_to_list_btn = gr.Button("⬅️ 返回列表")

            with gr.Group(elem_classes="detail-container"):
                # 详情内容
                detail_title = gr.Markdown("### 标题")
                detail_meta = gr.Markdown("*作者信息*")
                detail_tags = gr.Markdown("*标签*")
                detail_location = gr.Markdown("*位置*")
                detail_content = gr.Markdown("*内容*")
                detail_media = gr.Gallery(label="媒体内容")

                with gr.Row(elem_classes="action-row"):
                    detail_stats = gr.Markdown("*点赞和评论数*", elem_classes="stats-text")
                    detail_like_btn = gr.Button("👍 点赞")
                    detail_fav_btn = gr.Button("⭐ 收藏")
            # 点赞用户列表 - 添加这部分
            with gr.Group(elem_classes="likes-section"):
                gr.Markdown("### 点赞用户")
                detail_likes = gr.HTML("*加载中...*")
            # 评论区
            with gr.Group(elem_classes="comment-section"):
                gr.Markdown("### 评论区")
                comments_display = gr.Markdown("*加载中...*")

                # 发表评论
                comment_input = gr.Textbox(label="发表评论", placeholder="请输入您的评论...", lines=3)
                submit_comment_btn = gr.Button("发表评论", variant="primary")

        # 发布动态标签页
        with gr.Group(visible=False) as create_view:
            gr.Markdown("## 发布新动态")

            # 返回按钮
            with gr.Row():
                back_from_create_btn = gr.Button("⬅️ 返回列表")

            with gr.Group():
                # 基本信息
                post_title = gr.Textbox(label="标题", placeholder="请输入动态标题", lines=1)
                post_content = gr.Textbox(label="内容", placeholder="分享您的旅行经历...", lines=5)

                # 位置信息
                with gr.Row():
                    post_location = gr.Textbox(label="位置", placeholder="请输入位置名称")
                    use_current_location = gr.Checkbox(label="使用当前位置")

                # 标签
                post_tags = gr.Textbox(
                    label="标签",
                    placeholder="请输入标签，多个标签用空格分隔，如：美食 风景 自驾游",
                    lines=1
                )

                # 媒体上传
                post_media = gr.File(
                    label="上传图片/视频",
                    file_types=["image", "video"],
                    file_count="multiple"
                )

                # 隐私设置
                with gr.Row():
                    post_visibility = gr.Radio(
                        label="可见范围",
                        choices=["公开", "仅好友可见", "仅自己可见"],
                        value="公开"
                    )

                # 提交按钮
                with gr.Row():
                    cancel_create_btn = gr.Button("取消")
                    submit_post_btn = gr.Button("发布", variant="primary")

            # 发布结果提示
            post_result = gr.Markdown(visible=False)

        # 视图切换函数
        def switch_to_list_view():
            """切换到动态列表视图"""
            return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), "list"

        def switch_to_detail_view(post_id):
            """切换到动态详情视图"""
            return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), "detail", post_id

        def switch_to_create_view():
            """切换到发布动态视图"""
            return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), "create"

        # 定义获取动态数据的函数
        def get_posts_data(page, tag, location, friend_only_param, user_data):
            try:
                # 获取用户ID
                user_id = user_data.get("user_id") if user_data else None

                # 检查未登录情况
                if friend_only_param and not user_id:
                    gr.Info("请先登录后查看好友动态")
                    # 隐藏所有卡片
                    updates = []
                    for i in range(PAGE_SIZE):
                        updates.append(gr.update(visible=False))  # 卡片可见性
                        updates.extend([gr.update() for _ in range(9)])  # 9个内容组件无变化
                        updates.append(0)  # post_id_state

                    # 返回错误信息和更新列表
                    return (updates +  # 卡片更新
                            ["请先登录后查看好友动态", 1])  # 页面信息和总页数

                # 获取动态列表
                result = travel_post_service.get_posts(
                    user_id=user_id,
                    page=page,
                    page_size=PAGE_SIZE,
                    tag=tag if tag else None,
                    location=location if location else None,
                    friend_only=friend_only_param
                )

                posts = result.get("posts", [])
                total = result.get("total", 0)
                total_pages = result.get("total_pages", 1)

                # 准备更新列表
                updates = []

                # 处理每个卡片
                for i in range(PAGE_SIZE):
                    if i < len(posts):
                        # 有数据，显示卡片
                        post = posts[i]
                        post_id = post["id"]
                        title = post.get("title", "无标题")
                        username = post.get("nickname") or post.get("username", "用户")

                        # 格式化时间
                        created_time = post.get("created_at", "")
                        if isinstance(created_time, datetime.datetime):
                            created_time = created_time.strftime("%Y年%m月%d日 %H:%M")

                        # 内容预览
                        content = post.get("content", "")
                        if len(content) > 150:
                            content = content[:150] + "..."

                        # 标签
                        tags_text = ""
                        if post.get("tags"):
                            tags_text = " ".join([f"#{tag}" for tag in post["tags"]])

                        # 位置
                        location_text = ""
                        if post.get("location_name"):
                            location_text = f"📍 {post['location_name']}"

                        # 统计数据
                        like_count = post.get("like_count", 0)
                        comment_count = post.get("comment_count", 0)

                        # 用户交互状态
                        liked = post.get("user_liked", False)
                        favorited = post.get("user_favorited", False)

                        # 添加卡片可见性更新
                        updates.append(gr.update(visible=True))

                        # 添加内容更新
                        updates.append(f"### {title}")  # 标题
                        updates.append(f"**发布者:** {username} | **发布于:** {created_time}")  # 元数据
                        updates.append(location_text)  # 位置
                        updates.append(tags_text)  # 标签
                        updates.append(content)  # 内容
                        updates.append(f"👁️ {like_count + comment_count} 次查看")  # 统计

                        # 更新按钮文本
                        updates.append(gr.update(value="查看详情"))  # 查看按钮
                        updates.append(gr.update(
                            value=f"👍 {like_count}",
                            variant="primary" if liked else "secondary"
                        ))  # 点赞按钮
                        updates.append(gr.update(
                            value="⭐ 已收藏" if favorited else "⭐ 收藏",
                            variant="primary" if favorited else "secondary"
                        ))  # 收藏按钮

                        # 更新帖子ID
                        updates.append(post_id)
                    else:
                        # 无数据，隐藏卡片
                        updates.append(gr.update(visible=False))  # 卡片可见性
                        updates.extend([gr.update() for _ in range(9)])  # 9个内容组件无变化
                        updates.append(0)  # post_id_state

                # 添加页面信息和总页数
                updates.append(f"第 {page} 页，共 {total_pages} 页，总计 {total} 条动态")
                updates.append(total_pages)

                return updates

            except Exception as e:
                error_msg = f"加载动态失败: {str(e)}"

                # 隐藏所有卡片，只显示第一个卡片作为错误信息
                updates = []

                # 第一个卡片显示错误
                updates.append(gr.update(visible=True))  # 卡片可见性
                updates.append("### 加载失败")  # 标题
                updates.append("**错误信息**")  # 元数据
                updates.append("")  # 位置
                updates.append("")  # 标签
                updates.append(f"*{error_msg}*")  # 内容
                updates.append("")  # 统计
                updates.append(gr.update(visible=False))  # 查看按钮
                updates.append(gr.update(visible=False))  # 点赞按钮
                updates.append(gr.update(visible=False))  # 收藏按钮
                updates.append(0)  # post_id_state

                # 隐藏其余卡片
                for i in range(1, PAGE_SIZE):
                    updates.append(gr.update(visible=False))  # 卡片可见性
                    updates.extend([gr.update() for _ in range(9)])  # 9个内容组件无变化
                    updates.append(0)  # post_id_state

                # 添加页面信息和总页数
                    # 添加页面信息和总页数
                    updates.append(f"加载失败: {str(e)}")
                    updates.append(1)

                    return updates

        # 处理点赞操作
        def handle_like_post(post_id, user_data):
            if not post_id:
                return "未选择任何动态"

            if not user_data or not user_data.get("user_id"):
                gr.Info("请先登录后再点赞")
                return "请先登录后再点赞"

            try:
                success, message = travel_post_service.like_post(post_id, user_data["user_id"])
                if success:
                    gr.Info(message)  # Using the message returned from the service
                    return message
                else:
                    gr.Error(message)
                    return message
            except Exception as e:
                gr.Error(f"点赞失败: {str(e)}")
                return f"点赞失败: {str(e)}"

        # 处理收藏操作
        def handle_favorite_post(post_id, user_data):
            if not post_id:
                return "未选择任何动态"

            if not user_data or not user_data.get("user_id"):
                gr.Info("请先登录后再收藏")
                return "请先登录后再收藏"

            try:
                success, message = travel_post_service.favorite_post(post_id, user_data["user_id"])
                if success:
                    gr.Info(message)  # Using the message returned from the service
                    return message
                else:
                    gr.Error(message)
                    return message
            except Exception as e:
                gr.Error(f"收藏失败: {str(e)}")
                return f"收藏失败: {str(e)}"

        # 加载热门标签
        def get_tags_data():
            try:
                tags = travel_post_service.get_popular_tags()
                if not tags:
                    return "*没有热门标签*"

                # 格式化标签显示
                tag_links = []
                for tag in tags:
                    # Check different key formats the tags might have
                    tag_name = tag.get("tag_name") or tag.get("name", "未知标签")
                    tag_count = tag.get("count", 0)
                    tag_links.append(f"**#{tag_name}** ({tag_count})")

                if not tag_links:
                    return "*没有热门标签*"

                return " · ".join(tag_links)
            except Exception as e:
                return f"*加载标签失败: {str(e)}*"

        # 加载动态详情
        def load_post_detail(post_id, user_data):
            if not post_id:
                return (
                    "未选择动态", "", "", "",
                    "请先从列表中选择一个动态查看详情",
                    None, "", "", ""
                )

            try:
                # 获取用户ID
                user_id = user_data.get("user_id") if user_data else None

                # 获取帖子详情
                post = travel_post_service.get_post_detail(post_id, user_id)

                if not post:
                    return (
                        "动态不存在", "", "", "",
                        "未找到此动态，可能已被删除",
                        None, "", "", ""
                    )

                # 解析数据
                title = post.get("title", "无标题")
                username = post.get("nickname") or post.get("username", "用户")

                # 格式化时间
                created_time = post.get("created_at", "")
                if isinstance(created_time, datetime.datetime):
                    created_time = created_time.strftime("%Y年%m月%d日 %H:%M")

                # 元数据
                meta_text = f"**发布者:** {username} | **发布于:** {created_time}"

                # 标签
                tags_text = ""
                if post.get("tags"):
                    tags_text = " ".join([f"#{tag}" for tag in post["tags"]])

                # 位置
                location_text = ""
                if post.get("location_name"):
                    location_text = f"📍 {post['location_name']}"

                # 内容
                content = post.get("content", "")

                # 媒体内容
                # 媒体内容
                media = post.get("media", [])

                # Extract only URLs from media items
                processed_media = []
                if media:
                    for item in media:
                        if isinstance(item, dict):
                            # Try different possible keys for the URL
                            url = None
                            for key in ["media_url", "url", "thumbnail_url"]:
                                if key in item and item[key]:
                                    url = item[key]
                                    break

                            if url:
                                processed_media.append(url)
                        elif isinstance(item, str):
                            processed_media.append(item)

                # 统计数据
                like_count = post.get("like_count", 0)
                comment_count = post.get("comment_count", 0)
                view_count = post.get("view_count", 0)

                stats_text = f"👁️ {view_count} 次查看 | 👍 {like_count} 次点赞 | 💬 {comment_count} 条评论"

                # 用户交互状态
                liked = post.get("user_liked", False)
                favorited = post.get("user_favorited", False)

                # 点赞按钮
                like_btn_text = "👍 已点赞" if liked else "👍 点赞"
                like_btn_variant = "primary" if liked else "secondary"

                # 收藏按钮
                fav_btn_text = "⭐ 已收藏" if favorited else "⭐ 收藏"
                fav_btn_variant = "primary" if favorited else "secondary"

                return (
                    title, meta_text, tags_text, location_text,
                    content, processed_media,  # Use processed_media instead of media
                    stats_text,
                    gr.update(value=like_btn_text, variant=like_btn_variant),
                    gr.update(value=fav_btn_text, variant=fav_btn_variant)
                )

            except Exception as e:
                error_msg = f"加载动态详情失败: {str(e)}"
                return (
                    "加载失败", "", "", "",
                    f"*{error_msg}*",
                    None, "",
                    gr.update(), gr.update()
                )

        # 定义加载评论的函数
        def load_comments(post_id):
            if not post_id:
                return "*请先选择一个动态查看评论*"

            try:
                result = travel_post_service.get_comments(post_id)

                # Check if result is a string
                if isinstance(result, str):
                    return f"*{result}*"

                # Extract comments from the dictionary result
                comments = result.get('comments', [])

                if not comments:
                    return "*暂无评论，快来发表第一条评论吧！*"

                # 格式化评论显示
                comments_text = []
                for comment in comments:
                    # Check if comment is a dictionary
                    if not isinstance(comment, dict):
                        continue

                    username = comment.get("nickname") or comment.get("username", "用户")
                    content = comment.get("comment_content", "")  # Note: Using "comment_content" field

                    # 格式化时间
                    created_time = comment.get("created_at", "")
                    if isinstance(created_time, datetime.datetime):
                        created_time = created_time.strftime("%Y-%m-%d %H:%M")

                    comments_text.append(f"**{username}** ({created_time}):\n{content}\n")

                return "\n---\n".join(comments_text)

            except Exception as e:
                return f"*加载评论失败: {str(e)}*"

        # 发表评论
        def post_comment(post_id, comment_text, user_data):
            if not post_id:
                gr.Error("未选择动态，无法发表评论")
                return "未选择动态，无法发表评论", ""

            if not comment_text.strip():
                gr.Error("评论内容不能为空")
                return "评论内容不能为空", ""

            if not user_data or not user_data.get("user_id"):
                gr.Error("请先登录后再发表评论")
                return "请先登录后再发表评论", ""

            try:
                # 发表评论
                travel_post_service.add_comment(
                    post_id=post_id,
                    user_id=user_data["user_id"],
                    content=comment_text
                )

                gr.Info("评论发表成功！")

                # 重新加载评论
                updated_comments = load_comments(post_id)

                return "评论发表成功！", ""  # 清空评论框
            except Exception as e:
                error_msg = f"发表评论失败: {str(e)}"
                gr.Error(f"评论发表失败: {str(e)}")
                return error_msg, comment_text  # 保留评论框内容

        # 定义发布动态函数
        def create_new_post(title, content, location, use_current_loc, tags, media, visibility, user_data):
            if not user_data or not user_data.get("user_id"):
                gr.Error("请先登录后再发布动态")
                return gr.Markdown(value="*发布失败：请先登录*", visible=True)

            if not title.strip():
                gr.Error("标题不能为空")
                return gr.Markdown(value="*发布失败：标题不能为空*", visible=True)

            if not content.strip():
                gr.Error("内容不能为空")
                return gr.Markdown(value="*发布失败：内容不能为空*", visible=True)

            try:
                # Process tags
                tag_list = []
                if tags.strip():
                    tag_list = [tag.strip() for tag in tags.split() if tag.strip()]

                # Process location
                location_name = None
                location_coordinates = None

                if use_current_loc:
                    location_name = "当前位置"
                    location_coordinates = "0.0,0.0"  # Simplified for testing
                elif location.strip():
                    location_name = location.strip()

                # Process visibility
                visibility_map = {
                    "公开": "public",
                    "仅好友可见": "friends",
                    "仅自己可见": "private"
                }
                visibility_setting = visibility_map.get(visibility, "public")

                # Process media
                media_files = []
                if media:
                    for file in media:
                        media_files.append({
                            "type": "image" if file.name.lower().endswith(
                                ('.jpg', '.jpeg', '.png', '.gif')) else "video",
                            "url": file.name,
                            "thumbnail_url": None
                        })

                # Call service - note that it returns (success, post_id_or_error_message)
                success, result = travel_post_service.create_post(
                    user_id=user_data["user_id"],
                    title=title,
                    content=content,
                    location_name=location_name,
                    location_coordinates=location_coordinates,
                    privacy_level=visibility_setting,
                    tags=tag_list,
                    media_files=media_files
                )

                if success:
                    gr.Info("动态发布成功！")
                    return gr.Markdown(value="*动态发布成功！正在返回动态列表...*", visible=True)
                else:
                    gr.Error(f"发布失败: {result}")
                    return gr.Markdown(value=f"*发布失败: {result}*", visible=True)

            except Exception as e:
                gr.Error(f"发布动态失败: {str(e)}")
                return gr.Markdown(value=f"*发布失败: {str(e)}*", visible=True)

        # 清空表单函数
        def clear_post_form():
            return [
                "", "", "", False, "", None, "公开",
                gr.Markdown(visible=False)
            ]
        # 在详情页加载后，加载点赞用户
        def load_likes(post_id, user_data):
            if not post_id:
                return "*请先选择一个动态查看点赞*"

            try:
                post = travel_post_service.get_post_detail(post_id, user_data.get("user_id") if user_data else None)
                if not post:
                    return "*动态不存在或已被删除*"

                likes = post.get("recent_likes", [])
                like_count = post.get("like_count", 0)

                # 使用公共组件生成点赞用户列表
                return create_styled_likes_display(likes, like_count)
            except Exception as e:
                return f"*加载点赞用户失败: {str(e)}*"

        # 绑定事件
        # 为每个帖子卡片绑定事件
        for card_data in post_cards:
            # 查看详情按钮事件
            card_data["view_btn"].click(
                fn=switch_to_detail_view,
                inputs=[card_data["id_state"]],
                outputs=[list_view, detail_view, create_view, view_state, selected_post_id]
            ).then(
                fn=load_post_detail,
                inputs=[selected_post_id, user_info_state],
                outputs=[
                    detail_title, detail_meta, detail_tags,
                    detail_location, detail_content, detail_media,
                    detail_stats, detail_like_btn, detail_fav_btn
                ]
            ).then(
                fn=load_likes,  # 加载点赞用户
                inputs=[selected_post_id, user_info_state],
                outputs=[detail_likes]
            ).then(
                fn=load_comments,
                inputs=[selected_post_id],
                outputs=[comments_display]
            )

            # 点赞按钮事件
            card_data["like_btn"].click(
                fn=handle_like_post,
                inputs=[card_data["id_state"], user_info_state],
                outputs=[status_text]
            ).then(
                fn=lambda p, t, l, f, u: get_posts_data(p, t, l, f, u),
                inputs=[page_state, search_tag, search_location, friend_only, user_info_state],
                outputs=[p for card in post_cards for p in [
                    card["card"], card["title"], card["meta"], card["location"],
                    card["tags"], card["content"], card["stats"], card["view_btn"],
                    card["like_btn"], card["fav_btn"], card["id_state"]
                ]] + [page_info, total_pages_state]
            )

            # 收藏按钮事件
            card_data["fav_btn"].click(
                fn=handle_favorite_post,
                inputs=[card_data["id_state"], user_info_state],
                outputs=[status_text]
            ).then(
                fn=lambda p, t, l, f, u: get_posts_data(p, t, l, f, u),
                inputs=[page_state, search_tag, search_location, friend_only, user_info_state],
                outputs=[p for card in post_cards for p in [
                    card["card"], card["title"], card["meta"], card["location"],
                    card["tags"], card["content"], card["stats"], card["view_btn"],
                    card["like_btn"], card["fav_btn"], card["id_state"]
                ]] + [page_info, total_pages_state]
            )

        # 搜索按钮事件
        search_btn.click(
            fn=lambda t, l, f, u: get_posts_data(1, t, l, f, u),
            inputs=[search_tag, search_location, friend_only, user_info_state],
            outputs=[p for card in post_cards for p in [
                card["card"], card["title"], card["meta"], card["location"],
                card["tags"], card["content"], card["stats"], card["view_btn"],
                card["like_btn"], card["fav_btn"], card["id_state"]
            ]] + [page_info, total_pages_state]
        ).then(
            fn=lambda: 1,  # 重置页码
            inputs=[],
            outputs=[page_state]
        )

        # 刷新按钮事件
        refresh_btn.click(
            fn=lambda p, t, l, f, u: get_posts_data(p, t, l, f, u),
            inputs=[page_state, search_tag, search_location, friend_only, user_info_state],
            outputs=[p for card in post_cards for p in [
                card["card"], card["title"], card["meta"], card["location"],
                card["tags"], card["content"], card["stats"], card["view_btn"],
                card["like_btn"], card["fav_btn"], card["id_state"]
            ]] + [page_info, total_pages_state]
        )

        # 分页按钮事件
        prev_page.click(
            fn=lambda p: max(1, p - 1),
            inputs=[page_state],
            outputs=[page_state]
        ).then(
            fn=lambda p, t, l, f, u: get_posts_data(p, t, l, f, u),
            inputs=[page_state, search_tag, search_location, friend_only, user_info_state],
            outputs=[p for card in post_cards for p in [
                card["card"], card["title"], card["meta"], card["location"],
                card["tags"], card["content"], card["stats"], card["view_btn"],
                card["like_btn"], card["fav_btn"], card["id_state"]
            ]] + [page_info, total_pages_state]
        )

        next_page.click(
            fn=lambda p, tp: min(tp, p + 1),
            inputs=[page_state, total_pages_state],
            outputs=[page_state]
        ).then(
            fn=lambda p, t, l, f, u: get_posts_data(p, t, l, f, u),
            inputs=[page_state, search_tag, search_location, friend_only, user_info_state],
            outputs=[p for card in post_cards for p in [
                card["card"], card["title"], card["meta"], card["location"],
                card["tags"], card["content"], card["stats"], card["view_btn"],
                card["like_btn"], card["fav_btn"], card["id_state"]
            ]] + [page_info, total_pages_state]
        )

        # 刷新标签事件
        refresh_tags_btn.click(
            fn=get_tags_data,
            inputs=[],
            outputs=[tags_display]
        )

        # 详情页面的点赞按钮事件
        detail_like_btn.click(
            fn=handle_like_post,
            inputs=[selected_post_id, user_info_state],
            outputs=[status_text]
        ).then(
            fn=load_post_detail,
            inputs=[selected_post_id, user_info_state],
            outputs=[
                detail_title, detail_meta, detail_tags,
                detail_location, detail_content, detail_media,
                detail_stats, detail_like_btn, detail_fav_btn
            ]
        ).then(
            fn=lambda p, t, l, f, u: get_posts_data(p, t, l, f, u),
            inputs=[page_state, search_tag, search_location, friend_only, user_info_state],
            outputs=[p for card in post_cards for p in [
                card["card"], card["title"], card["meta"], card["location"],
                card["tags"], card["content"], card["stats"], card["view_btn"],
                card["like_btn"], card["fav_btn"], card["id_state"]
            ]] + [page_info, total_pages_state]
        )

        # 详情页面的收藏按钮事件
        detail_fav_btn.click(
            fn=handle_favorite_post,
            inputs=[selected_post_id, user_info_state],
            outputs=[status_text]
        ).then(
            fn=load_post_detail,
            inputs=[selected_post_id, user_info_state],
            outputs=[
                detail_title, detail_meta, detail_tags,
                detail_location, detail_content, detail_media,
                detail_stats, detail_like_btn, detail_fav_btn
            ]
        ).then(
            fn=lambda p, t, l, f, u: get_posts_data(p, t, l, f, u),
            inputs=[page_state, search_tag, search_location, friend_only, user_info_state],
            outputs=[p for card in post_cards for p in [
                card["card"], card["title"], card["meta"], card["location"],
                card["tags"], card["content"], card["stats"], card["view_btn"],
                card["like_btn"], card["fav_btn"], card["id_state"]
            ]] + [page_info, total_pages_state]
        )

        # 返回列表事件
        back_to_list_btn.click(
            fn=switch_to_list_view,
            inputs=[],
            outputs=[list_view, detail_view, create_view, view_state]
        )

        back_from_create_btn.click(
            fn=switch_to_list_view,
            inputs=[],
            outputs=[list_view, detail_view, create_view, view_state]
        )

        # 评论提交按钮事件
        submit_comment_btn.click(
            fn=post_comment,
            inputs=[selected_post_id, comment_input, user_info_state],
            outputs=[status_text, comment_input]
        ).then(
            fn=load_comments,
            inputs=[selected_post_id],
            outputs=[comments_display]
        )

        # 创建新动态按钮
        create_post_btn.click(
            fn=switch_to_create_view,
            inputs=[],
            outputs=[list_view, detail_view, create_view, view_state]
        )

        # 绑定发布按钮事件
        submit_post_btn.click(
            fn=create_new_post,
            inputs=[
                post_title, post_content, post_location,
                use_current_location, post_tags, post_media,
                post_visibility, user_info_state
            ],
            outputs=[post_result]
        ).then(
            fn=switch_to_list_view,  # 改为使用视图切换函数
            inputs=[],
            outputs=[list_view, detail_view, create_view, view_state]
        ).then(
            fn=clear_post_form,
            inputs=[],
            outputs=[
                post_title, post_content, post_location,
                use_current_location, post_tags, post_media,
                post_visibility, post_result
            ]
        ).then(
            fn=lambda p, t, l, f, u: get_posts_data(p, t, l, f, u),
            inputs=[page_state, search_tag, search_location, friend_only, user_info_state],
            outputs=[p for card in post_cards for p in [
                card["card"], card["title"], card["meta"], card["location"],
                card["tags"], card["content"], card["stats"], card["view_btn"],
                card["like_btn"], card["fav_btn"], card["id_state"]
            ]] + [page_info, total_pages_state]
        )

        # 取消按钮事件
        cancel_create_btn.click(
            fn=switch_to_list_view,
            inputs=[],
            outputs=[list_view, detail_view, create_view, view_state]
        )

        # 获取初始数据的函数
        def init_data():
            try:
                # 初始化更新列表
                updates = []

                # 为每个卡片添加更新
                for i in range(PAGE_SIZE):
                    updates.append(gr.update(visible=False))  # 卡片可见性
                    updates.extend([gr.update() for _ in range(10)])  # 10个内容组件
                    # 注意：这里是10而不是9，因为每个卡片有11个组件（卡片本身 + 10个子组件）

                # 添加页面信息和总页数
                updates.append("第 1 页，共 1 页")  # page_info
                updates.append(1)  # total_pages_state

                # 添加标签显示
                updates.append("*加载中...*")  # tags_display

                # 尝试获取动态数据
                try:
                    posts_data = travel_post_service.get_posts(page=1, page_size=PAGE_SIZE)

                    if posts_data and posts_data.get("posts"):
                        posts = posts_data.get("posts", [])
                        total = posts_data.get("total", 0)
                        total_pages = posts_data.get("total_pages", 1)

                        # 重新构建更新列表
                        updates = []

                        # 处理每个卡片
                        for i in range(PAGE_SIZE):
                            if i < len(posts):
                                # 有数据，显示卡片
                                post = posts[i]
                                post_id = post["id"]
                                title = post.get("title", "无标题")
                                username = post.get("nickname") or post.get("username", "用户")

                                # 格式化时间
                                created_time = post.get("created_at", "")
                                if isinstance(created_time, datetime.datetime):
                                    created_time = created_time.strftime("%Y年%m月%d日 %H:%M")

                                # 内容预览
                                content = post.get("content", "")
                                if len(content) > 150:
                                    content = content[:150] + "..."

                                # 标签
                                tags_text = ""
                                if post.get("tags"):
                                    tags_text = " ".join([f"#{tag}" for tag in post["tags"]])

                                # 位置
                                location_text = ""
                                if post.get("location_name"):
                                    location_text = f"📍 {post['location_name']}"

                                # 统计数据
                                like_count = post.get("like_count", 0)
                                comment_count = post.get("comment_count", 0)

                                # 用户交互状态
                                liked = post.get("user_liked", False)
                                favorited = post.get("user_favorited", False)

                                # 添加卡片可见性更新
                                updates.append(gr.update(visible=True))  # 卡片可见性

                                # 添加内容更新
                                updates.append(f"### {title}")  # 标题
                                updates.append(f"**发布者:** {username} | **发布于:** {created_time}")  # 元数据
                                updates.append(location_text)  # 位置
                                updates.append(tags_text)  # 标签
                                updates.append(content)  # 内容
                                updates.append(f"👁️ {like_count + comment_count} 次查看")  # 统计

                                # 更新按钮文本
                                updates.append(gr.update(value="查看详情"))  # 查看按钮
                                updates.append(gr.update(
                                    value=f"👍 {like_count}",
                                    variant="primary" if liked else "secondary"
                                ))  # 点赞按钮
                                updates.append(gr.update(
                                    value="⭐ 已收藏" if favorited else "⭐ 收藏",
                                    variant="primary" if favorited else "secondary"
                                ))  # 收藏按钮

                                # 更新帖子ID
                                updates.append(post_id)  # post_id_state
                            else:
                                # 无数据，隐藏卡片
                                updates.append(gr.update(visible=False))  # 卡片可见性
                                # 添加10个空更新 - 标题,元数据,位置,标签,内容,统计,查看按钮,点赞按钮,收藏按钮,ID
                                updates.extend([gr.update() for _ in range(10)])

                        # 添加页面信息和总页数
                        updates.append(f"第 1 页，共 {total_pages} 页，总计 {total} 条动态")  # page_info
                        updates.append(total_pages)  # total_pages_state

                    # 获取热门标签
                    tags = travel_post_service.get_popular_tags()
                    if tags:
                        tag_links = []
                        for tag in tags:
                            tag_name = tag.get("tag_name") or tag.get("name", "未知标签")
                            tag_count = tag.get("count", 0)
                            tag_links.append(f"**#{tag_name}** ({tag_count})")

                        tags_html = " · ".join(tag_links) if tag_links else "*没有热门标签*"
                    else:
                        tags_html = "*没有热门标签*"

                    # 添加标签显示
                    updates.append(tags_html)  # tags_display

                    return updates

                except Exception as e:
                    # 发生错误，回退到空数据
                    print(f"初始化数据加载失败: {str(e)}")

                    # 确保更新列表有正确数量的元素
                    updates = []

                    # 第一个卡片显示错误信息
                    updates.append(gr.update(visible=True))  # 卡片可见性
                    updates.append("### 加载失败")  # 标题
                    updates.append("**错误信息**")  # 元数据
                    updates.append("")  # 位置
                    updates.append("")  # 标签
                    updates.append(f"*加载动态失败: {str(e)}*")  # 内容
                    updates.append("")  # 统计
                    updates.append(gr.update(visible=False))  # 查看按钮
                    updates.append(gr.update(visible=False))  # 点赞按钮
                    updates.append(gr.update(visible=False))  # 收藏按钮
                    updates.append(0)  # post_id_state

                    # 隐藏其余卡片
                    for i in range(1, PAGE_SIZE):
                        updates.append(gr.update(visible=False))  # 卡片可见性
                        updates.extend([gr.update() for _ in range(10)])  # 10个内容组件

                    # 添加页面信息和总页数以及标签
                    updates.append(f"加载失败: {str(e)}")  # page_info
                    updates.append(1)  # total_pages_state
                    updates.append(f"*加载标签失败: {str(e)}*")  # tags_display

                    return updates

            except Exception as e:
                # 确保在任何情况下都返回正确数量的元素
                print(f"init_data函数执行失败: {str(e)}")

                # 创建完整的空更新列表
                empty_updates = []
                for i in range(PAGE_SIZE):
                    empty_updates.append(gr.update(visible=False))  # 卡片可见性
                    empty_updates.extend([gr.update() for _ in range(10)])  # 10个内容组件

                # 添加额外的3个元素
                empty_updates.append("加载失败")  # page_info
                empty_updates.append(1)  # total_pages_state
                empty_updates.append("*加载失败*")  # tags_display

                return empty_updates

        # 触发初始数据加载
        outputs_list = []
        for card in post_cards:
            outputs_list.append(card["card"])
            outputs_list.append(card["title"])
            outputs_list.append(card["meta"])
            outputs_list.append(card["location"])
            outputs_list.append(card["tags"])
            outputs_list.append(card["content"])
            outputs_list.append(card["stats"])
            outputs_list.append(card["view_btn"])
            outputs_list.append(card["like_btn"])
            outputs_list.append(card["fav_btn"])
            outputs_list.append(card["id_state"])

        outputs_list.extend([page_info, total_pages_state, tags_display])

        # Instead of gr.on()
        travel_post_tab.select(
            fn=init_data,
            inputs=None,
            outputs=outputs_list
        )

        # 返回组件和初始化函数
        return {
            "container": travel_post_tab,
            "posts_container": posts_container,
            "tags_display": tags_display,
            "refresh_posts": refresh_btn,
            "refresh_tags": refresh_tags_btn,
            "list_view": list_view,  # 添加各视图组件
            "detail_view": detail_view,
            "create_view": create_view
        }

