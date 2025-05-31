import gradio as gr


def amap_map():
    return gr.HTML(
        "<div style='height:400px; background:#d0eaf9; display:flex; align-items:center; justify-content:center; font-size:2em;'>🗺 这里是地图展示区域</div>"
    )


def user_home_page():
    with gr.Blocks(title="用户主页") as demo:
        # 左下角的用户设置按钮
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

        gr.Markdown("## 🏠 欢迎来到 TravelSmart 用户主页")

        with gr.Row():
            with gr.Column(scale=3, min_width=440):
                amap_map()
            with gr.Column(scale=2, min_width=280):
                gr.Markdown("### 🤖 AI 智能助手")
                gr.Markdown("欢迎使用 TravelSmart AI 助手，可以咨询任何旅行问题")
                chatbot = gr.Chatbot(type="messages", show_label=False)
                msg = gr.Textbox(placeholder="输入问题，回车提问...")
                # 这里只是示范流程，你应连接实际的AI处理逻辑
                msg.submit(
                    lambda m: [(m, "正在处理...")],
                    inputs=msg,
                    outputs=chatbot
                ).then(lambda: "", outputs=msg)

        gr.HTML(
            "<div style='text-align:center;color:#97a; font-size:0.95em; margin-top:30px;'>© 2024 TravelSmart</div>")

    return demo
