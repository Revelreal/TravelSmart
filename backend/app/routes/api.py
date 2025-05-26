from fastapi import APIRouter, Request
import httpx
router = APIRouter()

API_URL = "https://api.deepbricks.ai/v1/chat/completions"
API_KEY = "sk-5docNm9DYSqBZhiq6Gq93fijNr4zd0Hddqr80vC3riuQSQf0"  # (推荐生产环境放到环境变量)
# 官方API参考：https://platform.openai.com/docs/api-reference


@router.post("/ai/chat")
async def chat_ai(req: Request):
    data = await req.json()
    question = data.get("question", "")
    if not question:
        return {"answer": "提问不能为空"}
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": question}],
        "temperature": 0.7
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(API_URL, headers=headers, json=payload, timeout=25)
        if resp.is_error:
            return {"answer": "AI服务异常，请稍后再试"}
        resdata = resp.json()
        answer = resdata.get("choices", [{}])[0].get("message", {}).get("content", "AI无回复")
    return {"answer": answer}


# 接口：AI 路线规划接口
@router.get("/ai/route")
async def route_ai(req: Request):
    data = await req.json()
    start_location = data.get("start_location")
    end_location = data.get("end_location")
    # 调用 ai 模块的接口，返回路线规划结果
    resp = "从 {} 到 {} 的路线规划结果如下：".format(start_location, end_location)
    return {"route": resp}
