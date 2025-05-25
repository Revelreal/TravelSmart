from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from .common.common import Page_Dir
from pydantic import BaseModel
from backend.dbhelper.DBHelper import DBHelper
import os
router = APIRouter()


class RegisterReq(BaseModel):
    username: str
    password: str
    email: str


@router.post("/")
def register(data: RegisterReq):
    # 1. 接收前端传来的用户名、密码、邮箱
    username = data.username
    password = data.password
    email = data.email
    # 2. 验证用户名、密码、邮箱是否符合要求
    db = DBHelper()
    exists = db.fetchone(
        "SELECT id FROM Users WHERE username=%s OR email=%s", (data.username, data.email)
    )
    if exists:
        db.close()
        raise HTTPException(status_code=400, detail="用户名或邮箱已存在")
    # 3. 上传数据库对比用户名密码，确认注册成功，用户名不得重复
    result = db.execute(
        "INSERT INTO Users (username, password, email) VALUES (%s, %s, %s)",
        (username, password, email),
    )
    db.close()
    # 4. 返回注册成功信息
    if result == 1:
        return {"message": f"用户 {username} 注册成功"}
    else:
        raise HTTPException(status_code=500, detail="注册失败，数据库操作失败")


@router.get("/")
def show_page():
    # 1. 路径拼接要用 os.path.join，更通用
    file_path = os.path.join(Page_Dir, "register.html")
    # 2. 不要 open 文件对象，直接传路径字符串
    return FileResponse(file_path, media_type="text/html")
