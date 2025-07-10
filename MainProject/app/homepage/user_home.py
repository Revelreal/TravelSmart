import gradio as gr

from MainProject.app.API.ai_service import ask_ai_sync, extract_coordinates_from_ai_response
from MainProject.auth_utils import verify_token


# 构建AI问题
def build_ai_messages(history, question):
    messages = []
    for msg in (history or []):
        if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
            messages.append(msg)
    if question and question.strip():
        messages.append({"role": "user", "content": str(question)})
    return messages


# 地图接口（必须token核查）
def create_map_ui(token_box):
    def _iframe_html(token: str):
        if not token:
            return '<div style="color:red;padding:20px">未登录/参数缺失，无法加载地图</div>'
        return f"""
        <iframe
            id='map-iframe'
            src='/api/map?token={token}'
            style='width:100%; height:680px; border:none;'
            allow='geolocation'></iframe>
        """

    with gr.Column(scale=3):
        with gr.Group(elem_classes="map-border"):
            map_html = gr.HTML()
            # 用于执行地图脚本的隐藏组件
            map_script_html = gr.HTML(visible=False)

        # token变动时注册iframe
        token_box.change(_iframe_html, inputs=token_box, outputs=map_html)

    return map_html, map_script_html


# 快速提问内容建议
QUICK_SUGGESTIONS = [
    "北京天安门广场怎么去？", "上海外滩有什么好玩的？", "西湖十景都有哪些？",
    "故宫博物院开放时间", "长城一日游路线推荐", "成都美食推荐",
    "三亚海滩哪个最美？", "桂林山水甲天下在哪里？", "西安兵马俑门票价格",
    "张家界国家森林公园最佳路线", "九寨沟最佳旅游季节", "丽江古城有哪些特色客栈？",
    "鼓浪屿轮渡时刻表", "黄山看日出最佳地点", "乌镇东西栅区别",
    "平遥古城必去景点", "敦煌莫高窟参观攻略", "峨眉山金顶住宿推荐",
    "厦门曾厝垵小吃推荐", "阳朔西街酒吧哪家好？", "青海湖环湖骑行路线",
    "哈尔滨冰雪大世界门票", "婺源油菜花最佳观赏时间", "香格里拉松赞林寺介绍"
]

# 个性推荐内容建议
CUSTOM_SUGGESTIONS = [
    "我想了解最近的热门旅游景点", "帮我规划一个3天2夜的周末游",
    "推荐一些适合拍照的网红打卡地", "我想找性价比高的酒店住宿",
    "有什么特色美食值得尝试？", "当地的交通出行方式有哪些？",
    "适合带老人去的景点推荐", "亲子游最佳目的地", "自驾游路线规划",
    "雨季旅游注意事项", "冬季最佳旅游城市", "小众特色景点推荐"
]


def get_random_suggestions(suggestion_type):
    """随机获取建议"""
    import random
    if suggestion_type == "quick":
        return random.sample(QUICK_SUGGESTIONS, min(8, len(QUICK_SUGGESTIONS)))
    elif suggestion_type == "custom":
        return random.sample(CUSTOM_SUGGESTIONS, min(6, len(CUSTOM_SUGGESTIONS)))
    elif suggestion_type == "favorite":
        return  ["鼓浪屿", "乌镇", "阳朔", "九寨沟", "婺源", "香格里拉"] # 这里替换为用户收藏消息的组合函数
    elif suggestion_type == "trip":
        return ["我的行程1: 北京三日游", "我的行程2: 上海周末游", "我的行程3: 成都美食之旅",
                "我的行程4: 云南七日游", "我的行程5: 西安文化之旅", "我的行程6: 三亚海滨度假"]
    return []


def create_user_home_app():
    with gr.Blocks(
            title="TravelSmart",
            css="""
        .map-border { border: 1px solid #ddd; border-radius: 8px; padding: 8px; }
        .map-container { min-height: 580px !important; }

        /* AI聊天区域样式保持不变 */
        .ai-chat-container {
            border: 1px solid #e1e5e9;
            border-radius: 12px;
            padding: 16px;
        }

        .suggestion-item {
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 8px 12px;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 13px;
            text-align: center;
            margin: 2px;
        }

        .suggestion-item:hover {
            border-color: #4a6baf;
            transform: translateY(-1px);
        }

        .send-button {
            background: #4a6baf !important;
            border-radius: 8px !important;
            padding: 8px 16px !important;
            height: 40px !important;
        }

        .send-button:hover {
            background: #3a56a0 !important;
        }
        
        /* 顶部导航栏样式 */
        .top-navbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 20px;
            background: linear-gradient(135deg, #4a6baf, #3a56a0);
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
            color: white;
            margin-bottom: 15px;
            border-radius: 8px;
        }

        /* 用户头像样式 */
        .user-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #ffffff;;
            color: #4a6baf;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }

        /* 用户名称样式 */
        .username-display {
            margin-left: 10px;
            font-size: 16px;
            font-weight: 500;
            color: #ffffff;
            text-shadow: 0 1px 2px rgba(0,0,0,0.2);
        }

        /* 左侧用户区域 */
        .user-area {
            display: flex;
            align-items: center;
        }

        /* 悬浮菜单按钮 */
        .floating-menu-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: #4a6baf;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            cursor: pointer;
            z-index: 1000;
            transition: all 0.3s ease;
        }
        
        /* 使用纯CSS控制菜单显示 */
        .floating-menu-container {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 999;
        }
        
        .floating-menu-container:hover .floating-menu,
        .floating-menu-container:focus-within .floating-menu,
        .floating-menu.active {
            visibility: visible;
            opacity: 1;
            transform: translateY(0);
        }
        
        /* 悬浮菜单容器 */
        .floating-menu {
            position: absolute;
            bottom: 70px;
            right: 0;
            background: #4a6baf;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            padding: 15px;
            min-width: 180px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            
            /* 动画效果 */
            visibility: hidden;
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.3s ease;
        }
        """
    ) as demo:
        # 状态管理
        token_box = gr.Textbox(visible=False)
        map_coords_state = gr.State(value=None)  # 存储地图坐标状态
        map_update_counter = gr.State(value=0)  # 地图更新计数器

        navbar_html = gr.HTML("", elem_id="top-navbar")
        floating_menu_html = gr.HTML("", elem_id="floating-menu-container")

        # load回调保持不变
        # -------- load回调，token流转，并输出拼接好的导航栏HTML --------
        def load_user(request: gr.Request):
            token = request.query_params.get("token", "")
            info = verify_token(token)
            if not info or not info.get("username"):
                raise gr.Error("未登录或令牌无效，请重新登录")

            username = info["username"]
            avatar_letter = username[0].upper()  # 获取用户名第一个字符作为头像

            # 构建导航栏HTML（简化版，只显示用户信息和标题）
            navbar = f'''
             <div class="top-navbar">
                 <div class="user-area">
                     <div class="user-avatar">{avatar_letter}</div>
                     <span class="username-display">{username}</span>
                 </div>
                 <h1 class="page-title">TravelSmart 用户主页</h1>
             </div>
             '''

            # 构建悬浮菜单HTML
            floating_menu = f'''
             <!-- 悬浮菜单按钮 -->
             <div class="floating-menu-container">
                 <div class="floating-menu-btn" tabindex="0">☰</div>
                 <div class="floating-menu">
                     <a href="/api/trips?token={token}" class="menu-item">
                         <span class="menu-item-icon">🧳</span>
                         <span class="menu-item-text">我的行程</span>
                     </a>
                     <a href="/api/reviews?token={token}" class="menu-item">
                         <span class="menu-item-icon">⭐</span>
                         <span class="menu-item-text">我的评价</span>
                     </a>
                     <a href="/api/preferences?token={token}" class="menu-item">
                         <span class="menu-item-icon">❤️</span>
                         <span class="menu-item-text">旅行偏好</span>
                     </a>
                     <a href="/settings/user_settings?token={token}" class="menu-item">
                         <span class="menu-item-icon">⚙️</span>
                         <span class="menu-item-text">用户设置</span>
                     </a>
                     <a href="/notice/user_notice?token={token}" class="menu-item">
                         <span class="menu-item-icon">🔈</span>
                         <span class="menu-item-text">系统公告</span>
                     </a>
                     <a href="/friends?token={token}" class="menu-item">
                         <span class="menu-item-icon">😀</span>
                         <span class="menu-item-text">我的好友</span>
                     </a>
                 </div>
             </div>
             '''

            return token, navbar, floating_menu

        demo.load(
            fn=load_user,
            inputs=None,
            outputs=[token_box, navbar_html, floating_menu_html]
        )

        with gr.Row():
            # 地图组件 - 使用动态更新机制
            with gr.Column(scale=3):
                with gr.Group(elem_classes="map-border"):
                    # 地图iframe组件
                    map_iframe = gr.HTML(elem_classes="map-container")

                    # 地图更新函数
                    def update_map_iframe(token, coords_state, update_counter):
                        if not token:
                            return '<div style="color:red;padding:20px">未登录，无法加载地图</div>'

                        import time
                        timestamp = int(time.time() * 1000)

                        if coords_state:
                            lng, lat, place = coords_state
                            print(f"更新地图到坐标: lng={lng}, lat={lat}, place={place}")
                            return f"""
                            <iframe
                                id='map-iframe-{timestamp}'
                                src='/api/map?token={token}&lng={lng}&lat={lat}&zoom=15&place={place}&t={timestamp}'
                                style='width:100%; height:680px; border:none;'
                                allow='geolocation'></iframe>
                            """
                        else:
                            return f"""
                            <iframe
                                id='map-iframe-{timestamp}'
                                src='/api/map?token={token}&t={timestamp}'
                                style='width:100%; height:680px; border:none;'
                                allow='geolocation'></iframe>
                            """

                    # 绑定地图更新事件
                    map_update_counter.change(
                        fn=update_map_iframe,
                        inputs=[token_box, map_coords_state, map_update_counter],
                        outputs=[map_iframe]
                    )

                    # token变化时初始化地图
                    token_box.change(
                        fn=update_map_iframe,
                        inputs=[token_box, map_coords_state, map_update_counter],
                        outputs=[map_iframe]
                    )

            # AI聊天区域
            with gr.Column(scale=2, min_width=320):
                with gr.Group(elem_classes="ai-chat-container"):
                    # AI标题
                    gr.Markdown("### 🐱 AI 智能助手")
                    gr.Markdown("欢迎使用 TravelSmart AI 助手，可以咨询任何旅行问题")

                    # 聊天记录
                    chatbot = gr.Chatbot(type="messages", show_label=False, height=300)

                    # 快速建议
                    with gr.Tabs():
                        with gr.Tab("💡 快速提问"):
                            suggestions = get_random_suggestions("quick")
                            suggestion_buttons = []

                            for i in range(0, len(suggestions), 2):
                                with gr.Row():
                                    for j in range(2):
                                        if i + j < len(suggestions):
                                            btn = gr.Button(
                                                suggestions[i + j],
                                                elem_classes="suggestion-item",
                                                size="sm"
                                            )
                                            suggestion_buttons.append(btn)

                        with gr.Tab("🎯 个性推荐"):
                            custom_suggestions = get_random_suggestions("custom")
                            custom_buttons = []

                            for i in range(0, len(custom_suggestions), 2):
                                with gr.Row():
                                    for j in range(2):
                                        if i + j < len(custom_suggestions):
                                            btn = gr.Button(
                                                custom_suggestions[i + j],
                                                elem_classes="suggestion-item",
                                                size="sm"
                                            )
                                            custom_buttons.append(btn)

                        with gr.Tab("❤️ 我的收藏"):
                            favorite_suggestions = get_random_suggestions("favorite")
                            favorite_buttons = []

                            for i in range(0, len(favorite_suggestions), 2):
                                with gr.Row():
                                    for j in range(2):
                                        if i + j < len(favorite_suggestions):
                                            btn = gr.Button(
                                                favorite_suggestions[i + j],
                                                elem_classes="suggestion-item",
                                                size="sm"
                                            )
                                            favorite_buttons.append(btn)

                        with gr.Tab("🚆 我的行程"):
                            trip_suggestions = get_random_suggestions("trip")
                            trip_buttons = []

                            for i in range(0, len(trip_suggestions), 2):
                                with gr.Row():
                                    for j in range(2):
                                        if i + j < len(trip_suggestions):
                                            btn = gr.Button(
                                                trip_suggestions[i + j],
                                                elem_classes="suggestion-item",
                                                size="sm"
                                            )
                                            trip_buttons.append(btn)


                    # 输入区域
                    with gr.Row():
                        msg = gr.Textbox(
                            placeholder="输入问题，回车或点击发送按钮提问...",
                            show_label=False,
                            container=False,
                            scale=4
                        )
                        send_btn = gr.Button(
                            "📤 发送",
                            elem_classes="send-button",
                            size="sm",
                            scale=1
                        )

                # 增强的AI交互函数
                def enhanced_ai_chat(history, question, token, coords_state, update_counter):
                    # 调用原有AI聊天函数
                    info = verify_token(token)
                    if not info or not info.get("username"):
                        raise gr.Error("认证失效，请刷新页面重新登录")

                    history = history or []
                    if not question or not question.strip():
                        error_msg = {"role": "assistant", "content": "提问不能为空"}
                        return history + [error_msg], "", coords_state, update_counter

                    user_msg = {"role": "user", "content": str(question)}
                    updated_history = history + [user_msg]
                    messages = build_ai_messages(history, question)

                    try:
                        answer = ask_ai_sync(messages)
                    except Exception as e:
                        answer = f"AI请求错误: {str(e)}"

                    ai_msg = {"role": "assistant", "content": answer}
                    final_history = updated_history + [ai_msg]

                    # 检查AI回复中是否包含坐标
                    lng, lat = extract_coordinates_from_ai_response(answer)
                    print(f"从AI回复中提取坐标: lng={lng}, lat={lat}")

                    new_coords_state = coords_state
                    new_update_counter = update_counter

                    if lng is not None and lat is not None:
                        # 更新坐标状态
                        new_coords_state = (lng, lat, question)
                        new_update_counter = update_counter + 1

                        # 在AI回复中添加坐标确认信息
                        ai_msg["content"] += f"\n\n📍 已在地图上标记位置：经度 {lng:.6f}, 纬度 {lat:.6f}"
                        final_history[-1] = ai_msg

                        print(f"更新地图状态: coords={new_coords_state}, counter={new_update_counter}")

                    return final_history, "", new_coords_state, new_update_counter

                # 建议按钮点击事件
                def use_suggestion(suggestion_text):
                    return suggestion_text

                # 绑定建议按钮
                all_buttons = suggestion_buttons + custom_buttons + trip_buttons + favorite_buttons
                for btn in all_buttons:
                    btn.click(
                        fn=use_suggestion,
                        inputs=[btn],
                        outputs=[msg]
                    )

                # AI交互事件
                msg.submit(
                    fn=enhanced_ai_chat,
                    inputs=[chatbot, msg, token_box, map_coords_state, map_update_counter],
                    outputs=[chatbot, msg, map_coords_state, map_update_counter]
                )

                send_btn.click(
                    fn=enhanced_ai_chat,
                    inputs=[chatbot, msg, token_box, map_coords_state, map_update_counter],
                    outputs=[chatbot, msg, map_coords_state, map_update_counter]
                )

        gr.HTML("<div style='text-align:center;color:#97a;margin-top:30px;'>© 2025 TravelSmart</div>")

    return demo
