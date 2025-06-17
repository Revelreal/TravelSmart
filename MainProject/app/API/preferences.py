import gradio as gr


def create_travel_preferences_form():
    with gr.Blocks(title="旅行智能助手 - 旅行偏好", css="""
    .title-section {
        text-align: center;
        margin-bottom: 20px;
        background: linear-gradient(90deg, #e0f7fa, #b2ebf2, #e0f7fa);
        padding: 15px;
        border-radius: 10px;
    }
    .title-section h1 {
        margin: 0;
        color: #00796b;
    }
    .title-section p {
        color: #546e7a;
        margin: 10px 0 0 0;
    }
    .preference-section {
        background-color: #f5f5f5;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 15px;
        border-left: 4px solid #26a69a;
    }
    .section-title {
        margin-top: 0;
        color: #00796b;
        font-size: 1.2em;
    }
    .description {
        color: #546e7a;
        font-style: italic;
        margin-bottom: 15px;
    }
    .result-box {
        background-color: #e8f5e9;
        border: 1px solid #a5d6a7;
        border-radius: 8px;
        padding: 15px;
        margin-top: 20px;
    }
    .submit-btn {
        background-color: #26a69a !important;
        color: white !important;
    }
    .submit-btn:hover {
        background-color: #00897b !important;
    }
    .preference-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        background-color: white;
    }
    .required-field::after {
        content: " *";
        color: #e53935;
    }
    .example-text {
        background-color: #f1f8e9;
        border-left: 3px solid #7cb342;
        padding: 10px;
        font-size: 0.9em;
        margin: 10px 0;
    }
    """) as app:

        # 标题部分
        with gr.Row(elem_classes="title-section"):
            with gr.Column():
                gr.Markdown("# 🌍 旅行智能助手 - 旅行偏好表单")
                gr.Markdown("告诉我们您的旅行喜好，让AI为您量身定制完美的旅行计划")

        # 基本信息部分
        with gr.Group(elem_classes="preference-section"):
            gr.Markdown("## 基本信息", elem_classes="section-title")
            gr.Markdown("请告诉我们关于您此次旅行的基本情况", elem_classes="description")

            with gr.Row():
                with gr.Column():
                    destination = gr.Textbox(
                        label="目的地",
                        placeholder="例如：北京、上海、成都、厦门、云南...",
                        elem_classes="required-field"
                    )

                    travel_dates = gr.Textbox(
                        label="旅行日期",
                        placeholder="例如：2025年7月1日至7月7日，或者7天左右...",
                        elem_classes="required-field"
                    )

                with gr.Column():
                    num_travelers = gr.Slider(
                        minimum=1,
                        maximum=10,
                        value=2,
                        step=1,
                        label="旅行人数",
                    )

                    traveler_types = gr.CheckboxGroup(
                        choices=["家庭出游", "情侣旅行", "独自旅行", "朋友结伴", "亲子游", "老年人"],
                        label="旅行类型",
                        info="可多选"
                    )

            budget = gr.Radio(
                choices=["经济实惠 (1500元以下/人/天)", "中等预算 (1500-3000元/人/天)", "高端享受 (3000元以上/人/天)"],
                label="预算范围",
                value="中等预算 (1500-3000元/人/天)"
            )

        # 旅行偏好部分
        with gr.Group(elem_classes="preference-section"):
            gr.Markdown("## 旅行偏好", elem_classes="section-title")
            gr.Markdown("请告诉我们您在旅行中的喜好和关注点", elem_classes="description")

            travel_pace = gr.Slider(
                minimum=1,
                maximum=5,
                value=3,
                step=1,
                label="旅行节奏",
                info="1=非常悠闲，5=行程紧凑"
            )

            with gr.Row():
                with gr.Column():
                    interests = gr.CheckboxGroup(
                        choices=["历史文化", "自然风光", "美食体验", "购物", "博物馆/艺术",
                                 "户外活动", "城市观光", "主题公园", "文艺小资", "古镇村落"],
                        label="兴趣爱好",
                        info="选择您最感兴趣的活动类型（可多选）"
                    )

                with gr.Column():
                    accommodation_pref = gr.CheckboxGroup(
                        choices=["经济型酒店", "中端舒适酒店", "高端豪华酒店", "民宿/客栈", "特色主题酒店", "露营地"],
                        label="住宿偏好",
                        info="选择您偏好的住宿类型（可多选）"
                    )

            special_requirements = gr.CheckboxGroup(
                choices=["无障碍设施需求", "素食餐厅", "带宠物友好", "亲子设施", "适合老年人", "摄影打卡地"],
                label="特殊需求",
                info="有特殊需求请选择（可多选）"
            )

            avoid_places = gr.Textbox(
                label="希望避开的地方",
                placeholder="例如：人多拥挤的景点、商业化严重的区域...",
                lines=2
            )

        # 个性化信息部分
        with gr.Group(elem_classes="preference-section"):
            gr.Markdown("## 个性化信息", elem_classes="section-title")
            gr.Markdown("更多细节帮助我们为您提供个性化建议", elem_classes="description")

            previous_experience = gr.Radio(
                choices=["初次前往", "去过1-2次", "经常前往", "居住过"],
                label="目的地经验",
                value="初次前往"
            )

            with gr.Accordion("补充信息", open=False):
                specific_attractions = gr.Textbox(
                    label="特别想去的景点/活动",
                    placeholder="例如：一定要去故宫、想尝试当地特色美食...",
                    lines=2
                )

                travel_style = gr.Textbox(
                    label="旅行风格描述",
                    placeholder="用几句话描述您心目中理想的旅行体验是什么样的...",
                    lines=3
                )

        # 提示示例
        with gr.Accordion("查看提示词示例", open=False):
            gr.Markdown("""
            <div class="example-text">
            我正在计划一次去厦门的旅行，时间是2025年7月1日至7月7日，共7天。这是一次情侣旅行，共2人，预算中等约2000元/人/天。我们喜欢悠闲的旅行节奏，特别喜欢自然风光、美食体验和文艺小资类的活动。住宿方面偏好民宿/客栈或特色主题酒店。这是我们第一次去厦门，特别想去鼓浪屿和厦门大学。我们希望能体验当地的海鲜美食，也希望找到一些适合拍照的文艺小店和海边景点。请为我们推荐适合的行程安排、景点、餐厅和住宿选择。
            </div>
            """)

        # 提交按钮
        submit_btn = gr.Button("生成旅行偏好提示词", variant="primary", elem_classes="submit-btn")

        # 结果显示
        result = gr.Textbox(
            label="生成的提示词",
            placeholder="点击上方按钮生成旅行偏好提示词...",
            lines=10,
            elem_classes="result-box"
        )

        copy_btn = gr.Button("复制提示词")
        success_msg = gr.Markdown("")

        # 处理函数
        def generate_prompt(destination, travel_dates, num_travelers, traveler_types,
                            budget, travel_pace, interests, accommodation_pref,
                            special_requirements, avoid_places, previous_experience,
                            specific_attractions, travel_style):

            # 验证必填字段
            if not destination or not travel_dates:
                return "请填写必要的目的地和旅行日期信息。"

            # 旅行节奏描述
            pace_descriptions = {
                1: "非常悠闲",
                2: "比较悠闲",
                3: "中等节奏",
                4: "稍快节奏",
                5: "行程紧凑"
            }

            # 将预算字符串转换为实际预算描述
            budget_desc = budget.split(" ")[0]

            # 准备旅行类型
            traveler_type_text = "、".join(traveler_types) if traveler_types else "普通旅行"

            # 准备兴趣爱好
            interests_text = "、".join(interests) if interests else "常规旅游活动"

            # 准备住宿偏好
            accommodation_text = "、".join(accommodation_pref) if accommodation_pref else "标准酒店"

            # 准备特殊需求
            special_req_text = ""
            if special_requirements:
                special_req_text = f"我们有以下特殊需求：{', '.join(special_requirements)}。"

            # 准备避开的地方
            avoid_text = ""
            if avoid_places:
                avoid_text = f"我们希望避开：{avoid_places}。"

            # 准备目的地经验
            experience_text = f"这是我们{previous_experience}这个目的地。"

            # 准备特别想去的景点/活动
            attractions_text = ""
            if specific_attractions:
                attractions_text = f"我们特别想去/体验：{specific_attractions}。"

            # 准备旅行风格描述
            style_text = ""
            if travel_style:
                style_text = f"我们的旅行风格是：{travel_style}"

            # 构建完整提示词
            prompt = f"""我正在计划一次去{destination}的旅行，时间是{travel_dates}。这是一次{traveler_type_text}，共{num_travelers}人，预算{budget_desc}。我们喜欢{pace_descriptions[travel_pace]}的旅行节奏，特别喜欢{interests_text}。住宿方面偏好{accommodation_text}。{experience_text}{attractions_text}{special_req_text}{avoid_text}{style_text}

请为我们推荐适合的行程安排、景点、餐厅和住宿选择。"""

            return prompt

        def copy_text(text):
            return "✅ 提示词已复制到剪贴板！您可以将其粘贴到旅行智能助手对话中获取推荐。"

        # 事件绑定
        submit_btn.click(
            fn=generate_prompt,
            inputs=[
                destination, travel_dates, num_travelers, traveler_types,
                budget, travel_pace, interests, accommodation_pref,
                special_requirements, avoid_places, previous_experience,
                specific_attractions, travel_style
            ],
            outputs=result
        )

        copy_btn.click(
            fn=copy_text,
            inputs=result,
            outputs=success_msg
        )

    return app


# 如果直接运行
if __name__ == "__main__":
    app = create_travel_preferences_form()
    app.launch()
