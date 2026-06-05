# ================================================================
# Agent核心
# ================================================================

import json
import os
from openai import OpenAI
from models.schemas import PlanResponse, Route, Stop, Location
from agent.tools import TOOLS_SCHEMA, TOOLS_MAP
from cache_service import get_cached_route, set_cached_route

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
1. 分析用户意图，提取城市、时长、预算、人群、偏好、出发地等信息
2. 调用 search_poi 搜索合适的景点
3. 对候选景点调用 get_ugc_info 查看真实用户评价和排队情况
4. 根据用户约束（如"不想排队"、"腿脚不便"）筛选或替换景点
5. 如果用户提供了出发地，优先推荐距离出发地近的景点
6. 调用 calculate_route_time 计算时间安排
7. 调用 check_budget 验证预算是否超出，超出则调整
8. 生成3条路线：省时版、省钱版、网红版

## 重要：每个stop必须包含真实坐标
每个停留点的location字段必须填入该POI的真实经纬度坐标。
坐标从search_poi返回的结果里获取，不要编造坐标。

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
          "reason": "结合用户约束说明推荐理由",
          "location": {"lat": 31.2397, "lng": 121.4901}
        }
      ]
    },
    {"style": "省钱版", ...},
    {"style": "网红版", ...}
  ]
}

## 注意事项
- stops控制在3-5个，时间安排要合理
- reason要结合用户的具体需求说明，有针对性
- 如果用户说"不想排队"，查UGC后排队长的要换掉
- 如果预算不够，优先选免费或低价景点
- 老人腿脚不便：优先选室内、平路、距离近的景点
- location坐标必须来自search_poi返回的真实数据

## 严格要求
你的最终回复必须且只能是一个合法的JSON对象，从{开始，到}结束。
不要输出任何解释、分析、markdown格式或代码块。
不要输出```json或```。
直接输出JSON，不要有任何前缀或后缀文字。
"""


async def run(user_input: str, start_location: str = None) -> PlanResponse:
    cache_key = f"{user_input}|{start_location or ''}"
    cached = get_cached_route(cache_key)
    if cached:
        return PlanResponse(**cached)

    user_message = user_input
    if start_location:
        user_message += f"\n\n出发地：{start_location}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]

    client = get_client()

    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
            temperature=0.3,
            max_tokens=4096
        )

        message = response.choices[0].message
        messages.append(message)

        if message.tool_calls:
            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                func = TOOLS_MAP.get(func_name)
                result = func(**func_args) if func else {"error": f"未知工具: {func_name}"}
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False)
                })
        else:
            raw = message.content
            # LLM有时会在JSON外面包markdown代码块，清理掉
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as e:
                raise ValueError(f"LLM返回的JSON格式错误: {e}\n原始内容: {raw[:200]}")
            routes = _parse_routes(data["routes"])
            result = PlanResponse(
                status="success",
                user_input=user_input,
                routes=routes
            )
            set_cached_route(cache_key, result.model_dump())
            return result


def _parse_routes(raw_routes: list) -> list[Route]:
    routes = []
    for r in raw_routes:
        stops = []
        for s in r.get("stops", []):
            loc = s.get("location", {})
            stops.append(Stop(
                poi_id=s["poi_id"],
                name=s["name"],
                arrive_time=s["arrive_time"],
                duration=s["duration"],
                leave_time=s["leave_time"],
                cost=s["cost"],
                reason=s["reason"],
                location=Location(
                    lat=loc.get("lat", 0),
                    lng=loc.get("lng", 0)
                )
            ))
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