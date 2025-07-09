#MainProject/app/welcome/register.py:
import gradio as gr
from MainProject.dbhelper.SQLHelper import SQLHelper
from MainProject.auth_utils import create_token
import urllib.parse


def create_register_app():
    """标准范式 Gradio 注册页面，直接供 mount_gradio_app 使用"""
    with gr.Blocks(
            title="用户注册",
            theme=gr.themes.Soft(),
            css="""
            .register-form {
                max-width: 400px;
                margin: 2rem auto;
                padding: 2rem;
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
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
            .jump-link {
                display:inline-block; background:#3b82f6; color:white; font-weight:bold;
                border-radius:8px; padding:12px 28px; margin-top:12px; text-decoration:none;
                font-size:1.1em; transition:background 0.22s;
            }
            .jump-link:hover { background:#2563eb; }
        """
    ) as demo:
        with gr.Column(elem_classes="register-form"):
            gr.Markdown("# 📝 用户注册")
            status_msg = gr.HTML("")

            username = gr.Textbox(label="👤 用户名", placeholder="请输入用户名")
            password = gr.Textbox(label="🔒 密码", type="password", placeholder="请输入密码")
            confirm_password = gr.Textbox(label="🔒 确认密码", type="password", placeholder="请再次输入密码")

            with gr.Row():
                register_btn = gr.Button("🚀 注册", variant="primary")
                clear_btn = gr.Button("🔄 清空", variant="secondary")

            def do_register(u, p, cp):
                """处理注册逻辑"""
                if not u or not p or not cp:
                    return '<div class="error-box">❌ 请输入用户名和密码</div>'
                if p != cp:
                    return '<div class="error-box">❌ 两次输入的密码不一致</div>'
                db = SQLHelper()
                try:
                    if db.is_username_exists(u):
                        return '<div class="error-box">❌ 用户名已存在</div>'
                    user_info = {"username": u, "password": p, "role_name": "user"}
                    db.register_user(user_info)

                    # 标准token
                    token = create_token(u, "user", "user")
                    encoded_token = urllib.parse.quote(token)
                    jump_url = f"/homepage/user_home?token={encoded_token}"

                    return f'''
                        <div class="success-box">
                            <h4>✅ 注册成功！</h4>
                            <p><strong>用户名：</strong>{u}</p>
                            <a href="{jump_url}" class="jump-link">🚀 进入系统</a>
                        </div>
                    '''
                finally:
                    db.close()

            def clear_form():
                return "", "", "", ""

            register_btn.click(
                fn=do_register,
                inputs=[username, password, confirm_password],
                outputs=status_msg
            )
            clear_btn.click(
                fn=clear_form,
                outputs=[username, password, confirm_password, status_msg]
            )

            gr.HTML('''
                <div style="text-align: center; margin-top: 20px;">
                    <a href="/welcome/login" style="color: #007bff;">🔐 已有账号？去登录</a>
                </div>
            ''')

    return demo
