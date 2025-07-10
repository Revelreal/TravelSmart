import re

import gradio as gr
from datetime import datetime, timedelta
import os
import requests
import toml
from MainProject.dbhelper.MONGOHelper import MongoHelper
from MainProject.auth_utils import verify_token
import uuid


# 数据库操作相关的函数 - 放在应用类前面
def find_or_create_itinerary(user_id, title, start_date, end_date, description=""):
    """查找行程，如果不存在则创建新行程"""
    if not user_id or not title:
        return False, None, "用户ID和标题不能为空"

    print(f"查找或创建行程: {title}")

    mh = MongoHelper()
    try:
        # 先查找是否存在相同行程
        collection = mh.get_collection("Itineraries")
        existing = collection.find_one({
            "user_id": user_id,
            "title": title,
            "start_date": start_date,
            "end_date": end_date
        })

        # 如果找到，直接返回
        if existing:
            existing["_id"] = str(existing["_id"])
            print(f"找到已存在行程: {existing['_id']}")
            return True, existing, "找到已存在行程"

        # 不存在，创建新行程
        new_itinerary = {
            "_id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": title,
            "description": description,
            "start_date": start_date,
            "end_date": end_date,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "status": "active",
            "days_count": (end_date - start_date).days + 1,
            "days": []
        }

        # 插入数据库
        collection.insert_one(new_itinerary)
        print(f"创建新行程: {new_itinerary['_id']}")

        # 返回新创建的行程
        return True, new_itinerary, "创建新行程成功"
    except Exception as e:
        print(f"查找或创建行程失败: {e}")
        return False, None, f"操作失败: {str(e)}"
    finally:
        mh.close()


# 创建行程相关的数据库表
def create_itinerary_collections(mongo_helper):
    """创建行程表及相关索引"""
    # 行程主表
    itinerary_indexes = [
        [("user_id", 1)],
        [("created_at", -1)],
        [("start_date", 1)],
        [("end_date", 1)]
    ]
    mongo_helper.create_collection_with_indexes("Itineraries", itinerary_indexes)

    # 行程天数详情表
    day_indexes = [
        [("itinerary_id", 1)],
        [("day_number", 1)]
    ]
    mongo_helper.create_collection_with_indexes("ItineraryDays", day_indexes)

    # 行程项目表(每天的具体安排)
    item_indexes = [
        [("day_id", 1)],
        [("time_slot", 1)],
        [("type", 1)]
    ]
    mongo_helper.create_collection_with_indexes("ItineraryItems", item_indexes)


# Add this to your database operations
def get_user_itineraries(user_id, limit=10, skip=0):
    if not user_id:
        return []

    print(f"Starting query for user: {user_id}")

    mh = MongoHelper()
    try:
        # Use a context manager pattern if possible
        collection = mh.get_collection("Itineraries")
        cursor = collection.find(
            {"user_id": user_id},
            {"_id": 1, "title": 1, "start_date": 1, "end_date": 1,
             "days_count": 1, "created_at": 1}
        ).sort("created_at", -1).limit(limit)

        # Immediately materialize results
        result = list(cursor)

        # Process dates
        for item in result:
            item["_id"] = str(item["_id"])
            if isinstance(item.get("created_at"), datetime):
                item["created_at"] = item["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(item.get("start_date"), datetime):
                item["start_date"] = item["start_date"].strftime("%Y-%m-%d")
            if isinstance(item.get("end_date"), datetime):
                item["end_date"] = item["end_date"].strftime("%Y-%m-%d")

        return result
    finally:
        mh.close()


def get_itinerary_detail(itinerary_id):
    """获取行程详情，带有性能监控"""
    if not itinerary_id:
        print("Error: Empty itinerary ID received")
        return None

    print(f"Fetching itinerary details for ID: {itinerary_id}")
    start_time = datetime.now()

    mh = MongoHelper()
    try:
        # Get basic itinerary info first
        itineraries_col = mh.get_collection("Itineraries")

        # Try different ID formats if necessary
        # First try string format (which is what you're likely passing)
        itinerary = itineraries_col.find_one({"_id": itinerary_id})

        # If not found and appears to be a UUID, try UUID format
        if not itinerary and is_valid_uuid(itinerary_id):
            try:
                import uuid
                itinerary = itineraries_col.find_one({"_id": uuid.UUID(itinerary_id)})
                print(f"Searched using UUID format: {itinerary_id}")
            except:
                pass

        # If still not found, try ObjectId format
        if not itinerary and len(itinerary_id) == 24:
            try:
                from bson.objectid import ObjectId
                itinerary = itineraries_col.find_one({"_id": ObjectId(itinerary_id)})
                print(f"Searched using ObjectId format: {itinerary_id}")
            except:
                pass

        if not itinerary:
            print(f"No itinerary found with ID: {itinerary_id}")
            return None

        print(f"Found itinerary: {itinerary.get('title', 'Untitled')} with ID: {itinerary['_id']}")

        # Process dates and convert ID
        original_id = itinerary["_id"]
        itinerary["_id"] = str(itinerary["_id"])
        if isinstance(itinerary.get("created_at"), datetime):
            itinerary["created_at"] = itinerary["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(itinerary.get("start_date"), datetime):
            itinerary["start_date"] = itinerary["start_date"].strftime("%Y-%m-%d")
        if isinstance(itinerary.get("end_date"), datetime):
            itinerary["end_date"] = itinerary["end_date"].strftime("%Y-%m-%d")

        # Get days with limit
        days_col = mh.get_collection("ItineraryDays")
        days = list(days_col.find({"itinerary_id": original_id}).sort("day_number", 1).limit(30))
        print(f"Found {len(days)} days for itinerary")

        # If no days found, try with string ID
        if not days:
            print(f"Trying to find days with string ID: {itinerary_id}")
            days = list(days_col.find({"itinerary_id": itinerary_id}).sort("day_number", 1).limit(30))
            print(f"Found {len(days)} days using string ID")

        # Get items for each day
        items_col = mh.get_collection("ItineraryItems")
        days_data = []

        for day in days:
            day_id = day["_id"]
            day["_id"] = str(day["_id"])

            # Get items for this day with limit
            items = list(items_col.find({"day_id": day_id}).limit(50))
            for item in items:
                item["_id"] = str(item["_id"])

            day["items"] = items
            days_data.append(day)

        # Add days to itinerary
        itinerary["days"] = days_data

        query_time = (datetime.now() - start_time).total_seconds()
        print(f"Itinerary detail fetch completed in {query_time:.2f}s")
        return itinerary
    except Exception as e:
        print(f"获取行程详情失败: {e}")
        import traceback
        print(traceback.format_exc())  # Print the full stack trace
        return None
    finally:
        mh.close()
        print("Database connection closed")


def is_valid_uuid(uuid_string):
    """Check if string is a valid UUID"""
    try:
        import uuid
        uuid_obj = uuid.UUID(uuid_string)
        return str(uuid_obj) == uuid_string
    except:
        return False


# 保存行程到数据库 - 同步操作
def save_itinerary(itinerary_data, days_data):
    """保存行程到数据库，同步操作"""
    mh = MongoHelper()
    try:
        # 检查是否是更新已有行程
        if "_id" in itinerary_data and itinerary_data["_id"]:
            # 更新行程
            itinerary_id = itinerary_data["_id"]
            update_data = itinerary_data.copy()
            update_data["updated_at"] = datetime.now()

            # 更新主表
            itinerary_collection = mh.get_collection("Itineraries")
            itinerary_collection.update_one({"_id": itinerary_id}, {"$set": update_data})

            # 删除旧的天数和项目数据
            days_collection = mh.get_collection("ItineraryDays")
            items_collection = mh.get_collection("ItineraryItems")

            # 找到所有天数
            days = list(days_collection.find({"itinerary_id": itinerary_id}))
            for day in days:
                day_id = day["_id"]
                # 删除该天的所有项目
                items_collection.delete_many({"day_id": str(day_id)})

            # 删除所有天数
            days_collection.delete_many({"itinerary_id": itinerary_id})
        else:
            # 创建新行程
            itinerary_id = str(uuid.uuid4())
            itinerary_data["_id"] = itinerary_id
            itinerary_data["created_at"] = datetime.now()
            itinerary_data["updated_at"] = datetime.now()

            # 插入主表
            itinerary_collection = mh.get_collection("Itineraries")
            itinerary_collection.insert_one(itinerary_data)

        # 保存每天的数据
        days_collection = mh.get_collection("ItineraryDays")
        items_collection = mh.get_collection("ItineraryItems")

        for day_data in days_data:
            # 创建天数记录
            day_id = str(uuid.uuid4())
            day_record = {
                "_id": day_id,
                "itinerary_id": itinerary_id,
                "day_number": day_data["day_number"],
                "date": day_data["date"]
            }
            days_collection.insert_one(day_record)

            # 保存该天的具体项目
            for item in day_data["items"]:
                item["_id"] = str(uuid.uuid4())
                item["day_id"] = day_id
                items_collection.insert_one(item)

        return True, itinerary_id
    except Exception as e:
        print(f"保存行程失败: {str(e)}")
        return False, str(e)
    finally:
        mh.close()


# 删除行程 - 同步操作
def delete_itinerary(itinerary_id, user_id):
    """删除行程及相关数据，同步操作"""
    if not itinerary_id or not user_id:
        return False, "参数无效"

    mh = MongoHelper()
    try:
        # 验证行程所有权
        itinerary_collection = mh.get_collection("Itineraries")
        itinerary = itinerary_collection.find_one({"_id": itinerary_id, "user_id": user_id})
        if not itinerary:
            return False, "行程不存在或无权删除"

        # 删除行程相关数据
        days_collection = mh.get_collection("ItineraryDays")
        items_collection = mh.get_collection("ItineraryItems")

        # 找到所有天数
        days = list(days_collection.find({"itinerary_id": itinerary_id}))
        for day in days:
            day_id = day["_id"]
            # 删除该天的所有项目
            items_collection.delete_many({"day_id": str(day_id)})

        # 删除所有天数
        days_collection.delete_many({"itinerary_id": itinerary_id})

        # 删除行程主记录
        itinerary_collection.delete_one({"_id": itinerary_id})

        return True, "行程已成功删除"
    except Exception as e:
        print(f"删除行程失败: {str(e)}")
        return False, str(e)
    finally:
        mh.close()


# 检查重复行程 - 同步操作
def check_duplicate_itinerary(user_id, title, start_date, end_date, exclude_id=None):
    """检查是否存在相似行程，同步操作"""
    if not user_id:
        return False

    mh = MongoHelper()
    try:
        collection = mh.get_collection("Itineraries")
        query = {
            "user_id": user_id,
            "title": title,
            "start_date": start_date,
            "end_date": end_date
        }

        # 如果是更新现有行程，排除自身
        if exclude_id:
            query["_id"] = {"$ne": exclude_id}

        existing = collection.find_one(query)
        return existing is not None
    except Exception as e:
        print(f"检查重复行程错误: {e}")
        return False
    finally:
        mh.close()


# 高德地图API搜索地点 - 同步操作
def search_places_with_amap(keyword=None, location=None, city="全国", type_code=None, radius=1000):
    """使用高德地图API搜索地点，同步操作"""
    try:
        # 获取配置文件中的API密钥
        cfg_path = os.path.join(os.path.dirname(__file__), "../../../config.toml")
        cfg = toml.load(cfg_path)
        api_key = cfg["amap"]["amap_key"]

        # 确定使用关键字搜索还是周边搜索API
        if location:
            # 周边搜索
            url = "https://restapi.amap.com/v3/place/around"
            params = {
                "key": api_key,
                "location": location,  # 经纬度，格式：116.473168,39.993015
                "radius": radius,  # 搜索半径，单位：米
                "output": "json",
                "offset": 20,  # 返回结果数量
                "page": 1
            }

            # 关键词搜索可选
            if keyword:
                params["keywords"] = keyword
        else:
            # 关键字搜索
            url = "https://restapi.amap.com/v3/place/text"
            if not keyword or len(keyword.strip()) < 2:
                return []

            params = {
                "key": api_key,
                "keywords": keyword,
                "city": city,
                "output": "json",
                "offset": 20,
                "page": 1
            }

        # 根据类型筛选
        type_map = {
            "景点": "110000",  # 旅游景点POI类型编码
            "餐饮": "050000",  # 餐饮POI类型编码
            "住宿": "100000",  # 住宿POI类型编码
            "交通": "150000",  # 交通设施POI类型编码
            "购物": "060000"  # 购物POI类型编码
        }

        if type_code in type_map:
            params["types"] = type_map[type_code]

        # 发送请求
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if data.get("status") == "1":
            places = []
            for poi in data.get("pois", []):
                places.append({
                    "id": poi.get("id"),
                    "name": poi.get("name"),
                    "address": poi.get("address") or "地址未知",
                    "type": poi.get("type"),
                    "location": poi.get("location"),
                    "distance": poi.get("distance")  # 周边搜索时返回距离
                })
            return places
        else:
            print(f"高德地图API返回错误: {data.get('info')}")
            return []

    except Exception as e:
        print(f"搜索地点失败: {e}")
        return []


# 创建行程应用界面
def create_itinerary_app():
    with gr.Blocks(title="旅行智能助手 - 行程规划") as app:
        # 隐藏的状态变量
        token_box = gr.Textbox(visible=False)
        user_id_box = gr.Textbox(visible=False)
        username_box = gr.Textbox(visible=False)

        # 编辑模式标志
        edit_mode = gr.State(value=False)
        edit_id = gr.State(value="")

        # 页面标题
        gr.Markdown("## 🌍 旅行智能助手 - 行程规划")
        gr.Markdown("创建您的完美旅行计划，轻松规划每一天的行程")

        # 用户信息显示
        userbar = gr.HTML("正在加载用户信息...")
        gr.HTML("""
                <button onclick="window.history.back()" style="padding: 10px; border-radius: 5px; 
                border: 1px solid #ccc; cursor: pointer;">
                返回主页
                </button>
                """)

        # 主界面使用标签页
        with gr.Tabs() as main_tabs:
            # 我的行程列表页签
            with gr.TabItem("我的行程", id="tab_list"):
                with gr.Row():
                    create_new_btn = gr.Button("创建新行程", variant="primary")
                    refresh_list_btn = gr.Button("刷新列表")

                # 操作结果提示
                operation_result = gr.Markdown("")

                # 简化的行程选择
                gr.Markdown("### 选择行程")
                selected_row = gr.Dropdown(label="我的行程", choices=[], interactive=True)
                itinerary_ids = gr.State([])  # 存储下拉框选项对应的ID

                # 操作按钮
                with gr.Row():
                    view_btn = gr.Button("👁️ 查看行程")
                    edit_btn = gr.Button("✏️ 编辑行程")
                    delete_btn = gr.Button("🗑️ 删除行程")

                # 行程详情对话框
                with gr.Group(visible=False) as detail_modal:
                    gr.Markdown("### 行程详情")
                    itinerary_detail_display = gr.Markdown("加载中...")
                    close_detail_btn = gr.Button("关闭")

            # 创建/编辑行程页签
            with gr.TabItem("创建行程", id="tab_create"):
                # 行程状态
                current_day_number = gr.State(value=1)
                max_days = gr.State(value=1)
                itinerary_data = gr.State(value={
                    "title": "",
                    "description": "",
                    "start_date": "",
                    "end_date": "",
                    "days": []
                })

                # 基本信息表单
                with gr.Group():
                    edit_status = gr.Markdown("创建新行程")
                    gr.Markdown("### 基本信息")
                    title_input = gr.Textbox(label="行程标题", placeholder="例如：三亚5日游、北京历史文化之旅...")

                    with gr.Row():
                        start_date_input = gr.Textbox(label="开始日期", placeholder="YYYY-MM-DD格式")
                        end_date_input = gr.Textbox(label="结束日期", placeholder="YYYY-MM-DD格式")

                    description_input = gr.Textbox(label="行程描述", placeholder="简要描述此次旅行的目的、特点...",
                                                   lines=3)

                    calculate_days_btn = gr.Button("计算天数")
                    days_result = gr.Markdown("请先输入开始和结束日期")

                # 天数选择
                with gr.Group():
                    gr.Markdown("### 天数管理")

                    with gr.Row():
                        prev_day_btn = gr.Button("上一天")
                        day_indicator = gr.Markdown("第 1 天")
                        next_day_btn = gr.Button("下一天")

                    # 当前天的日期显示
                    current_day_date = gr.Markdown("日期：未设置")

                # 当天行程安排
                with gr.Accordion("当天行程安排", open=True):
                    # 上午安排
                    with gr.Group():
                        gr.Markdown("#### 上午")
                        with gr.Row():
                            morning_type = gr.Dropdown(
                                ["景点", "餐饮", "交通", "购物", "其他"],
                                label="类型",
                                value="景点"
                            )
                            morning_search = gr.Textbox(label="搜索地点", placeholder="输入地点名称")
                            morning_search_btn = gr.Button("搜索")

                        morning_results = gr.Dataframe(
                            headers=["名称", "地址", "类型"],
                            label="搜索结果",
                            interactive=True,
                            visible=False
                        )

                        with gr.Row(visible=False) as morning_selected_row:
                            morning_selected = gr.Textbox(label="已选地点")
                            morning_notes = gr.Textbox(label="备注", placeholder="添加备注信息...")
                            morning_confirm_btn = gr.Button("确认添加")

                        morning_place_cache = gr.State(value=[])
                        morning_selected_data = gr.State(value=None)

                    # 中午安排
                    with gr.Group():
                        gr.Markdown("#### 中午")
                        with gr.Row():
                            noon_type = gr.Dropdown(
                                ["景点", "餐饮", "交通", "购物", "其他"],
                                label="类型",
                                value="餐饮"
                            )
                            noon_search = gr.Textbox(label="搜索地点", placeholder="输入地点名称")
                            noon_search_btn = gr.Button("搜索")

                        noon_results = gr.Dataframe(
                            headers=["名称", "地址", "类型"],
                            label="搜索结果",
                            interactive=True,
                            visible=False
                        )

                        with gr.Row(visible=False) as noon_selected_row:
                            noon_selected = gr.Textbox(label="已选地点")
                            noon_notes = gr.Textbox(label="备注", placeholder="添加备注信息...")
                            noon_confirm_btn = gr.Button("确认添加")

                        noon_place_cache = gr.State(value=[])
                        noon_selected_data = gr.State(value=None)

                    # 下午安排
                    with gr.Group():
                        gr.Markdown("#### 下午")
                        with gr.Row():
                            afternoon_type = gr.Dropdown(
                                ["景点", "餐饮", "交通", "购物", "其他"],
                                label="类型",
                                value="景点"
                            )
                            afternoon_search = gr.Textbox(label="搜索地点", placeholder="输入地点名称")
                            afternoon_search_btn = gr.Button("搜索")

                        afternoon_results = gr.Dataframe(
                            headers=["名称", "地址", "类型"],
                            label="搜索结果",
                            interactive=True,
                            visible=False
                        )

                        with gr.Row(visible=False) as afternoon_selected_row:
                            afternoon_selected = gr.Textbox(label="已选地点")
                            afternoon_notes = gr.Textbox(label="备注", placeholder="添加备注信息...")
                            afternoon_confirm_btn = gr.Button("确认添加")

                        afternoon_place_cache = gr.State(value=[])
                        afternoon_selected_data = gr.State(value=None)

                    # 晚上安排
                    with gr.Group():
                        gr.Markdown("#### 晚上")
                        with gr.Row():
                            evening_type = gr.Dropdown(
                                ["景点", "餐饮", "交通", "购物", "其他"],
                                label="类型",
                                value="餐饮"
                            )
                            evening_search = gr.Textbox(label="搜索地点", placeholder="输入地点名称")
                            evening_search_btn = gr.Button("搜索")

                        evening_results = gr.Dataframe(
                            headers=["名称", "地址", "类型"],
                            label="搜索结果",
                            interactive=True,
                            visible=False
                        )

                        with gr.Row(visible=False) as evening_selected_row:
                            evening_selected = gr.Textbox(label="已选地点")
                            evening_notes = gr.Textbox(label="备注", placeholder="添加备注信息...")
                            evening_confirm_btn = gr.Button("确认添加")

                        evening_place_cache = gr.State(value=[])
                        evening_selected_data = gr.State(value=None)

                    # 住宿安排
                    with gr.Group():
                        gr.Markdown("#### 住宿")
                        with gr.Row():
                            accommodation_type = gr.Dropdown(
                                ["住宿"],
                                label="类型",
                                value="住宿"
                            )
                            accommodation_search = gr.Textbox(label="搜索酒店", placeholder="输入酒店名称")
                            accommodation_search_btn = gr.Button("搜索")

                        accommodation_results = gr.Dataframe(
                            headers=["名称", "地址", "类型"],
                            label="搜索结果",
                            interactive=True,
                            visible=False
                        )

                        with gr.Row(visible=False) as accommodation_selected_row:
                            accommodation_selected = gr.Textbox(label="已选酒店")
                            accommodation_notes = gr.Textbox(label="备注", placeholder="添加备注信息...")
                            accommodation_confirm_btn = gr.Button("确认添加")

                        accommodation_place_cache = gr.State(value=[])
                        accommodation_selected_data = gr.State(value=None)

                # 当前天的行程预览
                with gr.Group():
                    gr.Markdown("### 当天安排预览")
                    day_preview = gr.Markdown("暂无安排")

                # 保存行程按钮
                with gr.Row():
                    save_btn = gr.Button("保存行程", variant="primary")
                    generate_template_btn = gr.Button("生成行程模板")
                    back_to_list_btn = gr.Button("返回列表")

                save_result = gr.Markdown("")

        # 函数：加载用户信息 - 获取令牌
        def load_user_data(request: gr.Request):
            try:
                token = request.query_params.get("token", "")
                info = verify_token(token)
                if not info or not info.get("username"):
                    return token, "", "", "⚠️ 未登录或令牌无效，请重新登录"

                # 从token中获取用户ID
                user_id = info.get("id", "")
                username = info.get("username", "")

                return token, user_id, username, f"👤 当前用户: {username}"
            except Exception as e:
                print(f"加载用户信息失败: {e}")
                return "", "", "", "⚠️ 加载用户信息失败，请刷新页面重试"

        # 更新行程选择器
        def update_itinerary_selector(user_id):
            """加载用户行程到下拉选择器"""
            if not user_id:
                return gr.update(choices=[], value=None), []

            try:
                # 获取用户行程
                itineraries = get_user_itineraries(user_id)

                # 格式化下拉选项: "Title (ID: actual_id)"
                choices = []
                ids = []
                for item in itineraries:
                    itinerary_id = str(item["_id"])
                    title = item.get("title", "无标题")
                    formatted_item = f"{title} (ID: {itinerary_id})"
                    choices.append(formatted_item)
                    ids.append(itinerary_id)

                return gr.update(choices=choices, value=choices[0] if choices else None), ids
            except Exception as e:
                print(f"加载行程选择器失败: {e}")
                return gr.update(choices=[], value=None), []

        # 从选择中提取ID
        def get_selected_id(selection):
            """从下拉选择中提取行程ID"""
            print(f"Selection received: '{selection}'")

            if not selection:
                print("未选择行程 - selection is empty")
                return None

            try:
                # 从格式"Title (ID: actual_id)"中提取ID
                match = re.search(r'ID: ([^)]+)', selection)
                if match:
                    selected_id = match.group(1)
                    print(f"成功提取行程ID: {selected_id}")
                    return selected_id
                else:
                    print(f"无法从'{selection}'中提取ID - 正则表达式没有匹配")
                    return None
            except Exception as e:
                print(f"提取ID时出错: {e}")
                return None

        # 函数：搜索地点
        def search_places(keyword, place_type):
            """搜索地点"""
            try:
                if not keyword or len(keyword.strip()) < 2:
                    return gr.update(visible=False), [], "请输入至少2个字符进行搜索"

                # 调用高德地图API进行搜索
                places = search_places_with_amap(keyword=keyword, type_code=place_type)

                if not places:
                    return gr.update(visible=False), [], "未找到相关地点，请修改关键词重试"

                # 构建表格数据
                df_data = []
                for place in places:
                    df_data.append([
                        place["name"],
                        place.get("address", "地址未知"),
                        place.get("type", "").split(";")[0]
                    ])

                return gr.update(value=df_data, visible=True), places, ""
            except Exception as e:
                print(f"搜索地点失败: {e}")
                return gr.update(visible=False), [], f"搜索失败: {str(e)}"

        # 函数：选择地点
        def select_place(evt: gr.SelectData, places):
            """选择搜索结果中的地点"""
            try:
                if places is None or len(places) == 0 or evt.index[0] >= len(places):
                    return "选择无效", None, gr.update(visible=False)

                selected = places[evt.index[0]]
                return f"{selected['name']} ({selected['address']})", selected, gr.update(visible=True)
            except Exception as e:
                print(f"选择地点失败: {e}")
                return "选择失败，请重试", None, gr.update(visible=False)

        # 函数：确认添加地点
        def confirm_place(time_slot, day_number, selected_place, notes, m_itinerary_data):
            """确认添加地点到行程"""
            try:
                if selected_place is None:
                    return m_itinerary_data, "未选择地点"

                # 创建地点项数据
                place_item = {
                    "day_number": day_number,
                    "time_slot": time_slot,
                    "type": selected_place.get("type", "").split(";")[0] if "type" in selected_place else "景点",
                    "name": selected_place["name"],
                    "address": selected_place.get("address", ""),
                    "location": selected_place.get("location", ""),
                    "notes": notes,
                    "poi_id": selected_place["id"]
                }

                # 更新行程数据
                if not isinstance(m_itinerary_data, dict):
                    m_itinerary_data = {"days": []}

                if "days" not in m_itinerary_data:
                    m_itinerary_data["days"] = []

                # 查找当天数据
                day_found = False
                for day in m_itinerary_data["days"]:
                    if day.get("day_number") == day_number:
                        # 更新现有天数
                        if "items" not in day:
                            day["items"] = []

                        # 检查是否已有相同时间段的项目
                        slot_item_index = None
                        for i, item in enumerate(day["items"]):
                            if item.get("time_slot") == time_slot:
                                slot_item_index = i
                                break

                        if slot_item_index is not None:
                            # 替换现有项目
                            day["items"][slot_item_index] = place_item
                        else:
                            # 添加新项目
                            day["items"].append(place_item)

                        day_found = True
                        break

                if not day_found:
                    # 添加新的天数
                    m_itinerary_data["days"].append({
                        "day_number": day_number,
                        "items": [place_item]
                    })

                # 更新预览
                preview = generate_day_preview(day_number, m_itinerary_data)

                return m_itinerary_data, preview
            except Exception as e:
                print(f"添加地点失败: {e}")
                return m_itinerary_data, f"添加地点失败: {str(e)}"

        # 格式化行程详情
        # 修改 format_itinerary_display 函数
        def format_itinerary_display(itinerary_data):
            """格式化行程显示"""
            try:
                # 确保数据是字典类型
                if isinstance(itinerary_data, str):
                    import json
                    try:
                        itinerary = json.loads(itinerary_data)
                    except json.JSONDecodeError:
                        return "行程数据格式错误，无法解析JSON。"
                else:
                    itinerary = itinerary_data

                if not itinerary or not isinstance(itinerary, dict):
                    return "未找到有效的行程数据。"

                # 格式化基本信息
                display = f"## {itinerary.get('title', '未命名行程')}\n\n"
                display += f"**开始日期**: {itinerary.get('start_date', '未设置')}\n"
                display += f"**结束日期**: {itinerary.get('end_date', '未设置')}\n"

                if itinerary.get('description'):
                    display += f"\n**行程描述**: {itinerary.get('description')}\n"

                display += "\n---\n\n"

                # 处理天数据
                if 'days' in itinerary and itinerary['days']:
                    # 按天数排序
                    sorted_days = sorted(itinerary['days'], key=lambda d: d.get('day_number', 0))

                    for day in sorted_days:
                        if not isinstance(day, dict):
                            continue

                        day_num = day.get('day_number', '?')
                        display += f"### 第{day_num}天\n\n"

                        # 按时间段组织项目
                        time_slots = {
                            "morning": {"title": "上午", "items": []},
                            "noon": {"title": "中午", "items": []},
                            "afternoon": {"title": "下午", "items": []},
                            "evening": {"title": "晚上", "items": []},
                            "accommodation": {"title": "住宿", "items": []}
                        }

                        # 收集该天的项目
                        if 'items' in day and day['items']:
                            for item in day['items']:
                                if not isinstance(item, dict):
                                    continue

                                # 确定时间段
                                slot = item.get('time_slot', 'other')
                                if slot in time_slots:
                                    time_slots[slot]["items"].append(item)

                        # 显示每个时间段的内容
                        has_items = False
                        for slot_key, slot_data in time_slots.items():
                            if not slot_data["items"]:
                                continue

                            has_items = True
                            display += f"#### {slot_data['title']}\n"

                            for item in slot_data["items"]:
                                item_name = item.get('name', item.get('title', '未命名项目'))
                                item_type = item.get('type', '其他')

                                display += f"- **{item_name}** ({item_type})\n"

                                if item.get('address'):
                                    display += f"  📍 {item['address']}\n"

                                if item.get('notes'):
                                    display += f"  📝 {item['notes']}\n"

                                display += "\n"

                        if not has_items:
                            display += "该天暂无安排项目。\n\n"
                else:
                    display += "行程中暂无天数据。请添加至少一天的行程安排。\n"

                return display
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                return f"行程内容处理错误: {str(e)}\n\n```\n{error_trace}\n```"

        # 函数：计算天数
        def calculate_days(start_date_str, end_date_str):
            """计算行程天数"""
            try:
                if not start_date_str or not end_date_str:
                    return "请输入开始和结束日期", 1

                try:
                    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

                    if end_date < start_date:
                        return "⚠️ 结束日期不能早于开始日期", 1

                    days = (end_date - start_date).days + 1
                    return f"行程共 {days} 天", days
                except ValueError:
                    return "⚠️ 日期格式无效，请使用YYYY-MM-DD格式", 1
            except Exception as e:
                print(f"计算天数失败: {e}")
                return "⚠️ 计算天数失败，请重试", 1

        # 函数：生成当天预览
        def generate_day_preview(day_number, itinerary_data):
            """生成特定天数的行程预览"""
            try:
                if not isinstance(itinerary_data, dict):
                    return "暂无安排"

                if "days" not in itinerary_data:
                    return "暂无安排"

                # 查找当天数据
                day_data = None
                for day in itinerary_data["days"]:
                    if day.get("day_number") == day_number:
                        day_data = day
                        break

                if not day_data:
                    return "暂无安排"

                if "items" not in day_data or not day_data["items"]:
                    return "暂无安排"

                # 生成预览文本
                preview = f"### 第 {day_number} 天安排\n\n"

                # 按时间段分组
                time_slots = {
                    "morning": {"title": "上午", "items": []},
                    "noon": {"title": "中午", "items": []},
                    "afternoon": {"title": "下午", "items": []},
                    "evening": {"title": "晚上", "items": []},
                    "accommodation": {"title": "住宿", "items": []}
                }

                # 对项目进行分组
                for item in day_data["items"]:
                    slot = item.get("time_slot", "other")
                    if slot in time_slots:
                        time_slots[slot]["items"].append(item)

                # 生成每个时间段的文本
                for slot_key, slot_data in time_slots.items():
                    slot_items = slot_data["items"]
                    if not slot_items:
                        continue

                    preview += f"#### {slot_data['title']}\n"

                    for item in slot_items:
                        item_type = item.get("type", "其他")
                        item_name = item.get("name", "未命名")
                        item_address = item.get("address", "")
                        item_notes = item.get("notes", "")

                        preview += f"- **{item_name}** ({item_type})\n"
                        if item_address:
                            preview += f"  📍 {item_address}\n"
                        if item_notes:
                            preview += f"  📝 {item_notes}\n"

                    preview += "\n"

                return preview
            except Exception as e:
                print(f"生成预览失败: {e}")
                return "生成预览失败，请重试"

        # 函数：切换天数
        def change_day(action, current, m_max_days):
            """切换天数"""
            try:
                if action == "next" and current < m_max_days:
                    return current + 1
                elif action == "prev" and current > 1:
                    return current - 1
                return current
            except Exception as e:
                print(f"切换天数失败: {e}")
                return current

        # 函数：更新天数显示
        def update_day_display(day_number, start_date_str, m_itinerary_data):
            """更新天数显示"""
            try:
                # 计算当前天的日期
                date_display = "日期：未设置"
                if start_date_str:
                    try:
                        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                        current_date = start_date + timedelta(days=day_number - 1)
                        date_display = f"日期：{current_date.strftime('%Y-%m-%d')}"
                    except ValueError:
                        date_display = "日期：未设置"

                # 更新天数显示
                day_title = f"第 {day_number} 天"

                # 生成当天预览
                preview = generate_day_preview(day_number, m_itinerary_data)

                return day_title, date_display, preview
            except Exception as e:
                print(f"更新天数显示失败: {e}")
                return f"第 {day_number} 天", "日期：未设置", "加载预览失败，请重试"

        # 函数：生成行程模板
        def generate_itinerary_template(title, start_date_str, end_date_str, description):
            """生成行程模板"""
            try:
                # 验证基本信息
                if not start_date_str or not end_date_str:
                    return "⚠️ 请先输入开始和结束日期", {}

                try:
                    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

                    if end_date < start_date:
                        return "⚠️ 结束日期不能早于开始日期", {}

                    days_count = (end_date - start_date).days + 1
                except ValueError:
                    return "⚠️ 日期格式无效，请使用YYYY-MM-DD格式", {}

                # 创建新的行程数据
                new_itinerary = {
                    "title": title,
                    "description": description,
                    "start_date": start_date_str,
                    "end_date": end_date_str,
                    "days_count": days_count,
                    "days": []
                }

                # 为每天生成默认模板
                for day in range(1, days_count + 1):
                    day_items = [{
                        "day_number": day,
                        "time_slot": "morning",
                        "type": "景点",
                        "name": f"景点{day}-1",
                        "address": "请搜索并选择具体景点",
                        "notes": "上午景点游览",
                        "poi_id": f"template_morning_{day}"
                    }, {
                        "day_number": day,
                        "time_slot": "noon",
                        "type": "餐饮",
                        "name": f"午餐地点{day}",
                        "address": "请搜索并选择具体餐厅",
                        "notes": "午餐时间",
                        "poi_id": f"template_noon_{day}"
                    }, {
                        "day_number": day,
                        "time_slot": "afternoon",
                        "type": "景点",
                        "name": f"景点{day}-2",
                        "address": "请搜索并选择具体景点",
                        "notes": "下午景点游览",
                        "poi_id": f"template_afternoon_{day}"
                    }, {
                        "day_number": day,
                        "time_slot": "evening",
                        "type": "餐饮",
                        "name": f"晚餐地点{day}",
                        "address": "请搜索并选择具体餐厅",
                        "notes": "晚餐时间",
                        "poi_id": f"template_evening_{day}"
                    }, {
                        "day_number": day,
                        "time_slot": "accommodation",
                        "type": "住宿",
                        "name": f"住宿地点{day}",
                        "address": "请搜索并选择具体酒店",
                        "notes": "预订酒店",
                        "poi_id": f"template_accommodation_{day}"
                    }]

                    # 添加到天数
                    new_itinerary["days"].append({
                        "day_number": day,
                        "items": day_items
                    })

                # 更新当前预览
                preview = generate_day_preview(1, new_itinerary)

                return f"✅ 已生成{days_count}天的行程模板，请根据需要修改具体安排\n\n{preview}", new_itinerary
            except Exception as e:
                print(f"生成行程模板失败: {e}")
                return f"❌ 生成行程模板失败: {str(e)}", {}

        # 函数：保存行程数据
        def save_itinerary_data(token, user_id, username, title, start_date_str, end_date_str,
                                description, days_count, m_itinerary_data, edit_mode, edit_id):
            """保存行程数据"""
            try:
                # 验证用户登录状态
                info = verify_token(token)
                if not info or not info.get("username") or not info.get("id"):
                    return "⚠️ 未登录或会话已过期，请重新登录", edit_mode, edit_id, gr.update(selected="tab_create")

                # 验证必填字段
                if not title or not title.strip():
                    return "⚠️ 请输入行程标题", edit_mode, edit_id, gr.update(selected="tab_create")

                if not start_date_str or not end_date_str:
                    return "⚠️ 请输入行程开始日期和结束日期", edit_mode, edit_id, gr.update(selected="tab_create")

                # 验证日期格式
                try:
                    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

                    # 验证日期逻辑
                    if end_date < start_date:
                        return "⚠️ 结束日期不能早于开始日期", edit_mode, edit_id, gr.update(selected="tab_create")

                    # 计算天数范围
                    date_diff = (end_date - start_date).days + 1
                    if date_diff != days_count:
                        return f"⚠️ 日期范围({date_diff}天)与设定的行程天数({days_count}天)不匹配", edit_mode, edit_id, gr.update(
                            selected="tab_create")
                except ValueError:
                    return "⚠️ 日期格式无效，请使用YYYY-MM-DD格式", edit_mode, edit_id, gr.update(selected="tab_create")

                # 检查是否有行程内容
                if not m_itinerary_data.get("days"):
                    return "⚠️ 请至少添加一天的行程内容", edit_mode, edit_id, gr.update(selected="tab_create")

                # 检查重复行程
                current_id = edit_id if edit_mode else None
                if check_duplicate_itinerary(user_id, title, start_date, end_date, exclude_id=current_id):
                    return "⚠️ 已存在相同标题和日期的行程，请修改后重试", edit_mode, edit_id, gr.update(
                        selected="tab_create")

                # 更新行程基本信息
                m_itinerary_data["title"] = title
                m_itinerary_data["description"] = description
                m_itinerary_data["start_date"] = start_date
                m_itinerary_data["end_date"] = end_date
                m_itinerary_data["days_count"] = days_count
                m_itinerary_data["user_id"] = user_id
                m_itinerary_data["username"] = username
                m_itinerary_data["status"] = "active"

                # 如果是编辑模式，设置ID
                if edit_mode and edit_id:
                    m_itinerary_data["_id"] = edit_id

                # 构建天数数据
                days_data = []
                for day in m_itinerary_data["days"]:
                    day_num = day.get("day_number", 1)
                    day_date = start_date + timedelta(days=day_num - 1)

                    # 添加天数数据
                    day_data = {
                        "day_number": day_num,
                        "date": day_date,
                        "items": day.get("items", [])
                    }
                    days_data.append(day_data)

                # 按天数排序
                days_data.sort(key=lambda x: x["day_number"])

                # 保存到数据库
                success, result = save_itinerary(m_itinerary_data, days_data)

                if success:
                    # 重置编辑模式并跳转到列表页
                    return f"✅ 行程{'更新' if edit_mode else '创建'}成功! ID: {result}", False, "", gr.update(
                        selected="tab_list")
                else:
                    return f"❌ 保存失败: {result}", edit_mode, edit_id, gr.update(selected="tab_create")
            except Exception as e:
                print(f"保存行程数据失败: {e}")
                return f"❌ 保存失败: {str(e)}", edit_mode, edit_id, gr.update(selected="tab_create")

        itinerary_id_box = gr.Textbox(visible=False, value="")
        itinerary_data_box = gr.JSON(visible=False)  # 使用JSON组件存储结构化数据

        # 初始加载 - 获取token和用户信息
        app.load(
            fn=load_user_data,
            inputs=None,
            outputs=[token_box, user_id_box, username_box, userbar]
        )

        # 用户ID变化时加载行程列表
        user_id_box.change(
            fn=update_itinerary_selector,
            inputs=[user_id_box],
            outputs=[selected_row, itinerary_ids]
        )

        # 刷新行程列表
        refresh_list_btn.click(
            fn=update_itinerary_selector,
            inputs=[user_id_box],
            outputs=[selected_row, itinerary_ids]
        )

        # 查看按钮处理
        # Then use these components explicitly in your event chain
        view_btn.click(
            fn=get_selected_id,
            inputs=[selected_row],
            outputs=[itinerary_id_box]
        ).then(
            fn=get_itinerary_detail,
            inputs=[itinerary_id_box],
            outputs=[itinerary_data_box]
        ).then(
            fn=format_itinerary_display,
            inputs=[itinerary_data_box],
            outputs=[itinerary_detail_display]
        ).then(
            fn=lambda: gr.update(visible=True),
            inputs=[],
            outputs=[detail_modal]
        )

        # 编辑按钮处理
        edit_btn.click(
            fn=get_selected_id,
            inputs=[selected_row],
            outputs=[gr.State()]
        ).then(
            fn=get_itinerary_detail,
            inputs=[gr.State()],
            outputs=[gr.State()]
        ).then(
            fn=lambda itinerary: (
                True,  # 进入编辑模式
                itinerary["_id"] if itinerary else "",
                f"正在编辑: {itinerary['title'] if itinerary else '未找到行程'}",
                itinerary.get("title", "") if itinerary else "",
                itinerary.get("start_date", "") if itinerary else "",
                itinerary.get("end_date", "") if itinerary else "",
                itinerary.get("description", "") if itinerary else "",
                gr.update(selected="tab_create") if itinerary else gr.update(selected="tab_list"),
                itinerary if itinerary else {}
            ),
            inputs=[gr.State()],
            outputs=[
                edit_mode, edit_id, edit_status,
                title_input, start_date_input, end_date_input, description_input,
                main_tabs, itinerary_data
            ]
        )

        # 关闭详情对话框
        close_detail_btn.click(
            fn=lambda: gr.update(visible=False),
            inputs=None,
            outputs=[detail_modal]
        )

        # 创建新行程
        create_new_btn.click(
            fn=lambda: (False, "", "创建新行程", "", "", "", "", 1, "第 1 天", "日期：未设置", "暂无安排", {}),
            inputs=None,
            outputs=[edit_mode, edit_id, edit_status, title_input, start_date_input, end_date_input,
                     description_input, max_days, day_indicator, current_day_date, day_preview, itinerary_data]
        ).then(
            fn=lambda: gr.update(selected="tab_create"),
            inputs=None,
            outputs=[main_tabs]
        )

        # 返回列表
        back_to_list_btn.click(
            fn=lambda: gr.update(selected="tab_list"),
            inputs=None,
            outputs=[main_tabs]
        )

        # 计算天数
        calculate_days_btn.click(
            fn=calculate_days,
            inputs=[start_date_input, end_date_input],
            outputs=[days_result, max_days]
        )

        # 切换天数 - 下一天
        next_day_btn.click(
            fn=lambda current, m_max_days: change_day("next", current, m_max_days),
            inputs=[current_day_number, max_days],
            outputs=current_day_number
        ).then(
            fn=update_day_display,
            inputs=[current_day_number, start_date_input, itinerary_data],
            outputs=[day_indicator, current_day_date, day_preview]
        )

        # 切换天数 - 上一天
        prev_day_btn.click(
            fn=lambda current, m_max_days: change_day("prev", current, m_max_days),
            inputs=[current_day_number, max_days],
            outputs=current_day_number
        ).then(
            fn=update_day_display,
            inputs=[current_day_number, start_date_input, itinerary_data],
            outputs=[day_indicator, current_day_date, day_preview]
        )

        # 搜索地点事件 - 上午
        morning_search_btn.click(
            fn=search_places,
            inputs=[morning_search, morning_type],
            outputs=[morning_results, morning_place_cache, save_result]
        )

        morning_results.select(
            fn=select_place,
            inputs=[morning_place_cache],
            outputs=[morning_selected, morning_selected_data, morning_selected_row]
        )

        morning_confirm_btn.click(
            fn=confirm_place,
            inputs=[gr.State("morning"), current_day_number, morning_selected_data, morning_notes, itinerary_data],
            outputs=[itinerary_data, day_preview]
        )

        # 搜索地点事件 - 中午
        noon_search_btn.click(
            fn=search_places,
            inputs=[noon_search, noon_type],
            outputs=[noon_results, noon_place_cache, save_result]
        )

        noon_results.select(
            fn=select_place,
            inputs=[noon_place_cache],
            outputs=[noon_selected, noon_selected_data, noon_selected_row]
        )

        noon_confirm_btn.click(
            fn=confirm_place,
            inputs=[gr.State("noon"), current_day_number, noon_selected_data, noon_notes, itinerary_data],
            outputs=[itinerary_data, day_preview]
        )

        # 搜索地点事件 - 下午
        afternoon_search_btn.click(
            fn=search_places,
            inputs=[afternoon_search, afternoon_type],
            outputs=[afternoon_results, afternoon_place_cache, save_result]
        )

        afternoon_results.select(
            fn=select_place,
            inputs=[afternoon_place_cache],
            outputs=[afternoon_selected, afternoon_selected_data, afternoon_selected_row]
        )

        afternoon_confirm_btn.click(
            fn=confirm_place,
            inputs=[gr.State("afternoon"), current_day_number, afternoon_selected_data, afternoon_notes,
                    itinerary_data],
            outputs=[itinerary_data, day_preview]
        )

        # 搜索地点事件 - 晚上
        evening_search_btn.click(
            fn=search_places,
            inputs=[evening_search, evening_type],
            outputs=[evening_results, evening_place_cache, save_result]
        )

        evening_results.select(
            fn=select_place,
            inputs=[evening_place_cache],
            outputs=[evening_selected, evening_selected_data, evening_selected_row]
        )

        evening_confirm_btn.click(
            fn=confirm_place,
            inputs=[gr.State("evening"), current_day_number, evening_selected_data, evening_notes, itinerary_data],
            outputs=[itinerary_data, day_preview]
        )

        # 搜索地点事件 - 住宿
        accommodation_search_btn.click(
            fn=lambda keyword: search_places(keyword, "住宿"),
            inputs=[accommodation_search],
            outputs=[accommodation_results, accommodation_place_cache, save_result]
        )

        accommodation_results.select(
            fn=select_place,
            inputs=[accommodation_place_cache],
            outputs=[accommodation_selected, accommodation_selected_data, accommodation_selected_row]
        )

        accommodation_confirm_btn.click(
            fn=confirm_place,
            inputs=[gr.State("accommodation"), current_day_number, accommodation_selected_data, accommodation_notes,
                    itinerary_data],
            outputs=[itinerary_data, day_preview]
        )

        # 生成行程模板
        generate_template_btn.click(
            fn=generate_itinerary_template,
            inputs=[title_input, start_date_input, end_date_input, description_input],
            outputs=[day_preview, itinerary_data]
        )

        # 保存行程数据
        save_btn.click(
            fn=save_itinerary_data,
            inputs=[
                token_box, user_id_box, username_box,
                title_input, start_date_input, end_date_input, description_input,
                max_days, itinerary_data, edit_mode, edit_id
            ],
            outputs=[save_result, edit_mode, edit_id, main_tabs]
        ).then(
            # 保存后刷新列表
            fn=update_itinerary_selector,
            inputs=[user_id_box],
            outputs=[selected_row, itinerary_ids]
        )

        # 删除确认模态框定义
        with gr.Group(visible=False, elem_id="delete_confirmation_modal") as delete_modal:
            gr.Markdown("### 确认删除行程")
            delete_itinerary_id_box = gr.Textbox(visible=False, value="")
            confirmation_text = gr.Markdown("确认要删除此行程吗？")
            with gr.Row():
                cancel_delete_btn = gr.Button("取消", variant="secondary")
                confirm_delete_btn = gr.Button("确认删除", variant="stop")

        # 删除行程函数 - 修改为支持模态框
        def delete_itinerary(itinerary_id, user_id):
            """删除行程及相关数据"""
            if not itinerary_id:
                return "❌ 删除失败：未选择行程"

            try:
                # 验证行程所有权并删除
                mh = MongoHelper()
                itinerary_collection = mh.get_collection("Itineraries")
                itinerary = itinerary_collection.find_one({"_id": itinerary_id})

                if not itinerary:
                    return "❌ 行程不存在"

                if str(itinerary.get("user_id")) != str(user_id):
                    return "❌ 无权删除此行程"

                # 删除行程相关数据
                days_collection = mh.get_collection("ItineraryDays")
                items_collection = mh.get_collection("ItineraryItems")

                # 找到所有天数
                days = list(days_collection.find({"itinerary_id": itinerary_id}))
                for day in days:
                    day_id = day["_id"]
                    # 删除该天的所有项目
                    items_collection.delete_many({"day_id": str(day_id)})

                # 删除所有天数
                days_collection.delete_many({"itinerary_id": itinerary_id})

                # 删除行程主记录
                itinerary_collection.delete_one({"_id": itinerary_id})
                mh.close()

                return f"✅ 行程 '{itinerary.get('title', '未命名行程')}' 已成功删除"
            except Exception as e:
                print(f"删除行程失败: {str(e)}")
                return f"❌ 删除失败: {str(e)}"

        # 生成删除确认文本
        def confirm_delete(itinerary_id):
            """生成删除确认文本"""
            if not itinerary_id:
                return "无法删除：未选择行程"

            try:
                itinerary = get_itinerary_detail(itinerary_id)
                if not itinerary:
                    return "无法删除：找不到行程信息"

                title = itinerary.get('title', '未命名行程')
                start_date = itinerary.get('start_date', '未知日期')
                end_date = itinerary.get('end_date', '未知日期')

                return f"确认要删除行程 **{title}** ({start_date} 至 {end_date}) 吗？\n\n**此操作不可撤销。**"
            except Exception as e:
                print(f"生成确认文本失败: {e}")
                return f"确认要删除所选行程吗？此操作不可撤销。"

        # 删除按钮事件处理
        delete_btn.click(
            fn=get_selected_id,
            inputs=[selected_row],
            outputs=[delete_itinerary_id_box]
        ).then(
            fn=confirm_delete,
            inputs=[delete_itinerary_id_box],
            outputs=[confirmation_text]
        ).then(
            fn=lambda: gr.update(visible=True),
            inputs=[],
            outputs=[delete_modal]
        )

        # 取消删除按钮事件
        cancel_delete_btn.click(
            fn=lambda: gr.update(visible=False),
            inputs=[],
            outputs=[delete_modal]
        )

        # 确认删除按钮事件
        confirm_delete_btn.click(
            fn=delete_itinerary,
            inputs=[delete_itinerary_id_box, user_id_box],
            outputs=[operation_result]
        ).then(
            fn=update_itinerary_selector,  # 刷新行程列表
            inputs=[user_id_box],
            outputs=[selected_row, itinerary_ids]
        ).then(
            fn=lambda: gr.update(visible=False),  # 关闭模态框
            inputs=[],
            outputs=[delete_modal]
        )

        # 2. 完善修改功能 - 修复数据流转

        # 编辑行程ID和数据的隐藏存储
        edit_itinerary_id_box = gr.Textbox(visible=False, value="")
        edit_itinerary_data_box = gr.JSON(visible=False)

        # 编辑按钮处理 - 修复数据流转
        edit_btn.click(
            fn=get_selected_id,
            inputs=[selected_row],
            outputs=[edit_itinerary_id_box]
        ).then(
            fn=get_itinerary_detail,
            inputs=[edit_itinerary_id_box],
            outputs=[edit_itinerary_data_box]
        ).then(
            fn=lambda itinerary: (
                True,  # 进入编辑模式
                itinerary.get("_id", "") if itinerary else "",
                f"正在编辑: {itinerary.get('title', '未找到行程')}",
                itinerary.get("title", "") if itinerary else "",
                itinerary.get("start_date", "") if itinerary else "",
                itinerary.get("end_date", "") if itinerary else "",
                itinerary.get("description", "") if itinerary else "",
                gr.update(selected="tab_create"),
                itinerary if itinerary else {}
            ),
            inputs=[edit_itinerary_data_box],
            outputs=[
                edit_mode, edit_id, edit_status,
                title_input, start_date_input, end_date_input, description_input,
                main_tabs, itinerary_data
            ]
        ).then(
            # 编辑模式下，需要计算并更新天数
            fn=calculate_days,
            inputs=[start_date_input, end_date_input],
            outputs=[days_result, max_days]
        ).then(
            # 更新第一天的预览
            fn=lambda data: 1,  # 设置为第一天
            inputs=[itinerary_data],
            outputs=[current_day_number]
        ).then(
            fn=update_day_display,
            inputs=[current_day_number, start_date_input, itinerary_data],
            outputs=[day_indicator, current_day_date, day_preview]
        )

        return app

