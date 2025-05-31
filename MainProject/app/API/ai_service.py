import requests
import logging
import time

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = "https://api.deepbricks.ai/v1/chat/completions"
API_KEY = "sk-5docNm9DYSqBZhiq6Gq93fijNr4zd0Hddqr80vC3riuQSQf0"


def test_connection():
    """测试API连接是否正常"""
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10
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
    if not messages:
        return "没有提供消息内容"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2000
    }

    logger.info(f"发送AI请求，消息数量: {len(messages)}")

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=30  # 30秒超时
        )

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
            return "AI服务响应内容为空"

        answer = message["content"]

        if not answer or not answer.strip():
            return "AI未提供有效回复"

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


# 为了保持兼容性，保留异步接口
async def ask_ai(messages):
    """异步包装器，实际调用同步函数"""
    return ask_ai_sync(messages)


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


if __name__ == "__main__":
    main()