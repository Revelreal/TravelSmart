from fastapi import APIRouter
from fastapi.responses import FileResponse
from .common.common import Page_Dir
import os

router = APIRouter()


@router.get("/logout")
def show_page():
    # 1. 路径拼接要用 os.path.join，更通用
    file_path = os.path.join(Page_Dir, "etc", "logout.html")
    # 2. 不要 open 文件对象，直接传路径字符串
    return FileResponse(file_path, media_type="text/html")


@router.post("/logout")
def logout():
    # 1. 实现登出逻辑
    # 2. 返回响应
    return {"message": "Logout success"}
