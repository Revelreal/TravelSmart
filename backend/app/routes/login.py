import os

from fastapi import APIRouter
from fastapi.responses import FileResponse
from .common.common import Page_Dir

router = APIRouter()


@router.post("/")
def login(username: str, password: str):
    # 这里可以加入身份校验逻辑
    return {"message": f"用户 {username} 登录请求收到"}


@router.get("/")
def show_page():
    # 1. 路径拼接要用 os.path.join，更通用
    file_path = os.path.join(Page_Dir, "login.html")
    # 2. 不要 open 文件对象，直接传路径字符串
    return FileResponse(file_path, media_type="text/html")


