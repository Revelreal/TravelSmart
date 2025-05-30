# app/welcome/login.py
import gradio as gr
from MainProject.dbhelper.DBHelper import DBHelper


def login_page():
    with gr.Blocks() as demo:
        gr.Markdown("### 用户登录")
        msg = gr.Markdown("")
        username = gr.Textbox(label="用户名")
        password = gr.Textbox(label="密码", type="password")
        btn = gr.Button("登录")

        def do_login(u, p):
            db = DBHelper()
            ok, info = db.verify_user(u, p)
            db.close()
            if ok:
                # 检查是否为管理员
                if u == "admin":
                    return f"✅ {info}，<a href='/homepage/admin_home' target='_self'>进入管理页</a>"
                else:
                    return f"✅ {info}，<a href='/homepage/user_home' target='_self'>进入主页</a>"
            else:
                return f"❌ {info}"

        btn.click(do_login, [username, password], msg)

        # === 增加“去注册”链接 ===
        gr.HTML('<div style="margin-top:14px;text-align:right;">'
                '<a href="/welcome/register" style="color:#0275d8;font-size:0.98em;">没有账号？去注册</a>'
                '</div>')
    return demo
