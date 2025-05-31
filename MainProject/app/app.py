import os

from fastapi import FastAPI
import gradio as gr
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles

# 导入各个页面

# welcome 页面
from MainProject.app.welcome.login import login_page
from MainProject.app.welcome.register import register_page

# homepage 页面
from MainProject.app.homepage.root_home import root_home_page
from MainProject.app.homepage.user_home import user_home_page
from MainProject.app.homepage.admin_home import admin_home_page

# settings 页面
from MainProject.app.settings.user_settings import user_settings
from MainProject.app.settings.root_settings import root_settings
from MainProject.app.settings.admin_settings import admin_settings

app = FastAPI()


# 首页 `/` 自动跳转到登录页
@app.get("/")
def root():
    return RedirectResponse(url="/welcome/login")


# `/welcome` 也跳转到登录页
@app.get("/welcome")
def welcome_root():
    return RedirectResponse(url="/welcome/login")


# welcome 页面
gr.mount_gradio_app(app, login_page(), path="/welcome/login")
gr.mount_gradio_app(app, register_page(), path="/welcome/register")

# homepage 页面
gr.mount_gradio_app(app, root_home_page(), path="/homepage/root_home")
gr.mount_gradio_app(app, admin_home_page(), path="/homepage/admin_home")
gr.mount_gradio_app(app, user_home_page(), path="/homepage/user_home")

# settings 页面
gr.mount_gradio_app(app, user_settings(), path="/settings/user_settings")
gr.mount_gradio_app(app, root_settings(), path="/settings/root_settings")
gr.mount_gradio_app(app, admin_settings(), path="/settings/admin_settings")
