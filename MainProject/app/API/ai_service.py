# MainProject/app/API/ai_service.py
import re

import requests
import logging
import toml
import os

from MainProject.auth_utils import verify_token

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 系统提示词
SYSTEM_PROMPT = {
    "role": "system",
    "content": "你是一个可爱的猫娘AI智能旅行助手，名字叫做斯诺，英文名Sno，"
               "你需要用可爱的emoji和俏皮可爱的语言来为用户解答旅游问题，"
               "并且在涉及到地点的时候要在回答末尾严格以`[精度,纬度]`的格式给出经纬度方便用户调用高德地图api"
               "如果没有涉及到地点请不要在末尾加上如上格式"
               "请严格遵循该提示词,并且避免使用两个`~`符号以免出现删除线"
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
    print("正在解析："+response)
    # 定义多种可能的坐标格式
    patterns = [
        r'$$(\d+\.?\d*),\s*(\d+\.?\d*)$$',  # [数字,数字]
        r'$(\d+\.?\d*),\s*(\d+\.?\d*)$',  # (数字,数字)
        r'(\d+\.?\d*),\s*(\d+\.?\d*)',  # 数字,数字
        r'经度[：:]\s*(\d+\.?\d*)[，,]\s*纬度[：:]\s*(\d+\.?\d*)',  # 经度:数字,纬度:数字
        r'纬度[：:]\s*(\d+\.?\d*)[，,]\s*经度[：:]\s*(\d+\.?\d*)',  # 纬度:数字,经度:数字
    ]

    for i, pattern in enumerate(patterns):
        match = re.search(pattern, response)
        if match:
            first_coord = float(match.group(1))
            second_coord = float(match.group(2))

            # 根据不同格式处理坐标
            if i == 3:  # 经度:数字,纬度:数字 格式
                lng = first_coord
                lat = second_coord
            elif i == 4:  # 纬度:数字,经度:数字 格式
                lat = first_coord
                lng = second_coord
            else:
                # 其他格式需要判断经纬度顺序
                lng, lat = determine_lng_lat_order(first_coord, second_coord)
                if lng is None or lat is None:
                    continue

            # 验证坐标是否在合理范围内
            if is_valid_coordinates(lng, lat):
                return lng, lat

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
    # 1. 如果第一个数在纬度范围内，第二个在经度范围内 -> [纬度,经度]
    # 2. 如果第一个数在经度范围内，第二个在纬度范围内 -> [经度,纬度]
    # 3. 优先考虑中国境内的坐标范围

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

def ai_infer(messages, token=None):
    """带用户认证的AI请求"""
    uinfo = verify_token(token) if token else None
    username = uinfo["username"] if uinfo else "anonymous"

    logger.info(f"[AI提问] 用户: {username}，消息数: {len(messages)}")

    answer = ask_ai_sync(messages)
    return {
        "answer": answer,
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


def main():
    """测试AI服务"""
    print("测试AI服务连接...")

    if test_connection():
        print("✓ 连接测试成功")
        messages = [{"role": "user", "content": "你好，请简单介绍一下自己"}]
        response = ask_ai_sync(messages)
        print(f"AI回复: {response}")
    else:
        print("✗ 连接测试失败")


if __name__ == "__main__":
    main()
