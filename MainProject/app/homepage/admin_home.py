import gradio as gr
import pandas as pd
from MainProject.dbhelper.DBHelper import DBHelper


def fetch_users():
    db = DBHelper()
    result = db.query("SELECT id, username, nickname, email, phone, city, create_time FROM Users")
    db.close()
    # 限制只显示前30行
    if result:
        return pd.DataFrame(result).head(30)
    return pd.DataFrame(columns=["id", "username", "nickname", "email", "phone", "city", "create_time"])


def add_user(username, password, nickname, email):
    db = DBHelper()
    ok, msg = db.create_user(username, password, nickname, None, None, email, None)
    db.close()
    return msg


def delete_user(user_id):
    db = DBHelper()
    exists = db.fetchone("SELECT id FROM Users WHERE id=%s", (user_id,))
    if not exists:
        db.close()
        return f"❌ 未找到ID为{user_id}的用户"
    db.execute("DELETE FROM Users WHERE id=%s", (user_id,))
    db.close()
    return f"✅ ID为{user_id}的用户已删除"


def update_user(user_id, nickname, email, phone, city):
    db = DBHelper()
    exists = db.fetchone("SELECT id FROM Users WHERE id=%s", (user_id,))
    if not exists:
        db.close()
        return f"❌ 未找到ID为{user_id}的用户"
    db.execute(
        "UPDATE Users SET nickname=%s, email=%s, phone=%s, city=%s WHERE id=%s",
        (nickname, email, phone, city, user_id)
    )
    db.close()
    return f"✅ ID为{user_id}的资料已更新"


def admin_home_page():
    with gr.Blocks(title="管理员后台") as demo:
        gr.Markdown("# 🎛️ TravelSmart 管理员后台")
        with gr.Tabs():
            with gr.TabItem("用户管理"):
                gr.Markdown("### 用户列表&增改删")

                def refresh_table():
                    return fetch_users()

                with gr.Row():
                    refresh_btn = gr.Button("🔄 刷新用户列表")
                    users_df = gr.Dataframe(
                        label="用户列表",
                        value=fetch_users(),
                        interactive=False
                    )
                refresh_btn.click(refresh_table, None, users_df)

                gr.Markdown("#### ➕ 新增用户")
                with gr.Row():
                    new_username = gr.Textbox(label="用户名")
                    new_pwd = gr.Textbox(label="密码", type="password")
                    new_nickname = gr.Textbox(label="昵称", value="")
                    new_email = gr.Textbox(label="邮箱", value="")
                    add_btn = gr.Button("添加")
                    add_result = gr.Markdown()
                add_btn.click(
                    add_user, [new_username, new_pwd, new_nickname, new_email], add_result
                ).then(refresh_table, None, users_df)

                gr.Markdown("#### 📝 修改用户信息")
                with gr.Row():
                    upd_id = gr.Number(label="用户ID", precision=0)
                    upd_nickname = gr.Textbox(label="昵称", value="")
                    upd_email = gr.Textbox(label="邮箱", value="")
                    upd_phone = gr.Textbox(label="手机号", value="")
                    upd_city = gr.Textbox(label="城市", value="")
                upd_btn = gr.Button("更新资料")
                upd_res = gr.Markdown()
                upd_btn.click(
                    update_user,
                    [upd_id, upd_nickname, upd_email, upd_phone, upd_city],
                    upd_res
                ).then(refresh_table, None, users_df)

                gr.Markdown("#### ❌ 删除用户")
                with gr.Row():
                    del_id = gr.Number(label="用户ID", precision=0)
                    del_btn = gr.Button("删除")
                    del_result = gr.Markdown()
                del_btn.click(delete_user, [del_id], del_result).then(refresh_table, None, users_df)

    return demo
