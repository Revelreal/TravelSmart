import gradio as gr
import time
import uvicorn
from fastapi import FastAPI

# 模拟数据库中的文章和点赞信息
articles = [
    {"id": 1, "title": "Python入门指南", "content": "Python是一门简单易学的编程语言...", "likes": 5, "dislikes": 1},
    {"id": 2, "title": "深度学习基础", "content": "深度学习是机器学习的一个分支...", "likes": 10, "dislikes": 2},
    {"id": 3, "title": "Web开发技巧", "content": "现代Web开发需要掌握多种技术...", "likes": 7, "dislikes": 3}
]

# 用户反应记录(user_id -> {article_id: reaction})
user_reactions = {}


def create_article_app():
    """创建文章应用"""

    # 获取用户点赞状态
    def get_user_reaction(article_id, user_id):
        if user_id in user_reactions and article_id in user_reactions[user_id]:
            return user_reactions[user_id][article_id]
        return "none"

    # 为每篇文章创建点赞/踩组件
    def create_article_ui():
        with gr.Blocks(
                css="""
            .article-container {
                max-width: 800px;
                margin: 0 auto 30px auto;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .article-header {
                margin-bottom: 10px;
            }
            .article-content {
                margin-bottom: 15px;
            }
            .reaction-row {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .stats-text {
                color: #666;
                margin-right: auto;
            }
            .like-btn.active, .dislike-btn.active {
                background-color: #2196F3;
                color: white;
            }
            """
        ) as demo:
            gr.Markdown("# 📚 文章列表")

            # 用户ID (实际应用中会从登录系统获取)
            user_id = gr.State("user123")

            # 操作状态反馈
            status_text = gr.Markdown("")

            # 为每篇文章创建UI组件
            for article in articles:
                with gr.Group(elem_classes="article-container"):
                    gr.Markdown(f"### {article['title']}", elem_classes="article-header")
                    gr.Markdown(article['content'], elem_classes="article-content")

                    with gr.Row(elem_classes="reaction-row"):
                        view_text = gr.Markdown(f"👁️ {article['likes'] + article['dislikes']} 次查看",
                                                elem_classes="stats-text")

                        # 创建显示点赞数的组件
                        like_count = gr.Number(value=article['likes'], label="点赞", visible=False)
                        like_btn = gr.Button(f"👍 {article['likes']}", elem_id=f"like-btn-{article['id']}",
                                             elem_classes="like-btn")

                        # 创建显示踩数的组件
                        dislike_count = gr.Number(value=article['dislikes'], label="踩", visible=False)
                        dislike_btn = gr.Button(f"👎 {article['dislikes']}", elem_id=f"dislike-btn-{article['id']}",
                                                elem_classes="dislike-btn")

                    # 处理点赞按钮点击
                    def handle_like(article_id=article['id']):
                        return process_reaction(article_id, "like", "user123")

                    # 处理踩按钮点击
                    def handle_dislike(article_id=article['id']):
                        return process_reaction(article_id, "dislike", "user123")

                    # 点赞按钮事件绑定
                    like_btn.click(
                        fn=handle_like,
                        outputs=[status_text, like_btn, dislike_btn, like_count, dislike_count]
                    )

                    # 踩按钮事件绑定
                    dislike_btn.click(
                        fn=handle_dislike,
                        outputs=[status_text, like_btn, dislike_btn, like_count, dislike_count]
                    )

        return demo

    # 处理用户的点赞/踩操作
    def process_reaction(article_id, reaction_type, user_id):
        """处理用户的点赞/踩操作"""
        try:
            # 查找对应的文章
            article = next((a for a in articles if a["id"] == article_id), None)
            if not article:
                return "无效的文章ID", None, None, None, None

            # 获取用户之前的反应
            if user_id not in user_reactions:
                user_reactions[user_id] = {}

            previous_reaction = user_reactions[user_id].get(article_id)

            # 根据用户操作更新点赞/踩数量
            # 如果用户之前有反应，先取消之前的反应
            if previous_reaction == "like":
                article["likes"] -= 1
            elif previous_reaction == "dislike":
                article["dislikes"] -= 1

            # 如果用户点击的是和之前相同的反应，则取消反应
            if previous_reaction == reaction_type:
                user_reactions[user_id].pop(article_id, None)
                message = f"取消了{'点赞' if reaction_type == 'like' else '踩'}"
                like_active = ""
                dislike_active = ""
            else:
                # 否则添加新的反应
                user_reactions[user_id][article_id] = reaction_type
                if reaction_type == "like":
                    article["likes"] += 1
                    message = "点赞成功"
                    like_active = "active"
                    dislike_active = ""
                else:
                    article["dislikes"] += 1
                    message = "踩成功"
                    like_active = ""
                    dislike_active = "active"

            # 为了显示效果，添加一点延迟
            time.sleep(0.3)

            # 返回更新后的UI组件
            like_btn_text = f"👍 {article['likes']}"
            dislike_btn_text = f"👎 {article['dislikes']}"

            # 如果有活跃状态，需要添加相应的类
            like_btn = gr.Button(value=like_btn_text, elem_classes=f"like-btn {like_active}")
            dislike_btn = gr.Button(value=dislike_btn_text, elem_classes=f"dislike-btn {dislike_active}")

            return message, like_btn, dislike_btn, article['likes'], article['dislikes']

        except Exception as e:
            return f"处理反应时出错: {str(e)}", None, None, None, None

    return create_article_ui()


# 创建FastAPI应用
app = FastAPI()

# 创建Gradio接口
demo = create_article_app()

# 挂载Gradio应用到FastAPI
app = gr.mount_gradio_app(app, demo, path="/")

# 使用uvicorn启动应用
if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8089)
