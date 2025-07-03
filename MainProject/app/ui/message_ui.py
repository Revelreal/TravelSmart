import gradio as gr
import pandas as pd
import logging
from typing import Dict, Any, List, Union, Optional
from MainProject.app.services.message_service import MessageService
from MainProject.app.services.friendship_service import FriendshipService


def create_message_ui(user_info_state: gr.State) -> Dict[str, gr.components.Component]:
    # 初始化服务（添加类型注解）
    message_service: MessageService = MessageService()
    friendship_service: FriendshipService = FriendshipService()
    logger: logging.Logger = logging.getLogger(__name__)

    with gr.TabItem("消息"):
        # ========== UI布局 ==========
        gr.Markdown("## 消息中心")

        with gr.Row():
            # 好友列表列（添加类型注解）
            with gr.Column(scale=1):
                with gr.Group():
                    gr.Markdown("### 好友列表")
                    friend_list: gr.DataFrame = gr.Dataframe(
                        headers=["用户名", "昵称", "状态", "未读消息"],
                        interactive=False,
                        type="pandas"  # 明确指定使用pandas格式
                    )
                    refresh_friends_btn: gr.Button = gr.Button("刷新好友列表", variant="secondary")

            # 聊天窗口列（添加类型注解）
            with gr.Column(scale=2):
                with gr.Group():
                    gr.Markdown("### 聊天窗口")
                    selected_friend: gr.State = gr.State()  # 明确类型为gr.State
                    friend_info: gr.Markdown = gr.Markdown("请从左侧选择好友开始聊天")

                    chat_history: gr.Chatbot = gr.Chatbot(
                        label="聊天记录",
                        height=400,
                        show_label=False,
                        bubble_full_width=False
                    )

                    with gr.Row():
                        message_input: gr.Textbox = gr.Textbox(
                            placeholder="输入消息...",
                            lines=2,
                            max_lines=5,
                            container=False
                        )
                        send_btn: gr.Button = gr.Button("发送", variant="primary")

                    refresh_chat_btn: gr.Button = gr.Button("刷新聊天记录", variant="secondary")

        # ========== 核心功能函数（添加完整类型注解）==========
        def load_chat_friends(user_data: Optional[Dict[str, Any]]) -> pd.DataFrame:
            """加载好友列表（严格类型处理）"""
            default_df = pd.DataFrame(
                [["请先登录", "", "", 0]],
                columns=["用户名", "昵称", "状态", "未读消息"]
            )

            if not user_data or not isinstance(user_data, dict):
                return default_df

            try:
                # 类型安全访问
                user_id = str(user_data.get("user_id", ""))
                if not user_id:
                    return default_df

                # 获取数据（添加类型转换）
                friends: List[Dict[str, Any]] = friendship_service.get_friends(user_id) or []
                unread_counts: List[Dict[str, Any]] = message_service.get_unread_message_count(user_id) or []

                # 构建安全数据结构
                unread_dict: Dict[str, int] = {
                    str(item.get("sender_id", "")): int(item.get("count", 0))
                    for item in unread_counts
                    if item and "sender_id" in item
                }

                data: List[List[Union[str, int]]] = []
                for friend in friends:
                    if not isinstance(friend, dict):
                        continue

                    friend_id = str(friend.get("friend_id", ""))
                    data.append([
                        str(friend.get("username", "")),
                        str(friend.get("nickname", "")),
                        str(friend.get("status", "")),
                        int(unread_dict.get(friend_id, 0))
                    ])

                return pd.DataFrame(
                    data,
                    columns=["用户名", "昵称", "状态", "未读消息"]
                ).fillna("")

            except Exception as e:
                logger.error(f"加载好友列表失败: {str(e)}")
                return default_df

        def select_friend(evt: gr.SelectData, friends_data, user_data):
            """选择好友并加载聊天记录（修复ID获取问题）"""
            if not user_data:
                return None, "请先登录", []

            try:
                # 获取选择的好友信息
                selected = friends_data.iloc[evt.index[0]]
                username = selected["用户名"]

                # 修复方案：直接从好友列表数据中获取friend_id（因为friends_data来自get_friends查询）
                friend_id = None
                if isinstance(selected, pd.Series) and 'friend_id' in friends_data.columns:
                    friend_id = str(selected['friend_id'])
                else:
                    # 备用方案：通过username从好友列表数据中查找
                    friends_list = friendship_service.get_friends(user_data["user_id"])
                    for friend in friends_list:
                        if friend.get("username") == username:
                            friend_id = str(friend.get("friend_id"))
                            break

                if not friend_id:
                    return None, "获取好友ID失败", []

                display_name = selected["昵称"] or selected["用户名"]

                # 加载消息记录
                messages = message_service.get_recent_messages(
                    user_id=str(user_data["user_id"]),
                    friend_id=friend_id
                )

                # 标记为已读
                message_service.mark_messages_as_read(
                    user_id=str(user_data["user_id"]),
                    friend_id=friend_id
                )

                # 格式化聊天记录
                chat = []
                for msg in messages:
                    if not isinstance(msg, dict):
                        continue

                    content = str(msg.get("content", ""))
                    if msg.get("direction") == "sent":
                        chat.append([content, None])
                    else:
                        chat.append([None, content])

                return friend_id, f"正在与 {display_name} 聊天", chat

            except Exception as e:
                logging.error(f"选择好友失败: {str(e)}")
                return None, f"加载聊天失败: {str(e)}", []

        def send_message(
                friend_id: Optional[str],
                message: str,
                chat_history: List[List[Optional[str]]],
                user_data: Optional[Dict[str, Any]]
        ) -> tuple[Optional[str], str, List[List[Optional[str]]], Optional[gr.Warning]]:
            """发送消息（严格类型处理）"""
            default_return = (None, "", chat_history, gr.Warning("系统错误"))

            if not isinstance(user_data, dict):
                return None, "", chat_history, gr.Warning("请先登录")

            if not isinstance(friend_id, str) or not friend_id:
                return None, "", chat_history, gr.Warning("请选择好友")

            try:
                # 消息处理
                clean_msg: str = str(message).strip()
                if not clean_msg:
                    return None, "", chat_history, gr.Warning("消息不能为空")

                # 发送消息（添加类型检查）
                if not hasattr(message_service, 'send_message'):
                    return None, clean_msg, chat_history, gr.Warning("服务不可用")

                success, result = message_service.send_message(
                    sender_id=str(user_data.get("user_id", "")),
                    receiver_id=friend_id,
                    content=clean_msg
                )

                if not success:
                    return None, clean_msg, chat_history, gr.Warning(str(result))

                # 更新聊天记录（确保类型安全）
                new_chat: List[List[Optional[str]]] = chat_history + [[clean_msg, None]]
                return friend_id, "", new_chat, None

            except Exception as e:
                logger.error(f"发送消息失败: {str(e)}")
                return None, str(message), chat_history, gr.Warning(f"发送失败: {str(e)}")

        def refresh_chat(
                friend_id: Optional[str],
                chat_history: List[List[Optional[str]]],
                user_data: Optional[Dict[str, Any]]
        ) -> List[List[Optional[str]]]:
            """刷新聊天（严格类型处理）"""
            if not isinstance(user_data, dict) or not isinstance(friend_id, str):
                return chat_history

            try:
                # 获取消息（添加服务检查）
                if not hasattr(message_service, 'get_recent_messages'):
                    return chat_history

                messages: List[Dict[str, Any]] = message_service.get_recent_messages(
                    user_id=str(user_data.get("user_id", "")),
                    friend_id=friend_id
                ) or []

                # 构建新记录（严格None处理）
                new_chat: List[List[Optional[str]]] = []
                for msg in messages:
                    if not isinstance(msg, dict):
                        continue

                    direction = str(msg.get("direction", ""))
                    content = str(msg.get("content", "")) if msg.get("content") is not None else ""

                    if direction == "sent":
                        new_chat.append([content, None])
                    else:
                        new_chat.append([None, content])

                return new_chat if new_chat else chat_history

            except Exception as e:
                logger.error(f"刷新聊天失败: {str(e)}")
                return chat_history

        # ========== 事件绑定 ==========
        refresh_friends_btn.click(
            fn=load_chat_friends,
            inputs=[user_info_state],
            outputs=[friend_list]
        )

        friend_list.select(
            fn=select_friend,
            inputs=[friend_list, user_info_state],
            outputs=[selected_friend, friend_info, chat_history]
        )

        message_input.submit(
            fn=send_message,
            inputs=[selected_friend, message_input, chat_history, user_info_state],
            outputs=[selected_friend, message_input, chat_history, friend_info],
            api_name="send_msg"
        )

        send_btn.click(
            fn=send_message,
            inputs=[selected_friend, message_input, chat_history, user_info_state],
            outputs=[selected_friend, message_input, chat_history, friend_info]
        )

        refresh_chat_btn.click(
            fn=refresh_chat,
            inputs=[selected_friend, chat_history, user_info_state],
            outputs=[chat_history]
        )

        user_info_state.change(
            fn=load_chat_friends,
            inputs=[user_info_state],
            outputs=[friend_list]
        )

    return {
        "friend_list": friend_list,
        "chat_history": chat_history,
        "selected_friend": selected_friend
    }