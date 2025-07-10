# MainProject/app/ui/friends_component_ui.py
import gradio as gr
import sys

from MainProject.auth_utils import verify_token
from MainProject.app.ui.friendship_ui import create_friendship_ui  # 导入好友UI模块
from MainProject.app.ui.message_ui import create_message_ui  # 导入消息UI模块
from MainProject.app.ui.travel_post_ui import create_travel_post_ui  # 导入动态UI模块
from MainProject.app.ui.user_profile_ui import create_user_profile_ui  # 导入个人空间UI模块


def create_main_ui():
    """创建主界面 - 支持从URL参数获取token"""
    print("开始创建主界面...", file=sys.stderr)

    with gr.Blocks(title="TravelSmart 社交平台") as demo:
        # 全局状态存储
        print("创建全局状态变量...", file=sys.stderr)
        token_box = gr.Textbox(visible=False)
        user_info_state = gr.State(None)

        # 头部区域
        with gr.Row():
            gr.Markdown("# 旅行社交平台")
            userbar = gr.HTML("未登录", elem_classes="userbar-text")

        # 主标签页
        with gr.Tabs():
            # 使用模块化的好友标签页
            create_friendship_ui(user_info_state)

            # 使用模块化的消息标签页
            create_message_ui(user_info_state)

            # 使用模块化的动态标签页
            create_travel_post_ui(user_info_state)

            # 使用模块化的个人中心标签页
            create_user_profile_ui(user_info_state)

        # 页脚
        gr.HTML("<div style='text-align:center;color:#97a;margin-top:30px;'>© 2024 TravelSmart 旅行社交平台</div>")

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

                return user_data, token, welcome_html
            except Exception as m_e:
                print(f"URL token处理出错: {str(m_e)}", file=sys.stderr)
                return None, "", "未登录"

        demo.load(
            fn=load_from_url,
            inputs=None,
            outputs=[user_info_state, token_box, userbar]
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
