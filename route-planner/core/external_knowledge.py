import json
import os
import ssl
import time
import urllib.parse
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AMAP_PLACE_URL = "https://restapi.amap.com/v3/place/text"
AMAP_TIMEOUT_SECONDS = float(os.getenv("EXTERNAL_API_TIMEOUT", "1.2"))
AMAP_CACHE_TTL_SECONDS = 600

_amap_cache: dict[str, tuple[float, list[dict]]] = {}

FOOD_KNOWLEDGE = [
    {
        "keywords": ["生煎", "炸物", "酥", "锅贴", "炸鱼", "薯条"],
        "summary": "外带后水汽会让外壳变软，酥脆感下降；超过20-30分钟建议到店吃。",
        "takeout_quality": "low",
    },
    {
        "keywords": ["汤面", "小面", "拉面", "粉丝汤", "叻沙", "泡馍"],
        "summary": "面类和粉类长时间外带容易吸汤变坨，汤底温度下降后香气也会弱化；建议现场热吃或汤面分装。",
        "takeout_quality": "low",
    },
    {
        "keywords": ["火锅", "烤鸭", "寿司", "小笼包"],
        "summary": "这类餐品强依赖现做温度、蘸料和入口状态，外带会明显影响风味；优先预约堂食。",
        "takeout_quality": "low",
    },
    {
        "keywords": ["早茶", "茶点", "点心", "参鸡汤", "本帮菜", "川菜"],
        "summary": "短距离自取影响相对可控，但建议30分钟内食用；汤汁、蒸点和热菜最好保温。",
        "takeout_quality": "medium",
    },
    {
        "keywords": ["甜品", "冰品", "咖啡", "面包"],
        "summary": "甜品和饮品更适合短距离外带，但冰品会融化、咖啡会氧化降温，建议安排在路线后段或现场休息。",
        "takeout_quality": "medium",
    },
]


def fetch_amap_pois(city: str, keywords: str | None = None, category: str | None = None, limit: int = 5) -> list[dict]:
    key = os.getenv("AMAP_KEY")
    if not key:
        return []

    keyword = keywords or category or "景点"
    cache_key = f"{city}|{keyword}|{limit}"
    cached = _amap_cache.get(cache_key)
    if cached and time.time() - cached[0] < AMAP_CACHE_TTL_SECONDS:
        return cached[1]

    params = {
        "key": key,
        "keywords": keyword,
        "city": city,
        "offset": str(limit),
        "page": "1",
        "extensions": "all",
    }
    url = f"{AMAP_PLACE_URL}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=AMAP_TIMEOUT_SECONDS, context=_ssl_context()) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return []

    if payload.get("status") != "1":
        return []

    pois = [_normalize_amap_poi(item, city, category) for item in payload.get("pois", [])[:limit]]
    pois = [poi for poi in pois if poi is not None]
    _amap_cache[cache_key] = (time.time(), pois)
    return pois


def get_rag_context(query: str, city: str | None = None, category: str | None = None) -> dict:
    text = f"{query} {category or ''}"
    matched = []
    for item in FOOD_KNOWLEDGE:
        if any(keyword in text for keyword in item["keywords"]):
            matched.append(item)
    if not matched and ("外卖" in text or "打包" in text or "餐厅" in text or "美食" in text):
        matched = FOOD_KNOWLEDGE[:3]

    amap = fetch_amap_pois(city or "", keywords=query, category=category, limit=3) if city else []
    return {
        "city": city,
        "query": query,
        "food_takeout_knowledge": matched[:3],
        "external_poi_samples": amap,
        "latency_strategy": "外部POI请求设置1.2秒超时，失败时使用本地mock与RAG常识兜底。",
    }


def _normalize_amap_poi(item: dict, city: str, category: str | None) -> dict | None:
    location = item.get("location")
    if not location or "," not in location:
        return None
    lng, lat = location.split(",", 1)
    name = item.get("name")
    if not name:
        return None

    business = item.get("business") or {}
    photos = item.get("photos") or []
    type_text = item.get("type", "")
    is_food = "餐饮" in type_text or category == "美食"
    cost = _to_int(business.get("cost"), 80 if is_food else 0)
    tag_candidates = [part for part in type_text.split(";") if part][:3]
    if item.get("address"):
        tag_candidates.append("外部POI")

    return {
        "id": f"amap_{item.get('id', name)}",
        "name": name,
        "city": city,
        "category": ["美食" if is_food else "景点", "外部POI"],
        "cost": cost,
        "duration": 70 if is_food else 90,
        "location": {"lat": float(lat), "lng": float(lng)},
        "score": 4.2,
        "tags": tag_candidates[:4] or ["外部POI"],
        "taste_tags": tag_candidates[:2],
        "open_time": business.get("opentime_today") or "以外部地图为准",
        "suitable_for": ["朋友", "情侣", "亲子"],
        "poi_type": "food" if is_food else "attraction",
        "rank_info": "来自高德地图Place API的外部POI候选",
        "can_reserve": False,
        "supports_takeout": bool(is_food),
        "food_type": tag_candidates[0] if is_food and tag_candidates else "餐饮",
        "takeout_quality": "unknown",
        "last_50m": _last_50m_from_amap(item),
        "updated_at": "高德实时接口",
        "photo_url": photos[0].get("url") if photos else None,
        "external_source": "amap",
    }


def _last_50m_from_amap(item: dict) -> str:
    address = item.get("address") or "地图标注地址"
    business = item.get("business") or {}
    entrance = business.get("business_area") or item.get("adname") or "附近街区"
    return f"外部地图地址：{address}；到达{entrance}后优先核对门牌、商场导视和店名招牌。"


def _to_int(value, default: int) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()
