from fastapi import APIRouter
from fastapi.responses import FileResponse
from .common.common import Page_Dir
import os

router = APIRouter()


@router.get("/")
def show_page():
    # 1. 路径拼接要用 os.path.join，更通用
    file_path = os.path.join(Page_Dir, "dashboard.html")
    # 2. 不要 open 文件对象，直接传路径字符串
    return FileResponse(file_path, media_type="text/html")
