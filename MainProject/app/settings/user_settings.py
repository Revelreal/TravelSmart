import gradio as gr
from MainProject.dbhelper.SQLHelper import SQLHelper
from MainProject.auth_utils import verify_token


def create_user_settings():
    with gr.Blocks(title="用户设置页面") as demo:
        # --- 隐藏token和username控件，全页面流转 ---
        token_box = gr.Textbox(visible=False)
        username_box = gr.Textbox(visible=False)

        # 欢迎栏
        welcome_msg = gr.HTML("<div style='font-size:1.25em;color:#1976d2'>正在认证...</div>")

        with gr.Tabs():
            # === 1. 基础信息 ===
            with gr.TabItem("👤 基础信息"):
                gr.Markdown("在此处修改您的用户信息。")
                username_in = gr.Textbox(label="用户名", interactive=True, container=False)
                name = gr.Textbox(label="昵称")
                email = gr.Textbox(label="邮箱")
                info_msg = gr.Markdown()
                btn_fetch = gr.Button("🔍 获取信息")
                btn_save = gr.Button("💾 保存信息")
                save_output = gr.Markdown()

            # === 2. 修改密码 ===
            with gr.TabItem("🔒 修改密码"):
                gr.Markdown("### 更改账户密码")
                old_pwd = gr.Textbox(label="当前密码", type="password")
                new_pwd1 = gr.Textbox(label="新密码", type="password")
                new_pwd2 = gr.Textbox(label="确认新密码", type="password")
                pwd_btn = gr.Button("🔐 修改密码")
                pwd_output = gr.Markdown()

            # === 3. 退出登录 ===
            with gr.TabItem("🚪 退出登录"):
                gr.Markdown("### 安全退出当前账户")
                logout_btn = gr.Button("🚶‍♂️ 退出登录")
                logout_output = gr.Markdown()

            # === 4. 注销账户 ===
            with gr.TabItem("❌ 注销账户"):
                gr.Markdown("### 🚨 危险操作！不可恢复")
                del_user = gr.Textbox(label="确认昵称以注销", placeholder="请输入你的昵称")
                del_btn = gr.Button("💣 注销账号")
                del_output = gr.Markdown()

        # ------------------- 后端安全数据函数 -----------------------

        # 页面初始化：token严格校验+控件预填
        def load_profile(request: gr.Request):
            token = request.query_params.get("token", "")
            info = verify_token(token)
            if not info or not info.get("username"):
                raise gr.Error("认证失败，请重新登录")
            username = info["username"]
            db = SQLHelper()
            userrow = db.fetchone("SELECT username, nickname, email FROM Users WHERE username=%s", (username,))
            db.close()
            if not userrow:
                raise gr.Error("用户不存在")
            welcome_text = f"<div style='font-size:1.25em;color:#1976d2'>👤 您好，{username}！</div>"
            return token, username, welcome_text, userrow["username"], userrow["nickname"], userrow["email"]

        demo.load(
            fn=load_profile,
            inputs=None,
            outputs=[token_box, username_box, welcome_msg, username_in, name, email]
        )

        # 获取信息按钮
        def get_user_profile(curr_username, token):
            info = verify_token(token)
            if not info or not info.get("username") or info["username"] != curr_username:
                raise gr.Error("认证失效，请重新登录！")
            db = SQLHelper()
            profile = db.fetchone("SELECT username, nickname, email FROM Users WHERE username=%s", (curr_username,))
            db.close()
            if profile:
                return profile["username"], profile["nickname"], profile["email"], ""
            else:
                return "", "", "", "❌ 用户不存在"

        btn_fetch.click(
            fn=get_user_profile,
            inputs=[username_in, token_box],
            outputs=[username_in, name, email, info_msg]
        )

        # 保存信息按钮
        def save_profile(curr_username, new_username, m_name, m_email, token):
            info = verify_token(token)
            if (not info or not info.get("username")
                    or info["username"] != curr_username):
                raise gr.Error("认证失效，请重新登录！")
            if not new_username or not m_name or not m_email:
                return "❌ 请填写完整内容"
            db = SQLHelper()
            found = db.fetchone("SELECT id FROM Users WHERE username=%s", (curr_username,))
            if not found:
                db.close()
                return "❌ 当前用户不存在"
            if new_username != curr_username:
                exist = db.fetchone("SELECT id FROM Users WHERE username=%s", (new_username,))
                if exist:
                    db.close()
                    return "❌ 新用户名已被占用，请更换"
                db.execute("UPDATE Users SET username=%s WHERE username=%s", (new_username, curr_username))
            db.execute("UPDATE Users SET nickname=%s, email=%s WHERE username=%s", (m_name, m_email, new_username))
            db.close()
            return "✅ 信息保存成功！请刷新页面完成账号更新" if new_username != curr_username else "✅ 信息保存成功！"

        btn_save.click(
            fn=save_profile,
            inputs=[username_box, username_in, name, email, token_box],
            outputs=save_output
        )

        # 修改密码按钮
        def change_password(curr_username, old, new1, new2, token):
            info = verify_token(token)
            if (not info or not info.get("username")
                    or info["username"] != curr_username):
                raise gr.Error("认证失效，请重新登录！")
            if not curr_username or not old or not new1 or not new2:
                return "❌ 所有字段必填"
            if new1 != new2:
                return "❌ 两次新密码不一致"
            db = SQLHelper()
            user = db.fetchone("SELECT password FROM Users WHERE username=%s", (curr_username,))
            if not user:
                db.close()
                return "❌ 用户不存在"
            if user["password"] != old:
                db.close()
                return "❌ 当前密码错误"
            db.execute("UPDATE Users SET password=%s WHERE username=%s", (new1, curr_username))
            db.close()
            return "✅ 密码修改成功！"

        pwd_btn.click(
            fn=change_password,
            inputs=[username_box, old_pwd, new_pwd1, new_pwd2, token_box],
            outputs=pwd_output
        )

        # 退出登录按钮（本地侧其实就是引导跳转为主）
        def logout_action(token):
            info = verify_token(token)
            if not info or not info.get("username"):
                raise gr.Error("认证失效，请重新登录！")
            return "✅ 已退出登录，请 <a href='/welcome/login' style='color:#1976d2;'>点击返回登录页</a>"

        logout_btn.click(
            fn=logout_action,
            inputs=[token_box],
            outputs=logout_output
        )

        # 注销账号按钮
        def delete_account_action(curr_username, nickname_input, token):
            info = verify_token(token)
            if not info or not info.get("username") or info["username"] != curr_username:
                raise gr.Error("认证失效，请重新登录！")
            db = SQLHelper()
            profile = db.fetchone("SELECT nickname FROM Users WHERE username=%s", (curr_username,))
            if not profile:
                db.close()
                return "❌ 用户不存在"
            if nickname_input != profile["nickname"]:
                db.close()
                return "❌ 昵称输入错误"
            db.execute("DELETE FROM Users WHERE username=%s", (curr_username,))
            db.close()
            return "✅ 账户已注销，欢迎再使用！<br><a href='/welcome/login' style='color:#1976d2;'>点此登录新账号</a>"

        del_btn.click(
            fn=delete_account_action,
            inputs=[username_box, del_user, token_box],
            outputs=del_output,
        )

    return demo
