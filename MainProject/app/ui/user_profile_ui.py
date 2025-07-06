# MainProject/app/ui/user_profile_ui.py
import gradio as gr
from MainProject.app.services.user_profile_service import UserProfileService
from MainProject.app.services.travel_post_service import TravelPostService

def create_user_profile_ui(user_info_state):
    """创建用户个人中心UI（重构版）"""
    user_profile_service = UserProfileService()
    travel_post_service = TravelPostService()

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

                with gr.Row():
                    post_filter = gr.Radio(["全部", "公开", "仅好友", "私密"], label="筛选", value="全部")
                    posts_page = gr.Slider(1, 10, value=1, step=1, label="页码")
                    refresh_posts_btn = gr.Button("刷新")

                my_posts = gr.HTML("加载中...")
                posts_page_info = gr.Markdown("第 1 页，共 1 页")

                with gr.Row():
                    prev_posts_page = gr.Button("上一页")
                    next_posts_page = gr.Button("下一页")
                    delete_post_btn = gr.Button("删除动态", variant="stop")

                # 隐藏组件
                selected_post_id = gr.Number(visible=False)
                posts_current_page = gr.State(1)
                posts_total_pages = gr.State(1)

        # ==================== 我的收藏标签页 ====================
        with gr.TabItem("我的收藏"):
            with gr.Group():
                gr.Markdown("### 我的收藏内容")

                with gr.Row():
                    favorite_type = gr.Radio(["全部", "动态", "地点"], label="类型", value="全部")
                    favorites_page = gr.Slider(1, 10, value=1, step=1, label="页码")
                    refresh_favs_btn = gr.Button("刷新")

                favorites = gr.HTML("加载中...")
                favs_page_info = gr.Markdown("第 1 页，共 1 页")

                with gr.Row():
                    prev_favs_page = gr.Button("上一页")
                    next_favs_page = gr.Button("下一页")
                    remove_fav_btn = gr.Button("取消收藏", variant="stop")

                # 隐藏组件
                selected_fav_id = gr.Number(visible=False)
                favs_current_page = gr.State(1)
                favs_total_pages = gr.State(1)

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

        # 初始加载按钮
        initial_load_btn = gr.Button("加载个人资料", visible=True)

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
            stats_html = f"""
            <div class='stats'>
                <div class='stat-item'>
                    <span class='stat-value'>{profile.get('post_count', 0)}</span>
                    <span class='stat-label'>动态</span>
                </div>
                <div class='stat-item'>
                    <span class='stat-value'>{profile.get('friend_count', 0)}</span>
                    <span class='stat-label'>好友</span>
                </div>
            </div>
            """

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
        if not user_data:
            return "<div class='error'>请先登录</div>", 1, 1, "第 1 页，共 1 页"

        try:
            # 转换筛选条件为隐私级别
            privacy_map = {
                "全部": None,
                "公开": "public",
                "仅好友": "friends",
                "私密": "private"
            }
            privacy_level = privacy_map.get(filter_type)

            # 使用UserProfileService获取用户动态
            result = user_profile_service.get_user_posts(
                user_id=user_data["user_id"],
                viewer_id=user_data["user_id"],
                page=page,
                page_size=10
            )

            posts = result.get("posts", [])
            total = result.get("total", 0)
            total_pages_val = result.get("total_pages", 1)

            if not posts:
                return "<div class='no-posts'>没有找到符合条件的动态</div>", page, total_pages_val, f"第 {page} 页，共 {total_pages_val} 页"

            # 构建HTML内容
            html = "<div class='posts-container'>"
            for post in posts:
                title = post.get("title", "")
                content = post.get("content", "")[:100] + ("..." if len(post.get("content", "")) > 100 else "")
                location = f"📍 {post.get('location_name')}" if post.get('location_name') else ""
                time = post.get("created_at", "")
                likes = post.get("like_count", 0)
                comments = post.get("comment_count", 0)
                privacy = post.get("privacy_level", "public")
                privacy_icon = "🌍" if privacy == "public" else ("👥" if privacy == "friends" else "🔒")

                html += f"""
                <div class='post' data-post-id='{post["id"]}'>
                    <div class='post-header'>
                        <span class='post-privacy'>{privacy_icon}</span>
                        <span class='post-time'>{time}</span>
                    </div>
                    <h3 class='post-title'>{title}</h3>
                    <div class='post-content'>{content}</div>
                    {f"<div class='post-location'>{location}</div>" if location else ""}
                    <div class='post-footer'>
                        <span class='likes'>❤️ {likes}</span>
                        <span class='comments'>💬 {comments}</span>
                        <button class='delete-btn' onclick='selectPostId({post["id"]})'>删除</button>
                    </div>
                </div>
                """
            html += "</div>"
            html += """
            <script>
            function selectPostId(id) {
                document.querySelector('#selected_post_id input').value = id;
                document.querySelector('#delete_post_btn').click();
            }
            </script>
            """

            return html, page, total_pages_val, f"第 {page} 页，共 {total_pages_val} 页，总计 {total} 条动态"
        except Exception as e:
            return f"<div class='error'>错误: {str(e)}</div>", page, 1, "加载错误"

    def delete_post(post_id, user_data):
        if not user_data:
            return "请先登录"
        if not post_id:
            return "请选择要删除的动态"

        try:
            # 假设TravelPostService有delete_post方法
            success, message = travel_post_service.delete_post(
                post_id,
                user_data["user_id"]
            )
            return message
        except Exception as e:
            return f"删除动态失败: {str(e)}"

    def load_favorites(fav_type, page, user_data):
        if not user_data:
            return "<div class='error'>请先登录</div>", 1, 1, "第 1 页，共 1 页"

        try:
            # 转换筛选条件
            content_type_map = {
                "全部": None,
                "动态": "post",
                "地点": "location"
            }
            content_type = content_type_map.get(fav_type)

            result = user_profile_service.get_user_favorites(
                user_id=user_data["user_id"],
                content_type=content_type,
                page=page,
                page_size=10
            )

            favorites = result.get("favorites", [])
            total = result.get("total", 0)
            total_pages_val = result.get("total_pages", 1)

            if not favorites:
                return "<div class='no-favs'>没有找到收藏内容</div>", page, total_pages_val, f"第 {page} 页，共 {total_pages_val} 页"

            # 构建HTML内容
            html = "<div class='favorites-container'>"
            for fav in favorites:
                fav_id = fav.get("id")
                content_type = fav.get("content_type")
                created_at = fav.get("created_at")
                details = fav.get("details", {})

                if content_type == "post":
                    title = details.get("title", "无标题")
                    content = details.get("content", "")[:100] + (
                        "..." if len(details.get("content", "")) > 100 else "")
                    username = details.get("username") or details.get("nickname") or "用户"

                    html += f"""
                        <div class='favorite-item' data-fav-id='{fav_id}'>
                            <div class='fav-header'>
                                <span class='fav-type'>动态</span>
                                <span class='fav-time'>{created_at}</span>
                            </div>
                            <h3 class='fav-title'>{title}</h3>
                            <div class='fav-content'>{content}</div>
                            <div class='fav-footer'>
                                <span class='fav-author'>作者: {username}</span>
                                <button class='remove-btn' onclick='selectFavId({fav_id})'>取消收藏</button>
                            </div>
                        </div>
                        """
                elif content_type == "location":
                    name = details.get("name", "未知地点")
                    description = details.get("description", "")[:100] + (
                        "..." if len(details.get("description", "")) > 100 else "")

                    html += f"""
                        <div class='favorite-item' data-fav-id='{fav_id}'>
                            <div class='fav-header'>
                                <span class='fav-type'>地点</span>
                                <span class='fav-time'>{created_at}</span>
                            </div>
                            <h3 class='fav-title'>{name}</h3>
                            <div class='fav-content'>{description}</div>
                            <div class='fav-footer'>
                                <button class='remove-btn' onclick='selectFavId({fav_id})'>取消收藏</button>
                            </div>
                        </div>
                        """

            html += "</div>"
            html += """
                <script>
                function selectFavId(id) {
                    document.querySelector('#selected_fav_id input').value = id;
                    document.querySelector('#remove_fav_btn').click();
                }
                </script>
                """

            return html, page, total_pages_val, f"第 {page} 页，共 {total_pages_val} 页，总计 {total} 条收藏"
        except Exception as e:
            return f"<div class='error'>错误: {str(e)}</div>", page, 1, "加载错误"

    def remove_favorite(fav_id, user_data):
        if not user_data:
            return "请先登录"
        if not fav_id:
            return "请选择要取消的收藏"

        try:
            success, message = user_profile_service.remove_favorite(
                fav_id,
                user_data["user_id"]
            )
            return message
        except Exception as e:
            return f"取消收藏失败: {str(e)}"

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

    def load_privacy_settings(user_data):
        if not user_data:
            return "public", "public", True, True, "请先登录"

        try:
            settings = user_profile_service.get_privacy_settings(user_data["user_id"])

            return (
                settings.get("profile_visibility", "public"),
                settings.get("post_default_privacy", "public"),
                settings.get("allow_friend_requests", True),
                settings.get("show_online_status", True),
                "已加载隐私设置"
            )
        except Exception as e:
            return "public", "public", True, True, f"加载设置失败: {str(e)}"

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

    # ==================== 事件绑定 ====================
    # 个人资料标签页
    initial_load_btn.click(
        lambda user: (check_login(user), *load_profile_data(user), *load_privacy_settings(user)),
        inputs=[user_info_state],
        outputs=[login_status, profile_info, stats_container, profile_visibility, post_privacy, allow_requests,
                 show_online, save_result]
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

    # 我的动态标签页
    post_filter.change(
        lambda filter, page, user: load_my_posts(filter, page, user),
        inputs=[post_filter, posts_current_page, user_info_state],
        outputs=[my_posts, posts_current_page, posts_total_pages, posts_page_info]
    )

    refresh_posts_btn.click(
        lambda filter, page, user: load_my_posts(filter, page, user),
        inputs=[post_filter, posts_current_page, user_info_state],
        outputs=[my_posts, posts_current_page, posts_total_pages, posts_page_info]
    )

    prev_posts_page.click(
        lambda filter, page, total, user: load_my_posts(filter, max(1, page - 1), user),
        inputs=[post_filter, posts_current_page, posts_total_pages, user_info_state],
        outputs=[my_posts, posts_current_page, posts_total_pages, posts_page_info]
    )

    next_posts_page.click(
        lambda filter, page, total, user: load_my_posts(filter, min(total, page + 1), user),
        inputs=[post_filter, posts_current_page, posts_total_pages, user_info_state],
        outputs=[my_posts, posts_current_page, posts_total_pages, posts_page_info]
    )

    delete_post_btn.click(
        delete_post,
        inputs=[selected_post_id, user_info_state],
        outputs=update_result
    ).then(
        lambda filter, page, user: load_my_posts(filter, page, user),
        inputs=[post_filter, posts_current_page, user_info_state],
        outputs=[my_posts, posts_current_page, posts_total_pages, posts_page_info]
    )

    # 我的收藏标签页
    favorite_type.change(
        lambda type, page, user: load_favorites(type, page, user),
        inputs=[favorite_type, favs_current_page, user_info_state],
        outputs=[favorites, favs_current_page, favs_total_pages, favs_page_info]
    )

    refresh_favs_btn.click(
        lambda type, page, user: load_favorites(type, page, user),
        inputs=[favorite_type, favs_current_page, user_info_state],
        outputs=[favorites, favs_current_page, favs_total_pages, favs_page_info]
    )

    prev_favs_page.click(
        lambda type, page, total, user: load_favorites(type, max(1, page - 1), user),
        inputs=[favorite_type, favs_current_page, favs_total_pages, user_info_state],
        outputs=[favorites, favs_current_page, favs_total_pages, favs_page_info]
    )

    next_favs_page.click(
        lambda type, page, total, user: load_favorites(type, min(total, page + 1), user),
        inputs=[favorite_type, favs_current_page, favs_total_pages, user_info_state],
        outputs=[favorites, favs_current_page, favs_total_pages, favs_page_info]
    )

    remove_fav_btn.click(
        remove_favorite,
        inputs=[selected_fav_id, user_info_state],
        outputs=update_result
    ).then(
        lambda type, page, user: load_favorites(type, page, user),
        inputs=[favorite_type, favs_current_page, user_info_state],
        outputs=[favorites, favs_current_page, favs_total_pages, favs_page_info]
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

    return {
        "profile_info": profile_info,
        "my_posts": my_posts,
        "favorites": favorites,
        "notifications": notifications
    }
