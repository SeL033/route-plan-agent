# ================================================================
# Agent工具函数
#
# 职责：
# - 封装所有LLM可以调用的工具
# - TOOLS_SCHEMA 告诉LLM有哪些工具
# - TOOLS_MAP 供Agent执行实际调用
# ================================================================

from math import radians, sin, cos, sqrt, atan2
from core.poi_service import load_pois, filter_by_category, filter_by_budget, filter_by_group, filter_by_exclude
from core.ugc_service import get_reviews_by_poi


def search_poi(
    city: str,
    category: str = None,
    budget_max: int = None,
    suitable_for: str = None,
    exclude_ids: list = None
) -> list:
    """根据条件搜索POI，返回评分最高的结果，最多8条"""
    pois = load_pois()
    pois = [p for p in pois if p["city"] == city]
    if category:
        pois = filter_by_category(pois, category)
    if budget_max is not None:
        pois = filter_by_budget(pois, budget_max)
    if suitable_for:
        pois = filter_by_group(pois, suitable_for)
    if exclude_ids:
        pois = filter_by_exclude(pois, exclude_ids)
    pois.sort(key=lambda x: x["score"], reverse=True)
    return pois[:8]


def get_ugc_info(poi_id: str) -> dict:
    """获取某个POI的用户评价摘要，包括拥挤程度、排队时间"""
    data = get_reviews_by_poi(poi_id)
    return {
        "poi_id": poi_id,
        "poi_name": data.get("poi_name", ""),
        "crowd_level": data.get("crowd_level", "未知"),
        "avg_wait_minutes": data.get("avg_wait_minutes", 0),
        "best_time": data.get("best_time"),
        "avoid_time": data.get("avoid_time"),
        "sample_reviews": data.get("reviews", [])[:3]
    }


def calculate_route_time(poi_ids: list, start_time: str = "09:00") -> dict:
    """根据POI顺序计算路线时间安排"""
    all_pois = load_pois()
    poi_map = {p["id"]: p for p in all_pois}

    hour, minute = map(int, start_time.split(":"))
    current_minutes = hour * 60 + minute
    schedule = []
    total_cost = 0

    for i, poi_id in enumerate(poi_ids):
        poi = poi_map.get(poi_id)
        if not poi:
            continue

        arrive_time = f"{current_minutes // 60:02d}:{current_minutes % 60:02d}"
        stay = poi["duration"]
        total_cost += poi["cost"]
        leave_minutes = current_minutes + stay
        leave_time = f"{leave_minutes // 60:02d}:{leave_minutes % 60:02d}"

        schedule.append({
            "poi_id": poi_id,
            "name": poi["name"],
            "arrive_time": arrive_time,
            "duration": stay,
            "leave_time": leave_time,
            "cost": poi["cost"]
        })

        transit = _estimate_transit(poi_ids, i, poi_map)
        current_minutes = leave_minutes + transit

    return {
        "schedule": schedule,
        "total_duration_minutes": current_minutes - (hour * 60 + minute),
        "total_cost": total_cost,
        "end_time": f"{current_minutes // 60:02d}:{current_minutes % 60:02d}"
    }


def check_budget(poi_ids: list, total_budget: int) -> dict:
    """检查选定POI组合是否超出预算"""
    all_pois = load_pois()
    poi_map = {p["id"]: p for p in all_pois}

    breakdown = []
    total = 0
    for poi_id in poi_ids:
        poi = poi_map.get(poi_id)
        if poi:
            breakdown.append({"poi_id": poi_id, "name": poi["name"], "cost": poi["cost"]})
            total += poi["cost"]

    return {
        "total_cost": total,
        "budget": total_budget,
        "over_budget": total > total_budget,
        "over_amount": max(0, total - total_budget),
        "remaining": max(0, total_budget - total),
        "breakdown": breakdown
    }


def _estimate_transit(poi_ids: list, current_index: int, poi_map: dict) -> int:
    """估算两个相邻POI之间的交通时间（分钟）"""
    if current_index >= len(poi_ids) - 1:
        return 0
    curr = poi_map.get(poi_ids[current_index])
    next_poi = poi_map.get(poi_ids[current_index + 1])
    if not curr or not next_poi:
        return 30
    dist = _haversine(
        curr["location"]["lat"], curr["location"]["lng"],
        next_poi["location"]["lat"], next_poi["location"]["lng"]
    )
    if dist < 2:
        return 15
    elif dist < 10:
        return 30
    else:
        return 60


def _haversine(lat1, lon1, lat2, lon2) -> float:
    """计算两点之间的直线距离（km）"""
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


# LLM可调用的工具描述
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_poi",
            "description": "根据城市、类型、预算、适合人群搜索POI景点列表，返回评分最高的结果",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称，如'上海'"},
                    "category": {"type": "string", "description": "POI类型，可选：景点/美食/购物/文化/自然/亲子/网红"},
                    "budget_max": {"type": "integer", "description": "单个POI最高门票费用（元）"},
                    "suitable_for": {"type": "string", "description": "适合人群：亲子/老人/情侣/朋友/独行"},
                    "exclude_ids": {"type": "array", "items": {"type": "string"}, "description": "需要排除的POI id列表"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ugc_info",
            "description": "获取某个POI的用户评价摘要，包括拥挤程度、排队时间、最佳游览时间",
            "parameters": {
                "type": "object",
                "properties": {
                    "poi_id": {"type": "string", "description": "POI的唯一id"}
                },
                "required": ["poi_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_route_time",
            "description": "根据POI顺序计算路线的时间安排，包括每个地点的到达时间和总游览时长",
            "parameters": {
                "type": "object",
                "properties": {
                    "poi_ids": {"type": "array", "items": {"type": "string"}, "description": "按游览顺序排列的POI id列表"},
                    "start_time": {"type": "string", "description": "出发时间，格式HH:MM，默认09:00"}
                },
                "required": ["poi_ids"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_budget",
            "description": "检查选定的POI组合总费用是否超出用户预算",
            "parameters": {
                "type": "object",
                "properties": {
                    "poi_ids": {"type": "array", "items": {"type": "string"}, "description": "选定的POI id列表"},
                    "total_budget": {"type": "integer", "description": "用户总预算（元）"}
                },
                "required": ["poi_ids", "total_budget"]
            }
        }
    }
]

# 工具名称 → 函数映射
TOOLS_MAP = {
    "search_poi": search_poi,
    "get_ugc_info": get_ugc_info,
    "calculate_route_time": calculate_route_time,
    "check_budget": check_budget
}
