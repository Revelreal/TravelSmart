# app/homepage/settings.py
import gradio as gr


def settings_page():
    def logout_action():
        # 确认退出登录逻辑 todo
        return "✅ 退出登录成功，1秒后将回到登录页。<script>setTimeout(()=>{window.location='/welcome/login';},1000);</script>"

    def delete_account_action(username):
        if not username:
            return "❌ 请输入用户名"
        # 这里可调用后端数据库删除逻辑
        return f"✅ 用户 {username} 注销成功！<script>setTimeout(()=>{{window.location='/welcome/login';}},1200);</script>"

    def save_profile(name, email):
        # 这里写入数据库保存逻辑
        if name and email:
            return "✅ 保存成功！"
        else:
            return "❌ 请填写完整信息"

    # 侧边tab顺序决定初始
    with gr.Blocks(title="设置与帮助中心") as demo:
        with gr.Tabs():
            # 基础设置
            with gr.TabItem("基础信息"):
                gr.Markdown("### 👤 基础信息")
                with gr.Row():
                    name = gr.Textbox(label="昵称", value="张三", info="你的昵称可在个人主页展示")
                    email = gr.Textbox(label="电子邮箱", value="zhangsan@example.com", info="用于找回密码/通知")
                btn_save = gr.Button("保存信息")
                save_msg = gr.Markdown()
                btn_save.click(save_profile, [name, email], save_msg)

            # 安全与密码
            with gr.TabItem("安全设置"):
                gr.Markdown("""### 🔒 安全设置  
                                    - 修改密码
                                    - 管理两步验证
                                    - 查看登录记录""")
                old_pwd = gr.Textbox(label="当前密码", type="password")
                new_pwd1 = gr.Textbox(label="新密码", type="password")
                new_pwd2 = gr.Textbox(label="确认新密码", type="password")
                change_btn = gr.Button("修改密码")
                change_msg = gr.Markdown()

                def change_password(old, new1, new2):
                    if not old or not new1 or not new2:
                        return "❌ 请填写所有字段"
                    if new1 != new2:
                        return "❌ 两次新密码不一致"
                    # 这里加验证原密码、更新密码等逻辑
                    # todo
                    return "✅ 密码修改成功！"

                change_btn.click(change_password, [old_pwd, new_pwd1, new_pwd2], change_msg)

            # 退出登录
            with gr.TabItem("退出登录"):
                gr.Markdown("### 🚪 退出登录")
                btn_logout = gr.Button("退出登录")
                logout_msg = gr.Markdown()
                btn_logout.click(logout_action, outputs=logout_msg)

            # 注销账号
            with gr.TabItem("注销账号"):
                gr.Markdown("""### ❌ 注销账号  
                                请谨慎操作，注销将永久删除数据且不可恢复。""")
                del_user = gr.Textbox(label="请输入昵称以确认")
                btn_delete = gr.Button("确认注销")
                del_msg = gr.Markdown()
                btn_delete.click(delete_account_action, [del_user], del_msg)

            # 帮助中心
            with gr.TabItem("帮助中心"):
                gr.Markdown("""### 🧭 帮助中心  
                                **1. 如何修改个人信息？**  
                                在“基础信息”标签页修改并点击保存。  
                                
                                **2. 如何更改密码？**  
                                前往“安全设置”标签页。  
                                
                                **3. 忘记密码怎么办？**  
                                请在登录页点击“忘记密码”，发送找回邮件至注册邮箱。
                                
                                **4. 如何联系客服？**  
                                见下方联系我们。
                                """)

            # 关于产品
            with gr.TabItem("关于产品"):
                gr.Markdown("""
                            ### ℹ️ 关于  
                            TravelSmart 智能出行 — 提供个性化出行及智能推荐服务。  
                            版本：v1.0.0  
                            开源地址：[GitHub](https://github.com/your-repo)
                                            """)

            # 服务条款
            with gr.TabItem("服务条款"):
                gr.Markdown("""
                            ### 📃 服务条款  
                            使用本平台须同意并遵守相关法律法规，不得利用平台从事违法活动。更多内容请参见官网条款...  
                                            """)

            # 联系我们
            with gr.TabItem("联系我们"):
                gr.Markdown("""
                            ### 📞 联系方式  
                            - 邮箱：contact@travelsmart.com  
                            - 微信公众号：TravelSmart出行  
                            - 客服热线：400-800-9988
                                            """)
    return demo
