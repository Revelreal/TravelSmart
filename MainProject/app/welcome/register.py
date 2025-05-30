import gradio as gr
from MainProject.dbhelper.DBHelper import DBHelper


def register_page():
    with gr.Blocks() as demo:
        gr.Markdown("### 用户注册")
        msg = gr.Markdown("")
        username = gr.Textbox(label="用户名")
        password = gr.Textbox(label="密码", type="password")
        password2 = gr.Textbox(label="确认密码", type="password")
        btn = gr.Button("注册")

        def do_register(u, p1, p2):
            if not u or not p1 or not p2:
                return "❌ 请填写所有字段"
            if p1 != p2:
                return "❌ 两次输入的密码不一致"
            db = DBHelper()
            ok, info = db.create_user(u, p1)
            db.close()
            if ok:
                # 注册成功，JS自动跳转到登录页
                return (
                    "✅ 注册成功，正在跳转到登录页..."
                    "<script>setTimeout(function(){window.location='/welcome/login';}, 1000);</script>"
                )
            else:
                return f"❌ {info}"

        btn.click(do_register, [username, password, password2], msg)

        # 页面底部加“已有账号？去登录”链接
        gr.HTML('<div style="margin-top:14px;text-align:right;">'
                '<a href="/welcome/login" style="color:#0275d8;font-size:0.98em;">已有账号？去登录</a>'
                '</div>')
    return demo
