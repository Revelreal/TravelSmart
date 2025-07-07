# MainProject/app/ui/user_profile_ui.py
import datetime
import time

import gradio as gr
from MainProject.app.services.user_profile_service import UserProfileService
from MainProject.app.services.travel_post_service import TravelPostService
from MainProject.app.services.user_stats_service import UserStatsService  # 新增导入
from MainProject.app.ui.common_components import create_post_detail_view, create_styled_likes_display, create_styled_comments_display


def create_user_profile_ui(user_info_state):
    """创建用户个人中心UI（重构版）"""
    user_profile_service = UserProfileService()
    travel_post_service = TravelPostService()
    user_stats_service = UserStatsService()  # 新增初始化

    with gr.TabItem("个人中心"):
        gr.Markdown("## 个人中心")
        # ==================== 个人资料标签页 ====================
        with gr.TabItem("个人资料"):
            with gr.Row():
                with gr.Column(scale=1):
                    login_status = gr.Markdown("请先登录")

                    with gr.Group():
                        gr.Markdown("### 查看其他用户")
                        user_id_input = gr.Number(label="用户ID", precision=0)
                        view_user_btn = gr.Button("查看")
                        view_result = gr.Markdown()

                with gr.Column(scale=2):
                    with gr.Group():
                        gr.Markdown("### 我的资料")
                        profile_info = gr.HTML("请先登录查看个人资料")
                        refresh_profile_btn = gr.Button("刷新")

                    with gr.Group():
                        gr.Markdown("### 编辑资料")
                        nickname = gr.Textbox(label="昵称")
                        city = gr.Textbox(label="城市")
                        avatar = gr.File(label="上传头像")
                        update_btn = gr.Button("更新")
                        update_result = gr.Markdown()
            # 初始加载按钮
            initial_load_btn = gr.Button("加载个人资料", visible=True)

        # ==================== 统计信息标签页 ====================
        with gr.TabItem("统计信息"):
            with gr.Group():
                gr.Markdown("### 我的数据概览")
                stats_container = gr.HTML("加载中...")
                refresh_stats_btn = gr.Button("刷新数据")

        # ==================== 我的动态标签页 ====================
        with gr.TabItem("我的动态"):
            with gr.Group():
                gr.Markdown("### 我发布的动态")

                # 状态组件
                my_posts_view_state = gr.State("list")  # 可能的值: "list", "detail", "edit", "delete"
                my_post_selected_id = gr.State(None)  # 选中的动态ID

                # ===== 列表视图 =====
                with gr.Group(visible=True) as my_posts_list_view:
                    with gr.Row():
                        post_filter = gr.Radio(["全部", "公开", "仅好友", "私密"], label="筛选", value="全部")
                        refresh_posts_btn = gr.Button("刷新")

                    # 分页信息和控制
                    with gr.Row():
                        prev_posts_page = gr.Button("上一页")
                        posts_page_info = gr.Markdown("第 1 页，共 1 页")
                        next_posts_page = gr.Button("下一页")

                    # 创建动态卡片容器
                    my_post_cards = []
                    with gr.Group() as my_posts_container:
                        for i in range(6):  # 每页显示6条动态
                            with gr.Group(visible=False, elem_classes="post-card") as card:
                                post_title = gr.Markdown("### 标题")
                                post_meta = gr.Markdown("**发布于:** 时间")
                                post_privacy = gr.Markdown("🌍 公开", elem_classes="post-privacy")
                                post_location = gr.Markdown("", elem_classes="post-location")
                                post_tags = gr.Markdown("", elem_classes="post-tags")
                                post_content = gr.Markdown("内容")

                                with gr.Row(elem_classes="action-row"):
                                    post_stats = gr.Markdown("👁️ 0 次查看", elem_classes="stats-text")
                                    post_view_btn = gr.Button("查看详情")
                                    post_edit_btn = gr.Button("编辑")
                                    post_delete_btn = gr.Button("删除", variant="stop")

                                # 存储帖子ID (用于操作)
                                post_id_state = gr.State(0)

                                # 将组件添加到卡片列表
                                my_post_cards.append({
                                    "card": card,
                                    "title": post_title,
                                    "meta": post_meta,
                                    "privacy": post_privacy,
                                    "location": post_location,
                                    "tags": post_tags,
                                    "content": post_content,
                                    "stats": post_stats,
                                    "view_btn": post_view_btn,
                                    "edit_btn": post_edit_btn,
                                    "delete_btn": post_delete_btn,
                                    "id_state": post_id_state
                                })

                    # 隐藏状态
                    posts_current_page = gr.State(1)
                    posts_total_pages = gr.State(1)

                # ===== 详情视图 =====
                # 在my_post_detail_view中修改

                with gr.Group(visible=False) as my_post_detail_view:
                    with gr.Row():
                        back_to_my_posts_btn = gr.Button("⬅️ 返回列表")

                    with gr.Group(elem_classes="detail-container"):
                        my_post_title = gr.Markdown("### 标题")
                        my_post_meta = gr.Markdown("*发布信息*")
                        my_post_privacy = gr.Markdown("*可见性*")
                        my_post_tags = gr.Markdown("*标签*")
                        my_post_location = gr.Markdown("*位置*")
                        my_post_content = gr.Markdown("*内容*")
                        my_post_media = gr.Gallery(label="媒体内容")

                        with gr.Row():
                            my_post_stats = gr.Markdown("*统计数据*")
                            edit_post_btn = gr.Button("✏️ 编辑动态")
                            delete_post_btn = gr.Button("🗑️ 删除动态", variant="stop")

                    # 添加点赞用户列表
                    with gr.Group(elem_classes="likes-section"):
                        gr.Markdown("### 点赞用户")
                        my_post_likes = gr.HTML("*加载中...*")

                    # 增强评论区
                    with gr.Group(elem_classes="comments-section"):
                        gr.Markdown("### 评论区")
                        # 评论列表
                        my_post_comments = gr.HTML("*加载中...*")

                # ===== 编辑视图 =====
                with gr.Group(visible=False) as my_post_edit_view:
                    with gr.Row():
                        back_to_detail_btn = gr.Button("⬅️ 返回详情")

                    gr.Markdown("### 编辑动态")
                    edit_title = gr.Textbox(label="标题")
                    edit_content = gr.Textbox(label="内容", lines=5)

                    with gr.Row():
                        edit_location = gr.Textbox(label="位置", placeholder="请输入位置名称")
                        use_current_loc = gr.Checkbox(label="使用当前位置")

                    edit_tags = gr.Textbox(
                        label="标签",
                        placeholder="请输入标签，多个标签用空格分隔，如：美食 风景 自驾游"
                    )

                    edit_visibility = gr.Radio(
                        label="可见范围",
                        choices=["公开", "仅好友可见", "仅自己可见"]
                    )

                    edit_media = gr.File(
                        label="上传图片/视频",
                        file_types=["image", "video"],
                        file_count="multiple"
                    )
                    current_media_preview = gr.Gallery(label="当前媒体")
                    keep_current_media = gr.Checkbox(label="保留现有媒体", value=True)

                    with gr.Row():
                        cancel_edit_btn = gr.Button("取消")
                        update_post_btn = gr.Button("更新动态", variant="primary")

                    edit_result = gr.Markdown(visible=False)

                # ===== 删除确认对话框 =====
                with gr.Group(visible=False) as delete_confirm_dialog:
                    gr.Markdown("### 确认删除")
                    gr.Markdown("您确定要删除这条动态吗？此操作无法撤销。")

                    with gr.Row():
                        cancel_delete_btn = gr.Button("取消")
                        confirm_delete_btn = gr.Button("确认删除", variant="stop")

                    delete_result = gr.Markdown(visible=False)

        # ==================== 我的收藏标签页 ====================
        with gr.TabItem("我的收藏"):
            with gr.Group():
                gr.Markdown("### 我的收藏内容")

                # 刷新按钮
                refresh_favs_btn = gr.Button("🔄 刷新收藏")

                # 切换状态
                fav_view_state = gr.State("list")  # "list" 或 "detail"

                # 列表视图
                with gr.Group(visible=True) as fav_list_view:
                    fav_cards = []
                    with gr.Group() as favs_container:
                        for i in range(10):  # 假设最多显示10条收藏
                            with gr.Group(visible=False, elem_classes="fav-card") as fav_card:
                                fav_title = gr.Markdown("### 标题")
                                fav_meta = gr.Markdown("**类型:** 动态 | **收藏于:** 时间")
                                fav_author = gr.Markdown("**作者:** 用户名", elem_classes="fav-author")
                                fav_location = gr.Markdown("", elem_classes="fav-location")
                                fav_tags = gr.Markdown("", elem_classes="fav-tags")
                                fav_content = gr.Markdown("内容...", elem_classes="fav-content")
                                fav_media = gr.Gallery(label="媒体", show_label=False, visible=False,
                                                       elem_classes="fav-media")
                                view_detail_btn = gr.Button("查看详情", elem_classes="view-btn")
                                fav_remove_btn = gr.Button("取消收藏", variant="stop", elem_classes="unfav-btn")


                                # 存储收藏ID
                                fav_id_state = gr.State(None)
                                # 存储内容ID
                                content_id_state = gr.State(None)
                                # 将组件添加到卡片列表
                                fav_cards.append({
                                    "card": fav_card,
                                    "title": fav_title,
                                    "meta": fav_meta,
                                    "author": fav_author,
                                    "location": fav_location,
                                    "tags": fav_tags,
                                    "content": fav_content,
                                    "media": fav_media,
                                    "view_btn": view_detail_btn,  # 新增查看按钮
                                    "remove_btn": fav_remove_btn,
                                    "id_state": fav_id_state,
                                    "content_id_state": content_id_state  # 新增
                                })

                    # 添加"加载更多"按钮
                    load_more_favs_btn = gr.Button("加载更多", visible=False)

                # 详情视图 - 使用我们的通用函数创建
                fav_detail_components = create_post_detail_view(gr.Group(), is_from_favorites=True)
                fav_detail_view = fav_detail_components["view"]

                # 确认对话框
                with gr.Group(visible=False) as unfav_confirm_dialog:
                    gr.Markdown("### 确认取消收藏")
                    unfav_confirm_text = gr.Markdown("您确定要取消收藏这个内容吗？")

                    with gr.Row():
                        cancel_unfav_btn = gr.Button("取消")
                        confirm_unfav_btn = gr.Button("确认取消", variant="stop")

                    unfav_id_state = gr.State(None)  # 存储要取消收藏的ID

        # ==================== 隐私设置标签页 ====================
        with gr.TabItem("隐私设置"):
            with gr.Group():
                gr.Markdown("### 隐私与安全")

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 资料可见性")
                        profile_visibility = gr.Radio(
                            ["public", "friends", "private"],
                            label="个人资料",
                            value="public"
                        )
                        post_privacy = gr.Radio(
                            ["public", "friends", "private"],
                            label="动态默认",
                            value="public"
                        )

                    with gr.Column():
                        gr.Markdown("#### 互动设置")
                        allow_requests = gr.Checkbox(label="允许好友请求", value=True)
                        show_online = gr.Checkbox(label="显示在线状态", value=True)

                save_btn = gr.Button("保存设置")
                save_result = gr.Markdown()

        # ==================== 通知标签页 ====================
        with gr.TabItem("通知"):
            with gr.Group():
                gr.Markdown("### 我的通知")

                with gr.Row():
                    notification_filter = gr.Radio(["全部", "未读", "已读"], label="筛选", value="全部")
                    notifications_page = gr.Slider(1, 10, value=1, step=1, label="页码")
                    refresh_notifs_btn = gr.Button("刷新")

                notifications = gr.HTML("加载中...")
                notifs_page_info = gr.Markdown("第 1 页，共 1 页")

                with gr.Row():
                    prev_notifs_page = gr.Button("上一页")
                    next_notifs_page = gr.Button("下一页")
                    mark_read_btn = gr.Button("标记已读")

                # 隐藏组件
                notifs_current_page = gr.State(1)
                notifs_total_pages = gr.State(1)



    # ==================== 交互函数 ====================
    def check_login(user_data):
        return f"已登录: {user_data.get('username')}" if user_data else "请先登录"

    def load_profile_data(user_data):
        """加载个人资料数据"""
        if not user_data:
            return "<div>请先登录</div>", "<div>请先登录</div>"

        try:
            # 基本信息
            profile = user_profile_service.get_user_profile(
                user_data["user_id"],
                user_data["user_id"]
            )

            if not profile:
                return "<div>无法加载个人资料</div>", "<div>无法加载统计信息</div>"

            profile_html = f"""
            <div class='profile'>
                <img src='{profile.get('avatar', '/default.png')}' class='profile-avatar'/>
                <div class='profile-info'>
                    <h2>{profile.get('username')}</h2>
                    <p><strong>昵称:</strong> {profile.get('nickname', '未设置')}</p>
                    <p><strong>城市:</strong> {profile.get('city', '未设置')}</p>
                    <p><strong>注册时间:</strong> {profile.get('create_time')}</p>
                </div>
            </div>
            """

            # 统计信息
            stats_html = user_stats_service.get_simple_user_statistics(user_data["user_id"])
            stats_html += user_stats_service.generate_statistics_html(user_data["user_id"])

            return profile_html, stats_html
        except Exception as e:
            return f"<div class='error'>错误: {str(e)}</div>", f"<div class='error'>错误: {str(e)}</div>"

    def view_other_user(user_id, user_data):
        if not user_data:
            return "请先登录"
        if not user_id:
            return "请输入有效的用户ID"

        try:
            profile = user_profile_service.get_user_profile(
                user_id,
                user_data["user_id"]
            )

            if not profile:
                return "用户不存在"

            if profile.get("privacy") == "private":
                return "该用户的资料是私密的"
            elif profile.get("privacy") == "friends_only":
                return "只有好友才能查看"

            return f"已加载用户 {profile.get('username')} 的资料"
        except Exception as e:
            return f"错误: {str(e)}"

    def update_profile(nickname, city, avatar, user_data):
        if not user_data:
            return "请先登录"

        try:
            update_data = {}
            if nickname:
                update_data["nickname"] = nickname
            if city:
                update_data["city"] = city
            if avatar:
                update_data["avatar"] = "path/to/avatar.jpg"  # 实际应用中需要处理文件上传

            success, message = user_profile_service.update_user_profile(
                user_data["user_id"],
                update_data
            )
            return message
        except Exception as e:
            return f"错误: {str(e)}"

    def load_my_posts(filter_type, page, user_data):
        """加载用户自己的动态并填充卡片视图"""
        if not user_data:
            # 返回更新操作列表：所有卡片不可见
            updates = []
            for i in range(6):  # 假设每页最多6条动态
                updates.append(gr.update(visible=False))  # 卡片可见性
                updates.extend([gr.update() for _ in range(10)])  # 10个内容组件无变化
                updates.append(0)  # post_id_state

            return updates + [1, 1, "第 1 页，共 1 页，请先登录"]

        try:
            # 转换筛选条件为隐私级别
            privacy_map = {
                "全部": None,
                "公开": "public",
                "仅好友": "friends",
                "私密": "private"
            }
            privacy_level = privacy_map.get(filter_type)

            # 获取动态列表
            result = user_profile_service.get_self_posts(
                user_id=user_data["user_id"],
                privacy_level=privacy_level,
                page=page,
                page_size=6  # 每页显示6条动态
            )

            posts = result.get("posts", [])
            total = result.get("total", 0)
            total_pages_val = result.get("total_pages", 1)

            # 准备更新列表 - 将为每个卡片组件更新内容
            updates = []

            # 填充动态卡片
            for i in range(6):
                if i < len(posts):
                    # 有数据，显示卡片
                    post = posts[i]
                    post_id = post.get("id", 0)
                    title = post.get("title", "无标题")

                    # 格式化时间
                    created_time = post.get("created_at", "")
                    if isinstance(created_time, datetime.datetime):
                        created_time = created_time.strftime("%Y年%m月%d日 %H:%M")

                    # 获取内容预览
                    content = post.get("content", "")
                    if len(content) > 100:
                        content = content[:100] + "..."

                    # 隐私级别
                    privacy = post.get("privacy_level", "public")
                    privacy_icon = "🌍" if privacy == "public" else ("👥" if privacy == "friends" else "🔒")
                    privacy_text = f"{privacy_icon} " + (
                        "公开" if privacy == "public" else ("好友可见" if privacy == "friends" else "仅自己可见"))

                    # 位置
                    location_text = ""
                    if post.get("location_name"):
                        location_text = f"📍 {post.get('location_name')}"

                    # 标签
                    tags = post.get("tags", [])
                    tags_text = " ".join([f"#{tag}" for tag in tags]) if tags else ""

                    # 统计数据
                    like_count = post.get("like_count", 0)
                    comment_count = post.get("comment_count", 0)

                    # 更新卡片组件
                    updates.append(gr.update(visible=True))  # 卡片可见性
                    updates.append(f"### {title}")  # 标题
                    updates.append(f"**发布于:** {created_time}")  # 元数据
                    updates.append(privacy_text)  # 隐私级别
                    updates.append(location_text)  # 位置
                    updates.append(tags_text)  # 标签
                    updates.append(content)  # 内容
                    updates.append(f"❤️ {like_count} · 💬 {comment_count}")  # 统计

                    # 更新按钮文本和状态
                    updates.append(gr.update(value="查看详情"))  # 查看按钮
                    updates.append(gr.update(value="编辑"))  # 编辑按钮
                    updates.append(gr.update(value="删除"))  # 删除按钮

                    # 更新帖子ID
                    updates.append(post_id)
                else:
                    # 无数据，隐藏卡片
                    updates.append(gr.update(visible=False))  # 卡片可见性
                    updates.extend([gr.update() for _ in range(10)])  # 10个内容组件无变化
                    updates.append(0)  # post_id_state

            # 添加分页信息
            updates.extend([
                page,  # 当前页
                total_pages_val,  # 总页数
                f"第 {page} 页，共 {total_pages_val} 页，总计 {total} 条动态"  # 页面信息
            ])

            return updates

        except Exception as e:
            # 发生错误，所有卡片不可见
            updates = []
            for i in range(6):
                updates.append(gr.update(visible=False))  # 卡片可见性
                updates.extend([gr.update() for _ in range(10)])  # 10个内容组件无变化
                updates.append(0)  # post_id_state

            return updates + [page, 1, f"加载失败: {str(e)}"]

    def load_favorites(user_data):
        """加载收藏内容并填充卡片"""
        if not user_data:
            print("用户未登录，无法加载收藏")
            # 返回更新操作列表：所有卡片不可见
            updates = []
            for i in range(10):  # 假设最多10条收藏
                updates.append(gr.update(visible=False))  # 卡片可见性
                updates.extend([
                    gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(), gr.update(), gr.update(visible=False), gr.update(), None, None
                    # 增加一个None，对应content_id_state
                ])

            # 隐藏加载更多按钮
            updates.append(gr.update(visible=False))

            return updates

        try:
            print(f"正在加载用户 {user_data['user_id']} 的收藏")
            # 获取收藏列表
            result = user_profile_service.get_user_favorites(
                user_id=user_data["user_id"],
                content_type=None,  # 不筛选类型
                page=1,
                page_size=10  # 一次加载10条
            )

            favorites = result.get("favorites", [])
            total = result.get("total", 0)

            print(f"获取到 {len(favorites)} 条收藏，总共 {total} 条")

            # 准备更新列表
            updates = []

            # 填充收藏卡片
            for i in range(10):
                if i < len(favorites):
                    # 有数据，显示卡片
                    fav = favorites[i]
                    fav_id = fav.get("id")
                    content_id = fav.get("content_id")  # 获取内容ID
                    content_type = fav.get("content_type", "")
                    created_time = fav.get("created_at", "")

                    if isinstance(created_time, datetime.datetime):
                        created_time = created_time.strftime("%Y年%m月%d日 %H:%M")

                    details = fav.get("details", {})

                    print(f"处理第 {i + 1} 条收藏: 类型={content_type}, ID={fav_id}")

                    # 根据内容类型处理
                    if content_type == "post":
                        title = details.get("title", "无标题")
                        content = details.get("content", "")

                        username = details.get("username") or details.get("nickname", "用户")
                        type_text = "**类型:** 动态"

                        # 位置和标签
                        location = details.get("location_name", "")
                        location_text = f"📍 {location}" if location else ""

                        tags = details.get("tags", [])
                        tags_text = " ".join([f"#{tag}" for tag in tags]) if tags else ""

                        # 媒体
                        media_files = []
                        media_visible = False
                        if fav.get("media"):
                            for media in fav.get("media"):
                                if isinstance(media, dict) and media.get("media_url"):
                                    media_files.append(media.get("media_url"))
                                    media_visible = True

                    else:  # location
                        title = details.get("name", "未知地点")
                        content = details.get("description", "")

                        username = "系统"
                        type_text = "**类型:** 地点"

                        # 地址和分类
                        location = details.get("address", "")
                        location_text = f"📍 {location}" if location else ""

                        categories = details.get("categories", [])
                        tags_text = " ".join([f"#{cat}" for cat in categories]) if categories else ""

                        # 地点可能有图片
                        media_files = []
                        media_visible = False
                        if details.get("photos"):
                            for photo in details.get("photos"):
                                if isinstance(photo, str):
                                    media_files.append(photo)
                                    media_visible = True

                    # 更新卡片组件
                    updates.append(gr.update(visible=True))  # 卡片可见性
                    updates.append(f"### {title}")  # 标题
                    updates.append(f"{type_text} | **收藏于:** {created_time}")  # 元数据
                    updates.append(f"**作者:** {username}")  # 作者
                    updates.append(location_text)  # 位置
                    updates.append(tags_text)  # 标签
                    updates.append(content)  # 内容
                    updates.append(gr.update(value=media_files, visible=media_visible))  # 媒体
                    updates.append(gr.update(value="取消收藏"))  # 取消收藏按钮
                    updates.append(fav_id)  # 收藏ID
                    updates.append(content_id)  # 内容ID - 新增，确保返回这个值
                else:
                    # 无数据，隐藏卡片
                    updates.append(gr.update(visible=False))  # 卡片可见性
                    updates.extend([
                        gr.update(), gr.update(), gr.update(), gr.update(),
                        gr.update(), gr.update(), gr.update(visible=False), gr.update(), None, None  # 增加一个None
                    ])

            # 如果还有更多收藏，显示加载更多按钮
            if total > 10:
                updates.append(gr.update(visible=True))
            else:
                updates.append(gr.update(visible=False))

            return updates

        except Exception as e:
            print(f"加载收藏失败: {str(e)}")
            import traceback
            traceback.print_exc()

            # 发生错误，所有卡片不可见
            updates = []
            for i in range(10):
                updates.append(gr.update(visible=False))  # 卡片可见性
                updates.extend([
                    gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(), gr.update(), gr.update(visible=False), gr.update(), None, None  # 增加一个None
                ])

            # 隐藏加载更多按钮
            updates.append(gr.update(visible=False))

            gr.Error(f"加载收藏失败: {str(e)}")
            return updates

    def load_notifications(filter_type, page, user_data):
        if not user_data:
            return "<div class='error'>请先登录</div>", 1, 1, "第 1 页，共 1 页"

        try:
            # 转换筛选条件
            is_read_map = {
                "全部": None,
                "未读": False,
                "已读": True
            }
            is_read = is_read_map.get(filter_type)

            result = user_profile_service.get_user_notifications(
                user_id=user_data["user_id"],
                is_read=is_read,
                page=page,
                page_size=20
            )

            notifications_data = result.get("notifications", [])
            total = result.get("total", 0)
            total_pages_val = result.get("total_pages", 1)
            unread_count = result.get("unread_count", 0)

            if not notifications_data:
                return f"<div class='no-notifications'>没有{filter_type}通知</div>", page, total_pages_val, f"第 {page} 页，共 {total_pages_val} 页，未读: {unread_count}"

            # 构建HTML内容
            html = f"<div class='notifications-container'><div class='unread-count'>未读通知: {unread_count}</div>"

            for notif in notifications_data:
                notif_id = notif.get("_id", "")
                content = notif.get("content", "")
                created_at = notif.get("created_at", "")
                is_read = notif.get("is_read", False)
                notif_type = notif.get("type", "")

                # 获取发起者信息
                actor = notif.get("actor", {})
                actor_name = actor.get("username") or actor.get("nickname") or "用户"

                # 根据通知类型设置图标
                icon_map = {
                    "friend_request": "👥",
                    "friend_accept": "✅",
                    "post_like": "❤️",
                    "post_comment": "💬",
                    "system": "🔔"
                }
                icon = icon_map.get(notif_type, "🔔")

                # 未读通知样式
                read_class = "" if is_read else "unread"

                html += f"""
                        <div class='notification-item {read_class}' data-notif-id='{notif_id}'>
                            <div class='notif-icon'>{icon}</div>
                            <div class='notif-content'>
                                <div class='notif-text'><span class='actor'>{actor_name}</span> {content}</div>
                                <div class='notif-time'>{created_at}</div>
                            </div>
                        </div>
                        """

            html += "</div>"

            return html, page, total_pages_val, f"第 {page} 页，共 {total_pages_val} 页，未读: {unread_count}"
        except Exception as e:
            return f"<div class='error'>错误: {str(e)}</div>", page, 1, "加载错误"

    def mark_notifications_read(user_data):
        if not user_data:
            return "请先登录"

        try:
            success, message = user_profile_service.mark_notifications_read(
                user_data["user_id"]
            )
            return message
        except Exception as e:
            return f"标记已读失败: {str(e)}"

    def save_privacy_settings(profile_vis, post_priv, allow_req, show_online, user_data):
        if not user_data:
            return "请先登录"

        try:
            settings = {
                "profile_visibility": profile_vis,
                "post_default_privacy": post_priv,
                "allow_friend_requests": allow_req,
                "show_online_status": show_online
            }

            success, message = user_profile_service.update_privacy_settings(
                user_data["user_id"],
                settings
            )
            return message
        except Exception as e:
            return f"保存设置失败: {str(e)}"

    def convert_files_to_media_format(file_paths):
        """将Gradio File组件返回的文件路径转换为TravelPostService需要的格式"""
        if not file_paths or not isinstance(file_paths, list):
            return []

        media_files = []
        for file_path in file_paths:
            if not file_path:
                continue

            # 确定文件类型
            file_type = "image"  # 默认为图片
            if str(file_path).lower().endswith(('.mp4', '.avi', '.mov', '.wmv')):
                file_type = "video"

            # 创建媒体对象
            media_file = {
                "type": file_type,
                "url": str(file_path),
                "thumbnail_url": None
            }
            media_files.append(media_file)

        return media_files

    def handle_media_change(new_media, keep_current):
        """当上传新媒体或更改保留设置时更新UI"""
        if new_media and len(new_media) > 0:
            # 如果上传了新媒体，尝试显示预览
            try:
                media_paths = [file.name for file in new_media if hasattr(file, 'name')]
                return gr.update(value=media_paths, visible=True), gr.update(value=False)
            except:
                # 如果预览失败，至少更新保留设置
                return gr.update(visible=True), gr.update(value=False)
        return gr.update(), gr.update()

    def print_debug_info(new_media, keep_current):
        """打印媒体文件上传调试信息"""
        print(f"新上传媒体: {new_media}")
        print(f"保留现有媒体: {keep_current}")
        return None

    # ==================== 页面转换 ====================
    def switch_to_detail_view():
        """切换到详情视图"""
        return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(
            visible=False), "detail"

    def switch_to_edit_view():
        """切换到编辑视图"""
        return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), gr.update(
            visible=False), "edit"

    def switch_to_delete_view():
        """切换到删除确认视图"""
        return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(
            visible=True), "delete"

    def back_to_list_view():
        """返回列表视图"""
        return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(
            visible=False), "list"

    def load_post_detail(post_id, user_data):
        """加载动态详情数据，包括点赞用户和评论"""
        if not post_id or not user_data:
            return "未选择动态", "", "", "", "", "", None, "", "", ""

        try:
            # 获取动态详情
            post = travel_post_service.get_post_detail(post_id, user_data["user_id"])

            if not post or post.get("user_id") != user_data["user_id"]:
                return "无权查看此动态", "", "", "", "", "", None, "", "", ""

            # 提取数据
            title = post.get("title", "无标题")
            username = post.get("nickname") or post.get("username", "用户")
            created_at = post.get("created_at", "")
            if isinstance(created_at, datetime.datetime):
                created_at = created_at.strftime("%Y-%m-%d %H:%M")

            # 隐私级别
            privacy = post.get("privacy_level", "public")
            privacy_text = "🌍 公开" if privacy == "public" else (
                "👥 好友可见" if privacy == "friends" else "🔒 仅自己可见")

            # 标签
            tags = post.get("tags", [])
            tags_text = " ".join([f"#{tag}" for tag in tags]) if tags else "无标签"

            # 位置
            location = post.get("location_name", "")
            location_text = f"📍 {location}" if location else "未设置位置"

            # 内容
            content = post.get("content", "")

            # 媒体
            media = []
            if post.get("media"):
                for item in post.get("media"):
                    if isinstance(item, dict) and item.get("media_url"):
                        media.append(item["media_url"])

            # 统计
            like_count = post.get("like_count", 0)
            comment_count = post.get("comment_count", 0)
            stats = f"❤️ {like_count} 次点赞 | 💬 {comment_count} 条评论"

            # 使用公共组件生成点赞用户列表
            likes_html = create_styled_likes_display(
                post.get("recent_likes", []),
                like_count
            )

            # 使用公共组件生成评论列表
            comments_html = create_styled_comments_display(
                post.get("recent_comments", []),
                comment_count
            )

            return (
                f"### {title}",
                f"**发布者:** {username} | **时间:** {created_at}",
                privacy_text,
                f"**标签:** {tags_text}",
                f"**位置:** {location_text}",
                content,
                media,
                stats,
                likes_html,
                comments_html
            )
        except Exception as e:
            return (
                f"加载失败: {str(e)}", "", "", "", "", "", None, "",
                "<p>加载点赞用户失败</p>",
                "<p>加载评论失败</p>"
            )

    def load_post_for_edit(post_id, user_data):
        """加载动态数据用于编辑"""
        if not post_id or not user_data:
            return "", "", "", False, "", "公开", None, True

        try:
            # 获取动态详情
            post = travel_post_service.get_post_detail(post_id, user_data["user_id"])

            if not post or post.get("user_id") != user_data["user_id"]:
                return "", "", "", False, "", "公开", None, True

            # 提取数据
            title = post.get("title", "")
            content = post.get("content", "")
            location = post.get("location_name", "")

            # 标签 - 转换为空格分隔的字符串
            tags = " ".join(post.get("tags", []))

            # 隐私级别
            privacy_map = {
                "public": "公开",
                "friends": "仅好友可见",
                "private": "仅自己可见"
            }
            visibility = privacy_map.get(post.get("privacy_level", "public"), "公开")

            # 媒体文件
            media = []
            if post.get("media"):
                for item in post.get("media"):
                    if isinstance(item, dict) and item.get("media_url"):
                        media.append(item["media_url"])

            return title, content, location, False, tags, visibility, media, True
        except Exception as e:
            return "", "", "", False, "", "公开", None, True

    def update_post(post_id, title, content, location, use_current_loc, tags, visibility,
                    new_media, keep_current, user_data):
        """更新动态"""
        if not user_data or not post_id:
            return "*更新失败：请先登录*"

        if not title.strip():
            return "*更新失败：标题不能为空*"

        if not content.strip():
            return "*更新失败：内容不能为空*"

        try:
            # 处理标签
            tag_list = []
            if tags.strip():
                tag_list = [tag.strip() for tag in tags.split() if tag.strip()]

            # 处理位置
            location_name = None
            if use_current_loc:
                location_name = "当前位置"  # 简化处理
            elif location.strip():
                location_name = location.strip()

            # 处理隐私级别
            privacy_map = {
                "公开": "public",
                "仅好友可见": "friends",
                "仅自己可见": "private"
            }
            privacy_level = privacy_map.get(visibility, "public")

            # 处理媒体文件
            media_files = None
            if not keep_current:
                # 如果不保留现有媒体，转换新上传的媒体
                if new_media and len(new_media) > 0:
                    # 转换为正确的格式
                    media_files = convert_files_to_media_format(new_media)
                    print(f"更新媒体文件: {media_files}")
                else:
                    # 明确设置为空列表，表示清除所有媒体
                    media_files = []
                    print("清除所有媒体文件")
            else:
                print("保留现有媒体文件")

            # 调用服务更新动态
            success, message = travel_post_service.update_post(
                post_id=post_id,
                user_id=user_data["user_id"],
                title=title,
                content=content,
                location_name=location_name,
                privacy_level=privacy_level,
                tags=tag_list,
                media_files=media_files
            )

            if success:
                return "*更新成功！*"
            else:
                return f"*更新失败: {message}*"
        except Exception as e:
            print(f"更新动态错误: {str(e)}")
            return f"*更新失败: {str(e)}*"

    def delete_post(post_id, user_data):
        """删除动态"""
        if not user_data:
            return "请先登录"
        if not post_id:
            return "请选择要删除的动态"

        try:
            # 调用服务删除动态
            success, message = travel_post_service.delete_post(
                post_id=post_id,
                user_id=user_data["user_id"]
            )

            if success:
                return "动态已成功删除"
            else:
                return f"删除失败: {message}"
        except Exception as e:
            return f"删除动态失败: {str(e)}"

    def handle_update_result(result):
        """根据更新结果决定是否切换视图"""
        if "成功" in result:  # 直接检查字符串内容，不使用.value
            return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(
                visible=False), "detail"
        else:
            # 更新失败，保持在编辑视图
            return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), gr.update(
                visible=False), "edit"

    def view_post_detail(post_id, user_data, from_favorites=False, favorite_id=None):
        """加载动态详情数据的统一函数"""
        if not post_id or not user_data:
            return (
                "未选择动态", "", "", "", "", "", None, "",
                "<p>请先选择动态</p>", "<p>请先选择动态</p>", None, False
            )

        try:
            # 获取动态详情
            post = travel_post_service.get_post_detail(post_id, user_data["user_id"])

            if not post:
                return (
                    "动态不存在或无权查看", "", "", "", "", "", None, "",
                    "<p>无法加载点赞信息</p>", "<p>无法加载评论</p>", None, False
                )

            # 提取数据
            title = post.get("title", "无标题")
            username = post.get("nickname") or post.get("username", "用户")
            created_at = post.get("created_at", "")
            if isinstance(created_at, datetime.datetime):
                created_at = created_at.strftime("%Y-%m-%d %H:%M")

            # 隐私级别
            privacy = post.get("privacy_level", "public")
            privacy_text = "🌍 公开" if privacy == "public" else (
                "👥 好友可见" if privacy == "friends" else "🔒 仅自己可见")

            # 标签
            tags = post.get("tags", [])
            tags_text = " ".join([f"#{tag}" for tag in tags]) if tags else "无标签"

            # 位置
            location = post.get("location_name", "")
            location_text = f"📍 {location}" if location else "未设置位置"

            # 内容
            content = post.get("content", "")
            rich_content = post.get("rich_content", content)

            # 媒体
            media = []
            if post.get("media"):
                for item in post.get("media"):
                    if isinstance(item, dict) and item.get("media_url"):
                        media.append(item["media_url"])

            # 统计
            like_count = post.get("like_count", 0)
            comment_count = post.get("comment_count", 0)
            view_count = post.get("view_count", 0)
            stats = f"👁️ {view_count} 次查看 | ❤️ {like_count} 次点赞 | 💬 {comment_count} 条评论"
            # 检查收藏状态
            is_favorited = post.get("user_favorited", False)
            if not is_favorited and not from_favorites:  # 如果来自收藏列表，必然是已收藏状态
                # 再次确认收藏状态
                is_favorited = travel_post_service.get_favorite_status(post_id, user_data["user_id"])

            # 使用公共组件生成点赞用户列表
            likes_html = create_styled_likes_display(
                post.get("recent_likes", []),
                like_count
            )

            # 使用公共组件生成评论列表
            comments_html = create_styled_comments_display(
                post.get("recent_comments", []),
                comment_count
            )

            return (
                f"### {title}",
                f"**发布者:** {username} | **时间:** {created_at}",
                privacy_text,
                f"**标签:** {tags_text}",
                f"**位置:** {location_text}",
                rich_content,
                media,
                stats,
                likes_html,
                comments_html,
                post_id,
                is_favorited,
                favorite_id  # 新增返回收藏ID
            )
        except Exception as e:
            print(f"加载动态详情失败: {str(e)}")
            import traceback
            traceback.print_exc()

            return (
                f"加载失败: {str(e)}", "", "", "", "", "", None, "",
                "<p>加载点赞用户失败</p>",
                "<p>加载评论失败</p>",
                post_id,
                False
            )

    def submit_comment(post_id, comment_text, user_data):
        """提交评论"""
        if not user_data:
            gr.Error("请先登录")
            return "请先登录才能评论"

        if not post_id:
            gr.Error("未选择动态")
            return "请先选择动态"

        if not comment_text or not comment_text.strip():
            gr.Error("评论内容不能为空")
            return "评论内容不能为空"

        try:
            result = travel_post_service.add_comment(post_id, user_data["user_id"], comment_text)

            if result.get("success"):
                gr.Info("评论发表成功")
                return ""  # 清空输入框
            else:
                gr.Error(f"评论失败: {result.get('message')}")
                return comment_text  # 保留输入内容
        except Exception as e:
            gr.Error(f"评论失败: {str(e)}")
            return comment_text  # 保留输入内容

    # ==================== 事件绑定 ====================
    # 定义动态卡片输出组件列表（用于多处刷新操作）
    def get_post_card_outputs():
        return [comp for card in my_post_cards for comp in [
            card["card"], card["title"], card["meta"], card["privacy"],
            card["location"], card["tags"], card["content"], card["stats"],
            card["view_btn"], card["edit_btn"], card["delete_btn"], card["id_state"]
        ]] + [posts_current_page, posts_total_pages, posts_page_info]

    # 定义获取卡片输出组件的函数(用于收藏显示刷新)
    def get_fav_card_outputs():
        outputs = []
        for card in fav_cards:
            outputs.extend([
                card["card"], card["title"], card["meta"], card["author"],
                card["location"], card["tags"], card["content"], card["media"],
                card["remove_btn"], card["id_state"], card["content_id_state"]
            ])
        # 添加加载更多按钮
        outputs.append(load_more_favs_btn)
        return outputs

    # 页面跳转
    # 详情页面按钮
    back_to_my_posts_btn.click(
        back_to_list_view,
        inputs=[],
        outputs=[my_posts_list_view, my_post_detail_view, my_post_edit_view, delete_confirm_dialog, my_posts_view_state]
    )

    edit_post_btn.click(
        switch_to_edit_view,
        inputs=[],
        outputs=[my_posts_list_view, my_post_detail_view, my_post_edit_view, delete_confirm_dialog, my_posts_view_state]
    ).then(
        # 清空媒体上传组件 - 修复版
        lambda: gr.update(value=None),
        inputs=[],
        outputs=[edit_media]
    ).then(
        load_post_for_edit,
        inputs=[my_post_selected_id, user_info_state],
        outputs=[
            edit_title, edit_content, edit_location,
            use_current_loc, edit_tags, edit_visibility,
            current_media_preview, keep_current_media
        ]
    )

    delete_post_btn.click(
        switch_to_delete_view,
        inputs=[],
        outputs=[my_posts_list_view, my_post_detail_view, my_post_edit_view, delete_confirm_dialog, my_posts_view_state]
    )

    # 编辑页面按钮
    back_to_detail_btn.click(
        switch_to_detail_view,
        inputs=[],
        outputs=[my_posts_list_view, my_post_detail_view, my_post_edit_view, delete_confirm_dialog, my_posts_view_state]
    ).then(
        load_post_detail,
        inputs=[my_post_selected_id, user_info_state],
        outputs=[
            my_post_title, my_post_meta, my_post_privacy,
            my_post_tags, my_post_location, my_post_content,
            my_post_media, my_post_stats, my_post_likes, my_post_comments
        ]
    )

    cancel_edit_btn.click(
        switch_to_detail_view,
        inputs=[],
        outputs=[my_posts_list_view, my_post_detail_view, my_post_edit_view, delete_confirm_dialog, my_posts_view_state]
    ).then(
        load_post_detail,
        inputs=[my_post_selected_id, user_info_state],
        outputs=[
            my_post_title, my_post_meta, my_post_privacy,
            my_post_tags, my_post_location, my_post_content,
            my_post_media, my_post_stats, my_post_likes, my_post_comments
        ]
    )

    # 更新事件
    update_post_btn.click(
        print_debug_info,
        inputs=[edit_media, keep_current_media],
        outputs=None
    ).then(
        update_post,
        inputs=[
            my_post_selected_id, edit_title, edit_content,
            edit_location, use_current_loc, edit_tags,
            edit_visibility, edit_media, keep_current_media, user_info_state
        ],
        outputs=[edit_result]
    ).then(
        handle_update_result,
        inputs=[edit_result],
        outputs=[my_posts_list_view, my_post_detail_view, my_post_edit_view, delete_confirm_dialog, my_posts_view_state]
    ).then(
        lambda state, post_id, user: load_post_detail(post_id, user) if state == "detail" else (
            "", "", "", "", "", "", None, ""),
        inputs=[my_posts_view_state, my_post_selected_id, user_info_state],
        outputs=[
            my_post_title, my_post_meta, my_post_privacy,
            my_post_tags, my_post_location, my_post_content,
            my_post_media, my_post_stats
        ]
    ).then(
        # 不使用条件，直接刷新列表视图
        lambda filter, page, user: load_my_posts(filter, page, user),
        inputs=[post_filter, posts_current_page, user_info_state],
        outputs=get_post_card_outputs()
    )

    # 删除确认对话框按钮
    confirm_delete_btn.click(
        delete_post,
        inputs=[my_post_selected_id, user_info_state],
        outputs=[delete_result]
    ).then(
        back_to_list_view,
        inputs=[],
        outputs=[my_posts_list_view, my_post_detail_view, my_post_edit_view, delete_confirm_dialog, my_posts_view_state]
    ).then(
        lambda: None,  # 清除选中的动态ID
        inputs=[],
        outputs=[my_post_selected_id]
    ).then(
        lambda filter, page, user: load_my_posts(filter, page, user),
        inputs=[post_filter, posts_current_page, user_info_state],
        outputs=get_post_card_outputs()
    )

    # 个人资料标签页
    # 页面初始加载时触发
    # 初始加载
    initial_load_btn.click(
        lambda user: check_login(user),
        inputs=[user_info_state],
        outputs=[login_status]
    ).then(
        lambda user: load_profile_data(user)[0],
        inputs=[user_info_state],
        outputs=[profile_info]
    ).then(
        lambda user: load_profile_data(user)[1],
        inputs=[user_info_state],
        outputs=[stats_container]
    ).then(
        lambda filter, page, user: load_my_posts(filter, page, user),
        inputs=[post_filter, posts_current_page, user_info_state],
        outputs=get_post_card_outputs()
    ).then(
        load_favorites,  # 添加加载收藏的步骤
        inputs=[user_info_state],
        outputs=get_fav_card_outputs()
    ).then(
        lambda filter, page, user: load_notifications(filter, page, user),
        inputs=[notification_filter, notifs_current_page, user_info_state],
        outputs=[notifications, notifs_current_page, notifs_total_pages, notifs_page_info]
    )

    refresh_profile_btn.click(
        lambda user: load_profile_data(user)[0],
        inputs=[user_info_state],
        outputs=profile_info
    )

    refresh_stats_btn.click(
        lambda user: load_profile_data(user)[1],
        inputs=[user_info_state],
        outputs=stats_container
    )

    view_user_btn.click(
        view_other_user,
        inputs=[user_id_input, user_info_state],
        outputs=view_result
    )

    update_btn.click(
        update_profile,
        inputs=[nickname, city, avatar, user_info_state],
        outputs=update_result
    )

    # 为每个动态卡片的按钮绑定事件
    # 修改查看详情按钮事件
    for card in my_post_cards:
        # 查看详情按钮
        card["view_btn"].click(
            lambda post_id: post_id,  # 设置选中的动态ID
            inputs=[card["id_state"]],
            outputs=[my_post_selected_id]
        ).then(
            switch_to_detail_view,  # 切换到详情视图
            inputs=[],
            outputs=[my_posts_list_view, my_post_detail_view, my_post_edit_view, delete_confirm_dialog,
                     my_posts_view_state]
        ).then(
            load_post_detail,  # 加载动态详情
            inputs=[my_post_selected_id, user_info_state],
            outputs=[
                my_post_title, my_post_meta, my_post_privacy,
                my_post_tags, my_post_location, my_post_content,
                my_post_media, my_post_stats, my_post_likes, my_post_comments  # 添加了点赞和评论输出
            ]
        )

    # 筛选和分页事件
    post_filter.change(
        lambda filter, page, user: load_my_posts(filter, page, user),
        inputs=[post_filter, posts_current_page, user_info_state],
        outputs=get_post_card_outputs()
    )

    refresh_posts_btn.click(
        lambda filter, page, user: load_my_posts(filter, page, user),
        inputs=[post_filter, posts_current_page, user_info_state],
        outputs=get_post_card_outputs()
    )

    prev_posts_page.click(
        lambda page: max(1, page - 1),
        inputs=[posts_current_page],
        outputs=[posts_current_page]
    ).then(
        lambda filter, page, user: load_my_posts(filter, page, user),
        inputs=[post_filter, posts_current_page, user_info_state],
        outputs=get_post_card_outputs()
    )

    next_posts_page.click(
        lambda page, total: min(total, page + 1),
        inputs=[posts_current_page, posts_total_pages],
        outputs=[posts_current_page]
    ).then(
        lambda filter, page, user: load_my_posts(filter, page, user),
        inputs=[post_filter, posts_current_page, user_info_state],
        outputs=get_post_card_outputs()
    )

    def remove_favorite(fav_id, user_data):
        """确认取消收藏"""
        if not fav_id or not user_data:
            print("取消收藏失败：无效的收藏ID或用户未登录")
            return "无法取消收藏：请先登录或选择收藏"

        try:
            print(f"执行取消收藏: ID={fav_id}, 用户ID={user_data['user_id']}")
            # 调用服务移除收藏
            success, message = user_profile_service.remove_favorite(fav_id, user_data["user_id"])

            if success:
                print(f"取消收藏成功: {message}")
                gr.Info("已取消收藏")
                return message
            else:
                print(f"取消收藏失败: {message}")
                gr.Error(f"取消收藏失败: {message}")
                return message
        except Exception as e:
            print(f"取消收藏出现异常: {str(e)}")
            import traceback
            traceback.print_exc()
            gr.Error(f"取消收藏失败: {str(e)}")
            return f"取消收藏失败: {str(e)}"

    # 为每个收藏卡片添加查看详情功能
    for card in fav_cards:
        # 卡片点击事件 - 查看详情
        card["view_btn"].click(
            lambda content_id, fav_id: (content_id, fav_id),  # 同时传递内容ID和收藏ID
            inputs=[card["content_id_state"], card["id_state"]],  # 同时获取内容ID和收藏ID
            outputs=[fav_detail_components["post_id"], fav_detail_components["fav_id"]]  # 同时更新两个状态
        ).then(
            lambda: ("detail", gr.update(visible=False), gr.update(visible=True)),  # 切换视图
            inputs=[],
            outputs=[fav_view_state, fav_list_view, fav_detail_view]
        ).then(
            # 加载动态详情
            lambda post_id, user_data: view_post_detail(post_id, user_data, from_favorites=True),
            inputs=[fav_detail_components["post_id"], user_info_state],
            outputs=[
                fav_detail_components["title"],
                fav_detail_components["meta"],
                fav_detail_components["privacy"],
                fav_detail_components["tags"],
                fav_detail_components["location"],
                fav_detail_components["content"],
                fav_detail_components["media"],
                fav_detail_components["stats"],
                fav_detail_components["likes"],
                fav_detail_components["comments"],
                fav_detail_components["post_id"],
                fav_detail_components["fav_status"],
                fav_detail_components["fav_id"]  # 新增输出
            ]
        )

        card["remove_btn"].click(
            lambda fav_id: (fav_id, gr.update(visible=True)),
            inputs=[card["id_state"]],  # 这里已经是收藏ID了，不需要转换
            outputs=[unfav_id_state, unfav_confirm_dialog]
        )

    # 返回按钮事件
    fav_detail_components["back_btn"].click(
        lambda: ("list", gr.update(visible=True), gr.update(visible=False)),
        inputs=[],
        outputs=[fav_view_state, fav_list_view, fav_detail_view]
    )

    # 取消收藏按钮
    # 取消收藏按钮 - 直接执行取消操作，不显示确认对话框
    fav_detail_components["unfav_btn"].click(
        lambda post_id, user_data: direct_remove_favorite(post_id, user_data),
        inputs=[fav_detail_components["post_id"], user_info_state],
        outputs=[]
    ).then(
        lambda: ("list", gr.update(visible=True), gr.update(visible=False)),  # 切换回列表视图
        inputs=[],
        outputs=[fav_view_state, fav_list_view, fav_detail_view]
    ).then(
        lambda: time.sleep(0.5),  # 等待操作完成
        inputs=[],
        outputs=[]
    ).then(
        load_favorites,  # 重新加载收藏列表
        inputs=[user_info_state],
        outputs=get_fav_card_outputs()
    )

    # 直接删除
    def direct_remove_favorite(post_id, user_data):
        """直接取消收藏（无确认对话框）"""
        if not user_data or not post_id:
            gr.Error("取消收藏失败：请先登录或选择内容")
            return

        try:
            # 获取收藏ID
            fav_id = user_profile_service.get_favorite_id_by_content(post_id, user_data["user_id"])
            if not fav_id:
                gr.Warning("未找到对应的收藏记录")
                return

            # 执行取消收藏
            success, message = user_profile_service.remove_favorite(fav_id, user_data["user_id"])

            if success:
                gr.Info("已取消收藏")
            else:
                gr.Error(f"取消收藏失败: {message}")
        except Exception as e:
            print(f"取消收藏失败: {str(e)}")
            gr.Error(f"取消收藏失败: {str(e)}")

    # 提交评论
    fav_detail_components["submit_comment"].click(
        submit_comment,
        inputs=[
            fav_detail_components["post_id"],
            fav_detail_components["comment_input"],
            user_info_state
        ],
        outputs=[fav_detail_components["comment_input"]]
    ).then(
        # 重新加载评论区
        lambda post_id, user_data: travel_post_service.get_comments(post_id, page=1, page_size=10),
        inputs=[fav_detail_components["post_id"], user_info_state],
        outputs=[]
    ).then(
        # 刷新整个详情页
        lambda post_id, user_data: view_post_detail(post_id, user_data, from_favorites=True),
        inputs=[fav_detail_components["post_id"], user_info_state],
        outputs=[
            fav_detail_components["title"],
            fav_detail_components["meta"],
            fav_detail_components["privacy"],
            fav_detail_components["tags"],
            fav_detail_components["location"],
            fav_detail_components["content"],
            fav_detail_components["media"],
            fav_detail_components["stats"],
            fav_detail_components["likes"],
            fav_detail_components["comments"],
            fav_detail_components["post_id"],
            fav_detail_components["fav_status"]
        ]
    )

    # 确认取消收藏
    confirm_unfav_btn.click(
        remove_favorite,  # 执行取消收藏
        inputs=[unfav_id_state, user_info_state],
        outputs=[unfav_confirm_text]
    ).then(
        # 隐藏对话框并清空状态
        lambda: (gr.update(visible=False), None),
        inputs=[],
        outputs=[unfav_confirm_dialog, unfav_id_state]
    ).then(
        # 等待一小段时间以确保数据库操作完成
        lambda: time.sleep(0.5),
        inputs=[],
        outputs=[]
    ).then(
        # 重新加载收藏列表
        load_favorites,
        inputs=[user_info_state],
        outputs=get_fav_card_outputs()
    )

    # 初始加载
    initial_load_btn.click(
        load_favorites,
        inputs=[user_info_state],
        outputs=get_fav_card_outputs()
    )

    # 通知标签页
    notification_filter.change(
        lambda filter, page, user: load_notifications(filter, page, user),
        inputs=[notification_filter, notifs_current_page, user_info_state],
        outputs=[notifications, notifs_current_page, notifs_total_pages, notifs_page_info]
    )

    refresh_notifs_btn.click(
        lambda filter, page, user: load_notifications(filter, page, user),
        inputs=[notification_filter, notifs_current_page, user_info_state],
        outputs=[notifications, notifs_current_page, notifs_total_pages, notifs_page_info]
    )

    prev_notifs_page.click(
        lambda filter, page, total, user: load_notifications(filter, max(1, page - 1), user),
        inputs=[notification_filter, notifs_current_page, notifs_total_pages, user_info_state],
        outputs=[notifications, notifs_current_page, notifs_total_pages, notifs_page_info]
    )

    next_notifs_page.click(
        lambda filter, page, total, user: load_notifications(filter, min(total, page + 1), user),
        inputs=[notification_filter, notifs_current_page, notifs_total_pages, user_info_state],
        outputs=[notifications, notifs_current_page, notifs_total_pages, notifs_page_info]
    )

    mark_read_btn.click(
        mark_notifications_read,
        inputs=[user_info_state],
        outputs=update_result
    ).then(
        lambda filter, page, user: load_notifications(filter, page, user),
        inputs=[notification_filter, notifs_current_page, user_info_state],
        outputs=[notifications, notifs_current_page, notifs_total_pages, notifs_page_info]
    )

    # 隐私设置标签页
    save_btn.click(
        save_privacy_settings,
        inputs=[profile_visibility, post_privacy, allow_requests, show_online, user_info_state],
        outputs=save_result
    )

    # 添加取消删除按钮的事件处理
    cancel_delete_btn.click(
        back_to_list_view,
        inputs=[],
        outputs=[my_posts_list_view, my_post_detail_view, my_post_edit_view, delete_confirm_dialog, my_posts_view_state]
    )

    # 绑定媒体变化事件
    edit_media.change(
        handle_media_change,
        inputs=[edit_media, keep_current_media],
        outputs=[current_media_preview, keep_current_media]
    )

    # 刷新收藏按钮
    refresh_favs_btn.click(
        load_favorites,
        inputs=[user_info_state],
        outputs=get_fav_card_outputs()
    )

    # 为取消按钮添加事件处理
    cancel_unfav_btn.click(
        lambda: (gr.update(visible=False), None),  # 隐藏对话框并清空状态
        inputs=[],
        outputs=[unfav_confirm_dialog, unfav_id_state]
    )

    return {
        "profile_info": profile_info,
        "stats_container": stats_container,
        "my_posts_container": my_posts_container,
        "favorites": favs_container,  # 正确的变量名
        "notifications": notifications
    }