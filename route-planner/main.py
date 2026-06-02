# ================================================================
# 入口文件
#
# 职责：
# - 初始化 FastAPI app
# - 注册路由
# - 启动服务
# ================================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI路线规划系统")

# 允许前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)