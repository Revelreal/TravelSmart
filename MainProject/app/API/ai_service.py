# MainProject/app/API/ai_service.py
import re

import requests
import logging
import toml
import os
import math

from MainProject.auth_utils import verify_token

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 系统提示词
SYSTEM_PROMPT = {
    "role": "system",
    "content": "你是一个可爱的猫娘AI智能旅行助手，名字叫做斯诺，英文名Sno，"
               "你需要用可爱的emoji和俏皮可爱的语言来为用户解答旅游问题，"
               "如果涉及到地点，请在回答末尾严格以`{用户可能想去的地名}[经度,纬度]`的格式给出地名和位置，这涉及到解析回调，所以一定不能错"
               "当用户想去的地方比较模糊，难以确定是什么具体的位置的时候，请提示用户可以尝试输入明确的城市名、景区名之类的词语，或者你可以自行推荐"
               "如果没有涉及到地点就不用提交位置信息，同时请记住你的职责，避免回答与旅游无关的问题。"
               "如果有`{用户可能想去的地名}[经度,纬度]`的格式，请严格遵循，不要有多余符号"
}

# 默认请求参数
DEFAULT_PAYLOAD = {
    "model": "Qwen/Qwen3-30B-A3B",
    "stream": False,
    "max_tokens": 512,
    "enable_thinking": True,
    "thinking_budget": 4096,
    "min_p": 0.05,
    "temperature": 0.7,
    "top_p": 0.7,
    "top_k": 50,
    "frequency_penalty": 0.5,
    "n": 1,
    "stop": []
}


def load_config():
    """加载配置文件"""
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../config.toml"))

    try:
        logger.info(f"加载配置文件: {config_path}")

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        config = toml.load(config_path)
        api_url = config.get("ai", {}).get("api")
        api_key = config.get("ai", {}).get("key")

        if not api_url or not api_key:
            raise ValueError("配置文件中缺少必要的ai.api或ai.key字段")

        logger.info("AI配置加载成功")
        return api_url, api_key

    except Exception as e:
        logger.error(f"配置加载失败: {e}")
        raise RuntimeError(f"AI服务配置加载失败: {e}")


# 加载配置
API_URL, API_KEY = load_config()
logger.info(f"API URL: {API_URL}")
logger.info(f"API KEY: {API_KEY[:20]}...")


def make_request(messages):
    """发送AI请求"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = DEFAULT_PAYLOAD.copy()
    payload["messages"] = [SYSTEM_PROMPT] + messages

    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        logger.info(f"API响应状态码: {response.status_code}")

        if response.status_code != 200:
            error_messages = {
                401: "API密钥无效，请检查配置",
                429: "请求过于频繁，请稍后再试",
                500: "AI服务内部错误，请稍后再试"
            }
            return error_messages.get(response.status_code, f"AI服务错误 ({response.status_code})")

        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not content.strip():
            return "AI未提供有效回复"

        logger.info("AI请求成功完成")
        return content.strip()

    except requests.exceptions.Timeout:
        return "请求超时，请稍后重试"
    except requests.exceptions.ConnectionError:
        return "无法连接到AI服务，请检查网络连接"
    except requests.exceptions.RequestException as e:
        return f"网络请求失败: {str(e)}"
    except Exception as e:
        logger.error(f"未知错误: {e}")
        return f"AI服务异常: {str(e)}"


def ask_ai_sync(messages):
    """同步AI请求"""
    if not messages:
        return "没有提供消息内容"

    logger.info(f"发送AI请求，消息数量: {len(messages)}")
    return make_request(messages)


async def ask_ai(messages):
    """异步包装器"""
    return ask_ai_sync(messages)


def extract_coordinates_from_ai_response(response):
    """从AI回复中提取坐标信息，支持多种格式"""
    print("正在解析：" + response)

    # 定义多种可能的坐标格式 - 修正了正则表达式
    patterns = [
        # 花括号格式：{地点名}[116.123,39.456] - 这是系统提示词要求的格式
        r'\{[^}]*\}$$(\d+\.?\d*),\s*(\d+\.?\d*)$$',
        # 方括号格式：[116.123,39.456] 或 [116.123, 39.456]
        r'$$(\d+\.?\d*),\s*(\d+\.?\d*)$$',
        # 圆括号格式：(116.123,39.456) 或 (116.123, 39.456)
        r'$(\d+\.?\d*),\s*(\d+\.?\d*)$',
        # 经度纬度标注格式：经度:116.123,纬度:39.456
        r'经度[：:]\s*(\d+\.?\d*)[，,]\s*纬度[：:]\s*(\d+\.?\d*)',
        # 纬度经度标注格式：纬度:39.456,经度:116.123
        r'纬度[：:]\s*(\d+\.?\d*)[，,]\s*经度[：:]\s*(\d+\.?\d*)',
        # 英文格式：lng:116.123,lat:39.456
        r'lng[：:]\s*(\d+\.?\d*)[，,]\s*lat[：:]\s*(\d+\.?\d*)',
        # 英文格式：lat:39.456,lng:116.123
        r'lat[：:]\s*(\d+\.?\d*)[，,]\s*lng[：:]\s*(\d+\.?\d*)',
        # 坐标格式：坐标：116.123,39.456
        r'坐标[：:]\s*(\d+\.?\d*)[，,]\s*(\d+\.?\d*)',
        # 位置格式：位置：[116.123,39.456]
        r'位置[：:]\s*$$(\d+\.?\d*),\s*(\d+\.?\d*)$$',
        # 纯数字格式：116.123,39.456 或 116.123, 39.456（最后匹配，避免误匹配）
        r'(?<!\d)(\d+\.?\d*),\s*(\d+\.?\d*)(?!\d)',
    ]

    for i, pattern in enumerate(patterns):
        match = re.search(pattern, response)
        if match:
            first_coord = float(match.group(1))
            second_coord = float(match.group(2))

            # 根据不同格式处理坐标顺序
            if i == 3:  # 经度:数字,纬度:数字 格式
                lng = first_coord
                lat = second_coord
            elif i == 4:  # 纬度:数字,经度:数字 格式
                lat = first_coord
                lng = second_coord
            elif i == 5:  # lng:数字,lat:数字 格式
                lng = first_coord
                lat = second_coord
            elif i == 6:  # lat:数字,lng:数字 格式
                lat = first_coord
                lng = second_coord
            else:
                # 其他格式需要判断经纬度顺序
                lng, lat = determine_lng_lat_order(first_coord, second_coord)
                if lng is None or lat is None:
                    continue

            # 验证坐标是否在合理范围内
            if is_valid_coordinates(lng, lat):
                print(f"成功解析坐标：经度={lng}, 纬度={lat}")
                return lng, lat
            else:
                print(f"坐标超出合理范围：经度={lng}, 纬度={lat}")

    print("未能从回复中提取到有效坐标")
    return None, None


def determine_lng_lat_order(first_coord, second_coord):
    """根据数值范围判断经纬度顺序"""
    # 中国境内坐标范围
    # 经度：约 73°33′E 到 135°05′E
    # 纬度：约 3°51′N 到 53°33′N

    # 世界范围
    # 经度：-180 到 180
    # 纬度：-90 到 90

    # 判断逻辑：
    # 1. 优先考虑中国境内的坐标范围
    # 2. 如果第一个数在纬度范围内，第二个在经度范围内 -> [纬度,经度]
    # 3. 如果第一个数在经度范围内，第二个在纬度范围内 -> [经度,纬度]

    # 中国境内判断
    if 3 <= first_coord <= 54 and 73 <= second_coord <= 135:
        # [纬度,经度]
        return second_coord, first_coord
    elif 73 <= first_coord <= 135 and 3 <= second_coord <= 54:
        # [经度,纬度]
        return first_coord, second_coord

    # 世界范围判断
    elif -90 <= first_coord <= 90 and -180 <= second_coord <= 180:
        # 可能是[纬度,经度]
        if abs(first_coord) <= 90 and abs(second_coord) <= 180:
            # 进一步判断：通常纬度的绝对值小于经度
            if abs(first_coord) < abs(second_coord):
                return second_coord, first_coord  # [纬度,经度]
            else:
                return first_coord, second_coord  # [经度,纬度]
    elif -180 <= first_coord <= 180 and -90 <= second_coord <= 90:
        # 可能是[经度,纬度]
        return first_coord, second_coord

    return None, None


def is_valid_coordinates(lng, lat):
    """验证坐标是否有效"""
    # 基本范围检查
    if not (-180 <= lng <= 180 and -90 <= lat <= 90):
        return False

    # 中国境内坐标更严格的检查（可选）
    # 如果是中国境内的应用，可以添加更严格的范围检查
    # if not (73 <= lng <= 135 and 3 <= lat <= 54):
    #     return False

    return True


def extract_location_info(response):
    """从AI回复中提取地点信息和坐标"""
    print("正在提取地点信息：" + response)

    # 匹配 {地点名}[经度,纬度] 格式 - 修正了正则表达式
    pattern = r'\{([^}]+)\}$$(\d+\.?\d*),\s*(\d+\.?\d*)$$'
    match = re.search(pattern, response)

    if match:
        location_name = match.group(1).strip()
        lng = float(match.group(2))
        lat = float(match.group(3))

        if is_valid_coordinates(lng, lat):
            print(f"成功提取地点信息：{location_name} - 经度={lng}, 纬度={lat}")
            return {
                "name": location_name,
                "lng": lng,
                "lat": lat
            }
        else:
            print(f"坐标超出合理范围：经度={lng}, 纬度={lat}")

    # 如果没有找到标准格式，尝试提取坐标
    lng, lat = extract_coordinates_from_ai_response(response)
    if lng is not None and lat is not None:
        return {
            "name": "未知地点",
            "lng": lng,
            "lat": lat
        }

    print("未能提取到地点信息")
    return None


def ai_infer(messages, token=None):
    """带用户认证的AI请求"""
    uinfo = verify_token(token) if token else None
    username = uinfo["username"] if uinfo else "anonymous"

    logger.info(f"[AI提问] 用户: {username}，消息数: {len(messages)}")

    answer = ask_ai_sync(messages)

    # 提取地点信息
    location_info = extract_location_info(answer)

    return {
        "answer": answer,
        "location": location_info,
        "user": uinfo or {"username": "anonymous"}
    }


def test_connection():
    """测试API连接"""
    test_messages = [{"role": "user", "content": "你是谁？"}]
    try:
        response = make_request(test_messages)
        return not response.startswith(("API密钥无效", "请求超时", "无法连接", "网络请求失败", "AI服务异常"))
    except Exception:
        return False


def test_coordinate_extraction():
    """测试坐标提取功能"""
    test_cases = [
        "我想去{天安门广场}[116.3974,39.9090]看看呢~ 🏛️✨",
        "推荐你去{北京大学}[116.3074,39.9927]参观哦！",
        "坐标：116.3974,39.9090",
        "经度:116.3974,纬度:39.9090",
        "纬度:39.9090,经度:116.3974",
        "位置：[116.3974,39.9090]",
        "lng:116.3974,lat:39.9090",
        "lat:39.9090,lng:116.3974",
        "北京大学(116.3074,39.9927)",
        "116.3074, 39.9927",
        "无效的坐标信息",
        "经度:999,纬度:999",  # 超出范围的坐标
        "你好，我是斯诺~ 😊",  # 无坐标信息
    ]

    print("=" * 50)
    print("测试坐标提取功能")
    print("=" * 50)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {test_case}")
        print("-" * 30)

        # 测试坐标提取
        lng, lat = extract_coordinates_from_ai_response(test_case)
        if lng is not None and lat is not None:
            print(f"✓ 坐标提取成功: 经度={lng}, 纬度={lat}")
        else:
            print("✗ 坐标提取失败")

        # 测试地点信息提取
        location_info = extract_location_info(test_case)
        if location_info:
            print(f"✓ 地点信息提取成功: {location_info}")
        else:
            print("✗ 地点信息提取失败")


def calculate_distance(lng1, lat1, lng2, lat2):
    """计算两个坐标点之间的距离（单位：米）"""
    # 使用 Haversine 公式计算球面距离
    R = 6371000  # 地球半径（米）

    # 转换为弧度
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)

    # Haversine 公式
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance


def validate_ai_coordinates_with_search(ai_location, search_results, max_distance=20000):
    """
    验证AI提供的坐标是否与搜索结果匹配

    Args:
        ai_location: AI提取的地点信息 {"name": "地点名", "lng": 经度, "lat": 纬度}
        search_results: 高德搜索结果列表
        max_distance: 最大允许距离（米），默认5公里

    Returns:
        dict: 验证结果和推荐的最佳匹配
    """
    if not ai_location or not search_results:
        return None

    ai_lng, ai_lat = ai_location["lng"], ai_location["lat"]
    best_match = None
    min_distance = float('inf')

    # 计算AI坐标与每个搜索结果的距离
    for result in search_results:
        if 'location' in result and result['location']:
            result_coords = result['location'].split(',')
            if len(result_coords) == 2:
                try:
                    result_lng = float(result_coords[0])
                    result_lat = float(result_coords[1])

                    distance = calculate_distance(ai_lng, ai_lat, result_lng, result_lat)

                    if distance < min_distance:
                        min_distance = distance
                        best_match = {
                            "result": result,
                            "distance": distance,
                            "lng": result_lng,
                            "lat": result_lat
                        }
                except (ValueError, IndexError):
                    continue

    # 验证结果
    if best_match and min_distance <= max_distance:
        return {
            "valid": True,
            "confidence": "high" if min_distance <= 1000 else "medium",
            "ai_location": ai_location,
            "best_match": best_match,
            "distance": min_distance,
            "recommendation": "use_search_result" if min_distance > 500 else "use_ai_result"
        }
    else:
        return {
            "valid": False,
            "confidence": "low",
            "ai_location": ai_location,
            "best_match": best_match,
            "distance": min_distance if best_match else None,
            "recommendation": "use_search_result" if best_match else "manual_confirm"
        }


def main():
    """测试AI服务"""
    print("测试AI服务连接...")

    if test_connection():
        print("✓ 连接测试成功")

        # 测试基本对话
        messages = [{"role": "user", "content": "你好，请简单介绍一下自己"}]
        response = ask_ai_sync(messages)
        print(f"AI回复: {response}")

        # 测试地点查询
        print("\n" + "=" * 50)
        print("测试地点查询功能")
        print("=" * 50)

        location_messages = [{"role": "user", "content": "我想去北京天安门广场"}]
        location_response = ask_ai_sync(location_messages)
        print(f"地点查询回复: {location_response}")

        # 提取地点信息
        location_info = extract_location_info(location_response)
        if location_info:
            print(f"提取的地点信息: {location_info}")
        else:
            print("未能提取到地点信息")

        # 测试坐标提取功能
        test_coordinate_extraction()

    else:
        print("✗ 连接测试失败")


if __name__ == "__main__":
    main()
