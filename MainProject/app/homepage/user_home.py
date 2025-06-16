# MainProject/app/homepage/user_home.py:
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


# 地图/其它功能，同理加token参数和校验...

def create_map_ui(token_box):
    # token_box: gr.Textbox, 页面已另外预先定义

    # 支持动态token的地图iframe生成
    def _iframe_html(token: str):
        # token为None时iframe不渲染
        if not token:
            return '<div style="color:red;padding:20px">未登录/参数缺失，无法加载地图</div>'
        return f"""
        <iframe
            id="map-iframe"
            src="/api/map?token={token}"
            style="width:100%; height:480px; border:none;"
            allow="geolocation"
        ></iframe>
        """

    with gr.Column(scale=3):
        with gr.Group(elem_classes="map-border"):
            map_html = gr.HTML()  # 用于动态展示iframe

        with gr.Row():
            lng = gr.Number(value=116.397428, label="经度", elem_id="lng_input", precision=6)
            lat = gr.Number(value=39.90923, label="纬度", elem_id="lat_input", precision=6)
            zoom = gr.Slider(3, 18, value=13, label="缩放级别", step=0.1, elem_id="zoom_slider")

        # == token变化时动态更新iframe ==
        token_box.change(
            _iframe_html,
            inputs=token_box,
            outputs=map_html
        )
        # 页面初次装载也手动触发一次（防止加载时不出现地图）
        # 注意：如果你在demo.load返回token时，可以同步调用map_html.update...

    return lng, lat, zoom, map_html


def create_user_home_app():
    with gr.Blocks(
            title="TravelSmart",
            css="""
        .map-border { border: 1px solid #ddd; border-radius: 8px; padding: 8px; }
        #map-iframe { min-height: 480px !important; }
        .userbar-text {
            font-size:1.10em;
            color:#365;
            text-align:right;
            margin-top:10px;
            margin-right:42px;
        }
        #float-setting-btn {
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
            font-size: 2em;
            box-shadow: 0 2px 14px rgba(0,0,0,0.18);
            transition: background 0.15s;
        }
        #float-setting-btn:hover { background:#333;}
        """
    ) as demo:
        # -------- 必要控件 --------
        token_box = gr.Textbox(visible=False)
        userbar = gr.HTML("正在加载...", elem_classes="userbar-text")
        settings_btn_html = gr.HTML("", elem_id="setting-float-html")  # 悬浮窗按钮

        # -------- load回调，token流转，并输出拼接好的设置按钮HTML --------
        def load_user(request: gr.Request):
            token = request.query_params.get("token", "")
            info = verify_token(token)
            if not info or not info.get("username"):
                raise gr.Error("未登录或令牌无效，请重新登录")
            username = info["username"]
            userbar_html = f"👤 当前用户：<b>{username}</b>"
            settings_btn = (
                f'<a href="/settings/user_settings?token={token}" id="float-setting-btn" title="设置">&#9881;</a>'
            )
            return token, userbar_html, settings_btn

        demo.load(
            fn=load_user,
            inputs=None,
            outputs=[token_box, userbar, settings_btn_html]
        )

        gr.Markdown("## 🏠 TravelSmart 用户主页")
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
