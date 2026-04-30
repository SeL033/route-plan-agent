# ================================================================
# 入口文件
# 负责人：后端
#
# 职责：
# - 初始化 FastAPI app
# - 注册路由
# - 启动服务
# ================================================================

from fastapi import FastAPI
from api.routes import router

app = FastAPI(title="AI路线规划系统")
app.include_router(router)
