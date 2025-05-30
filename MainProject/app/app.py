import os
from urllib.request import Request

from fastapi import FastAPI
import gradio as gr
from starlette.responses import RedirectResponse, HTMLResponse
from starlette.staticfiles import StaticFiles

# 导入各个页面
from MainProject.app.welcome.login import login_page
from MainProject.app.welcome.register import register_page
from MainProject.app.homepage.settings import settings_page
from MainProject.app.homepage.user_home import user_home_page
from MainProject.app.homepage.admin_home import admin_home_page

app = FastAPI()

# 引入静态文件
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# 首页 `/` 自动跳转到登录页
@app.get("/")
def root():
    return RedirectResponse(url="/welcome/login")


# `/welcome` 也跳转到登录页
@app.get("/welcome")
def welcome_root():
    return RedirectResponse(url="/welcome/login")


# 将 Gradio 登录页面挂载到根路径
gr.mount_gradio_app(app, login_page(), path="/welcome/login")
gr.mount_gradio_app(app, register_page(), path="/welcome/register")
gr.mount_gradio_app(app, settings_page(), path="/homepage/settings")
gr.mount_gradio_app(app, user_home_page(), path="/homepage/user_home")
gr.mount_gradio_app(app, admin_home_page(), path="/homepage/admin_home")
