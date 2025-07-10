import gradio as gr
from MainProject.auth_utils import verify_token
from MainProject.dbhelper.NoticeManager import NoticeManager


def format_date(date_obj):
    """格式化日期显示"""
    if not date_obj:
        return ""
    try:
        return date_obj.strftime("%Y年%m月%d日 %H:%M")
    except:
        return str(date_obj)


def get_notice_type_css(notice_type):
    """根据公告类型返回对应的CSS类名"""
    if notice_type == "warning":
        return "notice-warning"
    elif notice_type == "error":
        return "notice-error"
    elif notice_type == "success":
        return "notice-success"
    else:
        return "notice-info"  # 默认为info类型


def create_notice_view_app():
    """创建公告查看应用"""

    notice_manager = NoticeManager()

    with gr.Blocks(
            title="公告中心",
            css="""
        .nav-button {
            display: flex;
            justify-content: flex-start;
            margin-bottom: 15px;
        }
        .nav-button a {
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 4px;
            background-color: #f0f0f0;
            color: #333;
            transition: background-color 0.3s;
        }
        .nav-button a:hover {
            background-color: #e0e0e0;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        
         /* 点赞/踩按钮样式 */
        .notice-actions button {
            color: black !important;
        }
        .notice-actions button.active {
            background-color: #2196F3;
        }

        .notice-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            margin-bottom: 20px;
            overflow: hidden;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }

        .notice-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }

        .notice-header {
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .notice-title {
            font-size: 18px;
            font-weight: bold;
            margin: 0;
        }

        .notice-meta {
            font-size: 14px;
            color: #666;
        }

        .notice-content {
            padding: 15px;
            line-height: 1.6;
        }

        .notice-footer {
            padding: 10px 15px;
            background-color: #f9f9f9;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .notice-stats {
            font-size: 14px;
            color: #666;
        }

        .notice-actions {
            display: flex;
            gap: 10px;
        }

        .notice-info {
            border-left: 4px solid #2196F3;
        }

        .notice-warning {
            border-left: 4px solid #FF9800;
        }

        .notice-error {
            border-left: 4px solid #F44336;
        }

        .notice-success {
            border-left: 4px solid #4CAF50;
        }

        .empty-notice {
            text-align: center;
            padding: 40px;
            color: #888;
            font-style: italic;
        }

        .pagination {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 20px;
            margin-bottom: 30px;
        }

        .reaction-active {
            font-weight: bold;
            color: #2196F3;
        }

        .dislike-active {
            font-weight: bold;
            color: #F44336;
        }

        .filter-container {
            margin-bottom: 20px;
        }
        """
    ) as demo:
        # 隐藏的状态变量
        token_state = gr.State("")
        user_id_state = gr.State("")
        current_page = gr.State(1)
        with gr.Group(visible=False) as reaction_controls:
            notice_id_input = gr.Number(label="公告ID", value=-1)
            reaction_type_input = gr.Radio(choices=["like", "dislike"], label="反应类型", value="like")
            submit_reaction_btn = gr.Button("提交反应")

        # 用户信息栏
        userbar = gr.HTML("请登录查看公告", elem_classes="userbar-text")

        # 导航按钮区域 - 单个按钮
        nav_button = gr.HTML("", elem_classes="nav-button")

        # 页面标题
        gr.Markdown("# 📢 公告中心")

        # 筛选选项
        with gr.Row(elem_classes="filter-container"):
            with gr.Column(scale=3):
                filter_dropdown = gr.Dropdown(
                    choices=["全部公告", "最新公告", "重要公告"],
                    value="全部公告",
                    label="筛选公告"
                )
            with gr.Column(scale=1):
                refresh_btn = gr.Button("🔄 刷新")

        # 公告列表容器
        notice_list = gr.HTML("")

        # 分页控件
        with gr.Row(elem_classes="pagination"):
            prev_btn = gr.Button("← 上一页")
            page_info = gr.Markdown("第 1 页")
            next_btn = gr.Button("下一页 →")

        # 点赞/踩操作的状态反馈
        reaction_status = gr.Markdown("", visible=False)

        # 加载公告列表
        def load_notices(token, user_id, page, filter_type="全部公告"):
            if not token or not user_id:
                return "<div class='empty-notice'>请先登录查看公告</div>", page, "第 0 页"

            try:
                page = int(page)
                if page < 1:
                    page = 1

                # 根据筛选类型获取不同的公告
                if filter_type == "最新公告":
                    notices, total = notice_manager.get_all_notices(page=page, page_size=5)
                    notices = sorted(notices, key=lambda x: x['created_at'], reverse=True)
                elif filter_type == "重要公告":
                    # 获取高优先级的公告
                    notices = notice_manager.get_active_notices(limit=10)
                    notices = sorted(notices, key=lambda x: x['priority'], reverse=True)
                    total = len(notices)
                    # 手动分页
                    start_idx = (page - 1) * 5
                    end_idx = start_idx + 5
                    notices = notices[start_idx:end_idx]
                else:  # 全部公告
                    notices, total = notice_manager.get_all_notices(page=page, page_size=5)

                max_page = (total + 4) // 5  # 向上取整

                if not notices:
                    return "<div class='empty-notice'>暂无公告</div>", page, f"第 {page} 页 / 共 {max_page} 页"

                html = "<div class='container'>"
                for notice in notices:
                    # 记录用户查看
                    notice_manager.record_view(notice['id'], user_id)

                    # 获取用户对该公告的反应
                    user_reaction = notice_manager.get_user_reaction(notice['id'], user_id)

                    # 获取公告统计信息
                    stats = notice_manager.get_notice_stats(notice['id'])

                    # 设置点赞/踩按钮的样式
                    like_class = "reaction-active" if user_reaction == "like" else ""
                    dislike_class = "dislike-active" if user_reaction == "dislike" else ""

                    # 获取公告类型的CSS类
                    notice_type_class = get_notice_type_css(notice['type'])

                    # 构建公告HTML
                    html += f"""
                    <div class="notice-card {notice_type_class}">
                        <div class="notice-header">
                            <h3 class="notice-title">{notice['title']}</h3>
                            <div class="notice-meta">
                                发布于: {format_date(notice['created_at'])}
                                {f" | 作者: {notice['created_by']}" if notice['created_by'] else ""}
                            </div>
                        </div>
                        <div class="notice-content">
                            {notice['content']}
                        </div>
                        <div class="notice-footer">
                            <div class="notice-stats">
                                {stats['view_count']} 次查看
                            </div>
                            <div class="notice-actions">
                                <form method="get" style="display:inline-block">
                                    <input type="hidden" name="token" value="{token}">
                                    <input type="hidden" name="notice_id" value="{notice['id']}">
                                    <input type="hidden" name="action" value="like">
                                    <button type="submit" class="gr-button gr-button-sm {like_class}" style="color: blue;">
                                        👍 {stats['like_count']}
                                    </button>
                                </form>
                                <form method="get" style="display:inline-block">
                                    <input type="hidden" name="token" value="{token}">
                                    <input type="hidden" name="notice_id" value="{notice['id']}">
                                    <input type="hidden" name="action" value="dislike">
                                    <button type="submit" class="gr-button gr-button-sm {dislike_class}" style="color: red;">
                                        👎 {stats['dislike_count']}
                                    </button>
                                </form>
                            </div>
                        </div>
                    </div>
                    """

                html += "</div>"
                return html, page, f"第 {page} 页 / 共 {max_page} 页"

            except Exception as e:
                return f"<div class='empty-notice'>加载公告时出错: {str(e)}</div>", page, "第 ? 页"

        # 处理点赞/踩操作
        # 修改 handle_reaction 函数，确保参数顺序和数量正确
        def handle_reaction(notice_id, reaction_type, token, user_id, current_pg):
            if not token or not user_id:
                return gr.update(visible=True, value="⚠️ 请先登录后再操作"), "", current_pg, ""

            try:
                if not notice_id or reaction_type not in ["like", "dislike"]:
                    return gr.update(visible=True, value="⚠️ 无效的操作"), "", current_pg, ""

                # 处理反应
                notice_manager = NoticeManager()
                result = notice_manager.add_reaction(notice_id, user_id, reaction_type)

                # 准备反馈消息
                if result == 'added':
                    message = f"✅ 您已{reaction_type == 'like' and '点赞' or '踩'}了这条公告"
                elif result == 'updated':
                    message = f"✅ 您已将反馈更改为{reaction_type == 'like' and '点赞' or '踩'}"
                elif result == 'removed':
                    message = f"✅ 您已取消{reaction_type == 'like' and '点赞' or '踩'}"
                else:
                    message = "⚠️ 操作失败，请稍后再试"

                # 获取当前筛选类型
                filter_type = gr.State(value="全部公告").value

                # 重新加载公告列表
                notices_html, page, page_text = load_notices(token, user_id, current_pg, filter_type)

                return gr.update(visible=True, value=message), notices_html, page, page_text
            except Exception as e:
                return gr.update(visible=True, value=f"⚠️ 处理请求时出错: {str(e)}"), "", current_pg, ""


        # 添加页面加载时处理URL参数的逻辑
        def on_load(request: gr.Request):
            token = request.query_params.get("token", "")
            action = request.query_params.get("action", "")
            notice_id = request.query_params.get("notice_id", "")

            user_info = verify_token(token)
            if not user_info or not user_info.get("username"):
                # 返回所有需要的值
                return "", "", 1, "请先登录查看公告", "<div class='empty-notice'>请先登录查看公告</div>", 1, "第 0 页", ""

            user_id = user_info.get("username")
            role = user_info.get("role", "user")

            # 处理点赞/踩操作
            message = ""
            if action in ["like", "dislike"] and notice_id:
                try:
                    notice_manager = NoticeManager()
                    result = notice_manager.add_reaction(int(notice_id), user_id, action)
                    if result:
                        message = f"已{action == 'like' and '点赞' or '踩'}公告"
                except Exception as e:
                    message = f"操作失败: {str(e)}"

            # 构建欢迎信息
            welcome_html = f"<b>{'👨‍💼 管理员' if role in ['admin', 'root'] else '👤 用户'} {user_id}</b>，欢迎查看公告！"
            if message:
                welcome_html += f" <span style='color:green'>{message}</span>"

            # 加载第一页公告
            notices_html, page, page_text = load_notices(token, user_id, 1, "全部公告")

            # 根据用户角色添加不同的返回按钮
            if role in ['admin', 'root']:
                nav_button = f'<a href="/settings/admin_settings?token={token}" class="gr-button gr-button-lg">⚙️ 返回管理员设置</a>'
            else:
                nav_button = f'<a href="/homepage/user_home?token={token}" class="gr-button gr-button-lg">🏠 返回主页</a>'

            # 确保返回所有需要的值
            return token, user_id, 1, welcome_html, notices_html, 1, page_text, nav_button

        # 注册页面加载回调
        demo.load(
            fn=on_load,
            outputs=[token_state, user_id_state, current_page, userbar, notice_list, current_page, page_info,nav_button]
        )

        # 注册筛选和刷新回调
        def refresh_notices(token, user_id, page, filter_type):
            notices_html, page, page_text = load_notices(token, user_id, page, filter_type)
            return notices_html, page_text

        filter_dropdown.change(
            fn=refresh_notices,
            inputs=[token_state, user_id_state, current_page, filter_dropdown],
            outputs=[notice_list, page_info]
        )

        refresh_btn.click(
            fn=refresh_notices,
            inputs=[token_state, user_id_state, current_page, filter_dropdown],
            outputs=[notice_list, page_info]
        )

        # 分页控件回调
        def change_page(direction, token, user_id, current, filter_type):
            new_page = current + direction
            if new_page < 1:
                new_page = 1

            notices_html, page, page_text = load_notices(token, user_id, new_page, filter_type)
            return notices_html, new_page, page_text

        prev_btn.click(
            fn=lambda token, user_id, current, filter_type: change_page(-1, token, user_id, current, filter_type),
            inputs=[token_state, user_id_state, current_page, filter_dropdown],
            outputs=[notice_list, current_page, page_info]
        )

        next_btn.click(
            fn=lambda token, user_id, current, filter_type: change_page(1, token, user_id, current, filter_type),
            inputs=[token_state, user_id_state, current_page, filter_dropdown],
            outputs=[notice_list, current_page, page_info]
        )

        # 处理表单提交（点赞/踩）
        # 替换为单独的点赞/踩按钮和处理函数
        with gr.Row(visible=False) as reaction_controls:
            notice_id_input = gr.Number(label="公告ID", visible=False)
            like_button = gr.Button("点赞")
            dislike_button = gr.Button("踩")

        # 注册按钮点击事件
        like_button.click(
            fn=lambda notice_id, token, user_id, current_pg, filter_type:
            handle_reaction(notice_id, "like", token, user_id, current_pg),
            inputs=[notice_id_input, token_state, user_id_state, current_page, filter_dropdown],
            outputs=[reaction_status, notice_list, current_page, page_info]
        )

        dislike_button.click(
            fn=lambda notice_id, token, user_id, current_pg, filter_type:
            handle_reaction(notice_id, "dislike", token, user_id, current_pg),
            inputs=[notice_id_input, token_state, user_id_state, current_page, filter_dropdown],
            outputs=[reaction_status, notice_list, current_page, page_info]
        )

        # 页脚
        gr.HTML("<div style='text-align:center;color:#97a;margin-top:30px;'>© 2024 公告中心</div>")

    return demo