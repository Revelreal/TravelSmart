import gradio as gr
from MainProject.app.API.ai_service import ask_ai_sync, test_connection


def amap_map():
    """地图展示组件"""
    return gr.HTML(
        "<div style='height:400px; background:#d0eaf9; display:flex; align-items:center; justify-content:center; font-size:2em;'>🗺 这里是地图展示区域</div>"
    )


def build_ai_messages(history, question):
    """构建发送给AI的消息格式"""
    messages = []
    # 遍历历史，处理messages格式
    for msg in (history or []):
        if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
            messages.append(msg)

    if question and question.strip():
        messages.append({"role": "user", "content": str(question)})
    return messages


def ai_chat_func(history, question):
    """AI聊天处理函数"""
    # 守护history为列表格式
    history = history or []

    if not question or not question.strip():
        # 添加一个错误消息到历史记录
        error_msg = {"role": "assistant", "content": "提问不能为空"}
        return history + [error_msg], ""

    # 先添加用户消息到历史记录
    user_msg = {"role": "user", "content": str(question)}
    updated_history = history + [user_msg]

    # 构建发送给AI的messages
    messages = build_ai_messages(history, question)

    try:
        # 使用同步版本，避免异步问题
        answer = ask_ai_sync(messages)
    except Exception as e:
        answer = f"AI请求错误: {str(e)}"
        print(f"详细错误信息: {e}")  # 添加调试信息

    # 添加AI回复到历史记录
    ai_msg = {"role": "assistant", "content": answer}
    final_history = updated_history + [ai_msg]

    return final_history, ""


def user_home_page():
    """创建用户主页界面"""
    with gr.Blocks(title="用户主页") as demo:
        # 左下角的用户设置（固定悬浮按钮）
        gr.HTML("""
            <a href='/settings/user_settings' target='_self'
                style='
                    position: fixed;
                    left: 32px;
                    bottom: 32px;
                    z-index: 9999;
                    background: #111;
                    color: #fff;
                    border-radius: 50%;
                    width: 52px;
                    height: 52px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    text-decoration: none;
                    box-shadow: 0 2px 14px rgba(0,0,0,0.18);
                    font-size: 2em;
                    transition: background 0.15s;
                '
                onmouseover="this.style.background='#333'"
                onmouseout="this.style.background='#111'"
                title="用户设置"
            >⚙️</a>
        """)

        # 页面标题
        gr.Markdown("## 🏠 欢迎来到 TravelSmart 用户主页")

        # 主要内容区域
        with gr.Row():
            # 左侧地图区域
            with gr.Column(scale=3, min_width=440):
                amap_map()

            # 右侧AI助手区域
            with gr.Column(scale=2, min_width=280):
                gr.Markdown("### 🤖 AI 智能助手")
                gr.Markdown("欢迎使用 TravelSmart AI 助手，可以咨询任何旅行问题")

                # 使用messages格式的Chatbot
                chatbot = gr.Chatbot(type="messages", show_label=False)
                msg = gr.Textbox(placeholder="输入问题，回车提问...")

                # 绑定提交事件
                msg.submit(
                    ai_chat_func,
                    inputs=[chatbot, msg],
                    outputs=[chatbot, msg]
                )

        # 页脚
        gr.HTML(
            "<div style='text-align:center;color:#97a; font-size:0.95em; margin-top:30px;'>© 2024 TravelSmart</div>"
        )

    return demo


# 主程序入口
if __name__ == "__main__":
    print("正在启动 TravelSmart 用户主页...")

    # 检查AI服务连接
    print("检查AI服务连接...")
    if test_connection():
        print("✓ AI服务连接正常")
        demo = user_home_page()
        demo.launch(
            server_name="0.0.0.0",  # 允许外部访问
            server_port=7860,  # 默认端口
            share=False,  # 不创建公共链接
            debug=True  # 启用调试模式
        )
    else:
        print("✗ AI服务连接失败，请检查网络和API配置")
        print("程序将仍然启动，但AI功能可能不可用")
        demo = user_home_page()
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            debug=True
        )
