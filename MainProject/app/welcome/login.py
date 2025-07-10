# MainProject/app/welcome/login_ui.py
import gradio as gr
from MainProject.dbhelper.SQLHelper import SQLHelper
from MainProject.auth_utils import create_token


def create_login_app():
    with gr.Blocks(title="登录", theme=gr.themes.Soft()) as login_app:
        gr.Markdown("## 🏝️ 智能旅游平台 - 登录")
        username = gr.Textbox(label="用户名")
        password = gr.Textbox(label="密码", type="password")
        login_btn = gr.Button("登录", variant="primary")
        msg = gr.Markdown()
        link = gr.HTML("")

        def login_fn(user, pwd):
            db = SQLHelper()
            try:
                success, info = db.verify_user(user, pwd)
                if not success:
                    return "❌ 用户名或密码错误", ""
                role = info["role_name"].lower()
                id = info["id"]
                token = create_token(user_id=id, username=info["username"], role=role)
                dest = {
                    "root": "/homepage/root_home",
                    "admin": "/homepage/admin_home",
                    "user": "/homepage/user_home"
                }.get(role, "/")
                html = (
                    f'<a href="{dest}?token={token}" '
                    'style="display:inline-block;background:#3b82f6;color:white;'
                    'font-weight:bold;border-radius:8px;padding:14px 32px;margin-top:18px;'
                    'text-decoration:none;font-size:1.2em;transition:background 0.2s;" '
                    'onmouseover="this.style.background=\'#2563eb\'" '
                    'onmouseout="this.style.background=\'#3b82f6\'">进入主页面</a>'
                )
                return "✅ 登录成功，请点击下方按钮进入", html
            finally:
                db.close()

        login_btn.click(fn=login_fn, inputs=[username, password], outputs=[msg, link])
        # 页脚：注册、找回密码
        gr.HTML("""
        <div style="text-align:center; margin-top:32px;">
            <a href="/welcome/register" 
               style="display:inline-block; margin:0 12px; background:#e0e7ef; color:#2563eb; font-weight:600;
                border-radius:7px; padding:10px 28px; text-decoration:none; font-size:1em; transition:background 0.2s;"
                onmouseover="this.style.background='#c7d5ee'" onmouseout="this.style.background='#e0e7ef'">
               没有账号？去注册
            </a>
            <a href="/welcome/forgot_password" 
               style="display:inline-block; margin:0 12px; background:#fce6c9; color:#c26a07; font-weight:600;
                border-radius:7px; padding:10px 28px; text-decoration:none; font-size:1em; transition:background 0.2s;"
                onmouseover="this.style.background='#ffedbb'" onmouseout="this.style.background='#fce6c9'">
               忘记密码？去找回
            </a>
        </div>
        """)
    return login_app
