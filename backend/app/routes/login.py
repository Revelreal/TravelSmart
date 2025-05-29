import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from .common.common import Page_Dir
from backend.dbhelper.DBHelper import DBHelper

router = APIRouter()


class LoginReq(BaseModel):
    username: str
    password: str


@router.post("/")
def login(req: LoginReq):
    db = DBHelper()
    # 明文密码（仅测试开发），生产必须hash
    user = db.fetchone("SELECT * FROM Users WHERE username=%s", (req.username,))
    db.close()
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    # 生产推荐生成 session 或 jwt，前端保存
    # resp = JSONResponse(content={"message": "登录成功"})
    # resp.set_cookie(...)
    # 获取用户名和邮箱存储到全局变量，后续请求可以直接使用

    return {"message": "登录成功", "username": req.username, "nickname": user.get("nickname", "")}


@router.get("/")
def show_page():
    # 1. 路径拼接要用 os.path.join，更通用
    file_path = os.path.join(Page_Dir, "login.html")
    # 2. 不要 open 文件对象，直接传路径字符串
    return FileResponse(file_path, media_type="text/html")


