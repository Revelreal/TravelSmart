# MainProject/app/welcome/forgot_password.py
import gradio as gr
from MainProject.dbhelper.SQLHelper import SQLHelper


def create_forgot_password_app():
    with gr.Blocks(
            title="重置密码",
            theme=gr.themes.Soft(),
            css="""
            .forgot-form {
                max-width: 400px;
                margin: 2rem auto;
                padding: 2rem;
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.08);
            }
            .success-box {
                background: #d4edda;
                border: 1px solid #c3e6cb;
                color: #155724;
                padding: 1rem;
                border-radius: 5px;
                margin: 1rem 0;
            }
            .error-box {
                background: #f8d7da;
                border: 1px solid #f5c6cb;
                color: #721c24;
                padding: 1rem;
                border-radius: 5px;
                margin: 1rem 0;
            }
        """
    ) as demo:
        with gr.Column(elem_classes="forgot-form"):
            gr.Markdown("# 🔑 找回/重置密码")
            status_msg = gr.HTML("")

            email = gr.Textbox(label="📧 邮箱", placeholder="请输入注册邮箱")
            username = gr.Textbox(label="👤 用户名", placeholder="请输入用户名")
            old_password = gr.Textbox(label="🔒 原密码", type="password", placeholder="请输入原密码")
            new_password = gr.Textbox(label="🆕 新密码", type="password", placeholder="设置新密码")
            confirm_new_password = gr.Textbox(label="🆕 确认新密码", type="password", placeholder="请再次输入新密码")

            submit_btn = gr.Button("重置密码", variant="primary")
            clear_btn = gr.Button("清空", variant="secondary")

            def do_reset_pwd(e, u, old_p, new_p, new_p2):
                if not e or e.strip() == "":
                    return '<div class="error-box">❌ 邮箱不能为空</div>'
                if not u or not old_p or not new_p or not new_p2:
                    return '<div class="error-box">❌ 所有信息都必须填写</div>'
                if new_p != new_p2:
                    return '<div class="error-box">❌ 两次输入的新密码不一致</div>'
                db = SQLHelper()
                try:
                    # 根据你的数据表定义，以下代码根据实际调整
                    if not db.is_username_exists(u):
                        return '<div class="error-box">❌ 用户名不存在</div>'
                    user_row = db.get_user_by_username(u)
                    if not user_row or not user_row.get("email"):
                        return '<div class="error-box">❌ 未找到该用户绑定的邮箱</div>'
                    if user_row.get("email").lower() != e.strip().lower():
                        return '<div class="error-box">❌ 邮箱与用户名不匹配</div>'
                    # 可选：可直接用 verify_user 检查密码
                    if not db.verify_user(u, old_p)[0]:
                        return '<div class="error-box">❌ 原密码错误</div>'
                    # 进行重置
                    db.update_user_password(username=u, new_password=new_p)
                    return '<div class="success-box">✅ 密码重置成功，请牢记您的新密码！<br><a href="/welcome/login">返回登录</a></div>'
                finally:
                    db.close()

            def clear_form():
                return "", "", "", "", "", ""

            submit_btn.click(
                fn=do_reset_pwd,
                inputs=[email, username, old_password, new_password, confirm_new_password],
                outputs=status_msg
            )
            clear_btn.click(
                fn=clear_form,
                outputs=[email, username, old_password, new_password, confirm_new_password, status_msg]
            )
            gr.HTML("""
            <div style="text-align:center;margin-top:16px;">
                <a href="/welcome/login" style="color: #2563eb;">🔙 返回登录</a>
            </div>
            """)
    return demo
