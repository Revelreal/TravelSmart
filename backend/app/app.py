import os

from fastapi import FastAPI
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
from .routes import index, login, register, dashboard, etc, api

app = FastAPI()


# 自动重定向到index
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/index/")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend目录
STATIC_DIR = os.path.join(BASE_DIR, "..", "frontend", "public", "static")
print("静态目录绝对路径:", STATIC_DIR)  # 可以用于调试
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# 路由注册
app.include_router(prefix="/index", router=index.router)
app.include_router(prefix="/login", router=login.router)
app.include_router(prefix="/register", router=register.router)
app.include_router(prefix="/dashboard", router=dashboard.router)
app.include_router(prefix="/api", router=api.router)
app.include_router(prefix="/etc", router=etc.router)
