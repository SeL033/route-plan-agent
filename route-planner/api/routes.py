# ================================================================
# HTTP路由
# 负责人：后端
#
# 职责：
# - 接收前端请求
# - 调用 planner_agent.run()
# - 返回 PlanResponse 给前端
# - 处理异常，返回友好错误信息
# ================================================================

from fastapi import APIRouter
from models.schemas import PlanRequest, PlanResponse

router = APIRouter()


@router.post("/api/plan", response_model=PlanResponse)
async def plan_route(request: PlanRequest) -> PlanResponse:
    # TODO: 调用 planner_agent.run(request.user_input)
    pass
