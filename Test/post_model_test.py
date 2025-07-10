import gradio as gr
import datetime

import uvicorn
from fastapi import FastAPI


def create_simplified_travel_post_ui(user_info_state):
    """创建简化版旅行动态UI，使用可见性切换代替标签页"""

    # 假设的数据服务
    def get_sample_posts():
        return [
            {
                "id": 1,
                "title": "美丽的海滩之旅",
                "username": "旅行达人",
                "created_at": datetime.datetime.now() - datetime.timedelta(days=2),
                "content": "这是一次难忘的海滩之旅，阳光、沙滩、海浪，一切都那么美好...",
                "location_name": "三亚海滩",
                "tags": ["海滩", "度假", "阳光"],
                "like_count": 42,
                "comment_count": 15,
                "user_liked": False,
                "user_favorited": True
            },
            {
                "id": 2,
                "title": "山间小屋的宁静时光",
                "username": "山野客",
                "created_at": datetime.datetime.now() - datetime.timedelta(days=5),
                "content": "远离城市的喧嚣，在山间小屋享受宁静的时光，听鸟鸣，闻花香...",
                "location_name": "莫干山",
                "tags": ["山野", "民宿", "宁静"],
                "like_count": 36,
                "comment_count": 8,
                "user_liked": True,
                "user_favorited": False
            }
        ]

    with gr.Blocks() as demo:
        # 状态变量 - 控制界面显示
        view_state = gr.State("list")  # 可能的值: "list", "detail", "create"
        selected_post_id = gr.State(None)

        # 主界面 - 旅行动态列表
        with gr.Group(visible=True) as list_view:
            gr.Markdown("## 旅行动态")

            # 搜索和功能区
            with gr.Row():
                search_input = gr.Textbox(placeholder="搜索动态...", label="搜索")
                search_btn = gr.Button("🔍 搜索")
                create_btn = gr.Button("✏️ 发布新动态", variant="primary")

            # 动态卡片示例
            with gr.Group(elem_classes="post-card"):
                post_title1 = gr.Markdown("### 美丽的海滩之旅")
                post_meta1 = gr.Markdown("**旅行达人** · 2天前 · 📍 三亚海滩")
                post_content1 = gr.Markdown("这是一次难忘的海滩之旅，阳光、沙滩、海浪，一切都那么美好...")
                post_tags1 = gr.Markdown("#海滩 #度假 #阳光")

                with gr.Row():
                    post_stats1 = gr.Markdown("👁️ 57次查看", elem_classes="stats-text")
                    view_btn1 = gr.Button("查看详情")
                    like_btn1 = gr.Button("👍 42")
                    fav_btn1 = gr.Button("⭐ 已收藏", variant="primary")

            with gr.Group(elem_classes="post-card"):
                post_title2 = gr.Markdown("### 山间小屋的宁静时光")
                post_meta2 = gr.Markdown("**山野客** · 5天前 · 📍 莫干山")
                post_content2 = gr.Markdown("远离城市的喧嚣，在山间小屋享受宁静的时光，听鸟鸣，闻花香...")
                post_tags2 = gr.Markdown("#山野 #民宿 #宁静")

                with gr.Row():
                    post_stats2 = gr.Markdown("👁️ 44次查看", elem_classes="stats-text")
                    view_btn2 = gr.Button("查看详情")
                    like_btn2 = gr.Button("👍 36", variant="primary")
                    fav_btn2 = gr.Button("⭐ 收藏")

            # 分页控制
            with gr.Row():
                prev_btn = gr.Button("上一页")
                page_info = gr.Markdown("第 1 页，共 5 页")
                next_btn = gr.Button("下一页")

        # 动态详情视图
        with gr.Group(visible=False) as detail_view:
            gr.Markdown("## 动态详情")

            # 返回按钮
            back_to_list_btn = gr.Button("← 返回列表")

            # 详情内容
            detail_title = gr.Markdown("### 动态标题")
            detail_meta = gr.Markdown("*作者信息*")
            detail_tags = gr.Markdown("*标签*")
            detail_content = gr.Markdown("*内容*")

            # 图片展示
            detail_images = gr.Gallery(label="图片")

            # 操作按钮
            with gr.Row():
                detail_stats = gr.Markdown("*统计信息*", elem_classes="stats-text")
                detail_like_btn = gr.Button("👍 点赞")
                detail_fav_btn = gr.Button("⭐ 收藏")

            # 评论区
            gr.Markdown("### 评论区")
            comments_display = gr.Markdown("*加载中...*")

            # 发表评论
            with gr.Row():
                comment_input = gr.Textbox(placeholder="发表你的评论...", label="评论")
                submit_comment_btn = gr.Button("发表", variant="primary")

        # 发布动态视图
        with gr.Group(visible=False) as create_view:
            gr.Markdown("## 发布新动态")

            # 返回按钮
            back_from_create_btn = gr.Button("← 返回列表")

            # 发布表单
            post_title = gr.Textbox(label="标题", placeholder="请输入动态标题")
            post_content = gr.Textbox(label="内容", placeholder="分享您的旅行经历...", lines=5)

            with gr.Row():
                post_location = gr.Textbox(label="位置", placeholder="请输入位置名称")
                post_tags = gr.Textbox(label="标签", placeholder="多个标签用空格分隔，如：美食 风景")

            post_media = gr.File(label="上传图片/视频", file_types=["image", "video"], file_count="multiple")

            with gr.Row():
                cancel_create_btn = gr.Button("取消")
                submit_post_btn = gr.Button("发布", variant="primary")

        # 结果消息
        message_box = gr.Textbox(label="消息", visible=False)

        # === 视图切换函数 ===

        def switch_to_list_view():
            return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), "list"

        def switch_to_detail_view(post_id):
            return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), "detail", post_id

        def switch_to_create_view():
            return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), "create"

        # === 加载详情函数 ===

        def load_post_detail(post_id):
            # 这里简化处理，实际应用中会从服务获取数据
            if post_id == 1:
                title = "### 美丽的海滩之旅"
                meta = "**旅行达人** · 2天前 · 📍 三亚海滩"
                tags = "#海滩 #度假 #阳光"
                content = "这是一次难忘的海滩之旅，阳光、沙滩、海浪，一切都那么美好...\n\n这里是更多详细内容..."
                images = [
                    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e",
                    "https://images.unsplash.com/photo-1519046904884-53103b34b206"
                ]
                stats = "👁️ 57次查看 | 👍 42次点赞 | 💬 15条评论"
                comments = """
                **海滩控** (3天前):  
                真漂亮！是哪个海滩呀？

                ---

                **旅行达人** (2天前):  
                是三亚的亚龙湾，非常推荐！
                """
                like_btn = gr.update(value="👍 点赞", variant="secondary")
                fav_btn = gr.update(value="⭐ 已收藏", variant="primary")
            else:
                title = "### 山间小屋的宁静时光"
                meta = "**山野客** · 5天前 · 📍 莫干山"
                tags = "#山野 #民宿 #宁静"
                content = "远离城市的喧嚣，在山间小屋享受宁静的时光，听鸟鸣，闻花香...\n\n这里有更多详细描述..."
                images = [
                    "https://images.unsplash.com/photo-1510798831971-661eb04b3739",
                    "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4"
                ]
                stats = "👁️ 44次查看 | 👍 36次点赞 | 💬 8条评论"
                comments = """
                **旅行家** (4天前):  
                请问这个民宿价格如何？

                ---

                **山野客** (4天前):  
                淡季600左右，旺季900，性价比很高！
                """
                like_btn = gr.update(value="👍 已点赞", variant="primary")
                fav_btn = gr.update(value="⭐ 收藏", variant="secondary")

            return title, meta, tags, content, images, stats, like_btn, fav_btn, comments

        # === 绑定事件 ===

        # 查看详情按钮事件
        view_btn1.click(
            fn=switch_to_detail_view,
            inputs=[gr.State(1)],
            outputs=[list_view, detail_view, create_view, view_state, selected_post_id]
        ).then(
            fn=load_post_detail,
            inputs=[gr.State(1)],
            outputs=[
                detail_title, detail_meta, detail_tags, detail_content,
                detail_images, detail_stats, detail_like_btn, detail_fav_btn,
                comments_display
            ]
        )

        view_btn2.click(
            fn=switch_to_detail_view,
            inputs=[gr.State(2)],
            outputs=[list_view, detail_view, create_view, view_state, selected_post_id]
        ).then(
            fn=load_post_detail,
            inputs=[gr.State(2)],
            outputs=[
                detail_title, detail_meta, detail_tags, detail_content,
                detail_images, detail_stats, detail_like_btn, detail_fav_btn,
                comments_display
            ]
        )

        # 返回列表按钮事件
        back_to_list_btn.click(
            fn=switch_to_list_view,
            inputs=None,
            outputs=[list_view, detail_view, create_view, view_state]
        )

        # 发布新动态按钮事件
        create_btn.click(
            fn=switch_to_create_view,
            inputs=None,
            outputs=[list_view, detail_view, create_view, view_state]
        )

        # 从发布页返回列表
        back_from_create_btn.click(
            fn=switch_to_list_view,
            inputs=None,
            outputs=[list_view, detail_view, create_view, view_state]
        )

        cancel_create_btn.click(
            fn=switch_to_list_view,
            inputs=None,
            outputs=[list_view, detail_view, create_view, view_state]
        )

        # 发布动态事件
        def handle_post_submit(title, content, location, tags, user_data):
            if not title or not content:
                return "标题和内容不能为空", gr.update(visible=True), gr.update(visible=False), gr.update(
                    visible=True), "create"

            # 简化的发布处理（实际中会调用服务）
            # ...

            return "动态发布成功！", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), "list"

        submit_post_btn.click(
            fn=handle_post_submit,
            inputs=[post_title, post_content, post_location, post_tags, user_info_state],
            outputs=[message_box, list_view, detail_view, create_view, view_state]
        ).then(
            fn=lambda: gr.update(visible=True),
            inputs=None,
            outputs=[message_box]
        )

    return demo



# 创建FastAPI应用
app = FastAPI()

# 创建Gradio接口
demo = create_simplified_travel_post_ui(gr.State({"user_id": 123, "username": "测试用户"}))

# 挂载Gradio应用到FastAPI
app = gr.mount_gradio_app(app, demo, path="/")

# 使用uvicorn启动应用
if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8089)
