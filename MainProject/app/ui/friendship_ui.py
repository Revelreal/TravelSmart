# MainProject/app/ui/friendship_ui.py
import gradio as gr
from MainProject.app.services.friendship_service import FriendshipService


def create_friendship_ui(user_info_state):
    """创建好友关系UI组件"""
    friendship_service = FriendshipService()

    with gr.TabItem("好友"):
        gr.Markdown("## 好友关系")

        with gr.Row():
            with gr.Column(scale=2):
                with gr.Group():
                    gr.Markdown("### 我的好友")
                    friend_list = gr.Dataframe(
                        headers=["用户名", "昵称", "状态", "操作"],
                        row_count=10,
                        col_count=(4, "fixed"),
                        interactive=False
                    )
                    refresh_friends_btn = gr.Button("刷新好友列表")

                with gr.Group():
                    gr.Markdown("### 好友请求")
                    request_list = gr.Dataframe(
                        headers=["用户名", "昵称", "请求时间", "操作"],
                        row_count=5,
                        col_count=(4, "fixed"),
                        interactive=False
                    )
                    refresh_requests_btn = gr.Button("刷新好友请求")

            with gr.Column(scale=1):
                with gr.Group():
                    gr.Markdown("### 添加好友")
                    username_input = gr.Textbox(label="用户名")
                    add_friend_btn = gr.Button("发送好友请求")
                    add_result = gr.Textbox(label="结果")

                with gr.Group():
                    gr.Markdown("### 好友操作")
                    friend_username = gr.Textbox(label="好友用户名")
                    action = gr.Radio(["接受请求", "拒绝请求", "删除好友", "屏蔽用户"], label="操作")
                    action_btn = gr.Button("执行")
                    action_result = gr.Textbox(label="结果")

                with gr.Group():
                    gr.Markdown("### 已屏蔽用户")
                    blocked_list = gr.Dataframe(
                        headers=["用户名", "昵称", "屏蔽时间"],
                        row_count=5,
                        col_count=(3, "fixed"),
                        interactive=False
                    )
                    refresh_blocked_btn = gr.Button("刷新屏蔽列表")
                    unblock_username = gr.Textbox(label="解除屏蔽的用户名")
                    unblock_btn = gr.Button("解除屏蔽")
                    unblock_result = gr.Textbox(label="结果")

        # 加载所有数据按钮
        load_all_btn = gr.Button("加载所有数据")

    # 定义所有交互函数
    def load_friends(user_data):
        if not user_data:
            return [["请先登录", "", "", ""]]

        try:
            friends = friendship_service.get_friends(user_data["user_id"])
            return [[
                f.get("username"),
                f.get("nickname") or "",
                f.get("status"),
                "删除" if f.get("status") == "accepted" else "接受/拒绝"
            ] for f in friends]
        except Exception as e:
            return [[f"错误: {str(e)}", "", "", ""]]

    def load_friend_requests(user_data):
        if not user_data:
            return [["请先登录", "", "", ""]]

        try:
            requests_data = friendship_service.get_friend_requests(user_data["user_id"])
            return [[
                r.get("username"),
                r.get("nickname") or "",
                r.get("created_at"),
                "接受/拒绝"
            ] for r in requests_data]
        except Exception as e:
            return [[f"错误: {str(e)}", "", "", ""]]

    def send_friend_request(username, user_data):
        if not user_data:
            return "请先登录"
        if not username:
            return "请输入用户名"

        try:
            friend = friendship_service.db.get_user_by_username(username)
            if not friend:
                return "用户不存在"

            success, message = friendship_service.send_friend_request(
                user_data["user_id"], friend["id"]
            )
            return message
        except Exception as e:
            return f"错误: {str(e)}"

    def perform_friend_action(username, action, user_data):
        if not user_data:
            return "请先登录"
        if not username:
            return "请输入好友用户名"

        try:
            friend = friendship_service.db.get_user_by_username(username)
            if not friend:
                return "用户不存在"

            if action == "接受请求":
                request = friendship_service.db.fetchone(
                    "SELECT id FROM Friendships WHERE user_id=%s AND friend_id=%s AND status='pending'",
                    (friend["id"], user_data["user_id"])
                )
                if not request:
                    return "未找到该用户的好友请求"

                success, message = friendship_service.accept_friend_request(
                    request["id"], user_data["user_id"]
                )
            elif action == "拒绝请求":
                request = friendship_service.db.fetchone(
                    "SELECT id FROM Friendships WHERE user_id=%s AND friend_id=%s AND status='pending'",
                    (friend["id"], user_data["user_id"])
                )
                if not request:
                    return "未找到该用户的好友请求"

                success, message = friendship_service.reject_friend_request(
                    request["id"], user_data["user_id"]
                )
            elif action == "删除好友":
                success, message = friendship_service.remove_friend(
                    user_data["user_id"], friend["id"]
                )
            elif action == "屏蔽用户":
                success, message = friendship_service.block_user(
                    user_data["user_id"], friend["id"]
                )
            else:
                return "未知操作"

            return message
        except Exception as e:
            return f"错误: {str(e)}"

    def load_blocked_users(user_data):
        if not user_data:
            return [["请先登录", "", ""]]

        try:
            blocked = friendship_service.get_blocked_users(user_data["user_id"])
            return [[
                b.get("username"),
                b.get("nickname") or "",
                b.get("created_at")
            ] for b in blocked]
        except Exception as e:
            return [[f"错误: {str(e)}", "", ""]]

    def unblock_user(username, user_data):
        if not user_data:
            return "请先登录"
        if not username:
            return "请输入用户名"

        try:
            friend = friendship_service.db.get_user_by_username(username)
            if not friend:
                return "用户不存在"

            success, message = friendship_service.unblock_user(
                user_data["user_id"], friend["id"]
            )
            return message
        except Exception as e:
            return f"错误: {str(e)}"

    def load_all_data(user_data):
        if not user_data:
            return ([["请先登录", "", "", ""]],
                    [["请先登录", "", "", ""]],
                    [["请先登录", "", ""]])

        try:
            friends = friendship_service.get_friends(user_data["user_id"])
            friend_data = [[
                f.get("username"),
                f.get("nickname") or "",
                f.get("status"),
                "删除" if f.get("status") == "accepted" else "接受/拒绝"
            ] for f in friends]

            requests_data = friendship_service.get_friend_requests(user_data["user_id"])
            request_data = [[
                r.get("username"),
                r.get("nickname") or "",
                r.get("created_at"),
                "接受/拒绝"
            ] for r in requests_data]

            blocked = friendship_service.get_blocked_users(user_data["user_id"])
            blocked_data = [[
                b.get("username"),
                b.get("nickname") or "",
                b.get("created_at")
            ] for b in blocked]

            return friend_data, request_data, blocked_data
        except Exception as e:
            error_msg = [[f"错误: {str(e)}", "", "", ""]]
            return error_msg, error_msg, [[f"错误: {str(e)}", "", ""]]

    # 绑定交互事件
    refresh_friends_btn.click(load_friends, inputs=[user_info_state], outputs=friend_list)
    refresh_requests_btn.click(load_friend_requests, inputs=[user_info_state], outputs=request_list)
    add_friend_btn.click(send_friend_request, inputs=[username_input, user_info_state], outputs=add_result)
    action_btn.click(perform_friend_action, inputs=[friend_username, action, user_info_state], outputs=action_result)
    refresh_blocked_btn.click(load_blocked_users, inputs=[user_info_state], outputs=blocked_list)
    unblock_btn.click(unblock_user, inputs=[unblock_username, user_info_state], outputs=unblock_result)
    load_all_btn.click(load_all_data, inputs=[user_info_state], outputs=[friend_list, request_list, blocked_list])

    return {
        "friend_list": friend_list,
        "request_list": request_list,
        "blocked_list": blocked_list
    }