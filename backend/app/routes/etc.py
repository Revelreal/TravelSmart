from fastapi import APIRouter
from fastapi.responses import FileResponse
from .common.common import Page_Dir
import os

router = APIRouter()


###
#                 <li><a href="/etc/settings">基础设置</a></li>
#                 <li><a href="/etc/logout">退出登录</a></li>
#                 <li><a href="/etc/delete-account">注销账号</a></li>
#                 <li><a href="/etc/help">帮助</a></li>
#                 <li><a href="/etc/about">关于</a></li>
#                 <li><a href="/etc/terms">服务条款</a></li>
#                 <li><a href="/etc/contact">联系我们</a></li>
#                 ###

@router.get("/logout")
def get_logout():
    # 1. 路径拼接要用 os.path.join，更通用
    file_path = os.path.join(Page_Dir, "etc", "logout.html")
    # 2. 不要 open 文件对象，直接传路径字符串
    return FileResponse(file_path, media_type="text/html")


@router.post("/logout")
def post_logout():
    # 1. 实现登出逻辑
    # 2. 返回响应
    return {"message": "Logout success"}


@router.get("/settings")
def get_settings():
    pass


@router.post("/settings")
def post_settings():
    pass


@router.get("/delete-account")
def get_delete_account():
    pass


@router.post("/delete-account")
def post_delete_account():
    # 获取当前用户名
    # 1. 删除数据库中用户信息
    # 2. 删除文件系统中用户相关文件
    # 3. 返回响应
    return {"message": "Delete account success"}


@router.get("/help")
def get_help():
    pass


@router.post("/help")
def post_help():
    pass


@router.get("/about")
def get_about():
    pass


@router.post("/about")
def post_about():
    pass


@router.get("/terms")
def get_terms():
    pass


@router.post("/terms")
def post_terms():
    pass


@router.get("/contact")
def get_contact():
    pass


@router.post("/contact")
def post_contact():
    pass
