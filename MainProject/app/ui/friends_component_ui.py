# MainProject/app/ui/main_ui.py
import gradio as gr
import time
import sys


from MainProject.auth_utils import verify_token, token_querystr
from MainProject.app.ui.friendship_ui import create_friendship_ui  # 导入好友UI模块
from MainProject.app.ui.message_ui import create_message_ui  # 导入消息UI模块
from MainProject.app.ui.travel_post_ui import create_travel_post_ui  # 导入动态UI模块
from MainProject.app.ui.user_profile_ui import create_user_profile_ui  # 导入个人空间UI模块
def create_main_ui():
    """创建主界面 - 支持从URL参数获取token"""
    print("开始创建主界面...", file=sys.stderr)

    with gr.Blocks(title="旅行社交平台") as demo:
        # 全局状态存储
        print("创建全局状态变量...", file=sys.stderr)
        token_box = gr.Textbox(visible=False)
        user_info_state = gr.State(None)
        debug_output = gr.Textbox(label="调试输出", lines=10, value="应用已启动", visible=True)

        # 头部区域
        with gr.Row():
            gr.Markdown("# 旅行社交平台")
            userbar = gr.HTML("未登录", elem_classes="userbar-text")

        # 主标签页
        with gr.Tabs() as main_tabs:
            # 登录测试标签页
            with gr.TabItem("登录测试"):
                gr.Markdown("## 登录测试")

                # Token输入区域
                token_input = gr.Textbox(label="输入Token", placeholder="请输入JWT token")
                verify_btn = gr.Button("验证Token")
                login_status = gr.Markdown("未登录")

                def verify_token_and_login(token_text):
                    print(f"验证token: {token_text[:10] if token_text else '无'}", file=sys.stderr)
                    try:
                        if not token_text:
                            return None, token_text, "未提供token", "未提供token"

                        user_data = verify_token(token_text)
                        if not user_data:
                            return None, token_text, "Token验证失败或已过期", "Token验证失败或已过期"

                        # 确保user_data包含user_id字段
                        if "id" in user_data and "user_id" not in user_data:
                            user_data["user_id"] = user_data["id"]

                        print(f"验证成功: {user_data}", file=sys.stderr)
                        username = user_data.get("username", "用户")
                        welcome_html = f"<b>👤 {username}</b> 已登录"
                        return user_data, token_text, welcome_html, f"验证成功: {user_data['username']}"
                    except Exception as e:
                        print(f"验证出错: {str(e)}", file=sys.stderr)
                        return None, token_text, "未登录", f"验证出错: {str(e)}"

                verify_btn.click(
                    fn=verify_token_and_login,
                    inputs=[token_input],
                    outputs=[user_info_state, token_box, userbar, login_status]
                )

                # 模拟登录按钮
                manual_login_btn = gr.Button("模拟登录")

                def simulate_login():
                    test_user = {
                        "id": "1",
                        "user_id": "1",
                        "username": "test_user",
                        "role": "user",
                        "exp": int(time.time()) + 3600
                    }
                    username = test_user.get("username", "用户")
                    welcome_html = f"<b>👤 {username}</b> 已登录"
                    return test_user, "test_token", welcome_html, f"模拟登录成功: {test_user['username']}"

                manual_login_btn.click(
                    fn=simulate_login,
                    outputs=[user_info_state, token_box, userbar, login_status]
                )

                # 添加生成链接功能
                gr.Markdown("### 生成带Token的链接")
                page_select = gr.Dropdown(
                    choices=["首页", "好友", "消息", "旅行动态", "个人中心"],
                    label="选择页面",
                    value="首页"
                )
                generated_link = gr.Textbox(label="生成的链接")

                def generate_link(page, token):
                    if not token:
                        return "请先登录获取token"

                    token_query = token_querystr(token)
                    base_url = f"http://localhost:7862/{page}"
                    return f"{base_url}{token_query}"

                gen_link_btn = gr.Button("生成链接")
                gen_link_btn.click(
                    fn=generate_link,
                    inputs=[page_select, token_box],
                    outputs=generated_link
                )

            # 使用模块化的好友标签页
            create_friendship_ui(user_info_state)

            # 使用模块化的消息标签页
            create_message_ui(user_info_state)

            # 使用模块化的动态标签页
            create_travel_post_ui(user_info_state)

            # 使用模块化的个人中心标签页
            create_user_profile_ui(user_info_state)

        # 页脚
        gr.HTML("<div style='text-align:center;color:#97a;margin-top:30px;'>© 2024 旅行社交平台</div>")

        # 从URL加载token并验证
        def load_from_url(request: gr.Request):
            try:
                token = request.query_params.get("token", "")
                print(f"从URL获取token: {token[:10] if token else '无'}", file=sys.stderr)

                if not token:
                    return None, "", "未登录", "URL中未提供token"

                user_data = verify_token(token)
                if not user_data:
                    return None, token, "登录已过期", "URL中的token验证失败或已过期"

                if "id" in user_data and "user_id" not in user_data:
                    user_data["user_id"] = user_data["id"]

                username = user_data.get("username", "用户")
                welcome_html = f"<b>👤 {username}</b> 已登录"
                print(f"URL token验证成功: {user_data}", file=sys.stderr)

                return user_data, token, welcome_html, f"URL token验证成功: {user_data['username']}"
            except Exception as e:
                print(f"URL token处理出错: {str(e)}", file=sys.stderr)
                return None, "", "未登录", f"URL token处理出错: {str(e)}"

        demo.load(
            fn=load_from_url,
            inputs=None,
            outputs=[user_info_state, token_box, userbar, debug_output]
        )

    print("主界面创建完成", file=sys.stderr)
    return demo


if __name__ == "__main__":
    print("开始启动应用...", file=sys.stderr)
    app = create_main_ui()
    print("应用创建完成，准备启动...", file=sys.stderr)
    try:
        app.launch(debug=True, show_error=True, server_port=7862)
        print("应用已启动", file=sys.stderr)
    except Exception as e:
        print(f"启动失败: {str(e)}", file=sys.stderr)