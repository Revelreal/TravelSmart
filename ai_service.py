import requests
import logging
import toml
import os
import json
import re # Import re for regex

from auth_utils import verify_token

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 读取配置文件（支持相对路径）
def load_default_config(filename="../../../config.toml"):
    """
    加载指定路径的配置文件
    :param filename: 配置文件的相对路径
    :return: 配置字典或None
    """
    try:
        abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), filename))
        logger.info(f"尝试加载配置文件: {abs_path}")

        if not os.path.exists(abs_path):
            logger.warning(f"配置文件不存在: {abs_path}")
            return None

        config = toml.load(abs_path)
        logger.info("配置文件加载成功")
        return config
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return None


def get_config_value(config, *keys, default=None):
    """
    从配置字典中安全获取嵌套值
    :param config: 配置字典
    :param keys: 嵌套的键，如 'ai', 'api'
    :param default: 默认值
    :return: 配置值或默认值
    """
    if not config:
        return default

    current = config
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


# 读取配置文件（当前目录）
def load_config():
    """
    按优先级加载配置文件：
    1. 先尝试当前目录 config.toml
    2. 再尝试相对路径 ../../../config.toml
    3. 最后使用默认配置
    :return: (api_url, api_key) 元组
    """
    config = None

    # 尝试当前目录
    config_file = "config.toml"
    if os.path.exists(config_file):
        try:
            logger.info(f"尝试加载当前目录配置文件: {config_file}")
            config = toml.load(config_file)
            logger.info("当前目录配置文件加载成功")
        except Exception as e:
            logger.error(f"读取当前目录配置文件失败: {e}")
            config = None
    else:
        logger.warning(f"当前目录配置文件不存在: {config_file}")

    # 如果当前目录配置不存在，尝试默认路径
    if config is None:
        config = load_default_config("../../../config.toml")

    # 解析配置
    if config:
        api_url = get_config_value(config, "ai", "api")
        api_key = get_config_value(config, "ai", "key")
        amap_key = get_config_value(config, "amap", "amap_key")

        if not api_url or not api_key:
            logger.error("配置文件中缺少必要的ai.api或ai.key字段")
            return None, None, None

        logger.info("AI配置加载成功")
        return api_url, api_key, amap_key
    else:
        logger.warning("无法加载任何配置文件")
        return None, None, None


# 加载配置
API_URL, API_KEY, AMAP_KEY = load_config()

# 如果配置文件读取失败，使用硬编码的默认值
if not API_URL or not API_KEY:
    logger.warning("使用默认配置")
    API_URL = "https://api.siliconflow.cn/v1/chat/completions"
    API_KEY = "sk-pnsskddlbxhdoybvyimlnlktoowxccjwogosmwnmyvnhzsjs"

if not AMAP_KEY:
    logger.warning("使用默认高德地图API密钥")
    AMAP_KEY = "你的默认高德地图API密钥" # REPLACE WITH YOUR ACTUAL KEY

logger.info(f"API URL: {API_URL}")
logger.info(f"API KEY: {API_KEY[:20]}...")  # 只显示前20个字符保护隐私
logger.info(f"AMAP KEY: {AMAP_KEY[:20]}...")  # 只显示前20个字符保护隐私


def search_location(keyword):
    """
    使用高德地图API搜索地点
    :param keyword: 搜索关键词
    :return: 地点的经纬度信息或None
    """
    if not AMAP_KEY:
        logger.error("高德地图API密钥未配置")
        return None

    url = "https://restapi.amap.com/v3/place/text"
    params = {
        "key": AMAP_KEY,
        "keywords": keyword,
        "output": "json"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "1" and data["count"] > 0:
                location = data["pois"][0]["location"].split(",")
                return {
                    "longitude": float(location[0]),
                    "latitude": float(location[1])
                }
            else:
                logger.warning(f"未找到地点: {keyword}")
                return None
        else:
            logger.error(f"高德地图API请求失败: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"搜索地点失败: {e}")
        return None


def test_connection():
    """测试API连接是否正常"""
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
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
            "stop": [],
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个可爱的猫娘AI智能旅行助手，名字叫做斯诺，英文名Sno，"
                               "你需要用可爱的emoji和俏皮可爱的语言来为用户解答旅游问题，"
                               "如果你的回答中提及了具体的地点信息，请在该回答的**最末尾**以`[经度,纬度]`的格式直接给出对应的经纬度，方便用户在地图上查看。"
                               "例如：'故宫博物院是一个很棒的地方喵！你可以看到很多古老的建筑和文物哦。这里是故宫的坐标：[116.397428,39.90923]'"
                               "如果没有涉及到地点请不要在末尾加上如上格式。"
                               "请严格遵循该提示词,并且避免使用两个`~`符号以免出现删除线"
                },
                {
                    "role": "user",
                    "content": "你是谁？"
                }
            ]
        }
        response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"连接测试失败: {e}")
        return False


def ask_ai_sync(messages):
    """
    同步版本的AI请求函数
    :param messages: [{'role': 'user'/'assistant', 'content': '...'}, ...]
    :return: AI模型回复字符串
    """
    url = "https://api.siliconflow.cn/v1/chat/completions"
    if not messages:
        return "没有提供消息内容"

    print(messages)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
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
        "stop": [],
        "messages": [
            {
                "role": "system",
                "content": "你是一个可爱的猫娘AI智能旅行助手，名字叫做斯诺，英文名Sno，"
                           "你需要用可爱的emoji和俏皮可爱的语言来为用户解答旅游问题，"
                           "如果你的回答中提及了具体的地点信息，请在该回答的**最末尾**以`[经度,纬度]`的格式直接给出对应的经纬度，方便用户在地图上查看。"
                           "故宫博物院是一个很棒的地方喵！😻 你可以看到很多古老的建筑和文物哦，仿佛穿越回了古代呢！🏯✨ 这里是故宫的坐标：[116.397428,39.90923] 📍"
                           "切记，坐标有且只能有一个并且只能位于句尾，不可位于句中"
                           "如果没有涉及到地点请不要在末尾加上如上格式。"
                           "请严格遵循该提示词,并且避免使用两个`~`符号以免出现删除线"
            }
        ] + messages  # 将用户的消息添加到系统提示词后面
    }

    logger.info(f"发送AI请求，消息数量: {len(messages)}")

    try:
        response = requests.request("POST", url, json=payload, headers=headers)

        logger.info(f"API响应状态码: {response.status_code}")

        if response.status_code != 200:
            error_text = response.text
            logger.error(f"AI服务请求错误: {response.status_code} - {error_text}")

            if response.status_code == 401:
                return "API密钥无效，请检查配置"
            elif response.status_code == 429:
                return "请求过于频繁，请稍后再试"
            elif response.status_code == 500:
                return "AI服务内部错误，请稍后再试"
            else:
                return f"AI服务错误 ({response.status_code})，请检查网络连接"

        try:
            data = response.json()
        except Exception as json_error:
            logger.error(f"解析响应JSON失败: {json_error}")
            return "AI服务响应格式错误"

        # 检查响应结构
        if "choices" not in data:
            logger.error(f"响应中缺少choices字段: {data}")
            return "AI服务响应格式异常"

        if not data["choices"]:
            logger.error("AI服务返回空的choices列表")
            return "AI服务无响应内容"

        choice = data["choices"][0]
        if "message" not in choice:
            logger.error(f"响应choice中缺少message字段: {choice}")
            return "AI服务响应格式异常"

        message = choice["message"]
        if "content" not in message:
            logger.error(f"响应message中缺少content字段: {message}")
            return "AI服务内容为空"

        answer = message["content"]

        if not answer or not answer.strip():
            return "AI未提供有效回复"

        # No longer extracting keyword and searching; AI is expected to provide coords directly.
        # The frontend will parse the coordinates from the 'answer' string.

        logger.info("AI请求成功完成")
        return answer.strip()

    except requests.exceptions.Timeout:
        logger.error("请求超时")
        return "请求超时，请检查网络连接或稍后重试"
    except requests.exceptions.ConnectionError as e:
        logger.error(f"连接错误: {e}")
        return "无法连接到AI服务，请检查网络连接"
    except requests.exceptions.RequestException as e:
        logger.error(f"请求错误: {e}")
        return "网络请求失败，请检查网络连接"
    except Exception as e:
        logger.error(f"未知错误: {e}")
        return f"AI服务异常: {str(e)}"


# This function is removed as the AI is expected to provide coordinates directly.
# def extract_location_keyword(answer):
#     """
#     从AI回答中提取地点关键词
#     :param answer: AI回答内容
#     :return: 地点关键词或None
#     """
#     import re
#     match = re.search(r"地点：(.+?)[\s,，]", answer)
#     if match:
#         return match.group(1).strip()
#     return None


# 为了保持兼容性，保留异步接口
async def ask_ai(messages):
    """异步包装器，实际调用同步函数"""
    return ask_ai_sync(messages)


def ai_infer(messages, token=None):
    """
    根据token识别当前提问用户，并提交AI请求
    :param messages: AI消息列表
    :param token: 用户JWT，可能来自前端/接口
    :return: dict { answer: AI回复, user: 用户信息 }
    """
    uinfo = verify_token(token) if token else None
    username = uinfo["username"] if uinfo else "anonymous"

    # 打印日志，你也可以写数据库
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[AI提问] 用户: {username}，消息数: {len(messages)}，内容首条: {messages[0] if messages else ''}")

    # 也可以把用户名/nickname加入messages历史上下文，如需精准定制回复
    answer = ask_ai_sync(messages)
    return {
        "answer": answer,
        "user": uinfo or {"username": "anonymous"}
    }


# 测试函数
def main():
    """测试AI服务"""
    print("测试AI服务连接...")

    # 测试连接
    if test_connection():
        print("✓ 连接测试成功")
    else:
        print("✗ 连接测试失败")
        return

    # 测试对话
    messages = [{"role": "user", "content": "你好，请简单介绍一下自己"}]
    response = ask_ai_sync(messages)
    print(f"AI回复: {response}")

    # Test with a location query
    print("\n测试地点查询...")
    location_messages = [{"role": "user", "content": "带我去故宫博物院"}]
    location_response = ask_ai_sync(location_messages)
    print(f"AI回复 (地点): {location_response}")


if __name__ == "__main__":
    main()