# MainProject/app/API/preferences.py
import gradio as gr
import pyperclip

from MainProject.dbhelper.SQLHelper import SQLHelper
from MainProject.auth_utils import verify_token


class TravelPreferencesDB(SQLHelper):
    """扩展SQLHelper类以支持旅行偏好功能"""

    def setup_travel_preferences_tables(self):
        """创建旅行偏好相关的所有表"""
        self.create_travel_preferences_table()
        self.create_interest_categories_table()
        self.create_user_interests_table()
        print("旅行偏好相关表创建完成")

    def create_travel_preferences_table(self):
        sql = '''
              CREATE TABLE IF NOT EXISTS TravelPreferences \
              ( \
                  id                   INT AUTO_INCREMENT PRIMARY KEY, \
                  user_id              INT          NOT NULL, \
                  preference_name      VARCHAR(100) NOT NULL, \
                  destination          VARCHAR(100) NOT NULL, \
                  travel_dates         VARCHAR(100), \
                  num_travelers        INT      DEFAULT 1, \
                  traveler_types       VARCHAR(255), \
                  budget               VARCHAR(100), \
                  travel_pace          INT      DEFAULT 3, \
                  accommodation_pref   VARCHAR(255), \
                  special_requirements VARCHAR(255), \
                  avoid_places         TEXT, \
                  previous_experience  VARCHAR(50), \
                  specific_attractions TEXT, \
                  travel_style         TEXT, \
                  generated_prompt     TEXT, \
                  created_at           DATETIME DEFAULT CURRENT_TIMESTAMP, \
                  updated_at           DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, \
                  is_favorite          BOOLEAN  DEFAULT FALSE, \
                  FOREIGN KEY (user_id) REFERENCES Users (id) ON DELETE CASCADE ON UPDATE CASCADE, \
                  INDEX (user_id)
              ) ENGINE = InnoDB \
                DEFAULT CHARSET = utf8mb4; \
              '''
        self.execute(sql)
        print("TravelPreferences表创建完成")

    def create_interest_categories_table(self):
        sql = '''
              CREATE TABLE IF NOT EXISTS InterestCategories \
              ( \
                  id            INT AUTO_INCREMENT PRIMARY KEY, \
                  category_name VARCHAR(50) NOT NULL UNIQUE, \
                  description   VARCHAR(255), \
                  icon          VARCHAR(50)
              ) ENGINE = InnoDB \
                DEFAULT CHARSET = utf8mb4; \
              '''
        self.execute(sql)

        # 预填充兴趣类别
        categories = [
            ("历史文化", "历史遗迹、古迹、文化遗产等", "🏛️"),
            ("自然风光", "山水、海滩、森林等自然景观", "🌄"),
            ("美食体验", "当地特色美食、餐厅、美食之旅", "🍜"),
            ("购物", "商场、特色市场、纪念品", "🛍️"),
            ("博物馆/艺术", "博物馆、美术馆、艺术展览", "🖼️"),
            ("户外活动", "徒步、登山、骑行、水上运动", "🏊"),
            ("城市观光", "都市景点、城市地标、街区", "🏙️"),
            ("主题公园", "游乐园、水上乐园、主题公园", "🎡"),
            ("文艺小资", "咖啡厅、书店、艺术区", "☕"),
            ("古镇村落", "传统村落、古镇、乡村风光", "🏘️")
        ]

        sql = 'INSERT IGNORE INTO InterestCategories (category_name, description, icon) VALUES (%s, %s, %s)'
        self.executemany(sql, categories)

    def create_user_interests_table(self):
        sql = '''
              CREATE TABLE IF NOT EXISTS UserInterests \
              ( \
                  id            INT AUTO_INCREMENT PRIMARY KEY, \
                  preference_id INT NOT NULL, \
                  category_id   INT NOT NULL, \
                  FOREIGN KEY (preference_id) REFERENCES TravelPreferences (id) ON DELETE CASCADE, \
                  FOREIGN KEY (category_id) REFERENCES InterestCategories (id) ON DELETE CASCADE, \
                  UNIQUE KEY (preference_id, category_id)
              ) ENGINE = InnoDB \
                DEFAULT CHARSET = utf8mb4; \
              '''
        self.execute(sql)

    def save_travel_preference(self, user_id, preference_data):
        try:
            # 验证必填字段
            required_fields = ["preference_name", "destination", "generated_prompt"]
            for field in required_fields:
                if field not in preference_data or not preference_data[field]:
                    return False, f"缺少必填字段: {field}"

            # 将列表类型的字段转换为字符串存储
            traveler_types = ",".join(preference_data.get("traveler_types", [])) if preference_data.get(
                "traveler_types") else ""
            accommodation_pref = ",".join(preference_data.get("accommodation_pref", [])) if preference_data.get(
                "accommodation_pref") else ""
            special_requirements = ",".join(preference_data.get("special_requirements", [])) if preference_data.get(
                "special_requirements") else ""

            # 插入主表数据
            sql = '''
                  INSERT INTO TravelPreferences (user_id, preference_name, destination, travel_dates, \
                                                 num_travelers, traveler_types, budget, travel_pace, \
                                                 accommodation_pref, special_requirements, avoid_places, \
                                                 previous_experience, specific_attractions, travel_style, \
                                                 generated_prompt) \
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
                  '''

            params = (
                user_id,
                preference_data["preference_name"],
                preference_data["destination"],
                preference_data.get("travel_dates", ""),
                preference_data.get("num_travelers", 1),
                traveler_types,
                preference_data.get("budget", ""),
                preference_data.get("travel_pace", 3),
                accommodation_pref,
                special_requirements,
                preference_data.get("avoid_places", ""),
                preference_data.get("previous_experience", ""),
                preference_data.get("specific_attractions", ""),
                preference_data.get("travel_style", ""),
                preference_data["generated_prompt"]
            )

            self.execute(sql, params)
            preference_id = self.cursor.lastrowid

            # 保存兴趣关联
            if "interests" in preference_data and preference_data["interests"]:
                self.save_user_interests(preference_id, preference_data["interests"])

            return True, preference_id
        except Exception as e:
            print(f"保存旅行偏好失败: {e}")
            return False, f"保存失败: {str(e)}"

    def save_user_interests(self, preference_id, interests):
        if not interests:
            return

        for interest in interests:
            category = self.fetchone("SELECT id FROM InterestCategories WHERE category_name = %s", (interest,))
            if category:
                sql = "INSERT IGNORE INTO UserInterests (preference_id, category_id) VALUES (%s, %s)"
                self.execute(sql, (preference_id, category["id"]))

    def get_user_preferences(self, user_id, limit=10):
        sql = '''
              SELECT * \
              FROM TravelPreferences
              WHERE user_id = %s
              ORDER BY updated_at DESC
              LIMIT %s \
              '''
        return self.query(sql, (user_id, limit))

    def get_preference_by_id(self, preference_id, user_id=None):
        if user_id:
            # 确保只能获取自己的偏好
            sql = "SELECT * FROM TravelPreferences WHERE id = %s AND user_id = %s"
            return self.fetchone(sql, (preference_id, user_id))
        else:
            sql = "SELECT * FROM TravelPreferences WHERE id = %s"
            return self.fetchone(sql, (preference_id,))

    def get_preference_interests(self, preference_id):
        sql = '''
              SELECT c.category_name
              FROM UserInterests ui
                       JOIN InterestCategories c ON ui.category_id = c.id
              WHERE ui.preference_id = %s \
              '''
        results = self.query(sql, (preference_id,))
        return [r["category_name"] for r in results]

    def delete_preference(self, preference_id, user_id):
        try:
            # 确认是否是用户自己的偏好
            pref = self.get_preference_by_id(preference_id, user_id)
            if not pref:
                return False, "偏好不存在或无权删除"

            # 删除主表数据 (关联表会自动级联删除)
            sql = "DELETE FROM TravelPreferences WHERE id = %s AND user_id = %s"
            self.execute(sql, (preference_id, user_id))
            return True, "删除成功"
        except Exception as e:
            return False, f"删除失败: {str(e)}"

    def toggle_favorite(self, preference_id, user_id):
        try:
            # 获取当前收藏状态
            pref = self.get_preference_by_id(preference_id, user_id)
            if not pref:
                return False, "偏好不存在或无权操作"

            # 切换状态
            new_status = not bool(pref["is_favorite"])
            sql = "UPDATE TravelPreferences SET is_favorite = %s WHERE id = %s AND user_id = %s"
            self.execute(sql, (new_status, preference_id, user_id))

            status_text = "已收藏" if new_status else "已取消收藏"
            return True, status_text
        except Exception as e:
            return False, f"操作失败: {str(e)}"

    def update_preference(self, preference_id, user_id, preference_data):
        """更新现有偏好"""
        try:
            # 验证权限
            pref = self.get_preference_by_id(preference_id, user_id)
            if not pref:
                return False, "偏好不存在或无权修改"

            # 提取兴趣爱好，单独处理
            interests = None
            if "interests" in preference_data:
                interests = preference_data.pop("interests")  # 从主数据中移除

            # 构建更新SQL
            update_fields = []
            params = []

            for field, value in preference_data.items():
                if field in ['traveler_types', 'accommodation_pref', 'special_requirements']:
                    # 列表字段转换为字符串
                    value = ",".join(value) if isinstance(value, list) else value
                update_fields.append(f"{field} = %s")
                params.append(value)

            params.extend([preference_id, user_id])

            # 如果没有要更新的字段，则不执行更新
            if update_fields:
                sql = f"UPDATE TravelPreferences SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = %s AND user_id = %s"
                self.execute(sql, params)

            # 更新兴趣爱好
            if interests is not None:
                # 删除现有的兴趣关联
                self.execute("DELETE FROM UserInterests WHERE preference_id = %s", (preference_id,))
                # 添加新的兴趣关联
                self.save_user_interests(preference_id, interests)

            return True, "更新成功"
        except Exception as e:
            return False, f"更新失败: {str(e)}"


def create_travel_preferences_app():
    with gr.Blocks(title="旅行智能助手 - 旅行偏好") as app:
        # 初始化数据库
        db = TravelPreferencesDB()
        try:
            db.setup_travel_preferences_tables()
        except Exception as e:
            print(f"初始化数据库失败: {e}")
        finally:
            db.close()

        # 隐藏的token和用户信息
        token_box = gr.Textbox(visible=False)
        user_id_box = gr.Textbox(visible=False)
        username_box = gr.Textbox(visible=False)

        # 用户信息显示
        with gr.Row():
            user_info = gr.Textbox(label="用户信息", interactive=False)
            gr.HTML("""
            <button onclick="window.history.back()" style="padding: 10px; border-radius: 5px; 
            border: 1px solid #ccc; cursor: pointer;">
            返回主页
            </button>
            """)

        gr.Markdown("# 🌍 旅行智能助手 - 旅行偏好管理")
        gr.Markdown("告诉我们您的旅行喜好，让AI为您量身定制完美的旅行计划")

        # 主界面标签页
        with gr.Tabs() as tabs:
            # 创建新偏好标签页
            with gr.TabItem("创建旅行偏好"):
                # 偏好名称
                preference_name = gr.Textbox(
                    label="偏好名称",
                    placeholder="为您的旅行偏好取个名字，如：厦门夏日之旅、云南自驾游..."
                )

                # 基本信息部分
                with gr.Group():
                    gr.Markdown("## 基本信息")
                    with gr.Row():
                        with gr.Column():
                            destination = gr.Textbox(
                                label="目的地",
                                placeholder="例如：北京、上海、成都、厦门、云南..."
                            )

                            travel_dates = gr.Textbox(
                                label="旅行日期",
                                placeholder="例如：2025年7月1日至7月7日，或者7天左右..."
                            )

                        with gr.Column():
                            num_travelers = gr.Slider(
                                minimum=1,
                                maximum=10,
                                value=2,
                                step=1,
                                label="旅行人数"
                            )

                            traveler_types = gr.CheckboxGroup(
                                choices=["家庭出游", "情侣旅行", "独自旅行", "朋友结伴", "亲子游", "老年人"],
                                label="旅行类型",
                                info="可多选"
                            )

                    budget = gr.Radio(
                        choices=["经济实惠 (1500元以下/人/天)", "中等预算 (1500-3000元/人/天)",
                                 "高端享受 (3000元以上/人/天)"],
                        label="预算范围",
                        value="中等预算 (1500-3000元/人/天)"
                    )

                # 旅行偏好部分
                with gr.Accordion("旅行偏好详情", open=True):
                    travel_pace = gr.Slider(
                        minimum=1,
                        maximum=5,
                        value=3,
                        step=1,
                        label="旅行节奏",
                        info="1=非常悠闲，5=行程紧凑"
                    )

                    with gr.Row():
                        interests = gr.CheckboxGroup(
                            choices=["历史文化", "自然风光", "美食体验", "购物", "博物馆/艺术",
                                     "户外活动", "城市观光", "主题公园", "文艺小资", "古镇村落"],
                            label="兴趣爱好",
                            info="选择您最感兴趣的活动类型（可多选）"
                        )

                        accommodation_pref = gr.CheckboxGroup(
                            choices=["经济型酒店", "中端舒适酒店", "高端豪华酒店", "民宿/客栈", "特色主题酒店",
                                     "露营地"],
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

                # 个性化信息
                with gr.Accordion("个性化信息", open=False):
                    previous_experience = gr.Radio(
                        choices=["初次前往", "去过1-2次", "经常前往", "居住过"],
                        label="目的地经验",
                        value="初次前往"
                    )

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

                # 操作按钮
                with gr.Row():
                    generate_btn = gr.Button("生成旅行偏好提示词", variant="primary")
                    clear_btn = gr.Button("清空表单", variant="secondary")

                # 结果显示
                result = gr.Textbox(
                    label="生成的提示词",
                    placeholder="点击上方按钮生成旅行偏好提示词...",
                    lines=8
                )

                # 结果操作
                with gr.Row():
                    copy_btn = gr.Button("复制提示词")
                    save_btn = gr.Button("保存偏好", interactive=False)

                status_msg = gr.Markdown("")

            # 我的旅行偏好标签页
            with gr.TabItem("我的旅行偏好"):
                with gr.Row():
                    refresh_btn = gr.Button("刷新列表", variant="secondary")
                    filter_dropdown = gr.Dropdown(
                        choices=["全部偏好", "已收藏", "最近创建"],
                        label="筛选方式",
                        value="全部偏好"
                    )

                # 添加提示信息
                gr.Markdown("💡 **使用提示**: 点击表格行选择偏好，然后使用下方按钮进行操作")

                # 偏好列表
                preferences_list = gr.Dataframe(
                    headers=["ID", "偏好名称", "目的地", "旅行日期", "创建时间", "收藏状态"],
                    label="我的旅行偏好",
                    interactive=False,
                    value=[],
                    wrap=True  # 允许文本换行
                )

                # 当前选中的偏好信息显示
                with gr.Row():
                    selected_info = gr.Textbox(
                        label="当前选中",
                        value="请点击表格选择一个偏好",
                        interactive=False
                    )

                # 选中的偏好ID (隐藏)
                selected_pref_id = gr.Number(label="选中的偏好ID", visible=False, value=0)

                # 偏好操作按钮
                with gr.Row():
                    view_btn = gr.Button("查看详情", variant="primary")
                    favorite_btn = gr.Button("收藏/取消收藏", variant="secondary")
                    edit_btn = gr.Button("编辑偏好", variant="secondary")
                    delete_btn = gr.Button("删除偏好", variant="stop")

                # 偏好详情显示区域
                with gr.Accordion("偏好详情", open=False) as detail_accordion:
                    pref_detail_info = gr.Markdown("请先选择一个偏好查看详情")
                    pref_prompt = gr.Textbox(label="完整提示词", lines=8, interactive=False)

                    with gr.Row():
                        detail_copy_btn = gr.Button("复制提示词", variant="primary")
                        close_detail_btn = gr.Button("关闭详情", variant="secondary")

                # 操作状态消息
                action_status = gr.Markdown("")

            # 编辑偏好标签页（动态显示）
            with gr.TabItem("编辑偏好", visible=False) as edit_tab:
                gr.Markdown("## 编辑旅行偏好")

                # 编辑表单（复用创建表单的组件）
                edit_preference_name = gr.Textbox(label="偏好名称")
                edit_destination = gr.Textbox(label="目的地")
                edit_travel_dates = gr.Textbox(label="旅行日期")
                edit_num_travelers = gr.Slider(minimum=1, maximum=10, value=2, step=1, label="旅行人数")
                edit_traveler_types = gr.CheckboxGroup(
                    choices=["家庭出游", "情侣旅行", "独自旅行", "朋友结伴", "亲子游", "老年人"],
                    label="旅行类型"
                )
                edit_budget = gr.Radio(
                    choices=["经济实惠 (1500元以下/人/天)", "中等预算 (1500-3000元/人/天)",
                             "高端享受 (3000元以上/人/天)"],
                    label="预算范围"
                )
                edit_travel_pace = gr.Slider(minimum=1, maximum=5, value=3, step=1, label="旅行节奏")
                edit_interests = gr.CheckboxGroup(
                    choices=["历史文化", "自然风光", "美食体验", "购物", "博物馆/艺术", "户外活动", "城市观光",
                             "主题公园", "文艺小资", "古镇村落"],
                    label="兴趣爱好"
                )
                edit_accommodation_pref = gr.CheckboxGroup(
                    choices=["经济型酒店", "中端舒适酒店", "高端豪华酒店", "民宿/客栈", "特色主题酒店", "露营地"],
                    label="住宿偏好"
                )
                edit_special_requirements = gr.CheckboxGroup(
                    choices=["无障碍设施需求", "素食餐厅", "带宠物友好", "亲子设施", "适合老年人", "摄影打卡地"],
                    label="特殊需求"
                )
                edit_avoid_places = gr.Textbox(label="希望避开的地方", lines=2)
                edit_previous_experience = gr.Radio(
                    choices=["初次前往", "去过1-2次", "经常前往", "居住过"],
                    label="目的地经验"
                )
                edit_specific_attractions = gr.Textbox(label="特别想去的景点/活动", lines=2)
                edit_travel_style = gr.Textbox(label="旅行风格描述", lines=3)

                # 编辑用的隐藏字段
                editing_pref_id = gr.Number(visible=False, value=0)

                with gr.Row():
                    update_prompt_btn = gr.Button("重新生成提示词", variant="primary")
                    save_edit_btn = gr.Button("保存修改", variant="primary")
                    cancel_edit_btn = gr.Button("取消编辑", variant="secondary")

                edit_result = gr.Textbox(label="更新的提示词", lines=8)
                edit_status = gr.Markdown("")

        # 加载用户信息
        def load_user_data(request: gr.Request):
            token = request.query_params.get("token", "")
            info = verify_token(token)
            if not info or not info.get("username"):
                return token, "", "", "⚠️ 未登录或登录已过期，请重新登录"

            user_id = info.get("id", "")
            username = info.get("username", "")

            return token, user_id, username, f"👤 当前用户: {username}"

        # 获取用户偏好列表
        def get_user_preferences_list(user_id, filter_type="全部偏好"):
            if not user_id:
                return [], "请先登录"

            db = TravelPreferencesDB()
            try:
                preferences = db.get_user_preferences(user_id, limit=50)

                # 根据筛选条件过滤
                if filter_type == "已收藏":
                    preferences = [p for p in preferences if p.get("is_favorite")]
                elif filter_type == "最近创建":
                    # 已经按created_at排序，取前10个
                    preferences = preferences[:10]

                # 格式化数据用于显示
                formatted_data = []
                for pref in preferences:
                    formatted_data.append([
                        pref["id"],
                        pref["preference_name"],
                        pref["destination"],
                        pref["travel_dates"] if pref["travel_dates"] else "未指定",
                        pref["created_at"].strftime("%Y-%m-%d %H:%M") if pref["created_at"] else "",
                        "⭐ 已收藏" if pref.get("is_favorite") else "未收藏"
                    ])

                return formatted_data, f"共找到 {len(formatted_data)} 个旅行偏好"
            except Exception as e:
                return [], f"获取偏好列表失败: {str(e)}"
            finally:
                db.close()

        # 处理表格选择事件
        def handle_table_select(evt: gr.SelectData, preferences_data):
            import pandas as pd

            if isinstance(preferences_data, pd.DataFrame):
                if preferences_data.empty:
                    return 0, "没有可选择的偏好"

                try:
                    if evt.index[0] < len(preferences_data.index):
                        selected_row = preferences_data.iloc[evt.index[0]]
                        # 使用.iloc而不是[]来避免警告
                        pref_id = selected_row.iloc[0]
                        pref_name = selected_row.iloc[1]
                        destination = selected_row.iloc[2]

                        return pref_id, f"已选择: {pref_name} - {destination}"
                    else:
                        return 0, "选择的行无效"
                except Exception as e:
                    return 0, f"选择失败: {str(e)}"
            else:
                # 处理普通列表
                if not preferences_data or len(preferences_data) == 0:
                    return 0, "没有可选择的偏好"

                try:
                    if evt.index[0] < len(preferences_data):
                        selected_row = preferences_data[evt.index[0]]
                        pref_id = selected_row[0]
                        pref_name = selected_row[1]
                        destination = selected_row[2]

                        return pref_id, f"已选择: {pref_name} - {destination}"
                    else:
                        return 0, "选择的行无效"
                except Exception as e:
                    return 0, f"选择失败: {str(e)}"

        # 查看偏好详情
        def view_preference_detail(user_id, pref_id):
            if not user_id or not pref_id:
                return "请先登录并选择一个偏好", "", gr.update(open=False)

            db = TravelPreferencesDB()
            try:
                pref = db.get_preference_by_id(pref_id, user_id)
                if not pref:
                    return "偏好不存在或无权查看", "", gr.update(open=False)

                # 获取关联的兴趣
                interests = db.get_preference_interests(pref_id)

                # 格式化详情信息
                detail_info = f"""
## {pref['preference_name']}

**目的地**: {pref['destination']}  
**旅行日期**: {pref['travel_dates'] if pref['travel_dates'] else '未指定'}  
**旅行人数**: {pref['num_travelers']}人  
**旅行类型**: {pref['traveler_types'] if pref['traveler_types'] else '未指定'}  
**预算**: {pref['budget'] if pref['budget'] else '未指定'}  
**旅行节奏**: {pref['travel_pace']}/5  
**兴趣爱好**: {', '.join(interests) if interests else '未指定'}  
**住宿偏好**: {pref['accommodation_pref'] if pref['accommodation_pref'] else '未指定'}  
**特殊需求**: {pref['special_requirements'] if pref['special_requirements'] else '无'}  
**避开地方**: {pref['avoid_places'] if pref['avoid_places'] else '无'}  
**目的地经验**: {pref['previous_experience'] if pref['previous_experience'] else '未指定'}  
**特别想去**: {pref['specific_attractions'] if pref['specific_attractions'] else '无'}  
**旅行风格**: {pref['travel_style'] if pref['travel_style'] else '未指定'}  

**创建时间**: {pref['created_at']}  
**更新时间**: {pref['updated_at']}  
**收藏状态**: {'已收藏' if pref.get('is_favorite') else '未收藏'}
                """

                return detail_info, pref['generated_prompt'], gr.update(open=True)
            except Exception as e:
                return f"获取详情失败: {str(e)}", "", gr.update(open=False)
            finally:
                db.close()

        # 切换收藏状态
        def toggle_preference_favorite(user_id, pref_id):
            if not user_id or not pref_id:
                return "请先登录并选择一个偏好"

            db = TravelPreferencesDB()
            try:
                success, message = db.toggle_favorite(pref_id, user_id)
                return f"✅ {message}" if success else f"❌ {message}"
            except Exception as e:
                return f"❌ 操作失败: {str(e)}"
            finally:
                db.close()

                # 删除偏好

        def delete_user_preference(user_id, pref_id):
            if not user_id or not pref_id:
                return "请先登录并选择一个偏好", []

            db = TravelPreferencesDB()
            try:
                success, message = db.delete_preference(pref_id, user_id)
                if success:
                    return f"✅ {message}", []
                else:
                    return f"❌ {message}", []
            except Exception as e:
                return f"❌ 删除失败: {str(e)}", []
            finally:
                db.close()

            # 生成提示词函数

        def generate_prompt(preference_name, destination, travel_dates, num_travelers, traveler_types,
                            budget, travel_pace, interests, accommodation_pref,
                            special_requirements, avoid_places, previous_experience,
                            specific_attractions, travel_style):

            # 验证必填字段
            if not destination or not travel_dates:
                return "请填写必要的目的地和旅行日期信息。", gr.update(interactive=False)

            if not preference_name:
                return "请为您的旅行偏好取个名字。", gr.update(interactive=False)

            # 旅行节奏描述
            pace_descriptions = {
                1: "非常悠闲",
                2: "比较悠闲",
                3: "中等节奏",
                4: "稍快节奏",
                5: "行程紧凑"
            }

            # 预算处理
            budget_desc = budget.split(" ")[0]

            # 处理各种列表字段
            traveler_type_text = "、".join(traveler_types) if traveler_types else "普通旅行"
            interests_text = "、".join(interests) if interests else "常规旅游活动"
            accommodation_text = "、".join(accommodation_pref) if accommodation_pref else "标准酒店"

            # 构建提示词片段
            special_req_text = f"我们有以下特殊需求：{', '.join(special_requirements)}。" if special_requirements else ""
            avoid_text = f"我们希望避开：{avoid_places}。" if avoid_places else ""
            experience_text = f"这是我们{previous_experience}这个目的地。" if previous_experience else ""
            attractions_text = f"我们特别想去/体验：{specific_attractions}。" if specific_attractions else ""
            style_text = f"我们的旅行风格是：{travel_style}" if travel_style else ""

            # 构建完整提示词
            prompt = f"""我正在计划一次去{destination}的旅行，时间是{travel_dates}。这是一次{traveler_type_text}，共{num_travelers}人，预算{budget_desc}。我们喜欢{pace_descriptions[travel_pace]}的旅行节奏，特别喜欢{interests_text}。住宿方面偏好{accommodation_text}。{experience_text}{attractions_text}{special_req_text}{avoid_text}{style_text}

            请为我们推荐适合的行程安排、景点、餐厅和住宿选择。"""

            return prompt, gr.update(interactive=True)

            # 保存偏好函数

        def save_preference(user_id, preference_name, destination, travel_dates, num_travelers, traveler_types,
                            budget, travel_pace, interests, accommodation_pref,
                            special_requirements, avoid_places, previous_experience,
                            specific_attractions, travel_style, generated_prompt):

            if not user_id:
                return "⚠️ 请先登录后再保存偏好"

            if not generated_prompt or not preference_name or not destination:
                return "⚠️ 请先生成提示词并确保填写了偏好名称和目的地"

            # 构建偏好数据
            preference_data = {
                "preference_name": preference_name,
                "destination": destination,
                "travel_dates": travel_dates,
                "num_travelers": num_travelers,
                "traveler_types": traveler_types,
                "budget": budget,
                "travel_pace": travel_pace,
                "interests": interests,
                "accommodation_pref": accommodation_pref,
                "special_requirements": special_requirements,
                "avoid_places": avoid_places,
                "previous_experience": previous_experience,
                "specific_attractions": specific_attractions,
                "travel_style": travel_style,
                "generated_prompt": generated_prompt
            }

            # 保存到数据库
            db = TravelPreferencesDB()
            try:
                success, result = db.save_travel_preference(user_id, preference_data)
                if success:
                    return f"✅ 旅行偏好保存成功！ID: {result}"
                else:
                    return f"❌ 保存失败: {result}"
            except Exception as e:
                return f"❌ 保存失败: {str(e)}"
            finally:
                db.close()

            # 清空表单

        def clear_form():
            return [
                "",  # preference_name
                "",  # destination
                "",  # travel_dates
                2,  # num_travelers
                [],  # traveler_types
                "中等预算 (1500-3000元/人/天)",  # budget
                3,  # travel_pace
                [],  # interests
                [],  # accommodation_pref
                [],  # special_requirements
                "",  # avoid_places
                "初次前往",  # previous_experience
                "",  # specific_attractions
                "",  # travel_style
                "",  # result
                gr.update(interactive=False),  # save_btn
                ""  # status_msg
            ]

            # 加载偏好数据用于编辑

        # 加载偏好数据用于编辑
        # 加载偏好数据用于编辑
        def load_preference_for_edit(user_id, pref_id):
            if not user_id or not pref_id:
                return [
                    gr.update(visible=False),  # 隐藏编辑标签页
                    "", "", "", 2, [], "中等预算 (1500-3000元/人/天)", 3,
                    [], [], [], "", "初次前往", "", "", 0, ""
                ]

            db = TravelPreferencesDB()
            try:
                pref = db.get_preference_by_id(pref_id, user_id)
                if not pref:
                    return [
                        gr.update(visible=False),
                        "", "", "", 2, [], "中等预算 (1500-3000元/人/天)", 3,
                        [], [], [], "", "初次前往", "", "", 0, "偏好不存在或无权编辑"
                    ]

                # 获取关联的兴趣
                interests = db.get_preference_interests(pref_id)

                # 处理列表字段
                traveler_types = pref["traveler_types"].split(",") if pref["traveler_types"] else []
                accommodation_pref = pref["accommodation_pref"].split(",") if pref["accommodation_pref"] else []
                special_requirements = pref["special_requirements"].split(",") if pref["special_requirements"] else []

                # 确保非空值传递
                travel_dates = pref["travel_dates"] if pref["travel_dates"] else ""
                avoid_places = pref["avoid_places"] if pref["avoid_places"] else ""
                previous_experience = pref["previous_experience"] if pref["previous_experience"] else "初次前往"
                specific_attractions = pref["specific_attractions"] if pref["specific_attractions"] else ""
                travel_style = pref["travel_style"] if pref["travel_style"] else ""

                # 确保数值型字段有合法值
                num_travelers = int(pref["num_travelers"]) if pref["num_travelers"] else 2
                travel_pace = int(pref["travel_pace"]) if pref["travel_pace"] else 3

                # 确保预算有合法值
                budget = pref["budget"] if pref["budget"] else "中等预算 (1500-3000元/人/天)"

                # 返回所有字段值和编辑标签页可见性更新
                return [
                    gr.update(visible=True),  # 显示编辑标签页，不使用selected参数
                    pref["preference_name"],
                    pref["destination"],
                    travel_dates,
                    num_travelers,
                    traveler_types,
                    budget,
                    travel_pace,
                    interests,
                    accommodation_pref,
                    special_requirements,
                    avoid_places,
                    previous_experience,
                    specific_attractions,
                    travel_style,
                    pref_id,
                    pref["generated_prompt"] if pref["generated_prompt"] else ""
                ]
            except Exception as e:
                print(f"加载偏好失败: {e}")
                return [
                    gr.update(visible=False),
                    "", "", "", 2, [], "中等预算 (1500-3000元/人/天)", 3,
                    [], [], [], "", "初次前往", "", "", 0,
                    f"加载失败: {str(e)}"
                ]
            finally:
                db.close()

        # 保存编辑后的偏好
        def save_edited_preference(user_id, pref_id, preference_name, destination, travel_dates,
                                   num_travelers, traveler_types, budget, travel_pace, interests,
                                   accommodation_pref, special_requirements, avoid_places,
                                   previous_experience, specific_attractions, travel_style, generated_prompt):
            if not user_id or not pref_id:
                return "请先登录并选择一个偏好", gr.update(visible=True)

            if not preference_name or not destination:
                return "请确保填写了偏好名称和目的地", gr.update(visible=True)

            # 确保提示词有值
            if not generated_prompt:
                return "请先生成提示词", gr.update(visible=True)

            preference_data = {
                "preference_name": preference_name,
                "destination": destination,
                "travel_dates": travel_dates,
                "num_travelers": num_travelers,
                "traveler_types": traveler_types,
                "budget": budget,
                "travel_pace": travel_pace,
                "interests": interests,
                "accommodation_pref": accommodation_pref,
                "special_requirements": special_requirements,
                "avoid_places": avoid_places,
                "previous_experience": previous_experience,
                "specific_attractions": specific_attractions,
                "travel_style": travel_style,
                "generated_prompt": generated_prompt
            }

            db = TravelPreferencesDB()
            try:
                success, message = db.update_preference(pref_id, user_id, preference_data)
                if success:
                    return f"✅ {message}", gr.update(visible=False)  # 不使用selected参数
                else:
                    return f"❌ {message}", gr.update(visible=True)
            except Exception as e:
                return f"❌ 更新失败: {str(e)}", gr.update(visible=True)
            finally:
                db.close()

        # 复制文本到剪贴板
        def copy_to_clipboard(text):
            """
            复制文本到系统剪贴板
            """
            if not text or text.strip() == "":
                return "⚠️ 没有可复制的内容"

            try:
                # 使用 pyperclip 复制到系统剪贴板
                pyperclip.copy(text.strip())
                return "✅ 提示词已复制到剪贴板！"
            except Exception as e:
                return f"❌ 复制失败：{str(e)}"

        # 关闭详情面板
        def close_detail_panel():
            return gr.update(open=False)

        # 取消编辑
        def cancel_edit():
            return gr.update(visible=False)

        # 绑定事件
        app.load(
            fn=load_user_data,
            inputs=None,
            outputs=[token_box, user_id_box, username_box, user_info]
        )

        # 用户加载完成后加载偏好列表
        user_id_box.change(
            fn=lambda user_id: get_user_preferences_list(user_id, "全部偏好"),
            inputs=[user_id_box],
            outputs=[preferences_list, action_status]
        )

        # 生成提示词
        generate_btn.click(
            fn=generate_prompt,
            inputs=[
                preference_name, destination, travel_dates, num_travelers, traveler_types,
                budget, travel_pace, interests, accommodation_pref,
                special_requirements, avoid_places, previous_experience,
                specific_attractions, travel_style
            ],
            outputs=[result, save_btn]
        )

        # 编辑页面重新生成提示词
        update_prompt_btn.click(
            fn=generate_prompt,
            inputs=[
                edit_preference_name, edit_destination, edit_travel_dates, edit_num_travelers, edit_traveler_types,
                edit_budget, edit_travel_pace, edit_interests, edit_accommodation_pref,
                edit_special_requirements, edit_avoid_places, edit_previous_experience,
                edit_specific_attractions, edit_travel_style
            ],
            outputs=[edit_result, save_edit_btn]
        )

        # 保存偏好
        save_btn.click(
            fn=save_preference,
            inputs=[
                user_id_box, preference_name, destination, travel_dates, num_travelers, traveler_types,
                budget, travel_pace, interests, accommodation_pref,
                special_requirements, avoid_places, previous_experience,
                specific_attractions, travel_style, result
            ],
            outputs=[status_msg]
        )

        # 清空表单
        clear_btn.click(
            fn=clear_form,
            inputs=[],
            outputs=[
                preference_name, destination, travel_dates, num_travelers, traveler_types,
                budget, travel_pace, interests, accommodation_pref,
                special_requirements, avoid_places, previous_experience,
                specific_attractions, travel_style, result, save_btn, status_msg
            ]
        )

        # 复制提示词
        copy_btn.click(
            fn=copy_to_clipboard,
            inputs=[result],
            outputs=[status_msg]
        )

        # 刷新偏好列表
        refresh_btn.click(
            fn=get_user_preferences_list,
            inputs=[user_id_box, filter_dropdown],
            outputs=[preferences_list, action_status]
        )

        # 筛选变化时更新列表
        filter_dropdown.change(
            fn=get_user_preferences_list,
            inputs=[user_id_box, filter_dropdown],
            outputs=[preferences_list, action_status]
        )

        # 表格选择事件
        preferences_list.select(
            fn=handle_table_select,
            inputs=[preferences_list],
            outputs=[selected_pref_id, selected_info]
        )

        # 查看详情
        view_btn.click(
            fn=view_preference_detail,
            inputs=[user_id_box, selected_pref_id],
            outputs=[pref_detail_info, pref_prompt, detail_accordion]
        )

        # 详情中的复制按钮
        detail_copy_btn.click(
            fn=copy_to_clipboard,
            inputs=[pref_prompt],
            outputs=[action_status]
        )

        # 收藏/取消收藏
        favorite_btn.click(
            fn=toggle_preference_favorite,
            inputs=[user_id_box, selected_pref_id],
            outputs=[action_status]
        ).then(
            fn=get_user_preferences_list,
            inputs=[user_id_box, filter_dropdown],
            outputs=[preferences_list, action_status]
        )

        # 删除偏好
        delete_btn.click(
            fn=delete_user_preference,
            inputs=[user_id_box, selected_pref_id],
            outputs=[action_status, preferences_list]
        ).then(
            fn=get_user_preferences_list,
            inputs=[user_id_box, filter_dropdown],
            outputs=[preferences_list, action_status]
        )

        # 关闭详情
        close_detail_btn.click(
            fn=close_detail_panel,
            inputs=None,
            outputs=[detail_accordion]
        )

        # 加载偏好到编辑表单
        edit_btn.click(
            fn=load_preference_for_edit,
            inputs=[user_id_box, selected_pref_id],
            outputs=[
                edit_tab, edit_preference_name, edit_destination, edit_travel_dates,
                edit_num_travelers, edit_traveler_types, edit_budget, edit_travel_pace,
                edit_interests, edit_accommodation_pref, edit_special_requirements,
                edit_avoid_places, edit_previous_experience, edit_specific_attractions,
                edit_travel_style, editing_pref_id, edit_result
            ]
        )

        # 保存编辑
        save_edit_btn.click(
            fn=save_edited_preference,
            inputs=[
                user_id_box, editing_pref_id, edit_preference_name, edit_destination,
                edit_travel_dates, edit_num_travelers, edit_traveler_types, edit_budget,
                edit_travel_pace, edit_interests, edit_accommodation_pref,
                edit_special_requirements, edit_avoid_places, edit_previous_experience,
                edit_specific_attractions, edit_travel_style, edit_result
            ],
            outputs=[edit_status, edit_tab]
        ).then(
            fn=get_user_preferences_list,
            inputs=[user_id_box, filter_dropdown],
            outputs=[preferences_list, action_status]
        )

        # 取消编辑
        cancel_edit_btn.click(
            fn=cancel_edit,
            inputs=None,
            outputs=[edit_tab]
        )

    return app


if __name__ == "__main__":
    app = create_travel_preferences_app()
    app.launch()
