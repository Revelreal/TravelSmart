from fastapi import FastAPI
from gradio import mount_gradio_app
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse

from MainProject.app.API.map_service import MapService

from MainProject.app.welcome.login import create_login_app
from MainProject.app.welcome.register import create_register_app
from MainProject.app.welcome.forgot_password import create_forgot_password_app

from MainProject.app.homepage.user_home import create_user_home_app
from MainProject.app.homepage.admin_home import create_admin_home_app
from MainProject.app.homepage.root_home import create_root_home_app

from MainProject.app.settings.user_settings import create_user_settings
from MainProject.app.settings.admin_settings import create_admin_settings
from MainProject.app.settings.root_settings import create_root_settings

from MainProject.auth_utils import verify_token

# 路由服务
app = FastAPI()
# 高德地图服务
map_service = MapService()


# =================== 路由注册 =========================
@app.get("/")
def root():
    return RedirectResponse(url="/welcome/login")


@app.get("/welcome/")
def welcome():
    return RedirectResponse(url="/welcome/login")


# welcome页面
app = mount_gradio_app(app, create_login_app(), path="/welcome/login")
app = mount_gradio_app(app, create_register_app(), path="/welcome/register")
app = mount_gradio_app(app, create_forgot_password_app(), path="/welcome/forgot_password")
# homepage页面
app = mount_gradio_app(app, create_user_home_app(), path="/homepage/user_home")
app = mount_gradio_app(app, create_admin_home_app(), path="/homepage/admin_home")
app = mount_gradio_app(app, create_root_home_app(), path="/homepage/root_home")
# settings页面
app = mount_gradio_app(app, create_user_settings(), path="/settings/user_settings")
app = mount_gradio_app(app, create_admin_settings(), path="/settings/admin_settings")
app = mount_gradio_app(app, create_root_settings(), path="/settings/root_settings")


# =================== 服务注册 =========================
# 地图服务
@app.get("/api/map", response_class=HTMLResponse)
async def show_amap(request: Request):
    # 1. 获取token
    token = request.query_params.get("token", "")
    # 2. 校验token
    info = verify_token(token)
    if not info or not info.get("username"):
        # 3. 鉴权失败直接拒绝
        raise HTTPException(status_code=401, detail="未授权：请登录后再访问地图功能")
    # 4. token通过返回地图html
    return map_service.get_map_html()
