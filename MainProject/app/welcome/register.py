# MainProject/app/welcome/register.py:
import gradio as gr
from MainProject.dbhelper.SQLHelper import SQLHelper


def register_page():
    with gr.Blocks() as demo:
        gr.Markdown("### 用户注册")
        # ----------------------
        # msg = gr.Markdown("") # 改为HTML
        msg = gr.HTML("")
        # ----------------------
        username = gr.Textbox(label="用户名")
        password = gr.Textbox(label="密码", type="password")
        password2 = gr.Textbox(label="确认密码", type="password")
        btn = gr.Button("注册")

        def do_register(u, p1, p2):
            if not u or not p1 or not p2:
                return "❌ 请填写所有字段"
            if p1 != p2:
                return "❌ 两次输入的密码不一致"
            if len(u) < 3 or len(u) > 50:
                return "❌ 用户名长度需为3~50字符"
            if len(p1) < 6 or len(p1) > 128:
                return "❌ 密码长度需为6~128字符"

            db = SQLHelper()
            exist = db.fetchone("SELECT id FROM Users WHERE username=%s", (u,))
            if exist:
                db.close()
                return "❌ 用户名已存在，请更换"
            try:
                ok, msginfo = db.create_user(
                    u, p1, u, None, None, None, 1, 3
                )
                db.close()
                if ok:
                    # 注意：只在HTML组件内返回JS才会生效
                    return (
                        "✅ 注册成功，<a href='/welcome/login' style='color:#166fb2;font-size:1.1em;font-weight:bold;'>立即登录</a>"
                        "<script>setTimeout(function(){window.location.href='/welcome/login'},2000);</script>"
                    )
                else:
                    return f"❌ 注册失败：{msginfo}"
            except Exception as e:
                db.close()
                return f"❌ 注册异常：{e}"

        btn.click(do_register, [username, password, password2], msg)

        gr.HTML(
            '<div style="margin-top:14px;text-align:right;">'
            '<a href="/welcome/login" style="color:#0275d8;font-size:0.98em;">已有账号？去登录</a>'
            '</div>'
        )
    return demo
