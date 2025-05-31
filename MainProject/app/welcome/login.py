# MainProject/app/welcome/login.py:
import gradio as gr
from MainProject.dbhelper.SQLHelper import SQLHelper


def login_page():
    with gr.Blocks() as demo:
        gr.Markdown("### 用户登录")
        msg = gr.HTML("")  # 必须用HTML支持JS跳转

        username = gr.Textbox(label="用户名")
        password = gr.Textbox(label="密码", type="password")
        btn = gr.Button("登录")

        def do_login(u, p):
            db = SQLHelper()
            ok, info = db.verify_user(u, p)
            db.close()
            if ok:
                role = info.get("role_name", "").lower()
                nickname = info.get("nickname") or info.get("username")

                # 跳转不同主页路径
                if role == "root":
                    url = "/homepage/root_home"
                    role_label = "ROOT管理主页"
                elif role == "admin":
                    url = "/homepage/admin_home"
                    role_label = "管理员主页"
                else:
                    url = "/homepage/user_home"
                    role_label = "普通用户主页"

                return (
                    f"✅ 登录成功，{nickname}！<br>"
                    f"<a href='{url}' style='color:#1976d2;font-size:1.15em;'>进入{role_label} &gt;&gt;</a>"
                )
            else:
                return f"❌ {info}"

        btn.click(do_login, [username, password], msg)

        gr.HTML(
            '<div style="margin-top:14px;text-align:right;">'
            '<a href="/welcome/register" style="color:#0275d8;font-size:0.98em;">没有账号？去注册</a>'
            '</div>'
        )
    return demo
