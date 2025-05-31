import gradio as gr
import pandas as pd
from MainProject.dbhelper.SQLHelper import SQLHelper
from MainProject.auth_utils import verify_token


# 严格校验管理员权限，默认admin和root都可访问（如只允许admin，请去掉 'root'）
def require_admin(token):
    info = verify_token(token)
    if not info or not info.get("username"):
        raise gr.Error("认证失败或无权限，请重新登录")
    if info.get("role") not in ("admin", "root"):
        raise gr.Error("权限不足，仅管理员可访问本页面！")
    return info


def get_users():
    db = SQLHelper()
    users = db.query(
        """
        SELECT u.id, u.username, u.nickname, u.email, u.phone, u.city, r.role_name, u.role_id
        FROM Users u LEFT JOIN Roles r ON u.role_id = r.id
        ORDER BY u.id LIMIT 30
        """
    )
    db.close()
    columns = ["id", "username", "nickname", "email", "phone", "city", "role_name", "role_id"]
    return pd.DataFrame(users, columns=columns) if users else pd.DataFrame(columns=columns)


def add_user(username, nickname, email, token):
    require_admin(token)
    if not username or not email:
        return "❌ 用户名和邮箱必填"
    db = SQLHelper()
    if db.is_username_exists(username):
        db.close()
        return f"❌ 用户名 {username} 已存在"
    if db.is_email_exists(email):
        db.close()
        return f"❌ 邮箱 {email} 已存在"
    try:
        ok, msg = db.create_user(username, "123456", nickname or username, None, email, None, 1, 3)
        db.close()
        if ok:
            return f"✅ 用户 {username} 已添加，初始密码123456"
        else:
            return f"❌ 添加失败：{msg}"
    except Exception as e:
        db.close()
        return f"❌ 添加异常：{e}"

def update_user(user_id, nickname, email, phone, city, token):
    require_admin(token)
    try:
        user_id = int(user_id)
    except Exception:
        return "❌ 用户ID格式不正确"
    db = SQLHelper()
    user = db.get_user_by_id(user_id)
    if not user:
        db.close()
        return f"❌ 未找到 ID 为 {user_id} 的用户"
    if user["role_id"] == 1:
        db.close()
        return "❌ 禁止修改 root 用户"
    if email:
        check = db.fetchone("SELECT id FROM Users WHERE email=%s AND id!=%s", (email, user_id))
        if check:
            db.close()
            return "❌ 此邮箱已被其他账号占用"
    db.execute(
        "UPDATE Users SET nickname=%s, email=%s, phone=%s, city=%s WHERE id=%s",
        (nickname, email, phone, city, user_id)
    )
    db.close()
    return f"✅ ID 为 {user_id} 的用户信息已更新"


def delete_user(user_id, token):
    require_admin(token)
    try:
        user_id = int(user_id)
    except Exception:
        return "❌ 用户ID格式不正确"
    db = SQLHelper()
    user = db.get_user_by_id(user_id)
    if not user:
        db.close()
        return f"❌ 未找到 ID 为 {user_id} 的用户"
    if user['role_id'] == 1:
        db.close()
        return "❌ 不允许删除 root 用户"
    if user['role_id'] == 2:
        db.close()
        return "❌ 不允许删除 admin 用户"
    db.execute("DELETE FROM Users WHERE id=%s", (user_id,))
    db.close()
    return f"✅ ID 为 {user_id} 的用户已删除"


def create_admin_home_app():
    with gr.Blocks(title="管理员后台") as demo:
        token_box = gr.Textbox(visible=False)
        adminbar = gr.HTML("正在认证管理员身份...", elem_classes="userbar-text")
        settings_btn_html = gr.HTML("", elem_id="setting-float-html")

        def load_admin(request: gr.Request):
            token = request.query_params.get("token", "")
            info = require_admin(token)
            username = info["username"]
            welcome_html = f"<b>👨‍💼 管理员 {username}</b>，欢迎来到后台控制台！"
            settings_btn = (
                f'<a href="/settings/admin_settings?token={token}" id="to_admin_settings" '
                f'style="position: fixed; right: 36px; bottom: 36px; z-index: 9999; width: 56px; height: 56px; border-radius: 50%;'
                f'background: #007BFF; color: #fff; font-size: 30px; font-weight: bold;'
                f'display: flex; align-items: center; justify-content: center;'
                f'box-shadow: 0 2px 14px rgba(0,0,0,0.18); text-decoration:none; transition: background 0.18s;"'
                f'onmouseover="this.style.background=\'#1557b1\'" '
                f'onmouseout="this.style.background=\'#007BFF\'" '
                f'title="跳转设置页面">⚙️</a>'
            )
            return token, welcome_html, settings_btn

        demo.load(
            fn=load_admin,
            inputs=None,
            outputs=[token_box, adminbar, settings_btn_html]
        )

        gr.Markdown("# 👨‍💼 管理员控制台")
        with gr.Tabs():
            with gr.TabItem("👥 用户管理"):
                gr.Markdown("## 用户列表")
                refresh_btn = gr.Button("🔄 刷新列表")
                users_df = gr.Dataframe(
                    value=get_users()[["id", "username", "nickname", "email", "phone", "city", "role_name"]],
                    interactive=False
                )
                refresh_btn.click(
                    fn=lambda token: get_users()[["id", "username", "nickname", "email", "phone", "city", "role_name"]],
                    inputs=token_box, outputs=users_df
                )
                gr.Markdown("## ➕ 添加用户")
                with gr.Row():
                    new_username = gr.Textbox(label="用户名")
                    new_nickname = gr.Textbox(label="昵称")
                    new_email = gr.Textbox(label="邮箱")
                    add_btn = gr.Button("添加用户")
                    add_output = gr.Markdown()
                add_btn.click(
                    fn=add_user,
                    inputs=[new_username, new_nickname, new_email, token_box],
                    outputs=add_output
                ).then(
                    lambda token: get_users()[["id", "username", "nickname", "email", "phone", "city", "role_name"]],
                    inputs=token_box, outputs=users_df
                )
                gr.Markdown("## 📝 修改用户信息")
                with gr.Row():
                    upd_id = gr.Number(label="用户ID", precision=0)
                    upd_nickname = gr.Textbox(label="昵称")
                    upd_email = gr.Textbox(label="邮箱")
                    upd_phone = gr.Textbox(label="手机号")
                    upd_city = gr.Textbox(label="城市")
                upd_btn = gr.Button("更新信息")
                upd_output = gr.Markdown()
                upd_btn.click(
                    fn=update_user,
                    inputs=[upd_id, upd_nickname, upd_email, upd_phone, upd_city, token_box],
                    outputs=upd_output
                ).then(
                    lambda token: get_users()[["id", "username", "nickname", "email", "phone", "city", "role_name"]],
                    inputs=token_box, outputs=users_df
                )
                gr.Markdown("## ❌ 删除用户")
                del_id = gr.Number(label="用户ID", precision=0)
                del_btn = gr.Button("删除用户")
                del_output = gr.Markdown()
                del_btn.click(
                    fn=delete_user,
                    inputs=[del_id, token_box],
                    outputs=del_output
                ).then(
                    lambda token: get_users()[["id", "username", "nickname", "email", "phone", "city", "role_name"]],
                    inputs=token_box, outputs=users_df
                )
        gr.HTML("<div style='text-align:center;color:#97a;margin-top:30px;'>© 2024 AdminBackend</div>")
    return demo
