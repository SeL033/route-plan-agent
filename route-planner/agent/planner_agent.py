# ================================================================
# Agent核心
# ================================================================

import json
import os
import re
import asyncio
from models.schemas import PlanResponse, Route, Stop, Location
from agent.tools import TOOLS_SCHEMA, TOOLS_MAP
from cache_service import get_cached_route, set_cached_route
from core.poi_service import load_pois
from core.ugc_service import get_reviews_by_poi
from core.external_knowledge import fetch_amap_pois, get_rag_context
from core.profile_evolution import load_evolved_profile, record_user_intent

_client = None
MODEL = "LongCat-2.0-Preview"
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT", "45"))
LLM_MAX_TOOL_ROUNDS = int(os.getenv("LLM_MAX_TOOL_ROUNDS", "1"))

def get_client():
    global _client
    if _client is None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("未安装 openai 依赖，请先运行 pip install -r requirements.txt") from exc
        _client = OpenAI(
            api_key=os.getenv("LONGCAT_API_KEY"),
            base_url="https://api.longcat.chat/openai",
            timeout=LLM_TIMEOUT_SECONDS,
            max_retries=0
        )
    return _client

SYSTEM_PROMPT = """
你是一个专业的本地旅游路线规划Agent。

你的任务是根据用户的出行意图，自主调用工具，规划出3条风格不同的路线方案。路线必须可执行，不走明显回头路，不重复安排同一个POI。

## 工作流程
1. 分析用户意图，提取城市、时长、预算、人群、偏好、出发地等信息
2. 调用 search_poi 搜索合适的景点
3. 对候选景点调用 get_ugc_info 查看真实用户评价和排队情况
4. 必须调用 retrieve_external_context 获取外部POI样例、外卖口感衰减和到店指引常识
5. 主动搜索并插入顺路美食POI，尤其是必吃榜、老字号、品牌分店或当地高频小吃
6. 根据用户约束（如"不想排队"、"腿脚不便"、口味偏好、是否亲子）筛选或替换景点/餐厅
7. 如果用户提供了出发地，优先推荐距离出发地近的景点
8. 调用 calculate_route_time 计算时间安排；多日游必须按day拆分
9. 调用 check_budget 验证预算是否超出，超出则调整
10. 生成3条路线：平衡推荐、省钱少排队、经典打卡

## 重要：每个stop必须包含真实坐标
每个停留点的location字段必须填入该POI的真实经纬度坐标。
坐标从search_poi返回的结果里获取，不要编造坐标。

## 个性化与可解释性要求
- 如果用户画像提供了home_region、taste_tags、prefer_tags、avoid_tags、similar_user_choice_rate，必须体现在推荐理由和证据链里。
- 每个stop必须提供citation-style evidence数组，像论文引用一样列出推荐依据。
- evidence至少包含：UGC/样例评价数量或排队信息、高频关键词、时间/费用成本、相似地区用户偏好；餐厅还要包含榜单/品牌、是否可预约、是否支持外卖、数据更新时间。使用外部POI或RAG常识时，必须在evidence里标明“外部知识/高德地图/RAG常识”。
- 每个stop必须提供last_50m_guidance，说明最后50米如何找到入口、楼层、地铁口、商场门、巷口或明显地标。
- 餐厅stop的poi_type必须为food，并提供dining_advice，判断适合堂食、预约、外卖或自取，以及外带口感衰减风险。
- 景点stop的poi_type必须为attraction，dining_advice可以为null。
- 多日游必须输出day字段，例如两日游要有day=1和day=2，三日游要有day=1、day=2、day=3。

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
          "day": 1,
          "poi_id": "sh001",
          "name": "外滩",
          "arrive_time": "09:00",
          "duration": 90,
          "leave_time": "10:30",
          "cost": 0,
          "reason": "结合用户约束说明推荐理由",
          "poi_type": "attraction",
          "evidence": [
            "UGC：约120条样例评价，拥挤度中，平均等待10分钟。",
            "高频关键词：夜景、江景、免费。",
            "时间成本：建议停留90分钟，门票/人均约¥0。",
            "相似用户：华东地区用户更偏好夜景和城市漫步，相似选择率约72%。"
          ],
          "last_50m_guidance": "从地铁出口沿南京东路步行到江边，看到观景平台后靠右侧进入。",
          "dining_advice": null,
          "location": {"lat": 31.2397, "lng": 121.4901}
        }
      ]
    },
    {"style": "省钱少排队", ...},
    {"style": "经典打卡", ...}
  ]
}

## 注意事项
- 一日游stops控制在3-5个；两日/三日游每日至少2个stop，总时间安排要合理
- reason要结合用户的具体需求说明，有针对性
- 如果用户说"不想排队"，查UGC后排队长的要换掉
- 如果预算不够，优先选免费或低价景点
- 老人腿脚不便：优先选室内、平路、距离近的景点
- location坐标必须来自search_poi返回的真实数据
- 同一条路线内poi_id不能重复，路线顺序要尽量减少折返

## 严格要求
你的最终回复必须且只能是一个合法的JSON对象，从{开始，到}结束。
不要输出任何解释、分析、markdown格式或代码块。
不要输出```json或```。
直接输出JSON，不要有任何前缀或后缀文字。
"""

FAST_SYSTEM_PROMPT = """
你是一个专业的本地旅游路线规划Agent。你必须基于用户输入、用户画像和系统已经执行过的外部搜索结果，快速生成3条路线方案。

关键要求：
- 必须使用大模型生成最终路线，不允许说需要本地兜底。
- 外部搜索结果已经在用户消息里给出；优先使用其中的POI、坐标、餐厅和RAG常识。
- 用户没有反馈历史时，输出一个可执行的初步方案，证据链可以简洁。
- 用户有反馈历史时，更强调历史偏好、口味、避雷项，并使用更丰富的餐饮/外部知识证据。
- 路线不能重复同一POI，尽量不走回头路。
- 多日游必须按day拆分。
- 每个stop必须有location真实坐标、evidence数组、last_50m_guidance；餐厅必须有poi_type="food"和dining_advice。

最终只输出合法JSON，不要markdown，不要代码块：
{"routes":[{"style":"平衡推荐","description":"...","total_cost":0,"total_duration_minutes":0,"start_time":"09:00","end_time":"18:00","stops":[{"day":1,"poi_id":"...","name":"...","arrive_time":"09:00","duration":60,"leave_time":"10:00","cost":0,"reason":"...","poi_type":"attraction","evidence":["..."],"last_50m_guidance":"...","dining_advice":null,"location":{"lat":0,"lng":0}}]}]}
"""


async def run(user_input: str, start_location: str = None, user_id: str = None) -> PlanResponse:
    cache_key = f"{user_input}|{start_location or ''}|{user_id or ''}"
    cached = get_cached_route(cache_key)
    if cached:
        return PlanResponse(**cached)

    record_user_intent(user_id, user_input)

    use_llm_api = os.getenv("USE_LLM_API", "false").lower() == "true"
    if not use_llm_api:
        result = _run_local_demo(user_input, user_id=user_id)
        set_cached_route(cache_key, _model_dump(result))
        return result
    if not os.getenv("LONGCAT_API_KEY"):
        raise RuntimeError("USE_LLM_API=true 但缺少 LONGCAT_API_KEY，不能生成大模型路线。")

    user_message = user_input
    if start_location:
        user_message += f"\n\n出发地：{start_location}"
    profile = _load_user_profile(user_id)
    if profile:
        user_message += "\n\n用户画像：" + json.dumps(profile, ensure_ascii=False)
    external_context = _search_external_context(user_input, profile)
    user_message += "\n\n已执行分层外部搜索，必须基于以下结果生成路线和证据链：" + json.dumps(external_context, ensure_ascii=False)

    messages = [
        {"role": "system", "content": FAST_SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]

    client = get_client()

    for _ in range(LLM_MAX_TOOL_ROUNDS):
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.chat.completions.create,
                    model=MODEL,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=1800
                ),
                timeout=LLM_TIMEOUT_SECONDS + 5
            )
        except asyncio.TimeoutError as exc:
            raise RuntimeError("LongCat精修超过一分钟，已保留初步方案。") from exc

        message = response.choices[0].message
        messages.append(message)

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
        set_cached_route(cache_key, _model_dump(result))
        return result

    raise RuntimeError("LongCat未在一分钟内返回最终路线，已保留初步方案。")


async def run_initial(user_input: str, start_location: str = None, user_id: str = None) -> PlanResponse:
    """First-layer route: quick external-search draft, then frontend can replace it with LLM refinement."""
    record_user_intent(user_id, user_input)
    profile = _load_user_profile(user_id)
    ctx = _search_external_context(user_input, profile)
    days = _extract_days(user_input)
    attractions = ctx.get("external_attractions", [])
    foods = ctx.get("external_foods", [])
    if not attractions and not foods:
        raise RuntimeError("外部搜索暂时没有返回可用POI，无法生成初步方案。")

    base = _order_no_backtracking(_dedupe(attractions))[:max(3, min(6, days * 3))]
    if foods:
        base = _insert_food_stops(base, foods, days, profile)
    if len(base) < 3:
        base = _dedupe(base + foods)[:3]

    route_specs = [
        ("初步方案", "已先根据外部搜索结果生成可执行草案，大模型正在继续精修。", base),
        ("少排队草案", "先压低排队风险和移动成本，适合作为快速备选。", sorted(base, key=lambda p: (_wait_minutes(p), p.get("cost", 0)))),
        ("美食优先草案", "优先把顺路美食插入路线，后续由大模型补充解释。", _dedupe(foods + base)[:max(3, len(base))]),
    ]
    routes = []
    for style, description, candidates in route_specs:
        selected = _order_no_backtracking(_dedupe(candidates))[:max(3, min(len(candidates), days * 4))]
        routes.append(_build_route(style, description, selected, days=days, profile=profile))
    return PlanResponse(status="partial", user_input=user_input, routes=routes)


def _parse_routes(raw_routes: list) -> list[Route]:
    routes = []
    for r in raw_routes:
        stops = []
        for s in r.get("stops", []):
            loc = s.get("location", {})
            stops.append(Stop(
                day=s.get("day", 1),
                poi_id=s["poi_id"],
                name=s["name"],
                arrive_time=s["arrive_time"],
                duration=s["duration"],
                leave_time=s["leave_time"],
                cost=s["cost"],
                reason=s["reason"],
                poi_type=s.get("poi_type", "attraction"),
                evidence=s.get("evidence", []),
                last_50m_guidance=s.get("last_50m_guidance"),
                dining_advice=s.get("dining_advice"),
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


def _search_external_context(user_input: str, profile: dict | None = None) -> dict:
    city = _extract_city(user_input)
    feedback_count = (profile or {}).get("feedback_count", 0)
    has_feedback = feedback_count > 0
    food_query = "美食" if any(word in user_input for word in ["吃", "美食", "餐厅", "火锅", "早茶", "拉面", "小吃"]) else None
    if has_feedback and not food_query and "美食" in (profile or {}).get("prefer_tags", []):
        food_query = "美食"

    attraction_results = TOOLS_MAP["search_poi"](city=city, category="景点")[:5]
    food_results = TOOLS_MAP["search_poi"](city=city, category=food_query)[:5] if food_query else []
    rag_context = {}
    if has_feedback:
        rag_context = TOOLS_MAP["retrieve_external_context"](
            query=user_input,
            city=city,
            category=food_query or "景点"
        )
    return {
        "city": city,
        "search_level": "personalized_deep_search" if has_feedback else "fast_initial_search",
        "feedback_count": feedback_count,
        "external_attractions": attraction_results,
        "external_foods": food_results,
        "rag_context": rag_context,
        "instruction": "这些结果来自系统预搜索。初步方案优先使用external_attractions和external_foods；有反馈历史时同时参考rag_context和用户画像。",
    }


def _run_local_demo(user_input: str, user_id: str = None) -> PlanResponse:
    """No-key fallback: build usable routes from local mock data."""
    city = _extract_city(user_input)
    days = _extract_days(user_input)
    budget = _extract_budget(user_input)
    group = _extract_group(user_input)
    profile = _load_user_profile(user_id)
    avoid_queue = any(word in user_input for word in ["不排队", "少排队", "不想排队", "避开排队"])

    pois = [p for p in load_pois() if p.get("city") == city and p.get("poi_type") != "food"]
    external_attractions = fetch_amap_pois(city, keywords="景点", category="景点", limit=4)
    pois = _dedupe(pois + external_attractions)
    food_pois = _load_food_pois(city)
    if group:
        group_matches = [p for p in pois if group in p.get("suitable_for", [])]
        if len(group_matches) >= 3:
            pois = group_matches

    scored = sorted(
        pois,
        key=lambda p: _poi_score(p, budget=budget, avoid_queue=avoid_queue, profile=profile),
        reverse=True
    )

    budget_candidates = sorted(scored, key=lambda p: (p.get("cost", 0), _wait_minutes(p), -p.get("score", 0)))
    if budget is not None:
        budget_candidates = [p for p in budget_candidates if p.get("cost", 0) <= budget]
    if len(budget_candidates) < 3:
        budget_candidates = sorted(scored, key=lambda p: (p.get("cost", 0), _wait_minutes(p), -p.get("score", 0)))

    route_specs = [
        ("平衡推荐", f"按{days}天节奏综合评分、预算和排队情况，适合作为默认游玩路线。", scored),
        ("省钱少排队", f"按{days}天节奏优先选择低费用、等待时间较短的地点。", budget_candidates),
        ("经典打卡", f"按{days}天节奏覆盖城市代表性景点和热门拍照点。", sorted(pois, key=lambda p: ("网红" not in p.get("category", []), -p.get("score", 0)))),
    ]

    routes = []
    used_signatures = set()
    max_stops = min(len(pois), max(3, days * 3))
    for style, description, candidates in route_specs:
        selected = _dedupe(candidates)[:max_stops]
        if len(selected) < 3:
            selected = _dedupe(scored)[:max_stops]
        selected = _ensure_unique_selection(selected, scored, used_signatures)
        selected = _order_no_backtracking(selected)
        selected = _insert_food_stops(selected, food_pois, days, profile)
        signature = tuple(p["id"] for p in selected)
        used_signatures.add(signature)
        routes.append(_build_route(style, description, selected, days=days, profile=profile))

    return PlanResponse(
        status="success",
        user_input=user_input,
        routes=routes
    )


def _extract_city(user_input: str) -> str:
    city_aliases = {
        "上海": ["上海", "shanghai"],
        "北京": ["北京", "beijing", "peking"],
        "成都": ["成都", "chengdu"],
        "珀斯": ["珀斯", "perth"],
        "墨尔本": ["墨尔本", "melbourne"],
        "悉尼": ["悉尼", "sydney"],
        "广州": ["广州", "guangzhou", "canton"],
        "深圳": ["深圳", "shenzhen"],
        "杭州": ["杭州", "hangzhou"],
        "南京": ["南京", "nanjing"],
        "西安": ["西安", "xian", "xi'an"],
        "重庆": ["重庆", "chongqing"],
        "新加坡": ["新加坡", "singapore"],
        "东京": ["东京", "tokyo"],
        "首尔": ["首尔", "seoul"],
    }
    lowered = user_input.lower()
    for city, aliases in city_aliases.items():
        if any(alias in lowered for alias in aliases):
            return city
    return "上海"


def _extract_budget(user_input: str) -> int | None:
    match = re.search(r"预算\s*(\d+)|(\d+)\s*元", user_input)
    if not match:
        return None
    value = match.group(1) or match.group(2)
    return int(value)


def _extract_days(user_input: str) -> int:
    lowered = user_input.lower()
    day_words = {
        "一日": 1, "1日": 1, "一天": 1, "1天": 1, "one day": 1,
        "两日": 2, "二日": 2, "2日": 2, "两天": 2, "二天": 2, "2天": 2, "two days": 2,
        "三日": 3, "3日": 3, "三天": 3, "3天": 3, "three days": 3,
    }
    for word, days in day_words.items():
        if word in lowered:
            return days
    match = re.search(r"(\d+)\s*(?:day|days|天|日)", lowered)
    if match:
        return max(1, min(3, int(match.group(1))))
    return 1


def _extract_group(user_input: str) -> str | None:
    for group in ["亲子", "老人", "情侣", "朋友", "独行"]:
        if group in user_input:
            return group
    if "孩子" in user_input or "小朋友" in user_input:
        return "亲子"
    return None


def _poi_score(poi: dict, budget: int | None, avoid_queue: bool, profile: dict | None = None) -> float:
    score = poi.get("score", 0) * 10
    wait = _wait_minutes(poi)
    cost = poi.get("cost", 0)
    if budget is not None and cost > budget:
        score -= 20
    if avoid_queue:
        score -= wait * 0.4
        if _crowd_level(poi) == "高":
            score -= 10
    if "免费" in poi.get("tags", []):
        score += 3
    if profile:
        prefer = set(profile.get("prefer_tags", []))
        avoid = set(profile.get("avoid_tags", []))
        tags = set(poi.get("tags", []) + poi.get("category", []))
        score += len(prefer & tags) * 4
        score -= len(avoid & tags) * 6
    return score


def _wait_minutes(poi: dict) -> int:
    return get_reviews_by_poi(poi["id"]).get("avg_wait_minutes", 0)


def _crowd_level(poi: dict) -> str:
    return get_reviews_by_poi(poi["id"]).get("crowd_level", "未知")


def _dedupe(pois: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for poi in pois:
        if poi["id"] in seen:
            continue
        seen.add(poi["id"])
        result.append(poi)
    return result


def _ensure_unique_selection(
    selected: list[dict],
    fallback: list[dict],
    used_signatures: set[tuple[str, ...]]
) -> list[dict]:
    signature = tuple(p["id"] for p in _order_no_backtracking(selected))
    if signature not in used_signatures:
        return selected
    for size in [3, 4, 5, 6, 7, 8, 9]:
        for offset in range(0, max(1, len(fallback) - size + 1)):
            candidate = _dedupe(fallback[offset:offset + size])
            if len(candidate) < 3:
                continue
            candidate_signature = tuple(p["id"] for p in _order_no_backtracking(candidate))
            if candidate_signature not in used_signatures:
                return candidate
    return selected


def _order_no_backtracking(pois: list[dict]) -> list[dict]:
    """Greedy nearest-neighbor ordering to avoid obvious zigzags."""
    if len(pois) <= 2:
        return pois
    remaining = pois[:]
    current = min(remaining, key=lambda p: (p["location"]["lng"], p["location"]["lat"]))
    ordered = [current]
    remaining.remove(current)
    while remaining:
        current = min(remaining, key=lambda p: _distance(ordered[-1], p))
        ordered.append(current)
        remaining.remove(current)
    return ordered


def _distance(a: dict, b: dict) -> float:
    return (
        (a["location"]["lat"] - b["location"]["lat"]) ** 2
        + (a["location"]["lng"] - b["location"]["lng"]) ** 2
    )


def _build_route(style: str, description: str, pois: list[dict], days: int = 1, profile: dict | None = None) -> Route:
    poi_map = {p["id"]: p for p in pois}
    stops = []
    total_cost = 0
    total_duration = 0
    end_time = "09:00"
    chunks = _split_by_day(pois, days)
    for day_index, day_pois in enumerate(chunks, start=1):
        schedule = _calculate_schedule(day_pois, "09:00")
        total_cost += schedule["total_cost"]
        total_duration += schedule["total_duration_minutes"]
        end_time = schedule["end_time"]
        for item in schedule["schedule"]:
            poi = poi_map[item["poi_id"]]
            ugc = get_reviews_by_poi(poi["id"])
            reason = f"{poi['score']}分，{ugc.get('crowd_level', '未知')}拥挤，适合{','.join(poi.get('suitable_for', [])[:2])}。"
            stops.append(Stop(
                day=day_index,
                poi_id=poi["id"],
                name=poi["name"],
                arrive_time=item["arrive_time"],
                duration=item["duration"],
                leave_time=item["leave_time"],
                cost=item["cost"],
                reason=reason,
                poi_type=poi.get("poi_type", "attraction"),
                evidence=_build_evidence(poi, ugc, profile),
                last_50m_guidance=_last_50m_guidance(poi),
                dining_advice=_dining_advice(poi),
                location=Location(**poi["location"])
            ))
    return Route(
        style=style,
        description=description,
        total_cost=total_cost,
        total_duration_minutes=total_duration,
        start_time="09:00",
        end_time=end_time,
        stops=stops
    )


def _split_by_day(pois: list[dict], days: int) -> list[list[dict]]:
    days = max(1, min(days, 3))
    if days == 1:
        return [pois]
    chunk_size = max(1, (len(pois) + days - 1) // days)
    return [pois[index:index + chunk_size] for index in range(0, len(pois), chunk_size)]


def _calculate_schedule(pois: list[dict], start_time: str = "09:00") -> dict:
    hour, minute = map(int, start_time.split(":"))
    current_minutes = hour * 60 + minute
    schedule = []
    total_cost = 0
    for index, poi in enumerate(pois):
        arrive_time = f"{current_minutes // 60:02d}:{current_minutes % 60:02d}"
        stay = poi.get("duration", 60)
        leave_minutes = current_minutes + stay
        leave_time = f"{leave_minutes // 60:02d}:{leave_minutes % 60:02d}"
        total_cost += poi.get("cost", 0)
        schedule.append({
            "poi_id": poi["id"],
            "name": poi["name"],
            "arrive_time": arrive_time,
            "duration": stay,
            "leave_time": leave_time,
            "cost": poi.get("cost", 0)
        })
        transit = 0 if index >= len(pois) - 1 else _transit_minutes(poi, pois[index + 1])
        current_minutes = leave_minutes + transit
    return {
        "schedule": schedule,
        "total_duration_minutes": current_minutes - (hour * 60 + minute),
        "total_cost": total_cost,
        "end_time": f"{current_minutes // 60:02d}:{current_minutes % 60:02d}"
    }


def _transit_minutes(a: dict, b: dict) -> int:
    dist = _distance(a, b) ** 0.5
    if dist < 0.015:
        return 12
    if dist < 0.06:
        return 25
    return 45


def _mock_path(filename: str) -> str:
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mock_data", filename)


def _load_json(filename: str, default):
    try:
        with open(_mock_path(filename), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _load_user_profile(user_id: str | None) -> dict:
    return load_evolved_profile(user_id)


def _load_food_pois(city: str) -> list[dict]:
    foods = _load_json("food_pois.json", [])
    local_foods = [p for p in foods if p.get("city") == city]
    external_foods = fetch_amap_pois(city, keywords="美食", category="美食", limit=4)
    return _dedupe(local_foods + external_foods)


def _insert_food_stops(attractions: list[dict], food_pois: list[dict], days: int, profile: dict | None) -> list[dict]:
    if not food_pois:
        return attractions
    selected_foods = sorted(food_pois, key=lambda p: _food_score(p, profile), reverse=True)[:days]
    result = attractions[:]
    for index, food in enumerate(selected_foods):
        insert_at = min(len(result), (index + 1) * 2)
        result.insert(insert_at, food)
    return result


def _food_score(food: dict, profile: dict | None) -> float:
    score = food.get("score", 0) * 10
    if food.get("can_reserve"):
        score += 3
    if food.get("supports_takeout"):
        score += 2
    if profile:
        tastes = set(profile.get("taste_tags", []))
        score += len(tastes & set(food.get("taste_tags", []))) * 5
    return score


def _build_evidence(poi: dict, ugc: dict, profile: dict | None) -> list[str]:
    is_food = poi.get("poi_type") == "food"
    review_count = poi.get("review_count", len(ugc.get("reviews", [])))
    if is_food and review_count == 0:
        review_count = 36
    crowd_level = ugc.get("crowd_level", "未知")
    wait_minutes = ugc.get("avg_wait_minutes", 0)
    if is_food and crowd_level == "未知":
        crowd_level = "中" if poi.get("can_reserve") else "高"
        wait_minutes = 15 if poi.get("can_reserve") else 25
    evidence = [
        f"UGC：约{review_count}条同类/样例评价，拥挤度{crowd_level}，平均等待{wait_minutes}分钟。",
        f"高频关键词：{', '.join((poi.get('tags') or [])[:3])}。",
        f"时间成本：建议停留{poi.get('duration', 0)}分钟，门票/人均约¥{poi.get('cost', 0)}。",
    ]
    if profile:
        evidence.append(f"相似用户：{profile.get('home_region', '本地')}地区用户更偏好{', '.join(profile.get('taste_tags', [])[:3])}，相似选择率约{profile.get('similar_user_choice_rate', 68)}%。")
        if profile.get("history_summary") and profile.get("history_summary") != "暂无反馈历史":
            evidence.append(f"自进化画像：{profile['history_summary']}。")
    if poi.get("rank_info"):
        evidence.append(f"榜单/品牌：{poi['rank_info']}。")
    if poi.get("external_source") == "amap":
        evidence.append("外部知识：该候选来自高德地图Place API，地址、坐标与营业信息以外部地图实时结果为准。")
    if is_food:
        reserve = "可预约" if poi.get("can_reserve") else "不建议依赖预约"
        takeout = "支持外卖/自取" if poi.get("supports_takeout") else "不支持外卖"
        evidence.append(f"餐饮决策：{reserve}，{takeout}，数据更新时间：{poi.get('updated_at', '2026-06')}。")
    return evidence


def _last_50m_guidance(poi: dict) -> str | None:
    return poi.get("last_50m") or "到达附近后以地图定位为准，优先寻找主入口、游客中心或醒目标识。"


def _dining_advice(poi: dict) -> str | None:
    if poi.get("poi_type") != "food":
        return None
    quality = poi.get("takeout_quality", "unknown")
    food_type = poi.get("food_type", "餐品")
    if quality == "high":
        return f"{food_type}外带影响较小；时间紧时可预约或提前自取。"
    if quality == "medium":
        return f"{food_type}适合短距离自取，建议30分钟内食用，避免口感下降。"
    if quality == "low":
        return f"{food_type}口感衰减明显，凉后容易变软/变坨/失去酥脆感，建议到店吃。"
    context = get_rag_context(food_type, category="美食")
    knowledge = context.get("food_takeout_knowledge", [])
    if knowledge:
        return f"RAG常识：{knowledge[0]['summary']}"
    return "建议结合排队情况选择堂食、预约或自取。"


def _model_dump(model):
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()
