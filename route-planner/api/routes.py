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
from models.schemas import FeedbackRequest, PlanRequest, PlanResponse
from agent import planner_agent
from core.profile_evolution import apply_feedback

router = APIRouter()


@router.post("/api/plan", response_model=PlanResponse)
async def plan_route(request: PlanRequest) -> PlanResponse:
    try:
        result = await planner_agent.run(
            request.user_input,
            start_location=request.start_location,
            user_id=request.user_id
        )
        return result
    except Exception as e:
        return PlanResponse(
            status="error",
            user_input=request.user_input,
            routes=[],
            error_msg=str(e)
        )

@router.post("/api/plan/initial", response_model=PlanResponse)
async def initial_plan_route(request: PlanRequest) -> PlanResponse:
    try:
        result = await planner_agent.run_initial(
            request.user_input,
            start_location=request.start_location,
            user_id=request.user_id
        )
        return result
    except Exception as e:
        return PlanResponse(
            status="error",
            user_input=request.user_input,
            routes=[],
            error_msg=str(e)
        )


@router.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest) -> dict:
    state = apply_feedback(
        user_id=request.user_id,
        route_style=request.route_style,
        liked=request.liked,
        stops=request.stops,
        comment=request.comment
    )
    return {
        "status": "success",
        "message": "用户偏好已更新，下次规划会优先参考这次反馈。",
        "history_summary": state.get("history_summary", "暂无反馈历史"),
        "feedback_count": state.get("feedback_count", 0),
    }
