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

from MainProject.app.API.reviews import create_reviews_app
from MainProject.app.API.preferences import create_travel_preferences_app
from MainProject.app.API.trips import create_itinerary_app

from MainProject.app.notice.notice_page import create_notice_view_app
from MainProject.app.notice.admin_notice_page import create_notice_admin_app

from MainProject.app.ui.friends_component_ui import create_main_ui

from MainProject.auth_utils import verify_token

# 路由服务
app = FastAPI()

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
# =================== 接口注册 ===========================
app = mount_gradio_app(app, create_reviews_app(), path="/api/reviews")
app = mount_gradio_app(app, create_travel_preferences_app(), path="/api/preferences")
app = mount_gradio_app(app, create_itinerary_app(), path="/api/trips")
# notice页面
app = mount_gradio_app(app, create_notice_view_app(), path="/notice/user_notice")
app = mount_gradio_app(app, create_notice_admin_app(), path="/notice/admin_notice")
# ui页面
app = mount_gradio_app(app, create_main_ui(), path="/friends")



# =================== 服务注册 =========================
# 地图服务
@app.get("/api/map", response_class=HTMLResponse)
async def show_amap(request: Request):
    # 1. 获取token
    token = request.query_params.get("token", "")
    # 2. 校验token
    info = verify_token(token)
    if not info or not info.get("username"):
        raise HTTPException(status_code=401, detail="未授权：请登录后再访问地图功能")

    # 3. 获取坐标参数
    lng = request.query_params.get("lng")
    lat = request.query_params.get("lat")
    zoom = request.query_params.get("zoom", "15")
    place = request.query_params.get("place", "")
    timestamp = request.query_params.get("t", "")

    print(f"地图服务接收参数: lng={lng}, lat={lat}, zoom={zoom}, place={place}, t={timestamp}")

    # 4. 创建地图服务实例
    map_service = MapService()

    # 5. 设置坐标参数
    auto_locate_coords = None
    if lng and lat:
        try:
            map_service.center_lng = float(lng)
            map_service.center_lat = float(lat)
            map_service.zoom = int(float(zoom))
            auto_locate_coords = (map_service.center_lng, map_service.center_lat)
            print(f"设置地图中心点为：[{map_service.center_lng}, {map_service.center_lat}]")
        except ValueError:
            print("坐标参数解析失败，使用默认值")

    # 6. 返回地图HTML
    return map_service.get_map_html(
        initial_place=place,
        auto_locate_coords=auto_locate_coords
    )

