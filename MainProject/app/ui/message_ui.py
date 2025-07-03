# MainProject/app/ui/message_ui.py
import gradio as gr
import logging
import time
from typing import Dict

import pandas as pd

from MainProject.app.services.message_service import MessageService
from MainProject.app.services.friendship_service import FriendshipService


def create_message_ui(user_info_state: gr.State) -> Dict[str, gr.components.Component]:
    # 初始化服务
    message_service: MessageService = MessageService()
    friendship_service: FriendshipService = FriendshipService()
    logger: logging.Logger = logging.getLogger(__name__)

    with gr.TabItem("消息"):
        # ========== UI布局 ==========
        gr.Markdown("## 消息中心")

        # 状态变量
        selected_friend = gr.State(None)
        last_update_time = gr.State(time.time())
        auto_refresh = gr.State(True)
        view_mode = gr.State("list")  # "list" 或 "chat"

        # 响应式布局
        with gr.Row():
            # 左侧面板 - 好友列表/聊天列表
            with gr.Column(scale=1, elem_id="message-left-panel"):
                # 顶部导航栏
                with gr.Row(elem_id="message-nav"):
                    back_btn = gr.Button("← 返回", visible=False, elem_id="back-btn")
                    title_md = gr.Markdown("### 最近消息", elem_id="message-title")

                # 搜索框
                search_box = gr.Textbox(
                    placeholder="搜索好友...",
                    show_label=False,
                    elem_id="friend-search"
                )

                # 使用DataFrame代替HTML组件
                friend_df = gr.DataFrame(
                    value=pd.DataFrame(columns=["friend_id", "name", "preview", "time", "unread"]),
                    headers=["好友", "预览", "时间", "未读"],  # 4个表头
                    col_count=(4, "fixed"),  # 修改为显示4列，与headers匹配
                    interactive=False,
                    elem_id="friend-dataframe"
                )
                # 底部工具栏
                with gr.Row(elem_id="message-toolbar"):
                    refresh_btn = gr.Button("🔄 刷新", variant="secondary")
                    show_friends_btn = gr.Button("👥 好友列表", variant="secondary")

            # 右侧面板 - 聊天窗口
            with gr.Column(scale=2, elem_id="message-right-panel"):
                # 聊天头部
                with gr.Row(elem_id="chat-header"):
                    friend_info = gr.Markdown("请选择好友开始聊天", elem_id="friend-info")

                # 使用Chatbot组件代替HTML
                chat_history = gr.Chatbot(
                    value=[],
                    elem_id="chat-history",
                    height=400,
                    bubble_full_width=False,
                    show_label=False
                )

                # 消息输入区
                with gr.Group(elem_id="message-input-area"):
                    with gr.Row():
                        message_input = gr.Textbox(
                            placeholder="输入消息...",
                            show_label=False,
                            lines=3,
                            max_lines=8,
                            elem_id="message-input"
                        )
                        send_btn = gr.Button("发送", variant="primary", elem_id="send-btn")

                # 底部工具栏
                with gr.Row(elem_id="chat-toolbar"):
                    auto_refresh_toggle = gr.Checkbox(
                        label="自动刷新",
                        value=True,
                        interactive=True,
                        elem_id="auto-refresh"
                    )
                    manual_refresh_btn = gr.Button("刷新聊天", variant="secondary")

        # 自定义CSS
        gr.HTML("""
                <style>
                    /* 整体布局 */
                    #message-left-panel, #message-right-panel {
                        border: 1px solid #e0e0e0;
                        border-radius: 8px;
                        padding: 0 !important;
                        height: 600px;
                        display: flex;
                        flex-direction: column;
                        overflow: hidden;
                    }
                
                    /* 导航栏 */
                    #message-nav, #chat-header {
                        padding: 10px 15px;
                        border-bottom: 1px solid #e0e0e0;
                    }
                
                    /* 搜索框 */
                    #friend-search {
                        margin: 10px;
                    }
                
                    /* 好友列表样式 */
                    #friend-dataframe {
                        flex: 1;
                        overflow-y: auto;
                    }
                    #friend-dataframe table {
                        width: 100%;
                        border-collapse: collapse;
                    }
                    #friend-dataframe tr {
                        cursor: pointer;
                        transition: background-color 0.2s;
                    }
                    #friend-dataframe tr:hover {
                        background-color: #f5f5f5;
                    }
                    #friend-dataframe tr.active {
                        background-color: #e6f7ff;
                    }
                
                    /* 未读消息样式 */
                    .unread-badge {
                        border-radius: 10px;
                        padding: 0 6px;
                        font-size: 12px;
                        min-width: 18px;
                        text-align: center;
                    }
                
                    /* 移动端适配 */
                    @media (max-width: 768px) {
                        #message-left-panel.chat-view {
                            display: none;
                        }
                        #message-right-panel.list-view {
                            display: none;
                        }
                    }
                </style>
                """)

        # ========== 核心功能函数 ==========
        def format_time(timestamp):
            """格式化时间显示"""
            if not timestamp:
                return ""

            # 如果是字符串，尝试转换为时间对象
            if isinstance(timestamp, str):
                try:
                    from datetime import datetime
                    timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                except:
                    return timestamp

            # 获取当前时间
            from datetime import datetime
            now = datetime.now()

            # 如果是今天的消息，只显示时间
            if timestamp.date() == now.date():
                return timestamp.strftime("%H:%M")
            # 如果是昨天的消息
            elif (now.date() - timestamp.date()).days == 1:
                return "昨天 " + timestamp.strftime("%H:%M")
            # 如果是今年的消息
            elif timestamp.year == now.year:
                return timestamp.strftime("%m-%d %H:%M")
            # 其他情况显示完整日期
            else:
                return timestamp.strftime("%Y-%m-%d %H:%M")

        def load_chat_messages(friend_id, user_data):
            """加载聊天记录"""
            if not user_data or not friend_id:
                return []

            try:
                user_id = str(user_data.get("user_id", ""))

                # 获取消息记录
                messages = message_service.get_recent_messages(user_id, friend_id, limit=50)

                # 标记为已读
                message_service.mark_messages_as_read(user_id, friend_id)

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

                return chat
            except Exception as e:
                logger.error(f"加载聊天记录失败: {str(e)}")
                return [[f"加载失败: {str(e)}", None]]

        def load_friend_dataframe(user_data, mode="recent"):
            """加载好友列表DataFrame"""
            if not user_data:
                return pd.DataFrame(columns=["friend_id", "name", "preview", "time", "unread"])

            try:
                user_id = str(user_data.get("user_id", ""))

                # 获取好友列表
                friends = friendship_service.get_friends(user_id) or []
                friends_dict = {str(f.get("friend_id")): f for f in friends if f}

                # 获取未读消息数
                unread_counts = message_service.get_unread_message_count(user_id) or []
                unread_dict = {str(item.get("sender_id", "")): int(item.get("count", 0))
                               for item in unread_counts if item}

                data = []

                if mode == "recent":
                    # 获取有过对话的用户ID列表
                    conversation_user_ids = message_service.get_conversation_users(user_id)

                    # 首先添加有未读消息的好友
                    unread_friends = []
                    for friend_id, count in unread_dict.items():
                        if count > 0 and friend_id in friends_dict:
                            unread_friends.append(friend_id)

                    # 然后添加最近聊天的好友
                    recent_friends = [uid for uid in conversation_user_ids
                                      if uid in friends_dict and uid not in unread_friends]

                    # 合并列表，确保未读消息的好友排在前面
                    chat_order = unread_friends + recent_friends

                    # 如果没有聊天记录，显示所有好友
                    if not chat_order:
                        chat_order = [str(f.get("friend_id")) for f in friends if f]

                    # 生成数据
                    for friend_id in chat_order:
                        if friend_id not in friends_dict:
                            continue

                        friend = friends_dict[friend_id]
                        name = friend.get("nickname") or friend.get("username") or "用户"
                        unread = unread_dict.get(friend_id, 0)

                        # 获取最后一条消息预览
                        last_message = "暂无消息"
                        last_time = ""
                        messages = message_service.get_recent_messages(user_id, friend_id, limit=1)
                        if messages:
                            last_message = messages[0].get("content", "")[:20]
                            last_time = format_time(messages[0].get("created_at"))

                        data.append({
                            "friend_id": friend_id,
                            "name": name,
                            "preview": last_message,
                            "time": last_time,
                            "unread": unread
                        })
                else:
                    # 显示所有好友
                    for friend in friends:
                        if not friend:
                            continue

                        friend_id = str(friend.get("friend_id", ""))
                        name = friend.get("nickname") or friend.get("username") or "用户"
                        status = friend.get("status", "")

                        data.append({
                            "friend_id": friend_id,
                            "name": name,
                            "preview": status,
                            "time": "",
                            "unread": unread_dict.get(friend_id, 0)
                        })

                # 创建DataFrame
                df = pd.DataFrame(data)
                if len(df) > 0:
                    # 隐藏friend_id列，但保留数据
                    visible_df = df[["name", "preview", "time", "unread"]]
                    return df
                else:
                    return pd.DataFrame(columns=["friend_id", "name", "preview", "time", "unread"])

            except Exception as e:
                logger.error(f"加载好友列表失败: {str(e)}")
                return pd.DataFrame(columns=["friend_id", "name", "preview", "time", "unread"])

        def send_message_handler(friend_id, message, user_data):
            """发送消息处理函数"""
            if not user_data:
                return friend_id, "", []  # 返回空列表而不是HTML

            if not friend_id:
                return friend_id, "", []  # 返回空列表而不是HTML

            try:
                # 消息处理
                clean_msg = str(message).strip()
                if not clean_msg:
                    return friend_id, "", gr.update()

                # 发送消息
                success, result = message_service.send_message(
                    sender_id=str(user_data.get("user_id", "")),
                    receiver_id=friend_id,
                    content=clean_msg
                )

                if not success:
                    # 返回错误消息
                    return friend_id, message, [[f"发送失败: {result}", None]]

                # 重新加载聊天记录
                messages = message_service.get_recent_messages(
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

                return friend_id, "", chat
            except Exception as e:
                logger.error(f"发送消息失败: {str(e)}")
                return friend_id, message, [[f"发送失败: {str(e)}", None]]

        def select_friend_handler(evt: gr.SelectData, df, user_data):
            """选择好友处理函数"""
            if not user_data or df.empty:
                return None, "请先登录", [], gr.update(visible=True), gr.update(visible=False), "chat", "返回"

            try:
                # 从DataFrame获取选中行的friend_id
                selected_row = df.iloc[evt.index[0]]
                friend_id = selected_row["friend_id"]

                if not friend_id:
                    return None, "请选择好友", [], gr.update(visible=True), gr.update(visible=False), "chat", "返回"

                # 获取好友信息
                name = selected_row["name"]

                # 加载聊天记录
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

                # 在移动端切换到聊天视图
                return friend_id, f"### {name}", chat, gr.update(visible=True), gr.update(visible=False), "chat", "返回"
            except Exception as e:
                logger.error(f"选择好友失败: {str(e)}")
                return None, f"加载失败: {str(e)}", [], gr.update(visible=True), gr.update(visible=False), "chat", "返回"

        def back_to_list():
            """返回到消息列表"""
            return None, "请选择好友开始聊天", [], gr.update(visible=False), gr.update(visible=True), "list", "最近消息"

        def auto_refresh_handler(friend_id, user_data, auto_refresh, last_update):
            """自动刷新处理函数"""
            current_time = time.time()

            # 如果不需要自动刷新或者没有选择好友，返回原样
            if not auto_refresh or not friend_id or not user_data:
                return gr.update(), current_time

            # 如果距离上次更新不到5秒，不更新
            if current_time - last_update < 5:
                return gr.update(), last_update

            try:
                # 重新加载聊天记录
                return load_chat_messages(friend_id, user_data), current_time
            except Exception as e:
                logger.error(f"自动刷新失败: {str(e)}")
                return gr.update(), current_time

        def search_friends(query, user_data, view_mode):
            """搜索好友"""
            if not user_data:
                return gr.update()

            try:
                # 如果搜索框为空，加载默认列表
                if not query:
                    return load_friend_dataframe(user_data, "recent" if view_mode == "list" else "friends")

                user_id = str(user_data.get("user_id", ""))

                # 获取好友列表
                friends = friendship_service.get_friends(user_id) or []

                # 过滤符合搜索条件的好友
                filtered_friends = []
                for friend in friends:
                    if not friend:
                        continue

                    name = friend.get("nickname") or friend.get("username") or ""
                    if query.lower() in name.lower():
                        filtered_friends.append(friend)

                # 构建数据
                data = []
                for friend in filtered_friends:
                    friend_id = str(friend.get("friend_id", ""))
                    name = friend.get("nickname") or friend.get("username") or "用户"

                    data.append({
                        "friend_id": friend_id,
                        "name": name,
                        "preview": "点击开始聊天",
                        "time": "",
                        "unread": 0
                    })

                # 创建DataFrame
                df = pd.DataFrame(data)
                if len(df) == 0:
                    df = pd.DataFrame(columns=["friend_id", "name", "preview", "time", "unread"])

                return df
            except Exception as e:
                logger.error(f"搜索好友失败: {str(e)}")
                return pd.DataFrame(columns=["friend_id", "name", "preview", "time", "unread"])

        # ========== 事件绑定 ==========
        # 初始加载
        user_info_state.change(fn=load_friend_dataframe, inputs=[user_info_state], outputs=[friend_df])
        # 刷新按钮
        refresh_btn.click(fn=load_friend_dataframe, inputs=[user_info_state], outputs=[friend_df]).then(
            fn=lambda: time.time(),outputs=last_update_time)
        # 切换好友列表/聊天列表
        show_friends_btn.click(fn=lambda mode: ("friends" if mode == "recent" else "recent"), inputs=[view_mode], outputs=[view_mode]).then(
            fn=lambda mode, user: load_friend_dataframe(user, mode), inputs=[view_mode, user_info_state], outputs=[friend_df]).then(
            fn=lambda mode: "好友列表" if mode == "friends" else "最近消息", inputs=[view_mode], outputs=[title_md])
        # 返回按钮
        back_btn.click(fn=back_to_list, outputs=[selected_friend, friend_info, chat_history, back_btn, show_friends_btn, view_mode, title_md])
        # 选择好友
        friend_df.select(fn=select_friend_handler, inputs=[friend_df, user_info_state], outputs=[selected_friend, friend_info, chat_history, back_btn, show_friends_btn, view_mode, title_md])

        # 发送消息
        send_btn.click(
            fn=send_message_handler,
            inputs=[selected_friend, message_input, user_info_state],
            outputs=[selected_friend, message_input, chat_history]  # 替换chat_container为chat_history
        ).then(
            fn=lambda: time.time(),
            outputs=last_update_time
        )

        message_input.submit(
            fn=send_message_handler,
            inputs=[selected_friend, message_input, user_info_state],
            outputs=[selected_friend, message_input, chat_history]  # 替换chat_container为chat_history
        ).then(
            fn=lambda: time.time(),
            outputs=last_update_time
        )

        # 手动刷新聊天
        manual_refresh_btn.click(
            fn=lambda friend_id, user: load_chat_messages(friend_id, user),
            inputs=[selected_friend, user_info_state],
            outputs=chat_history
        ).then(
            fn=lambda: time.time(),
            outputs=last_update_time
        )

        # 自动刷新设置
        auto_refresh_toggle.change(
            fn=lambda value: value,
            inputs=[auto_refresh_toggle],
            outputs=[auto_refresh]
        )

        # 搜索功能
        search_box.change(
            fn=search_friends,
            inputs=[search_box, user_info_state, view_mode],
            outputs=[friend_df]  # 替换recent_chats和friend_list为friend_df
        )

        # 自动刷新定时器
        # 添加自定义JavaScript来实现定时刷新
        gr.HTML("""
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // 每5秒触发一次刷新按钮点击
            setInterval(function() {
                const refreshBtn = document.getElementById('auto-refresh-trigger');
                if (refreshBtn) {
                    refreshBtn.click();
                }
            }, 5000);
        });
        </script>
        """)

        # 添加一个隐藏的按钮作为刷新触发器
        auto_refresh_trigger = gr.Button("刷新", visible=False, elem_id="auto-refresh-trigger")

        # 绑定刷新触发器的点击事件
        auto_refresh_trigger.click(
            fn=auto_refresh_handler,
            inputs=[selected_friend, user_info_state, auto_refresh, last_update_time],
            outputs=[chat_history, last_update_time]
        )

    return {
        "friend_list": friend_df,
        "chat_history": chat_history,
        "selected_friend": selected_friend
    }
