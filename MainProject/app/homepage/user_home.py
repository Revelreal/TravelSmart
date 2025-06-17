import gradio as gr
from MainProject.app.API.ai_service import ask_ai_sync
from MainProject.auth_utils import verify_token


def build_ai_messages(history, question):
    messages = []
    for msg in (history or []):
        if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
            messages.append(msg)
    if question and question.strip():
        messages.append({"role": "user", "content": str(question)})
    return messages


# AI接口（必须token核查）
def ai_chat_func(history, question, token):
    # 1. token认证
    info = verify_token(token)
    if not info or not info.get("username"):
        raise gr.Error("认证失效，请刷新页面重新登录")
    history = history or []
    if not question or not question.strip():
        error_msg = {"role": "assistant", "content": "提问不能为空"}
        return history + [error_msg], ""
    user_msg = {"role": "user", "content": str(question)}
    updated_history = history + [user_msg]
    messages = build_ai_messages(history, question)
    try:
        answer = ask_ai_sync(messages)
    except Exception as e:
        answer = f"AI请求错误: {str(e)}"
    ai_msg = {"role": "assistant", "content": answer}
    final_history = updated_history + [ai_msg]
    return final_history, ""


def create_map_ui(token_box):
    def _iframe_html(token: str):
        if not token:
            return '<div style="color:red;padding:20px">未登录/参数缺失，无法加载地图</div>'
        # 仅注册iframe
        return f"""
        <iframe
            id='map-iframe'
            src='/api/map?token={token}'
            style='width:100%; height:680px; border:none;'
            allow='geolocation'></iframe>
        """

    with gr.Column(scale=3):
        with gr.Group(elem_classes="map-border"):
            map_html = gr.HTML()

        # 1. token变动时注册iframe
        token_box.change(_iframe_html, inputs=token_box, outputs=map_html)

    return map_html


def create_user_home_app():
    with gr.Blocks(
            title="TravelSmart",
            css="""
        .map-border { border: 1px solid #ddd; border-radius: 8px; padding: 8px; }
        #map-iframe { min-height: 580px !important; }

        /* 顶部导航栏样式 */
        .top-navbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 20px;
            background: #ffffff;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 15px;
            border-radius: 8px;
        }

        /* 用户头像样式 */
        .user-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #4a6baf;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
        }

        /* 用户名称样式 */
        .username-display {
            margin-left: 10px;
            font-size: 16px;
            font-weight: 500;
            color: #333;
        }

        /* 左侧用户区域 */
        .user-area {
            display: flex;
            align-items: center;
        }

        /* 右侧功能按钮区 */
        .nav-buttons {
            display: flex;
            gap: 16px;
        }

        /* 导航按钮样式 */
        .nav-btn {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #f5f5f5;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: #555;
            text-decoration: none;
            font-size: 18px;
            transition: all 0.2s;
        }

        .nav-btn:hover {
            background: #e0e0e0;
            transform: translateY(-2px);
        }

        /* 页面标题样式 */
        .page-title {
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin: 0;
            padding: 0;
        }
        """
    ) as demo:
        # -------- 必要控件 --------
        token_box = gr.Textbox(visible=False)
        navbar_html = gr.HTML("", elem_id="top-navbar")

        # -------- load回调，token流转，并输出拼接好的导航栏HTML --------
        def load_user(request: gr.Request):
            token = request.query_params.get("token", "")
            info = verify_token(token)
            if not info or not info.get("username"):
                raise gr.Error("未登录或令牌无效，请重新登录")

            username = info["username"]
            avatar_letter = username[0].upper()  # 获取用户名第一个字符作为头像

            # 构建导航栏HTML
            navbar = f'''
            <div class="top-navbar">
                <div class="user-area">
                    <div class="user-avatar">{avatar_letter}</div>
                    <span class="username-display">{username}</span>
                </div>
                <h1 class="page-title">TravelSmart 用户主页</h1>
                <div class="nav-buttons">
                    <a href="/api/trips?token={token}" class="nav-btn" title="我的行程">🧳</a>
                    <a href="/api/reviews?token={token}" class="nav-btn" title="我的评价">⭐</a>
                    <a href="/api/preferences?token={token}" class="nav-btn" title="旅行偏好">❤️</a>
                    <a href="/settings/user_settings?token={token}" class="nav-btn" title="用户设置">⚙️</a>
                </div>
            </div>
            '''

            return token, navbar

        demo.load(
            fn=load_user,
            inputs=None,
            outputs=[token_box, navbar_html]
        )

        with gr.Row():
            create_map_ui(token_box)  # 地图组件
            with gr.Column(scale=2, min_width=280):
                gr.Markdown("### 🤖 AI 智能助手")
                gr.Markdown("欢迎使用 TravelSmart AI 助手，可以咨询任何旅行问题")
                chatbot = gr.Chatbot(type="messages", show_label=False)
                msg = gr.Textbox(placeholder="输入问题，回车提问...")

                # -------- 交互：所有调用都带token校验 --------
                msg.submit(
                    fn=ai_chat_func,
                    inputs=[chatbot, msg, token_box],
                    outputs=[chatbot, msg]
                )

        gr.HTML("<div style='text-align:center;color:#97a;margin-top:30px;'>© 2024 TravelSmart</div>")

    return demo

