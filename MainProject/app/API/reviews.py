import gradio as gr
from datetime import datetime
import os
import requests
import toml
import json
from MainProject.dbhelper.MONGOHelper import MongoHelper
from MainProject.auth_utils import verify_token

# 评价系统的标签约束
REVIEW_TAGS = {
    "景点": ["风景优美", "历史悠久", "人流量大", "适合拍照", "交通便利",
             "性价比高", "环境清幽", "服务周到", "设施完善", "适合家庭"],
    "美食": ["味道好", "环境好", "服务好", "性价比高", "分量足",
             "特色菜", "干净卫生", "装修精美", "停车方便", "适合聚会"],
    "服务": ["服务态度好", "专业水平高", "响应速度快", "解决问题彻底",
             "沟通顺畅", "价格合理", "有耐心", "服务热情", "设施现代化"]
}


def validate_review_tags(target_type, tags):
    """验证评价标签是否合法"""
    if target_type not in REVIEW_TAGS:
        return False, f"无效的评价类型: {target_type}"

    allowed_tags = REVIEW_TAGS[target_type]
    invalid_tags = [tag for tag in tags if tag not in allowed_tags]

    if invalid_tags:
        return False, f"包含无效标签: {invalid_tags}"

    return True, "标签验证通过"


def add_review(review_data):
    """添加一条评价"""
    mh = MongoHelper()
    try:
        # 验证必填字段
        required_fields = ["user_id", "username", "target_id", "target_name",
                           "target_type", "rating", "content"]
        for field in required_fields:
            if field not in review_data or not review_data[field]:
                return False, f"缺少必填字段: {field}"

        # 验证评分范围
        try:
            rating = float(review_data.get("rating", 0))
            if not (1 <= rating <= 5):
                return False, "评分必须在1-5之间"
            review_data["rating"] = rating
        except:
            return False, "评分必须是有效数字"

        # 验证标签
        tags = review_data.get("tags", [])
        valid, message = validate_review_tags(review_data["target_type"], tags)
        if not valid:
            return False, message

        # 添加时间戳
        now = datetime.now()
        review_data["created_at"] = now

        # 确保图片字段存在
        if "images" not in review_data:
            review_data["images"] = []

        # 插入数据库
        collection = mh.get_collection("Reviews")
        result = collection.insert_one(review_data)
        return True, f"评价添加成功 (ID: {result.inserted_id})"
    except Exception as e:
        return False, f"添加评价失败: {str(e)}"
    finally:
        mh.close()


def get_user_reviews(user_id, limit=10):
    """获取用户的所有评价"""
    mh = MongoHelper()
    try:
        collection = mh.get_collection("Reviews")
        reviews = list(collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit))
        # 将ObjectId转换为字符串，方便JSON序列化
        for review in reviews:
            review["_id"] = str(review["_id"])
            if isinstance(review["created_at"], datetime):
                review["created_at"] = review["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        return reviews
    except Exception as e:
        print(f"获取评价失败: {e}")
        return []
    finally:
        mh.close()


def get_target_reviews(target_id, target_type=None, limit=10, skip=0):
    """获取指定目标的评价"""
    mh = MongoHelper()
    try:
        collection = mh.get_collection("Reviews")
        query = {"target_id": target_id}
        if target_type:
            query["target_type"] = target_type

        # 按时间倒序排列
        reviews = list(collection.find(query).sort("created_at", -1).skip(skip).limit(limit))
        # 将ObjectId转换为字符串，方便JSON序列化
        for review in reviews:
            review["_id"] = str(review["_id"])
            if isinstance(review["created_at"], datetime):
                review["created_at"] = review["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        return reviews
    except Exception as e:
        print(f"获取评价失败: {e}")
        return []
    finally:
        mh.close()


def search_reviews(target_type=None, min_rating=None, tag=None, limit=20):
    """搜索评价"""
    mh = MongoHelper()
    try:
        collection = mh.get_collection("Reviews")
        query = {}

        if target_type and target_type != "全部":
            query["target_type"] = target_type

        if min_rating and min_rating > 1:
            query["rating"] = {"$gte": min_rating}

        if tag and tag != "全部标签":
            query["tags"] = tag

        # 按时间倒序排列
        reviews = list(collection.find(query).sort("created_at", -1).limit(limit))
        # 将ObjectId转换为字符串，方便JSON序列化
        for review in reviews:
            review["_id"] = str(review["_id"])
            if isinstance(review["created_at"], datetime):
                review["created_at"] = review["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        return reviews
    except Exception as e:
        print(f"搜索评价失败: {e}")
        return []
    finally:
        mh.close()


def get_targets_by_type(target_type):
    """根据类型获取可评价的目标列表"""
    mh = MongoHelper()
    try:
        # 根据类型确定集合名称
        collection_map = {
            "景点": "Spots",
            "美食": "Foods",
            "服务": "Routes"  # 假设服务对应Routes集合
        }

        if target_type not in collection_map:
            return []

        collection_name = collection_map[target_type]
        collection = mh.get_collection(collection_name)

        # 从对应集合中查询目标数据
        targets = list(collection.find({}, {"_id": 1, "name": 1}))
        return [{"id": str(t["_id"]), "name": t["name"]} for t in targets]
    except Exception as e:
        print(f"获取目标列表失败: {e}")
        return []
    finally:
        mh.close()


def get_all_tags(target_type=None):
    """获取所有标签"""
    if target_type and target_type in REVIEW_TAGS:
        return ["全部标签"] + REVIEW_TAGS[target_type]

    # 如果未指定类型，返回所有标签
    all_tags = ["全部标签"]
    for tags in REVIEW_TAGS.values():
        all_tags.extend(tags)
    return list(set(all_tags))  # 去重


def format_reviews_html(reviews):
    """将评价列表格式化为HTML显示"""
    if not reviews:
        return "<div class='no-reviews'>暂无评价数据</div>"

    html = "<div class='reviews-container'>"
    for review in reviews:
        # 评分星星
        stars = "★" * int(review["rating"])
        if review["rating"] % 1 == 0.5:
            stars += "½"
        stars += "☆" * int(5 - review["rating"])

        # 标签
        tags_html = ""
        if review.get("tags"):
            tags_html = "<div class='review-tags'>" + " ".join(
                [f"<span class='tag'>{tag}</span>" for tag in review["tags"]]) + "</div>"

        # 图片
        images_html = ""
        if review.get("images") and len(review["images"]) > 0:
            images_html = "<div class='review-images'>"
            for img in review["images"]:
                images_html += f"<img src='{img['url']}' alt='{img.get('description', '')}' class='review-img'/>"
            images_html += "</div>"

        # 地址信息
        location_html = ""
        if review.get("target_address"):
            location_html = f"<div class='review-location'><i class='location-icon'>📍</i> {review['target_address']}</div>"

        html += f"""
        <div class='review-item'>
            <div class='review-header'>
                <span class='review-user'>{review["username"]}</span>
                <span class='review-rating'>{stars}</span>
                <span class='review-date'>{review["created_at"]}</span>
            </div>
            <div class='review-target'>{review["target_name"]} ({review["target_type"]})</div>
            {location_html}
            {tags_html}
            <div class='review-content'>{review["content"]}</div>
            {images_html}
        </div>
        """

    html += "</div>"

    # 改进CSS样式以提高可读性
    html += """
    <style>
    .reviews-container { font-family: Arial, sans-serif; background-color: #ffffff; }
    .review-item { border: 1px solid #dddddd; border-radius: 8px; padding: 16px; margin-bottom: 16px; background-color: #fcfcfc; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .review-header { display: flex; justify-content: space-between; margin-bottom: 8px; border-bottom: 1px solid #eee; padding-bottom: 8px; }
    .review-user { font-weight: bold; color: #2c3e50; }
    .review-rating { color: #f39c12; font-size: 1.1em; }
    .review-date { color: #7f8c8d; font-size: 0.9em; }
    .review-target { font-weight: bold; margin-bottom: 4px; color: #3498db; background-color: #f8f9fa; padding: 4px 8px; border-radius: 4px; display: inline-block; }
    .review-location { color: #7f8c8d; margin-bottom: 8px; font-size: 0.9em; }
    .location-icon { margin-right: 4px; }
    .review-tags { margin-bottom: 8px; }
    .tag { background: #e9f7fe; color: #0366d6; padding: 4px 8px; border-radius: 4px; font-size: 0.9em; margin-right: 6px; display: inline-block; margin-bottom: 4px; }
    .review-content { line-height: 1.5; margin-bottom: 12px; color: #333333; background-color: #ffffff; padding: 8px; border-left: 3px solid #eee; }
    .review-images { display: flex; flex-wrap: wrap; gap: 8px; }
    .review-img { max-width: 150px; max-height: 150px; border-radius: 4px; border: 1px solid #eee; }
    .no-reviews { text-align: center; padding: 30px; color: #95a5a6; font-style: italic; background-color: #f9f9f9; border-radius: 8px; }
    </style>
    """

    return html


# 高德地图API集成
def search_places_with_amap(keyword=None, location=None, city="全国", type_code=None, radius=1000):
    """
    使用高德地图API搜索地点
    可通过关键词或经纬度搜索
    """
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
            "美食": "050000",  # 餐饮POI类型编码
            "服务": "070000"  # 生活服务POI类型编码
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


# 解析位置信息
def parse_location(location_text):
    """
    解析位置文本，尝试提取经纬度
    支持多种格式：
    - 经度,纬度
    - 纬度,经度
    - 包含经纬度的JSON或其他文本
    """
    try:
        # 清理输入文本
        location_text = location_text.strip()

        # 检查是否是简单的"经度,纬度"格式
        if ',' in location_text and location_text.count(',') == 1:
            parts = location_text.split(',')
            if len(parts) == 2 and all(is_valid_coordinate(p.strip()) for p in parts):
                # 高德地图API使用"经度,纬度"格式
                return location_text.strip()

        # 尝试从文本中提取经纬度数字
        import re
        coords = re.findall(r'[-+]?[0-9]*\.?[0-9]+', location_text)
        if len(coords) >= 2:
            # 假设前两个数字是经度和纬度
            longitude = coords[0]
            latitude = coords[1]
            if is_valid_coordinate(longitude) and is_valid_coordinate(latitude):
                return f"{longitude},{latitude}"

        # 尝试解析JSON
        try:
            data = json.loads(location_text)
            # 检查常见的JSON格式
            if isinstance(data, dict):
                # 检查常见的字段名
                for lng_field in ['lng', 'longitude', 'lon', 'x']:
                    for lat_field in ['lat', 'latitude', 'y']:
                        if lng_field in data and lat_field in data:
                            return f"{data[lng_field]},{data[lat_field]}"

            # 检查是否为坐标数组 [经度, 纬度]
            elif isinstance(data, list) and len(data) >= 2:
                if all(isinstance(x, (int, float)) for x in data[:2]):
                    return f"{data[0]},{data[1]}"
        except:
            pass

        return None
    except Exception as e:
        print(f"解析位置失败: {e}")
        return None


def is_valid_coordinate(coord_str):
    """检查字符串是否可能是有效的坐标值"""
    try:
        value = float(coord_str)
        # 简单的范围检查
        return -180 <= value <= 180
    except:
        return False


def create_reviews_app():
    with gr.Blocks(title="旅行智能助手 - 评价系统", css="""
    /* 全局样式改进，增强可读性 */
    body {
        font-family: "Helvetica Neue", Arial, sans-serif;
        color: #333333;
    }

    /* 提高所有文本的对比度 */
    .gradio-container {
        color: #222222;
    }

    /* 浮动按钮样式 */
    .review-float-btn {
        position: fixed;
        right: 36px;
        bottom: 36px;
        z-index: 9999;
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background: #007BFF;
        color: #fff;
        font-size: 30px;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 14px rgba(0,0,0,0.18);
        text-decoration: none;
        transition: background 0.18s;
    }
    .review-float-btn:hover {
        background: #1557b1;
    }

    /* 选中地点样式改进 */
    .selected-place {
        padding: 12px;
        background: #e8f4fc;
        border-radius: 6px;
        border-left: 4px solid #2980b9;
        margin-bottom: 12px;
        cursor: default;  /* 防止看起来可编辑 */
        user-select: none; /* 防止选择文本 */
    }
    .selected-place h4 {
        margin: 0 0 5px 0;
        color: #2980b9;
        font-weight: bold;
    }
    .place-address {
        margin: 0;
        color: #2c3e50; /* 更深的颜色提高可读性 */
        font-size: 0.9em;
    }
    .place-distance {
        margin: 5px 0 0 0;
        color: #27ae60;
        font-size: 0.85em;
        font-weight: bold;
    }
    .place-coords {
        font-family: monospace;
        margin: 5px 0 0 0;
        color: #7f8c8d;
        font-size: 0.85em;
    }
    .no-place {
        padding: 10px;
        color: #666;
        font-style: italic;
        text-align: center;
        background-color: #f9f9f9;
        border-radius: 4px;
    }

    /* 用户信息样式改进 */
    .userbar-text {
        font-size: 16px;
        background-color: #f8f9fa;
        padding: 8px 16px;
        border-radius: 4px;
        margin-bottom: 12px;
        border-left: 4px solid #007BFF;
        color: #333;
        font-weight: 500;
    }

    /* 必填字段标记 */
    .required-field::after {
        content: " *";
        color: #e74c3c;
        font-weight: bold;
    }

    /* 搜索区域样式 */
    .search-method-tabs {
        margin-bottom: 10px;
    }
    .search-container {
        margin-top: 10px;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        background-color: #f9f9f9;
    }

    /* 位置信息显示 */
    .location-info {
        font-family: monospace;
        padding: 8px;
        background: #f5f5f5;
        border-radius: 4px;
        margin-bottom: 8px;
        word-break: break-all;
        color: #333;
        border-left: 3px solid #3498db;
    }

    /* 加载指示器 */
    .loading-indicator {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
        color: #333;
    }
    .loading-spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #3498db;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        animation: spin 2s linear infinite;
        margin-right: 10px;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    /* 评价显示样式改进 */
    .reviews-container { 
        font-family: "Helvetica Neue", Arial, sans-serif; 
        background-color: #ffffff; 
    }
    .review-item { 
        border: 1px solid #dddddd; 
        border-radius: 8px; 
        padding: 16px; 
        margin-bottom: 16px; 
        background-color: #fcfcfc; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); 
    }
    .review-header { 
        display: flex; 
        justify-content: space-between; 
        margin-bottom: 8px; 
        border-bottom: 1px solid #eee; 
        padding-bottom: 8px; 
    }
    .review-user { 
        font-weight: bold; 
        color: #2c3e50; 
    }
    .review-rating { 
        color: #f39c12; 
        font-size: 1.1em; 
    }
    .review-date { 
        color: #34495e; 
        font-size: 0.9em; 
    }
    .review-target { 
        font-weight: bold; 
        margin-bottom: 4px; 
        color: #3498db; 
        background-color: #f8f9fa; 
        padding: 4px 8px; 
        border-radius: 4px; 
        display: inline-block; 
    }
    .review-location { 
        color: #34495e; 
        margin: 8px 0; 
        font-size: 0.9em; 
        background: #f8f9fa;
        padding: 4px 8px;
        border-radius: 4px;
        display: inline-block;
    }
    .location-icon { 
        margin-right: 4px; 
        color: #e74c3c;
    }
    .review-tags { 
        margin: 8px 0; 
    }
    .tag { 
        background: #e9f7fe; 
        color: #0366d6; 
        padding: 4px 8px; 
        border-radius: 4px; 
        font-size: 0.9em; 
        margin-right: 6px; 
        display: inline-block; 
        margin-bottom: 4px; 
    }
    .review-content { 
        line-height: 1.5; 
        margin: 12px 0; 
        color: #333333; 
        background-color: #ffffff; 
        padding: 12px; 
        border-left: 3px solid #eee; 
        border-radius: 2px;
    }
    .review-images { 
        display: flex; 
        flex-wrap: wrap; 
        gap: 8px; 
        margin-top: 10px;
    }
    .review-img { 
        max-width: 150px; 
        max-height: 150px; 
        border-radius: 4px; 
        border: 1px solid #eee; 
    }
    .no-reviews { 
        text-align: center; 
        padding: 30px; 
        color: #666; 
        font-style: italic; 
        background-color: #f9f9f9; 
        border-radius: 8px; 
    }

    /* 按钮样式统一 */
    .primary-button {
        background-color: #007BFF !important;
        color: white !important;
    }
    .primary-button:hover {
        background-color: #0056b3 !important;
    }
    """) as app:
        # 隐藏的token输入框和用户信息
        token_box = gr.Textbox(visible=False)
        user_id_box = gr.Textbox(visible=False)
        username_box = gr.Textbox(visible=False)

        # 用于存储POI数据的状态变量
        selected_poi_data = gr.State(value=None)
        search_results_cache = gr.State(value=[])

        # 页面标题
        gr.Markdown("## ⭐ 旅行智能助手 - 评价系统")
        gr.Markdown("分享您的旅行体验，帮助更多的旅行者")

        # 用户信息显示
        userbar = gr.HTML("正在加载用户信息...", elem_classes="userbar-text")
        back_btn_html = gr.HTML("")

        with gr.Tabs():
            # 提交评价表单页签
            with gr.TabItem("提交评价"):
                with gr.Row():
                    with gr.Column(scale=2):
                        # 评价表单
                        target_type = gr.Radio(
                            ["景点", "美食", "服务"],
                            label="评价类型",
                            info="选择您想要评价的对象类型",
                            elem_classes="required-field"
                        )

                        # 搜索方式切换
                        search_method = gr.Radio(
                            ["关键词搜索", "位置搜索"],
                            label="搜索方式",
                            value="关键词搜索",
                            elem_classes="search-method-tabs"
                        )

                        # 关键词搜索容器
                        with gr.Group(elem_classes="search-container") as keyword_search_container:
                            with gr.Row():
                                place_search = gr.Textbox(
                                    label="搜索地点",
                                    placeholder="输入地点名称，如: 故宫博物院、西湖、外滩...",
                                    lines=1
                                )
                                search_btn = gr.Button("搜索", variant="secondary")

                        # 位置搜索容器
                        with gr.Group(visible=False, elem_classes="search-container") as location_search_container:
                            location_input = gr.Textbox(
                                label="输入位置坐标",
                                placeholder="输入经纬度，如: 116.397428,39.90923 或粘贴位置信息",
                                lines=3
                            )

                            location_search_radius = gr.Slider(
                                minimum=100,
                                maximum=5000,
                                value=1000,
                                step=100,
                                label="搜索半径(米)",
                                info="设置搜索范围，单位：米"
                            )

                            location_parsed = gr.HTML(
                                "<div class='no-place'>请输入位置信息</div>",
                                label="解析结果"
                            )

                            location_search_btn = gr.Button("搜索周边", variant="secondary")

                        # 搜索结果状态指示
                        search_status = gr.HTML("")

                        # 地点搜索结果
                        place_results = gr.Dataframe(
                            headers=["名称", "地址", "类型", "距离(米)"],
                            label="搜索结果",
                            interactive=True,
                            visible=False
                        )

                        # 选择地点后显示
                        selected_place = gr.HTML(
                            "<div class='no-place'>尚未选择地点</div>",
                            label="已选地点"
                        )

                        # 移除了"从系统地点中选择"下拉框
                        # 保留原始选择器但设为不可见，用于数据传递
                        gr.Dropdown(
                            [],
                            visible=False
                        )

                        rating = gr.Slider(
                            minimum=1,
                            maximum=5,
                            value=5,
                            step=0.5,
                            label="评分",
                            info="1-5分，可选半星",
                            elem_classes="required-field"
                        )

                        tags = gr.CheckboxGroup(
                            [],
                            label="标签",
                            info="选择适合的标签(可多选)"
                        )

                        content = gr.Textbox(
                            label="评价内容",
                            placeholder="请输入您的详细评价...",
                            lines=5,
                            elem_classes="required-field"
                        )

                        images = gr.Gallery(
                            label="上传的图片",
                            visible=True,
                            columns=4,
                            height="auto"
                        )

                        image_upload = gr.File(
                            label="上传图片",
                            file_types=["image"],
                            file_count="multiple"
                        )

                    with gr.Column(scale=1):
                        # 右侧提示信息
                        gr.Markdown("""
                        ### 📝 评价指南

                        **好的评价应该包含:**

                        1. 详细的体验描述
                        2. 值得推荐的特色或亮点
                        3. 需要注意的事项
                        4. 个人建议或小贴士

                        **上传图片可以:**

                        - 增加评价的真实性和说服力
                        - 帮助其他用户更直观地了解体验
                        - 分享美好的旅行瞬间

                        **位置搜索说明:**
                        您可以粘贴从地图APP复制的位置信息，系统会自动解析经纬度并搜索周边地点。

                        感谢您的宝贵意见!
                        """)

                # 提交按钮和结果反馈
                submit_btn = gr.Button("提交评价", variant="primary", elem_classes="primary-button")
                result_message = gr.Markdown("")

            # 我的评价历史页签
            with gr.TabItem("我的评价"):
                refresh_btn = gr.Button("刷新评价列表")
                my_reviews_html = gr.HTML("<div class='no-reviews'>加载中...</div>")

            # 浏览评价页签
            with gr.TabItem("浏览评价"):
                with gr.Row():
                    # 筛选条件
                    browse_type = gr.Radio(
                        ["全部", "景点", "美食", "服务"],
                        label="类型筛选",
                        value="全部"
                    )

                    browse_rating = gr.Slider(
                        minimum=1,
                        maximum=5,
                        value=1,
                        step=0.5,
                        label="最低评分",
                        info="筛选指定评分及以上的评价"
                    )

                    browse_tags = gr.Dropdown(
                        ["全部标签"],
                        label="标签筛选",
                        value="全部标签"
                    )

                    browse_search_btn = gr.Button("搜索评价", variant="primary", elem_classes="primary-button")

                # 评价展示区域
                browse_results = gr.HTML("<div class='no-reviews'>请选择筛选条件并点击搜索</div>")

            # 目标评价页签 - 与提交评价页面类似的搜索体验
            with gr.TabItem("目标评价"):
                gr.Markdown("### 🔍 搜索目标地点")
                with gr.Row():
                    # 评价类型
                    target_review_type = gr.Radio(
                        ["景点", "美食", "服务"],
                        label="评价类型",
                        value="景点"
                    )

                # 搜索方式切换
                target_search_method = gr.Radio(
                    ["关键词搜索", "位置搜索"],
                    label="搜索方式",
                    value="关键词搜索"
                )

                # 关键词搜索容器
                with gr.Group(elem_classes="search-container") as target_keyword_container:
                    with gr.Row():
                        target_place_search = gr.Textbox(
                            label="搜索地点",
                            placeholder="输入地点名称，如: 故宫博物院、西湖、外滩...",
                            lines=1
                        )
                        target_search_btn = gr.Button("搜索", variant="secondary")

                # 位置搜索容器
                with gr.Group(visible=False, elem_classes="search-container") as target_location_container:
                    target_location_input = gr.Textbox(
                        label="输入位置坐标",
                        placeholder="输入经纬度，如: 116.397428,39.90923 或粘贴位置信息",
                        lines=3
                    )

                    target_search_radius = gr.Slider(
                        minimum=100,
                        maximum=5000,
                        value=1000,
                        step=100,
                        label="搜索半径(米)",
                        info="设置搜索范围，单位：米"
                    )

                    target_location_parsed = gr.HTML(
                        "<div class='no-place'>请输入位置信息</div>",
                        label="解析结果"
                    )

                    target_location_btn = gr.Button("搜索周边", variant="secondary")

                # 搜索结果状态
                target_search_status = gr.HTML("")

                # 搜索结果表格
                target_places_results = gr.Dataframe(
                    headers=["名称", "地址", "类型", "距离(米)"],
                    label="搜索结果",
                    interactive=True,
                    visible=False
                )

                # 选中的目标
                target_selected_place = gr.HTML(
                    "<div class='no-place'>请先搜索并选择要查看评价的地点</div>",
                    label="已选地点"
                )

                # 用于保存选中POI数据的状态变量
                target_selected_poi = gr.State(value=None)
                target_search_cache = gr.State(value=[])

                # 保留原始目标选择器但设为不可见，用于兼容
                target_review_selector = gr.Dropdown(
                    [],
                    visible=False
                )

                # 查看评价按钮
                target_review_btn = gr.Button("查看评价", variant="primary", elem_classes="primary-button")

                # 目标评价展示区域
                target_reviews_results = gr.HTML("<div class='no-reviews'>请选择目标并点击查看</div>")

        # 加载用户信息
        def load_user_data(request: gr.Request):
            token = request.query_params.get("token", "")
            info = verify_token(token)
            if not info or not info.get("username"):
                return token, "", "", "<div class='userbar-text'>⚠️ 未登录或令牌无效，请重新登录</div>"

            # 从token中获取用户ID
            user_id = info.get("id", "")
            username = info.get("username", "")

            # 返回按钮
            back_btn = f"""<a href="/" class="review-float-btn" title="返回首页">🏠</a>"""

            # 只显示用户名，避免重影
            return token, user_id, username, f"<div class='userbar-text'>👤 {username}</div>", back_btn

        app.load(
            fn=load_user_data,
            inputs=None,
            outputs=[token_box, user_id_box, username_box, userbar, back_btn_html]
        )

        # 切换搜索方式 - 评价提交页
        def toggle_search_method(method):
            if method == "关键词搜索":
                return gr.Group(visible=True), gr.Group(visible=False)
            else:
                return gr.Group(visible=False), gr.Group(visible=True)

        search_method.change(
            fn=toggle_search_method,
            inputs=search_method,
            outputs=[keyword_search_container, location_search_container]
        )

        # 切换搜索方式 - 目标评价页
        target_search_method.change(
            fn=toggle_search_method,
            inputs=target_search_method,
            outputs=[target_keyword_container, target_location_container]
        )

        # 解析位置信息 - 评价提交页
        def parse_location_input(location_text):
            location = parse_location(location_text)
            if location:
                return f"<div class='location-info'>已解析坐标: {location}</div>"
            else:
                return "<div class='no-place'>无法解析位置信息，请检查输入格式</div>"

        location_input.change(
            fn=parse_location_input,
            inputs=location_input,
            outputs=location_parsed
        )

        # 解析位置信息 - 目标评价页
        target_location_input.change(
            fn=parse_location_input,
            inputs=target_location_input,
            outputs=target_location_parsed
        )

        # 当评价类型变化时，更新标签选项
        def update_tags_by_type(target_type):
            tags_options = REVIEW_TAGS.get(target_type, [])
            return gr.CheckboxGroup(choices=tags_options)

        target_type.change(
            fn=update_tags_by_type,
            inputs=target_type,
            outputs=tags
        )

        # 处理图片上传
        def handle_images(files):
            image_paths = [file.name for file in files]
            return image_paths

        image_upload.change(
            fn=handle_images,
            inputs=image_upload,
            outputs=images
        )

        # 处理关键词搜索 - 评价提交页
        def search_places_by_keyword(keyword, target_type):
            if not keyword or len(keyword.strip()) < 2:
                return (
                    "<div class='loading-indicator'><div>请输入至少2个字符进行搜索</div></div>",
                    gr.Dataframe(visible=False),
                    "<div class='no-place'>请输入搜索关键词</div>",
                    []
                )

            # 显示加载状态
            """
            <div class='loading-indicator'>
                <div class='loading-spinner'></div>
                <div>正在搜索，请稍候...</div>
            </div>
            """

            places = search_places_with_amap(keyword=keyword, type_code=target_type)

            if not places:
                return (
                    "",
                    gr.Dataframe(visible=False),
                    "<div class='no-place'>未找到相关地点，请修改关键词重试</div>",
                    []
                )

            # 构建表格数据
            df_data = []
            for place in places:
                distance = place.get("distance", "")
                df_data.append([
                    place["name"],
                    place.get("address", "地址未知"),
                    place.get("type", "").split(";")[0],
                    distance
                ])

            return (
                "",
                gr.Dataframe(value=df_data, visible=True),
                "<div class='no-place'>请从搜索结果中选择一个地点</div>",
                places
            )

        search_btn.click(
            fn=search_places_by_keyword,
            inputs=[place_search, target_type],
            outputs=[search_status, place_results, selected_place, search_results_cache]
        )

        # 处理关键词搜索 - 目标评价页
        target_search_btn.click(
            fn=search_places_by_keyword,
            inputs=[target_place_search, target_review_type],
            outputs=[target_search_status, target_places_results, target_selected_place, target_search_cache]
        )

        # 处理位置搜索 - 评价提交页
        def search_places_by_location(location_text, radius, target_type):
            location = parse_location(location_text)
            if not location:
                return (
                    "<div class='loading-indicator'>无法解析位置信息，请检查输入格式</div>",
                    gr.Dataframe(visible=False),
                    "<div class='no-place'>无法解析位置信息</div>",
                    []
                )

            # 显示加载状态
            """
            <div class='loading-indicator'>
                <div class='loading-spinner'></div>
                <div>正在搜索周边，请稍候...</div>
            </div>
            """

            places = search_places_with_amap(location=location, type_code=target_type, radius=radius)

            if not places:
                return (
                    "",
                    gr.Dataframe(visible=False),
                    "<div class='no-place'>该位置周边未找到相关地点，请尝试增加搜索半径</div>",
                    []
                )

            # 构建表格数据
            df_data = []
            for place in places:
                distance = place.get("distance", "")
                df_data.append([
                    place["name"],
                    place.get("address", "地址未知"),
                    place.get("type", "").split(";")[0],
                    distance
                ])

            return (
                "",
                gr.Dataframe(value=df_data, visible=True),
                "<div class='no-place'>请从搜索结果中选择一个地点</div>",
                places
            )

        location_search_btn.click(
            fn=search_places_by_location,
            inputs=[location_input, location_search_radius, target_type],
            outputs=[search_status, place_results, selected_place, search_results_cache]
        )

        # 处理位置搜索 - 目标评价页
        target_location_btn.click(
            fn=search_places_by_location,
            inputs=[target_location_input, target_search_radius, target_review_type],
            outputs=[target_search_status, target_places_results, target_selected_place, target_search_cache]
        )

        # 处理地点选择 - 评价提交页
        def select_place(evt: gr.SelectData, places_data):
            if not places_data or evt.index[0] >= len(places_data):
                return "<div class='no-place'>选择无效，请重新搜索</div>", None

            selected = places_data[evt.index[0]]

            # 生成显示HTML
            distance_html = ""
            if "distance" in selected and selected["distance"]:
                distance_html = f"<p class='place-distance'>距离: {selected['distance']}米</p>"

            html = f"""
            <div class='selected-place'>
                <h4>{selected["name"]}</h4>
                <p class='place-address'>{selected["address"]}</p>
                <p class='place-type'>{selected["type"].split(";")[0] if "type" in selected else ""}</p>
                {distance_html}
                <p class='place-coords'>坐标: {selected["location"]}</p>
            </div>
            """

            # 返回选中的POI数据用于后续处理
            return html, selected

        place_results.select(
            fn=select_place,
            inputs=[search_results_cache],
            outputs=[selected_place, selected_poi_data]
        )

        # 处理地点选择 - 目标评价页
        target_places_results.select(
            fn=select_place,
            inputs=[target_search_cache],
            outputs=[target_selected_place, target_selected_poi]
        )

        # 提交评价
        def submit_review(token, user_id, username, target_type, selected_poi, rating, tags, content, image_files):
            # 验证用户登录状态
            info = verify_token(token)
            if not info or not info.get("username") or not info.get("id"):
                return "### ⚠️ 未登录或会话已过期，请重新登录"

            # 检查是否选择了地点
            if not selected_poi:
                return "### ⚠️ 请先搜索并选择评价对象"

            if not content or len(content.strip()) < 10:
                return "### ⚠️ 评价内容太短，请至少输入10个字符"

            # 处理目标信息
            target_name = selected_poi["name"]
            target_id = f"poi_{selected_poi['id']}"
            target_address = selected_poi.get("address", "")
            target_location = selected_poi.get("location", "")
            target_distance = selected_poi.get("distance", "")

            # 处理图片文件
            images_data = []
            if image_files:
                for file in image_files:
                    # 实际应用中需要处理图片上传存储
                    # 这里简化为记录文件名
                    try:
                        file_path = f"/static/uploads/{os.path.basename(file.name)}"
                        images_data.append({
                            "url": file_path,
                            "description": "用户上传图片"
                        })
                    except Exception as e:
                        print(f"处理图片失败: {e}")

            # 构建评价数据
            review_data = {
                "user_id": user_id,
                "username": username,
                "target_id": target_id,
                "target_name": target_name,
                "target_type": target_type,
                "target_address": target_address,
                "target_location": target_location,
                "target_distance": target_distance,
                "rating": rating,
                "tags": tags,
                "content": content,
                "images": images_data,
                "is_poi": True
            }

            # 添加评价
            success, message = add_review(review_data)
            if success:
                # 成功后清空表单
                return f"### ✅ {message}"
            else:
                return f"### ❌ {message}"

        # 提交按钮点击事件
        submit_btn.click(
            fn=submit_review,
            inputs=[
                token_box,
                user_id_box,
                username_box,
                target_type,
                selected_poi_data,  # 选中的POI数据
                rating,
                tags,
                content,
                image_upload
            ],
            outputs=result_message
        )

        # 刷新评价列表并格式化为HTML
        def refresh_reviews_html(user_id):
            if not user_id:
                return "<div class='no-reviews'>请先登录</div>"

            reviews = get_user_reviews(user_id)
            if not reviews:
                return "<div class='no-reviews'>您还没有发表过评价</div>"

            return format_reviews_html(reviews)

        # 刷新按钮点击事件
        refresh_btn.click(
            fn=refresh_reviews_html,
            inputs=user_id_box,
            outputs=my_reviews_html
        )

        # 初始加载时也获取评价列表
        user_id_box.change(
            fn=refresh_reviews_html,
            inputs=user_id_box,
            outputs=my_reviews_html
        )

        # 浏览页标签选项更新
        def update_browse_tags(target_type):
            return gr.Dropdown(choices=get_all_tags(target_type))

        browse_type.change(
            fn=update_browse_tags,
            inputs=browse_type,
            outputs=browse_tags
        )

        # 搜索评价
        def search_reviews_handler(target_type, min_rating, tag):
            if target_type == "全部":
                target_type = None
            if tag == "全部标签":
                tag = None

            reviews = search_reviews(target_type, min_rating, tag)
            return format_reviews_html(reviews)

        browse_search_btn.click(
            fn=search_reviews_handler,
            inputs=[browse_type, browse_rating, browse_tags],
            outputs=browse_results
        )

        # 查看目标评价
        def view_target_reviews(selected_poi, target_type):
            if not selected_poi:
                return "<div class='no-reviews'>请先搜索并选择要查看评价的地点</div>"

            # 使用POI ID查询评价
            target_id = f"poi_{selected_poi['id']}"
            reviews = get_target_reviews(target_id, target_type)

            if not reviews:
                return f"<div class='no-reviews'>暂无关于{selected_poi['name']}的评价</div>"

            return format_reviews_html(reviews)

        target_review_btn.click(
            fn=view_target_reviews,
            inputs=[target_selected_poi, target_review_type],
            outputs=target_reviews_results
        )

        # 页脚
        gr.HTML("<div style='text-align:center;color:#555;margin-top:30px;font-size:14px;'>© 2025 旅行智能助手</div>")
    return app
