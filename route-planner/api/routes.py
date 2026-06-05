# ================================================================
# HTTP路由
#
# 职责：
# - 接收前端请求
# - 调用 planner_agent.run()
# - 返回 PlanResponse 给前端
# - 处理异常，返回友好错误信息
# ================================================================

from fastapi import APIRouter
from models.schemas import PlanRequest, PlanResponse
from agent import planner_agent

router = APIRouter()


@router.post("/api/plan", response_model=PlanResponse)
async def plan_route(request: PlanRequest) -> PlanResponse:
    try:
        result = await planner_agent.run(
            request.user_input,
            start_location=request.start_location
        )
        return result
    except Exception as e:
        return PlanResponse(
            status="error",
            user_input=request.user_input,
            routes=[],
            error_msg=str(e)
        )