# ================================================================
# Agent核心
#
# 职责：
# - 接收用户原始输入
# - 用LongCat function calling让LLM自主决定调用哪些工具
# - 收集工具调用结果，驱动LLM持续推理直到生成完整路线
# - 最终返回 PlanResponse
# ================================================================

import json
import os
from openai import OpenAI
from models.schemas import PlanResponse, Route, Stop
from agent.tools import TOOLS_SCHEMA, TOOLS_MAP
from cache_service import get_cached_route, set_cached_route

# 懒加载client，避免import时env还没加载
_client = None

def get_client():
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.getenv("LONGCAT_API_KEY"),
            base_url="https://api.longcat.chat/openai"
        )
    return _client

MODEL = "LongCat-2.0-Preview"

SYSTEM_PROMPT = """
你是一个专业的本地旅游路线规划Agent。

你的任务是根据用户的出行意图，自主调用工具，规划出3条风格不同的路线方案。

## 工作流程
1. 分析用户意图，提取城市、时长、预算、人群、偏好等信息
2. 调用 search_poi 搜索合适的景点
3. 对候选景点调用 get_ugc_info 查看真实用户评价和排队情况
4. 根据用户约束（如"不想排队"）筛选或替换景点
5. 调用 calculate_route_time 计算时间安排
6. 调用 check_budget 验证预算是否超出，超出则调整
7. 生成3条路线：省时版、省钱版、网红版

## 输出格式
完成规划后，输出以下JSON格式（不要输出其他内容）：
{
    "routes": [
    {
        "style": "省时版",
        "description": "一句话亮点描述",
        "total_cost": 220,
        "total_duration_minutes": 420,
        "start_time": "09:00",
        "end_time": "16:00",
        "stops": [
        {
            "poi_id": "sh001",
            "name": "外滩",
            "arrive_time": "09:00",
            "duration": 90,
            "leave_time": "10:30",
            "cost": 0,
            "reason": "结合用户约束说明推荐理由"
        }
        ]
    },
    {"style": "省钱版", "description": "...", "total_cost": 0, "total_duration_minutes": 0, "start_time": "09:00", "end_time": "17:00", "stops": []},
    {"style": "网红版", "description": "...", "total_cost": 0, "total_duration_minutes": 0, "start_time": "09:00", "end_time": "17:00", "stops": []}
    ]
}

## 注意事项
- stops控制在3-5个，时间安排要合理
- reason要结合用户的具体需求说明，有针对性
- 如果用户说"不想排队"，查UGC后排队长的要换掉
- 如果预算不够，优先选免费或低价景点
"""


async def run(user_input: str) -> PlanResponse:
    """
    Agent主入口。
    先查Redis缓存，命中直接返回。
    未命中则启动Agent规划，结果写入缓存。
    """
    # 查缓存
    cached = get_cached_route(user_input)
    if cached:
        return PlanResponse(**cached)

    # 启动Agent
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]

    client = get_client()

    # function calling循环
    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=4096
        )

        message = response.choices[0].message
        messages.append(message)

        # LLM决定调用工具
        if message.tool_calls:
            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                func = TOOLS_MAP.get(func_name)
                if func:
                    result = func(**func_args)
                else:
                    result = {"error": f"未知工具: {func_name}"}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False)
                })

        # LLM输出最终结果
        else:
            raw = message.content
            data = json.loads(raw)
            routes = _parse_routes(data["routes"])

            result = PlanResponse(
                status="success",
                user_input=user_input,
                routes=routes
            )

            set_cached_route(user_input, result.model_dump())
            return result


def _parse_routes(raw_routes: list) -> list[Route]:
    """把LLM输出的原始路线数据转换为Route对象列表"""
    routes = []
    for r in raw_routes:
        stops = [Stop(**s) for s in r.get("stops", [])]
        routes.append(Route(
            style=r["style"],
            description=r["description"],
            total_cost=r["total_cost"],
            total_duration_minutes=r["total_duration_minutes"],
            start_time=r["start_time"],
            end_time=r["end_time"],
            stops=stops
        ))
    return routes