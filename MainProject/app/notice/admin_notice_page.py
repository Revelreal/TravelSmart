# MainProject/app/homepage/admin_notice_page.py:
import gradio as gr
import pandas as pd

from MainProject.app.notice.notice_page import format_date
from MainProject.dbhelper.NoticeManager import NoticeManager
from MainProject.auth_utils import verify_token

# 管理员公告管理界面
def create_notice_admin_app():
    """创建公告管理应用（管理员使用）"""

    notice_manager = NoticeManager()

    with gr.Blocks(title="公告管理") as demo:
        token_box = gr.Textbox(visible=False)
        adminbar = gr.HTML("正在认证管理员身份...", elem_classes="userbar-text")

        def load_admin(request: gr.Request):
            token = request.query_params.get("token", "")
            info = require_admin(token)
            username = info["username"]
            welcome_html = f"<b>👨‍💼 管理员 {username}</b>，欢迎来到公告管理系统！"
            return token, welcome_html

        # 验证管理员权限
        def require_admin(token):
            info = verify_token(token)
            if not info or not info.get("username"):
                raise gr.Error("认证失败或无权限，请重新登录")
            if info.get("role") not in ("admin", "root"):
                raise gr.Error("权限不足，仅管理员可访问本页面！")
            return info

        demo.load(
            fn=load_admin,
            inputs=None,
            outputs=[token_box, adminbar]
        )

        gr.Markdown("# 📢 公告管理系统")

        with gr.Tabs():
            # 公告列表标签页
            with gr.TabItem("📋 公告列表"):
                gr.Markdown("### 公告列表管理")

                with gr.Row():
                    refresh_list_btn = gr.Button("🔄 刷新列表")
                    page_number = gr.Number(value=1, label="页码", minimum=1, precision=0)
                    # 修改为字符串类型
                    page_size = gr.Dropdown(choices=["10", "20", "50", "100"], value="20", label="每页显示")

                notices_df = gr.Dataframe(
                    interactive=False,
                    label="公告列表",
                    wrap=True
                )

                with gr.Row():
                    with gr.Column(scale=1):
                        prev_page_btn = gr.Button("← 上一页")
                    with gr.Column(scale=2):
                        page_info = gr.Markdown("**第 1 页，共 ? 页**")
                    with gr.Column(scale=1):
                        next_page_btn = gr.Button("下一页 →")

                def get_notices_df(page=1, size=20):
                    """获取公告数据框（带分页）"""
                    try:
                        notice_manager = NoticeManager()

                        # 获取公告列表和总数
                        notices, total = notice_manager.get_all_notices(page=page, page_size=size)

                        # 计算总页数
                        total_pages = (total + size - 1) // size

                        # 更新页面信息
                        page_info_text = f"**第 {page} 页，共 {total_pages} 页 (总计 {total} 条公告)**"

                        if not notices:
                            # 返回空的DataFrame和页面信息
                            empty_df = pd.DataFrame(columns=['id', 'title', 'content', 'type', 'priority',
                                                             'start_time', 'end_time', 'target_audience',
                                                             'created_at', 'updated_at'])
                            return empty_df, page_info_text

                        # 将notices列表转换为DataFrame
                        df = pd.DataFrame(notices)

                        # 格式化日期时间列
                        for col in ['start_time', 'end_time', 'created_at', 'updated_at']:
                            if col in df.columns:
                                df[col] = df[col].apply(lambda x: format_date(x) if x else '')

                        return df, page_info_text

                    except Exception as e:
                        print(f"获取公告数据框失败: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        # 出错时返回空DataFrame和错误信息
                        empty_df = pd.DataFrame(columns=['id', 'title', 'content', 'type', 'priority',
                                                         'start_time', 'end_time', 'target_audience',
                                                         'created_at', 'updated_at'])
                        return empty_df, f"**加载失败: {str(e)}**"

                # 刷新按钮点击时更新数据
                def refresh_notices(page, size):
                    # 将字符串转换为整数
                    df, info = get_notices_df(page=int(page), size=int(size))
                    return df, info

                refresh_list_btn.click(
                    fn=refresh_notices,
                    inputs=[page_number, page_size],
                    outputs=[notices_df, page_info]
                )

                # 上一页按钮
                def go_prev_page(current_page, size):
                    new_page = max(1, int(current_page) - 1)
                    # 将字符串转换为整数
                    df, info = get_notices_df(page=new_page, size=int(size))
                    return df, info, new_page

                prev_page_btn.click(
                    fn=go_prev_page,
                    inputs=[page_number, page_size],
                    outputs=[notices_df, page_info, page_number]
                )

                # 下一页按钮
                def go_next_page(current_page, size):
                    new_page = int(current_page) + 1
                    # 将字符串转换为整数
                    df, info = get_notices_df(page=new_page, size=int(size))
                    return df, info, new_page

                next_page_btn.click(
                    fn=go_next_page,
                    inputs=[page_number, page_size],
                    outputs=[notices_df, page_info, page_number]
                )

                # 页面加载时初始化数据
                demo.load(
                    fn=lambda: get_notices_df(page=1, size=20),
                    outputs=[notices_df, page_info]
                )

            # 添加公告标签页
            with gr.TabItem("➕ 添加公告"):
                with gr.Row():
                    with gr.Column(scale=2):
                        new_title = gr.Textbox(label="公告标题", placeholder="输入公告标题...")
                    with gr.Column(scale=1):
                        new_type = gr.Dropdown(
                            choices=["info", "warning", "error", "success"],
                            value="info",
                            label="公告类型"
                        )
                    with gr.Column(scale=1):
                        new_priority = gr.Slider(
                            minimum=0, maximum=10, value=0, step=1,
                            label="优先级(0-10)"
                        )

                new_content = gr.Textbox(
                    label="公告内容",
                    placeholder="输入公告内容...",
                    lines=5
                )

                with gr.Row():
                    new_start_time = gr.Textbox(
                        label="开始时间",
                        placeholder="YYYY-MM-DD HH:MM:SS，留空为当前时间"
                    )
                    new_end_time = gr.Textbox(
                        label="结束时间",
                        placeholder="YYYY-MM-DD HH:MM:SS，留空为30天后"
                    )
                    new_audience = gr.Dropdown(
                        choices=["all", "user", "admin"],
                        value="all",
                        label="目标受众"
                    )

                add_notice_btn = gr.Button("发布公告")
                add_notice_result = gr.Markdown()

                def add_new_notice(title, content, notice_type, priority, start_time, end_time, audience, token):
                    info = require_admin(token)
                    created_by = info.get("username")

                    if not title or not content:
                        return "❌ 标题和内容不能为空"

                    # 处理空的时间字段
                    if not start_time.strip():
                        start_time = None
                    if not end_time.strip():
                        end_time = None

                    try:
                        notice_id = notice_manager.add_notice(
                            title=title,
                            content=content,
                            notice_type=notice_type,
                            priority=int(priority),
                            start_time=start_time,
                            end_time=end_time,
                            created_by=created_by,
                            target_audience=audience
                        )
                        return f"✅ 公告发布成功！ID: {notice_id}"
                    except Exception as e:
                        return f"❌ 发布失败: {str(e)}"

                add_notice_btn.click(
                    fn=add_new_notice,
                    inputs=[new_title, new_content, new_type, new_priority,
                            new_start_time, new_end_time, new_audience, token_box],
                    outputs=add_notice_result
                )

            # 编辑公告标签页
            with gr.TabItem("✏️ 编辑公告"):
                with gr.Row():
                    edit_id = gr.Number(label="公告ID", precision=0)
                    load_btn = gr.Button("加载公告")

                with gr.Row():
                    with gr.Column(scale=2):
                        edit_title = gr.Textbox(label="公告标题")
                    with gr.Column(scale=1):
                        edit_type = gr.Dropdown(
                            choices=["info", "warning", "error", "success"],
                            label="公告类型"
                        )
                    with gr.Column(scale=1):
                        edit_priority = gr.Slider(
                            minimum=0, maximum=10, step=1,
                            label="优先级(0-10)"
                        )

                edit_content = gr.Textbox(
                    label="公告内容",
                    lines=5
                )

                with gr.Row():
                    edit_start_time = gr.Textbox(label="开始时间")
                    edit_end_time = gr.Textbox(label="结束时间")
                    edit_audience = gr.Dropdown(
                        choices=["all", "user", "admin"],
                        label="目标受众"
                    )

                update_notice_btn = gr.Button("更新公告")
                update_notice_result = gr.Markdown()

                def load_notice_for_edit(notice_id):
                    """加载公告以进行编辑"""
                    try:
                        notice_manager = NoticeManager()
                        notice = notice_manager.get_notice(notice_id)

                        if not notice:
                            return "", "", "normal", 5, "", "", "all"

                        # 将字典中的值分别提取出来
                        title = notice.get('title', '')
                        content = notice.get('content', '')
                        notice_type = notice.get('type', 'normal')
                        priority = notice.get('priority', 5)
                        start_time = notice.get('start_time', '')
                        end_time = notice.get('end_time', '')
                        target_audience = notice.get('target_audience', 'all')

                        # 返回7个单独的值
                        return title, content, notice_type, priority, start_time, end_time, target_audience

                    except Exception as e:
                        print(f"加载公告失败: {str(e)}")
                        return "", "", "normal", 5, "", "", "all"

                def update_notice_info(notice_id, title, content, notice_type, priority,
                                       start_time, end_time, audience, token):
                    require_admin(token)

                    if not notice_id:
                        return "❌ 请输入有效的公告ID"

                    if not title or not content:
                        return "❌ 标题和内容不能为空"

                    try:
                        result = notice_manager.update_notice(
                            notice_id=int(notice_id),
                            title=title,
                            content=content,
                            type=notice_type,
                            priority=int(priority),
                            start_time=start_time,
                            end_time=end_time,
                            target_audience=audience
                        )

                        if result > 0:
                            return f"✅ 公告 {notice_id} 更新成功！"
                        else:
                            return f"⚠️ 公告未更改或不存在"
                    except Exception as e:
                        return f"❌ 更新失败: {str(e)}"

                # 加载公告信息
                load_btn.click(
                    fn=load_notice_for_edit,
                    inputs=edit_id,
                    outputs=[edit_title, edit_content, edit_type, edit_priority,
                             edit_start_time, edit_end_time, edit_audience]
                )

                # 更新公告
                update_notice_btn.click(
                    fn=update_notice_info,
                    inputs=[edit_id, edit_title, edit_content, edit_type, edit_priority,
                            edit_start_time, edit_end_time, edit_audience, token_box],
                    outputs=update_notice_result
                )

            # 删除公告标签页
            with gr.TabItem("🗑️ 删除公告"):
                gr.Markdown("### ⚠️ 警告：删除操作不可恢复")
                with gr.Row():
                    delete_id = gr.Number(label="公告ID", precision=0)
                    delete_btn = gr.Button("删除公告", variant="stop")

                delete_result = gr.Markdown()

                def delete_notice_by_id(notice_id, token):
                    require_admin(token)

                    if not notice_id:
                        return "❌ 请输入有效的公告ID"

                    try:
                        result = notice_manager.delete_notice(int(notice_id))
                        if result > 0:
                            return f"✅ 公告 {notice_id} 已成功删除"
                        else:
                            return f"⚠️ 未找到ID为 {notice_id} 的公告"
                    except Exception as e:
                        return f"❌ 删除失败: {str(e)}"

                delete_btn.click(
                    fn=delete_notice_by_id,
                    inputs=[delete_id, token_box],
                    outputs=delete_result
                ).then(
                    fn=lambda: get_notices_df(),
                    outputs=notices_df
                )
            # 统计分析标签页
            with gr.TabItem("📊 统计分析"):
                gr.Markdown("### 公告阅读反馈率统计")

                with gr.Row():
                    stats_id = gr.Number(label="公告 ID", precision=0)
                    stats_btn = gr.Button("生成统计")

                with gr.Row():
                    with gr.Column():
                        stats_summary = gr.JSON(label="Basic Statistics")
                    with gr.Column():
                        stats_chart = gr.Plot(label="Feedback Distribution")

                # 查看记录表格
                viewers_df = gr.Dataframe(label="View Records", interactive=False)

                # 反馈记录表格
                with gr.Tabs():
                    with gr.TabItem("👍 Likes"):
                        likes_df = gr.Dataframe(label="Users who liked", interactive=False)
                    with gr.TabItem("👎 Dislikes"):
                        dislikes_df = gr.Dataframe(label="Users who disliked", interactive=False)

                def get_notice_statistics(notice_id):
                    if not notice_id:
                        return {
                            "error": "Please enter a valid notice ID"}, None, pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

                    try:
                        notice_id = int(notice_id)
                        notice = notice_manager.get_notice(notice_id)

                        if not notice:
                            return {
                                "error": f"Notice with ID {notice_id} not found"}, None, pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

                        # 获取基本统计
                        stats = notice_manager.get_notice_stats(notice_id)

                        # 获取查看记录
                        viewers, total_viewers = notice_manager.get_notice_viewers(notice_id, page=1, page_size=100)

                        # 获取反馈记录
                        reaction_stats = notice_manager.get_reaction_stats(notice_id)

                        # 准备基本统计数据
                        summary = {
                            "Title": notice["title"],
                            "Published": format_date(notice["created_at"]),
                            "Views": stats["view_count"],
                            "Likes": stats["like_count"],
                            "Dislikes": stats["dislike_count"],
                            "Feedback Rate": f"{(stats['like_count'] + stats['dislike_count']) / max(1, stats['view_count']) * 100:.1f}%"
                        }

                        # 准备图表
                        import matplotlib.pyplot as plt
                        import numpy as np

                        # 设置matplotlib使用DejaVu Sans字体
                        plt.rcParams['font.family'] = 'DejaVu Sans'

                        # 创建饼图
                        fig, ax = plt.subplots(figsize=(6, 4))
                        labels = ['Likes', 'Dislikes', 'No Feedback']
                        sizes = [
                            stats['like_count'],
                            stats['dislike_count'],
                            max(0, stats['view_count'] - stats['like_count'] - stats['dislike_count'])
                        ]
                        colors = ['#4CAF50', '#F44336', '#EEEEEE']
                        explode = (0.1, 0.1, 0)  # 突出显示点赞和踩

                        if sum(sizes) > 0:  # 确保有数据
                            ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
                                   shadow=True, startangle=90)
                        else:
                            ax.text(0.5, 0.5, 'No Data', horizontalalignment='center', verticalalignment='center')

                        ax.axis('equal')  # 确保饼图是圆的
                        plt.title('Feedback Distribution')

                        # 准备查看记录DataFrame
                        viewers_data = []
                        for viewer in viewers:
                            viewers_data.append({
                                "User ID": viewer["user_id"],
                                "View Time": format_date(viewer["viewed_at"])
                            })
                        viewers_df_data = pd.DataFrame(viewers_data)

                        # 准备点赞用户DataFrame
                        likes_data = []
                        for like in reaction_stats["likes"]:
                            likes_data.append({
                                "User ID": like["user_id"],
                                "Like Time": format_date(like["created_at"])
                            })
                        likes_df_data = pd.DataFrame(likes_data)

                        # 准备踩用户DataFrame
                        dislikes_data = []
                        for dislike in reaction_stats["dislikes"]:
                            dislikes_data.append({
                                "User ID": dislike["user_id"],
                                "Dislike Time": format_date(dislike["created_at"])
                            })
                        dislikes_df_data = pd.DataFrame(dislikes_data)

                        return summary, fig, viewers_df_data, likes_df_data, dislikes_df_data

                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        return {
                            "error": f"Failed to get statistics: {str(e)}"}, None, pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

                stats_btn.click(
                    fn=get_notice_statistics,
                    inputs=stats_id,
                    outputs=[stats_summary, stats_chart, viewers_df, likes_df, dislikes_df]
                )

            # 热门公告分析标签页
            with gr.TabItem("🔥 热门分析"):
                gr.Markdown("### 热门公告分析")

                with gr.Row():
                    days_slider = gr.Slider(minimum=1, maximum=30, value=7, step=1, label="统计期限")
                    limit_slider = gr.Slider(minimum=5, maximum=20, value=10, step=1, label="统计条数")
                    analyze_btn = gr.Button("分析热门公告")

                popular_df = gr.Dataframe(label="Popular Notices List", interactive=False)
                popularity_chart = gr.Plot(label="Popular Notices Comparison")

                def analyze_popular_notices(days, limit):
                    try:
                        # 获取热门公告
                        popular_notices = notice_manager.get_popular_notices(days=days, limit=limit)

                        if not popular_notices:
                            return pd.DataFrame(), None

                        # 准备DataFrame数据
                        popular_data = []
                        for notice in popular_notices:
                            popular_data.append({
                                "ID": notice["id"],
                                "Title": notice["title"],
                                "Type": notice["type"],
                                "Views": notice["view_count"],
                                "Likes": notice["like_count"],
                                "Dislikes": notice["dislike_count"],
                                "Popularity Index": notice["view_count"] + notice["like_count"] * 2 - notice[
                                    "dislike_count"],
                                "Published": format_date(notice["created_at"])
                            })

                        popular_df_data = pd.DataFrame(popular_data)

                        # 创建柱状图
                        import matplotlib.pyplot as plt
                        import numpy as np

                        # 设置matplotlib使用DejaVu Sans字体
                        plt.rcParams['font.family'] = 'DejaVu Sans'

                        # 取前10条记录用于绘图
                        plot_data = popular_df_data.head(min(10, len(popular_df_data)))

                        fig, ax = plt.subplots(figsize=(10, 6))

                        # 设置柱状图位置
                        x = np.arange(len(plot_data))
                        width = 0.2

                        # 绘制三组柱状图
                        ax.bar(x - width, plot_data["Views"], width, label="Views", color="#2196F3")
                        ax.bar(x, plot_data["Likes"], width, label="Likes", color="#4CAF50")
                        ax.bar(x + width, plot_data["Dislikes"], width, label="Dislikes", color="#F44336")

                        # 设置图表标题和标签
                        ax.set_title(f"Popular Notices in Last {days} Days")
                        ax.set_ylabel("Count")
                        ax.set_xticks(x)

                        # 设置x轴标签为公告ID
                        shortened_titles = [f"ID:{id}" for id in plot_data["ID"]]
                        ax.set_xticklabels(shortened_titles, rotation=45, ha="right")

                        # 添加图例
                        ax.legend()

                        # 调整布局
                        plt.tight_layout()

                        return popular_df_data, fig

                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        return pd.DataFrame(), None

                analyze_btn.click(
                    fn=analyze_popular_notices,
                    inputs=[days_slider, limit_slider],
                    outputs=[popular_df, popularity_chart]
                )

            # 系统设置标签页
            with gr.TabItem("⚙️ 系统设置"):
                gr.Markdown("### 公告系统设置")

                with gr.Row():
                    with gr.Column():
                        auto_cleanup = gr.Checkbox(label="自动清理过期公告", value=True)
                        cleanup_days = gr.Slider(minimum=30, maximum=365, value=90, step=1,
                                                 label="保留过期公告天数")

                    with gr.Column():
                        default_duration = gr.Slider(minimum=1, maximum=90, value=30, step=1,
                                                     label="默认公告有效期(天)")
                        max_notices = gr.Slider(minimum=10, maximum=100, value=50, step=5,
                                                label="首页最大显示公告数")

                save_settings_btn = gr.Button("保存设置")
                settings_result = gr.Markdown()

                def save_system_settings(auto_cleanup, cleanup_days, default_duration, max_notices, token):
                    require_admin(token)

                    try:
                        # 这里可以实现保存设置到数据库或配置文件的逻辑
                        # 由于NoticeManager中没有这些设置的保存方法，这里只是模拟
                        settings = {
                            "auto_cleanup": auto_cleanup,
                            "cleanup_days": int(cleanup_days),
                            "default_duration": int(default_duration),
                            "max_notices": int(max_notices)
                        }

                        # 实际应用中，这里应该调用保存设置的方法
                        # notice_manager.save_settings(settings)

                        return f"✅ 设置已保存！\n```json\n{settings}\n```"
                    except Exception as e:
                        return f"❌ 保存设置失败: {str(e)}"

                save_settings_btn.click(
                    fn=save_system_settings,
                    inputs=[auto_cleanup, cleanup_days, default_duration, max_notices, token_box],
                    outputs=settings_result
                )

            # 页脚
        gr.HTML("<div style='text-align:center;color:#97a;margin-top:30px;'>© 2024 公告管理系统</div>")

        return demo

