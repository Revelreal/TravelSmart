import gradio as gr
from MainProject.dbhelper.SQLHelper import SQLHelper


def user_settings():
    def get_user_profile(username):
        if not username:
            return "", "", "❌ 请输入用户名"
        db = SQLHelper()
        info = db.fetchone("SELECT nickname, email, username FROM Users WHERE username=%s", (username,))
        db.close()
        if info:
            return info.get("nickname", ""), info.get("email", ""), ""
        else:
            return "", "", "❌ 用户不存在"

    def save_profile(username, name, email):
        if not username or not name or not email:
            return "❌ 请填写完整内容"
        db = SQLHelper()
        found = db.fetchone("SELECT id FROM Users WHERE username=%s", (username,))
        if not found:
            db.close()
            return "❌ 用户不存在"
        try:
            db.execute("UPDATE Users SET nickname=%s, email=%s WHERE username=%s", (name, email, username))
            db.close()
            return "✅ 信息保存成功！"
        except Exception as e:
            return f"❌ 信息保存失败: {e}"

    def change_password(username, old, new1, new2):
        if not username or not old or not new1 or not new2:
            return "❌ 所有字段必填"
        if new1 != new2:
            return "❌ 两次新密码不一致"
        db = SQLHelper()
        user = db.fetchone("SELECT password FROM Users WHERE username=%s", (username,))
        if not user:
            db.close()
            return "❌ 用户不存在"
        # 明文对比，生产应加密
        if user["password"] != old:
            db.close()
            return "❌ 当前密码错误"
        try:
            db.execute("UPDATE Users SET password=%s WHERE username=%s", (new1, username))
            db.close()
            return "✅ 密码修改成功！"
        except Exception as e:
            return f"❌ 修改失败: {e}"

    def logout_action():
        return "✅ 已退出登录，请 <a href='/welcome/login' style='color:#1976d2;'>点击返回登录页</a>"

    def delete_account_action(username, nickname_input):
        if not username or not nickname_input:
            return "❌ 请输入用户名和昵称"
        db = SQLHelper()
        profile = db.fetchone("SELECT nickname FROM Users WHERE username=%s", (username,))
        if not profile:
            db.close()
            return "❌ 用户不存在"
        if nickname_input != profile["nickname"]:
            db.close()
            return "❌ 昵称输入错误"
        try:
            db.execute("DELETE FROM Users WHERE username=%s", (username,))
            db.close()
            return ("✅ 账户已注销，欢迎再使用！"
                    "<br><a href='/welcome/login' style='color:#1976d2;'>点此登录新账号</a>")
        except Exception as e:
            return f"❌ 注销失败: {e}"

    with gr.Blocks(title="用户设置页面") as demo:
        gr.HTML("""
        <style>
            body {
                background: url("/static/bg.png") no-repeat center center fixed;
                background-size: cover;
                font-family: 'KaiTi', cursive;
                backdrop-filter: blur(3px);
            }
            .gr-box, .gr-tabitem, .gr-markdown, .gr-row, .gr-column {
                background-color: rgba(255, 255, 255, 0.85);
                border-radius: 12px;
                padding: 15px;
                margin: 10px 0;
            }
            #input-box input {
                background-color: #fefefe;
                border: 1px solid #aaa;
                border-radius: 8px;
                padding: 8px 12px;
                font-family: 'KaiTi', cursive;
            }
            #primary-btn, #warn-btn, #danger-btn {
                font-size: 16px;
                padding: 12px 25px;
                border-radius: 10px;
                background: linear-gradient(to right, #ffecd2, #fcb69f);
                color: #000;
                border: none;
                font-weight: bold;
                cursor: pointer;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
                transition: all 0.3s ease;
            }
            #primary-btn:hover, #warn-btn:hover, #danger-btn:hover {
                transform: scale(1.03);
            }
            h1, h2, h3 {
                font-family: 'KaiTi', cursive;
                color: #222;
            }
        </style>
        """)

        with gr.Tabs():
            with gr.TabItem("👤 基础信息"):
                gr.Markdown("### ✏️ 修改你的基本信息")
                username1 = gr.Textbox(label="用户名", placeholder="请输入用户名", elem_id="input-box")
                name = gr.Textbox(label="新昵称", placeholder="请输入新昵称", elem_id="input-box")
                email = gr.Textbox(label="新邮箱", placeholder="请输入新邮箱", elem_id="input-box")
                fetch_info_btn = gr.Button("🔍 获取当前信息（自动填充下方）", elem_id="primary-btn")
                info_msg = gr.Markdown()

                def do_fetch_info(name_username):
                    n, e, msg = get_user_profile(name_username)
                    if msg:
                        return gr.update(value=''), gr.update(value=''), msg
                    return gr.update(value=n), gr.update(value=e), "✅ 已获取信息，请编辑修改"

                fetch_info_btn.click(do_fetch_info, [username1], [name, email, info_msg])

                save_btn = gr.Button("💾 保存信息", elem_id="primary-btn")
                save_output = gr.Markdown()
                save_btn.click(save_profile, [username1, name, email], save_output)

            with gr.TabItem("🔒 修改密码"):
                gr.Markdown("### 更改账户密码")
                username2 = gr.Textbox(label="用户名", placeholder="请输入用户名", elem_id="input-box")
                old_pwd = gr.Textbox(label="当前密码", type="password", elem_id="input-box")
                new_pwd1 = gr.Textbox(label="新密码", type="password", elem_id="input-box")
                new_pwd2 = gr.Textbox(label="确认新密码", type="password", elem_id="input-box")
                pwd_btn = gr.Button("🔐 修改密码", elem_id="primary-btn")
                pwd_output = gr.Markdown()
                pwd_btn.click(change_password, [username2, old_pwd, new_pwd1, new_pwd2], pwd_output)

            with gr.TabItem("🚪 退出登录"):
                gr.Markdown("### 安全退出当前账户")
                logout_btn = gr.Button("🚶‍♂️ 退出登录", elem_id="warn-btn")
                logout_output = gr.Markdown()
                logout_btn.click(logout_action, outputs=logout_output)

            with gr.TabItem("❌ 注销账户"):
                gr.Markdown("### 🚨 危险操作！不可恢复")
                username3 = gr.Textbox(label="用户名", placeholder="请输入用户名", elem_id="input-box")
                del_user = gr.Textbox(label="确认昵称以注销", placeholder="请输入你的昵称", elem_id="input-box")
                del_btn = gr.Button("💣 注销账号", elem_id="danger-btn")
                del_output = gr.Markdown()
                del_btn.click(delete_account_action, [username3, del_user], del_output)

            with gr.TabItem("❓ 帮助中心"):
                gr.Markdown("""
                ### 🤔 常见问题
                - 如何修改信息？在“基础信息”中修改后点击保存
                - 如何联系客服？在“联系我们”页面获取支持
                """)

            with gr.TabItem("ℹ️ 关于产品"):
                gr.Markdown("""
                ### TravelSmart 智能出行系统  
                - 版本：v1.0.0  
                - 作者：智能推荐团队  
                - GitHub：[点击查看](#)
                """)

            with gr.TabItem("📜 使用条款"):
                gr.Markdown("请勿违反国家法律法规，使用本平台即表示你同意我们的使用条款。")

            with gr.TabItem("📞 联系我们"):
                gr.Markdown("""
                - 客服邮箱：support@travelsmart.com  
                - 电话：400-800-9988  
                - 微信公众号：TravelSmart官方
                """)

    return demo

# 示例挂载方式
# gr.mount_gradio_app(app, user_settings(), path="/settings/user_settings")