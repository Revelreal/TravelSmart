import gradio as gr
from MainProject.dbhelper.SQLHelper import SQLHelper
from MainProject.auth_utils import verify_token


def get_admin_info(username):
    db = SQLHelper()
    user = db.fetchone(
        "SELECT nickname, email, phone, city FROM Users WHERE username=%s", (username,)
    )
    db.close()
    if user:
        return {
            "用户名": username,
            "昵称": user["nickname"] or "",
            "邮箱": user["email"] or "",
            "手机号": user["phone"] or "",
            "当前城市": user["city"] or ""
        }
    else:
        return {
            "用户名": username, "昵称": "", "邮箱": "", "手机号": "", "当前城市": ""
        }


def update_admin_info(nickname, email, phone, city, username):
    db = SQLHelper()
    try:
        db.execute(
            "UPDATE Users SET nickname=%s, email=%s, phone=%s, city=%s WHERE username=%s",
            (nickname, email, phone, city, username)
        )
        db.close()
        return f"✅ 信息已保存（昵称={nickname} 邮箱={email} 手机={phone} 城市={city}）"
    except Exception as e:
        db.close()
        return f"❌ 保存失败：{e}"


def change_pwd(oldpwd, newpwd, newpwd2, username):
    if not oldpwd or not newpwd or not newpwd2:
        return "❌ 全部字段不能为空"
    if newpwd != newpwd2:
        return "❌ 两次新密码输入不一致"
    db = SQLHelper()
    user = db.fetchone("SELECT password FROM Users WHERE username=%s", (username,))
    if not user:
        db.close()
        return "❌ 用户不存在"
    if user["password"] != oldpwd:
        db.close()
        return "❌ 原密码错误，请重试"
    try:
        db.execute("UPDATE Users SET password=%s WHERE username=%s", (newpwd, username))
        db.close()
        return "✅ 密码修改成功！"
    except Exception as e:
        db.close()
        return f"❌ 修改失败：{e}"


def admin_announce(content, username):
    # 实际应写入公告表，这里模拟
    return f"✅ 公告已发布：{content[:20]}..." if content else "❌ 公告内容不能为空"


def load_simple_stat():
    db = SQLHelper()
    try:
        total = db.fetchone("SELECT COUNT(*) as n FROM Users")["n"]
        new_today = db.fetchone("SELECT COUNT(*) as n FROM Users WHERE TO_DAYS(create_time)=TO_DAYS(NOW())")["n"]
        return {"用户总数": total, "今日新用户": new_today}
    finally:
        db.close()


def require_admin(token):
    info = verify_token(token)
    if not info or not info.get("username"):
        raise gr.Error("认证失败，请重新登录！")
    # 只允许admin管理员登录，其他角色禁止访问
    if info.get("role") != "admin":
        raise gr.Error("权限不足，仅管理员可访问本页面！")
    return info


def create_admin_settings():
    with gr.Blocks(title="管理员设置页面") as page:
        token_box = gr.Textbox(visible=False)
        welcome_msg = gr.HTML("<div style='font-size:1.15em;color:#117ac9'>正在认证...</div>")
        with gr.Tabs():
            with gr.Tab("个人信息"):
                nickname = gr.Textbox(label="昵称")
                email = gr.Textbox(label="邮箱")
                phone = gr.Textbox(label="手机号")
                city = gr.Textbox(label="当前城市")
                save_btn = gr.Button("保存个人信息")
                reload_btn = gr.Button("⟳ 刷新最新数据")
                tip = gr.Markdown()
            with gr.Tab("修改密码"):
                oldpwd = gr.Textbox(label="原密码", type="password")
                newpwd = gr.Textbox(label="新密码", type="password")
                newpwd2 = gr.Textbox(label="重复新密码", type="password")
                pwd_btn = gr.Button("提交修改")
                pwd_tip = gr.Markdown()
            with gr.Tab("推送公告"):
                ann = gr.Textbox(label="公告内容", lines=4, placeholder="此公告将显示给用户")
                ann_btn = gr.Button("发布公告")
                ann_tip = gr.Markdown()
            with gr.Tab("工作台概览（简要统计）"):
                gr.Markdown("#### 你的管理面板（统计数据演示）")
                stat_box = gr.JSON(value=load_simple_stat(), label="当前数据简报")
                stat_btn = gr.Button("⟳ 刷新统计数据")
            with gr.Tab("安全提示"):
                gr.Markdown("""
                    - 请妥善保管账户及密码，勿外泄。
                    - 无需操作的高危功能请勿触碰，必要时联系系统最高管理员。
                    - 定期检查邮箱、电话等信息是否为本人，以便于取回账户或接收重要通知。
                    """
                            )

        # -------- 页面load认证（token -> 欢迎词&token流转） --------
        def load_admin_page(request: gr.Request):
            token = request.query_params.get("token", "")
            info = require_admin(token)
            username = info["username"]
            welcome = f"🛠️ 管理员，<b>{username}</b>，你好！"
            return token, welcome

        page.load(
            fn=load_admin_page,
            inputs=None,
            outputs=[token_box, welcome_msg]
        )

        # 填充信息
        def fill_info(token):
            info = require_admin(token)
            userinfo = get_admin_info(info["username"])
            return userinfo["昵称"], userinfo["邮箱"], userinfo["手机号"], userinfo["当前城市"], ""

        reload_btn.click(
            fn=fill_info,
            inputs=[token_box],
            outputs=[nickname, email, phone, city, tip]
        )

        # 保存个人信息
        def save_info(n, e, p, c, token):
            info = require_admin(token)
            return update_admin_info(n, e, p, c, info["username"])

        save_btn.click(
            fn=save_info,
            inputs=[nickname, email, phone, city, token_box],
            outputs=tip
        )

        # 修改密码
        def pwd_change(o, n1, n2, token):
            info = require_admin(token)
            return change_pwd(o, n1, n2, info["username"])

        pwd_btn.click(
            fn=pwd_change,
            inputs=[oldpwd, newpwd, newpwd2, token_box],
            outputs=pwd_tip
        )

        # 公告
        def ann_pub(content, token):
            info = require_admin(token)
            return admin_announce(content, info["username"])

        ann_btn.click(
            fn=ann_pub,
            inputs=[ann, token_box],
            outputs=ann_tip
        )
        # 工作台统计
        stat_btn.click(
            fn=load_simple_stat,
            inputs=None,
            outputs=stat_box
        )

    return page
