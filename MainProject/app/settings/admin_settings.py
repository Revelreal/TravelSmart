# MainProject/app/settings/admin_settings.py
import gradio as gr
from MainProject.dbhelper.SQLHelper import SQLHelper


def get_admin_info(username="admin001"):
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
            "用户名": username,
            "昵称": "", "邮箱": "", "手机号": "", "当前城市": ""
        }


def update_admin_info(nickname, email, phone, city, username="admin001"):
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


def change_pwd(oldpwd, newpwd, newpwd2, username="admin001"):
    if not oldpwd or not newpwd or not newpwd2:
        return "❌ 全部字段不能为空"
    if newpwd != newpwd2:
        return "❌ 两次新密码输入不一致"
    db = SQLHelper()
    user = db.fetchone("SELECT password FROM Users WHERE username=%s", (username,))
    if not user:
        db.close()
        return "❌ 用户不存在"
    # 生产环境应做hash对比，这里明文举例
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


def admin_announce(content, username="admin001"):
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


def admin_settings():
    username = "admin001"  # 实际项目应用session/State传参

    def reload_info():
        # 用于点击刷新按钮和初始页面加载
        info = get_admin_info(username)
        return info["昵称"], info["邮箱"], info["手机号"], info["当前城市"], "✅ 数据已更新"

    with gr.Blocks() as page:
        gr.Markdown("## 🛠️ 管理员设置面板")

        with gr.Tab("个人信息"):
            nickname = gr.Textbox(label="昵称")
            email = gr.Textbox(label="邮箱")
            phone = gr.Textbox(label="手机号")
            city = gr.Textbox(label="当前城市")
            save_btn = gr.Button("保存个人信息")
            reload_btn = gr.Button("⟳ 刷新最新数据", elem_id="refresh_btn")
            tip = gr.Markdown()

            # 数据自动填充
            def fill_info():
                info = get_admin_info(username)
                return info["昵称"], info["邮箱"], info["手机号"], info["当前城市"], ""

            nickname.value, email.value, phone.value, city.value, _ = fill_info()
            # 保存按钮绑定
            save_btn.click(
                lambda n, e, p, c: update_admin_info(n, e, p, c, username),
                inputs=[nickname, email, phone, city],
                outputs=tip
            )
            # 刷新按钮
            reload_btn.click(
                reload_info,
                inputs=None,
                outputs=[nickname, email, phone, city, tip]
            )

        with gr.Tab("修改密码"):
            oldpwd = gr.Textbox(label="原密码", type="password")
            newpwd = gr.Textbox(label="新密码", type="password")
            newpwd2 = gr.Textbox(label="重复新密码", type="password")
            pwd_btn = gr.Button("提交修改")
            pwd_tip = gr.Markdown()
            pwd_btn.click(
                lambda o, n1, n2: change_pwd(o, n1, n2, username),
                inputs=[oldpwd, newpwd, newpwd2],
                outputs=pwd_tip
            )

        with gr.Tab("推送公告"):
            ann = gr.Textbox(label="公告内容", lines=4, placeholder="此公告将显示给用户")
            ann_btn = gr.Button("发布公告")
            ann_tip = gr.Markdown()
            ann_btn.click(
                lambda x: admin_announce(x, username),
                inputs=ann,
                outputs=ann_tip
            )

        with gr.Tab("工作台概览（简要统计）"):
            gr.Markdown("#### 你的管理面板（统计数据演示）")
            stat_box = gr.JSON(value=load_simple_stat(), label="当前数据简报")
            stat_btn = gr.Button("⟳ 刷新统计数据")
            # 动态刷新
            stat_btn.click(
                load_simple_stat,
                inputs=None,
                outputs=stat_box
            )

        with gr.Tab("安全提示"):
            gr.Markdown(
                """
                - 请妥善保管账户及密码，勿外泄。
                - 无需操作的高危功能请勿触碰，必要时联系系统最高管理员。
                - 定期检查邮箱、电话等信息是否为本人，以便于取回账户或接收重要通知。
                """
            )
    return page
