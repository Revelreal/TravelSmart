import gradio as gr
import pandas as pd
from MainProject.dbhelper.SQLHelper import SQLHelper


def fetch_admins():
    db = SQLHelper()
    sql = """
    SELECT u.id, u.username, u.nickname, u.email, u.phone,
           r.role_name, s.status_name, u.create_time
    FROM Users u
    LEFT JOIN Roles r ON u.role_id = r.id
    LEFT JOIN UserStatus s ON u.status_id = s.id
    WHERE r.role_name = 'admin'
    ORDER BY u.create_time DESC
    """
    result = db.query(sql)
    db.close()
    if result:
        return pd.DataFrame(result).head(30)
    return pd.DataFrame(columns=["id", "username", "nickname", "email", "phone", "role_name", "status_name", "create_time"])


def add_admin(username, password, nickname, email, phone, status_name):
    db = SQLHelper()
    role_row = db.fetchone("SELECT id FROM Roles WHERE role_name='admin'")
    status_row = db.fetchone("SELECT id FROM UserStatus WHERE status_name=%s", (status_name,))
    if not role_row or not status_row:
        db.close()
        return "❌ 角色或状态不存在"
    exists = db.fetchone("SELECT id FROM Users WHERE username=%s", (username,))
    if exists:
        db.close()
        return "❌ 用户名已存在"
    sql = """
    INSERT INTO Users (username, password, nickname, email, phone, role_id, status_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    db.execute(sql, (username, password, nickname, email, phone, role_row["id"], status_row["id"]))
    db.close()
    return "✅ 管理员已添加"


def delete_admin(admin_id):
    db = SQLHelper()
    role = db.fetchone("""
        SELECT r.role_name FROM Users u
        LEFT JOIN Roles r ON u.role_id = r.id
        WHERE u.id=%s
    """, (admin_id,))
    if not role:
        db.close()
        return f"❌ 未找到ID为{admin_id}的管理员"
    if role["role_name"] == "root":
        db.close()
        return "❌ 禁止删除系统root用户"
    db.execute("DELETE FROM Users WHERE id=%s", (admin_id,))
    db.close()
    return f"✅ ID为{admin_id}的管理员用户已删除"


def update_admin(admin_id, nickname, email, phone, status_name):
    db = SQLHelper()
    status = db.fetchone("SELECT id FROM UserStatus WHERE status_name=%s", (status_name,))
    if not status:
        db.close()
        return f"❌ 状态不存在"
    user = db.fetchone("SELECT id FROM Users WHERE id=%s", (admin_id,))
    if not user:
        db.close()
        return f"❌ 未找到ID为{admin_id}的管理员"
    db.execute(
        "UPDATE Users SET nickname=%s, email=%s, phone=%s, status_id=%s WHERE id=%s",
        (nickname, email, phone, status["id"], admin_id)
    )
    db.close()
    return f"✅ ID为{admin_id}的管理员资料已更新"


def get_status_names():
    db = SQLHelper()
    names = [row["status_name"] for row in db.query("SELECT status_name FROM UserStatus")]
    db.close()
    return names or ["正常"]


def root_home_page():
    with gr.Blocks(title="ROOT超级管理员后台") as demo:
        # 悬浮设置页面链接（右上角）
        gr.HTML(
            """
            <a href='/settings/admin_settings' target='_self' style="
                position: fixed;
                top: 24px; right: 32px;
                z-index: 1001;
                background: #007BFF;
                color: white;
                text-decoration: none;
                padding: 9px 18px;
                border-radius: 25px;
                font-weight: 600;
                box-shadow:0 2px 8px rgba(0,0,0,0.06);
                transition: background 0.2s;
                font-size: 16px;
            " onmouseover="this.style.background='#1557b1'" onmouseout="this.style.background='#007BFF'">
                ⚙️ 前往设置页面
            </a>
            """
        )
        gr.Markdown("# 👑 ROOT超级管理员后台 - 管理员账户管理")
        with gr.Tabs():
            with gr.TabItem("管理员账户管理"):
                gr.Markdown("### 管理员（role=admin）用户 增删改查")

                def refresh_table():
                    return fetch_admins()

                with gr.Row():
                    refresh_btn = gr.Button("🔄 刷新列表")
                    admins_df = gr.Dataframe(
                        label="管理员用户列表",
                        value=fetch_admins(),
                        interactive=False
                    )
                refresh_btn.click(refresh_table, None, admins_df)

                gr.Markdown("#### ➕ 新增管理员")
                with gr.Row():
                    new_username = gr.Textbox(label="用户名")
                    new_pwd = gr.Textbox(label="密码", type="password")
                    new_nickname = gr.Textbox(label="昵称", value="")
                    new_email = gr.Textbox(label="邮箱", value="")
                    new_phone = gr.Textbox(label="手机号", value="")
                    new_status = gr.Dropdown(label="状态", choices=get_status_names(), value="正常")
                    add_btn = gr.Button("添加管理员")
                    add_result = gr.Markdown()
                add_btn.click(
                    add_admin, [new_username, new_pwd, new_nickname, new_email, new_phone, new_status], add_result
                ).then(refresh_table, None, admins_df)

                gr.Markdown("#### 📝 修改管理员信息")
                with gr.Row():
                    upd_id = gr.Number(label="管理员ID", precision=0)
                    upd_nickname = gr.Textbox(label="昵称", value="")
                    upd_email = gr.Textbox(label="邮箱", value="")
                    upd_phone = gr.Textbox(label="手机号", value="")
                    upd_status = gr.Dropdown(label="状态", choices=get_status_names(), value="正常")
                upd_btn = gr.Button("更新资料")
                upd_res = gr.Markdown()
                upd_btn.click(
                    update_admin,
                    [upd_id, upd_nickname, upd_email, upd_phone, upd_status],
                    upd_res
                ).then(refresh_table, None, admins_df)

                gr.Markdown("#### ❌ 删除管理员")
                with gr.Row():
                    del_id = gr.Number(label="管理员ID", precision=0)
                    del_btn = gr.Button("删除")
                    del_result = gr.Markdown()
                del_btn.click(delete_admin, [del_id], del_result).then(refresh_table, None, admins_df)

                gr.Markdown("> 提示：拥有root权限的账号不可被删除。后台所有操作请谨慎！")
    return demo
