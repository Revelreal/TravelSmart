import gradio as gr


def settings_page():
    def logout_action():
        # 这里可以处理后端登出逻辑，前端自动跳登录页
        return "✅ 退出登录成功，1秒后将回到登录页。<script>setTimeout(()=>{window.location='/welcome/login';},1000);</script>"

    def delete_account_action(username):
        # 实际应做数据库删除等操作
        if not username:
            return "❌ 请输入用户名"
        # 这里可调用DBHelper删除账号
        # db.delete_user(username)
        return f"✅ 用户 {username} 注销成功，欢迎下次注册！<script>setTimeout(()=>{{window.location='/welcome/login';}},1200);</script>"

    with gr.Blocks(title="设置与帮助中心") as demo:
        with gr.Tabs():
            with gr.TabItem("基础设置"):
                gr.Markdown("### ⚙️ 基础设置\n（此处可添加个性化设置表单等）")
                gr.Markdown("> 示例：这里可编辑邮箱、手机号、头像、通知开关等。")

            with gr.TabItem("退出登录"):
                gr.Markdown("### 🚪 退出登录")
                btn_logout = gr.Button("退出登录")
                logout_msg = gr.Markdown("")
                btn_logout.click(logout_action, outputs=logout_msg)

            with gr.TabItem("注销账号"):
                gr.Markdown("### ❌ 注销账号")
                username = gr.Textbox(label="确认用户名", placeholder="请输入要注销的账号")
                btn_delete = gr.Button("确认注销")
                delete_msg = gr.Markdown("")
                btn_delete.click(delete_account_action, [username], delete_msg)
                gr.Markdown(
                    """<span style="color:#e26a6a;">注意：此操作不可撤销，注销将永久删除所有数据！</span>"""
                )

            with gr.TabItem("帮助"):
                gr.Markdown("### 🧭 帮助\n - 常见问题：<br>1. 如何注册？2. 如何重置密码？...")

            with gr.TabItem("关于"):
                gr.Markdown("### ℹ️ 关于\n本产品由 TravelSmart 团队开发，开源地址：https://github.com/your-repo")

            with gr.TabItem("服务条款"):
                gr.Markdown("### 📃 服务条款\n请你阅读并同意完整的服务条款...")

            with gr.TabItem("联系我们"):
                gr.Markdown(
                    "### 📞 联系我们\n邮箱：contact@travelsmart.com<br>客服电话：400-800-xxxx"
                )

    return demo
