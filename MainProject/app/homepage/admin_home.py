import gradio as gr
import pandas as pd
from MainProject.dbhelper.SQLHelper import SQLHelper


def get_users():
    db = SQLHelper()
    users = db.query(
        """
        SELECT u.id, u.username, u.nickname, u.email, u.phone, u.city, r.role_name
        FROM Users u LEFT JOIN Roles r ON u.role_id = r.id
        ORDER BY u.id LIMIT 30
        """
    )
    db.close()
    return pd.DataFrame(users) if users else pd.DataFrame(columns=["id", "username", "nickname", "email", "phone", "city", "role_name"])


def add_user(username, nickname, email):
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


def update_user(user_id, nickname, email, phone, city):
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
    # 邮箱不得重复
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


def delete_user(user_id):
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
    db.execute("DELETE FROM Users WHERE id=%s", (user_id,))
    db.close()
    return f"✅ ID 为 {user_id} 的用户已删除"


def admin_home_page():
    with gr.Blocks(title="管理员后台") as demo:
        gr.Markdown("# 👨‍💼 管理员控制台")

        with gr.Tabs():
            with gr.TabItem("👥 用户管理"):
                gr.Markdown("## 用户列表")
                refresh_btn = gr.Button("🔄 刷新列表")
                users_df = gr.Dataframe(value=get_users(), interactive=False)
                refresh_btn.click(fn=get_users, outputs=users_df)

                gr.Markdown("## ➕ 添加用户")
                with gr.Row():
                    new_username = gr.Textbox(label="用户名")
                    new_nickname = gr.Textbox(label="昵称")
                    new_email = gr.Textbox(label="邮箱")
                    add_btn = gr.Button("添加用户")
                    add_output = gr.Markdown()
                add_btn.click(
                    fn=add_user,
                    inputs=[new_username, new_nickname, new_email],
                    outputs=add_output
                ).then(fn=get_users, outputs=users_df)

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
                    inputs=[upd_id, upd_nickname, upd_email, upd_phone, upd_city],
                    outputs=upd_output
                ).then(fn=get_users, outputs=users_df)

                gr.Markdown("## ❌ 删除用户")
                del_id = gr.Number(label="用户ID", precision=0)
                del_btn = gr.Button("删除用户")
                del_output = gr.Markdown()
                del_btn.click(
                    fn=delete_user,
                    inputs=[del_id],
                    outputs=del_output
                ).then(fn=get_users, outputs=users_df)

        # ============ 右下角悬浮跳转设置按钮 =============
        gr.HTML("""
            <a href='/settings/admin_settings' target='_self'
                style="
                    position: fixed;
                    right: 36px;
                    bottom: 36px;
                    z-index: 9999;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    width: 56px;
                    height: 56px;
                    background: #007BFF;
                    color: #fff;
                    border-radius: 50%;
                    text-align: center;
                    box-shadow: 0 2px 14px rgba(0,0,0,0.18);
                    font-size: 30px;
                    font-weight: bold;
                    transition: background 0.18s;
                    text-decoration:none;
                "
                onmouseover="this.style.background='#1557b1'"
                onmouseout="this.style.background='#007BFF'"
                title="跳转设置页面"
            >⚙️</a>
        """)
        # ===============================================

    return demo
