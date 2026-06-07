import json
import os
import re
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_PATH = os.path.join(BASE_DIR, "mock_data", "user_state.json")
PROFILE_PATH = os.path.join(BASE_DIR, "mock_data", "user_profiles.json")

TAG_KEYWORDS = {
    "少排队": ["不排队", "少排队", "不想排队", "避开排队"],
    "美食": ["美食", "吃", "餐厅", "小吃"],
    "咖啡": ["咖啡", "cafe"],
    "海边": ["海边", "海滩", "沙滩", "beach"],
    "夜景": ["夜景", "晚上", "夜游"],
    "亲子": ["亲子", "孩子", "小朋友"],
    "文化": ["文化", "博物馆", "历史", "老城区"],
    "自然": ["自然", "公园", "山", "湖"],
    "免费": ["免费", "省钱", "预算低"],
}

TASTE_KEYWORDS = {
    "清淡": ["清淡", "早茶", "茶点"],
    "甜口": ["甜", "甜口", "甜品"],
    "辣味": ["辣", "火锅", "川菜", "小面"],
    "海鲜": ["海鲜", "炸鱼", "fish"],
    "咖啡": ["咖啡"],
}


def load_evolved_profile(user_id: str | None) -> dict:
    base_profiles = _load_json(PROFILE_PATH, {})
    profile = dict(base_profiles.get(user_id or "demo_user", base_profiles.get("demo_user", {})))
    state = _load_json(STATE_PATH, {}).get(user_id or "demo_user", {})
    profile["prefer_tags"] = _merge_weighted(
        profile.get("prefer_tags", []),
        state.get("prefer_weights", {})
    )
    profile["taste_tags"] = _merge_weighted(
        profile.get("taste_tags", []),
        state.get("taste_weights", {})
    )
    profile["avoid_tags"] = _merge_weighted(
        profile.get("avoid_tags", []),
        state.get("avoid_weights", {})
    )
    profile["history_summary"] = state.get("history_summary", "暂无反馈历史")
    profile["feedback_count"] = state.get("feedback_count", 0)
    return profile


def record_user_intent(user_id: str | None, user_input: str) -> dict:
    uid = user_id or "demo_user"
    state = _load_all_state()
    user_state = state.setdefault(uid, _default_state())
    _apply_text_weights(user_state, user_input, weight=1)
    user_state["search_count"] = user_state.get("search_count", 0) + 1
    user_state["last_intent"] = user_input[:120]
    user_state["history_summary"] = _build_summary(user_state)
    user_state["updated_at"] = _now()
    _save_all_state(state)
    return user_state


def apply_feedback(user_id: str | None, route_style: str, liked: bool, stops: list[dict], comment: str | None = None) -> dict:
    uid = user_id or "demo_user"
    state = _load_all_state()
    user_state = state.setdefault(uid, _default_state())
    delta = 2 if liked else -2
    for stop in stops:
        tags = _stop_tags(stop)
        for tag in tags:
            if liked:
                _bump(user_state["prefer_weights"], tag, delta)
            else:
                _bump(user_state["avoid_weights"], tag, abs(delta))
        if stop.get("poi_type") == "food":
            for tag in tags:
                _bump(user_state["taste_weights"], tag, delta if liked else -1)
    if comment:
        _apply_text_weights(user_state, comment, weight=2 if liked else -1)
    user_state["feedback_count"] = user_state.get("feedback_count", 0) + 1
    user_state["last_feedback"] = {
        "route_style": route_style,
        "liked": liked,
        "comment": comment,
        "updated_at": _now(),
    }
    user_state["history_summary"] = _build_summary(user_state)
    user_state["updated_at"] = _now()
    _save_all_state(state)
    return user_state


def _default_state() -> dict:
    return {
        "prefer_weights": {},
        "taste_weights": {},
        "avoid_weights": {},
        "search_count": 0,
        "feedback_count": 0,
        "history_summary": "暂无反馈历史",
    }


def _apply_text_weights(user_state: dict, text: str, weight: int) -> None:
    lowered = text.lower()
    for tag, words in TAG_KEYWORDS.items():
        if any(word in lowered for word in words):
            _bump(user_state["prefer_weights"], tag, weight)
    for tag, words in TASTE_KEYWORDS.items():
        if any(word in lowered for word in words):
            _bump(user_state["taste_weights"], tag, weight)
    budget = re.search(r"预算\s*(\d+)|(\d+)\s*元", text)
    if budget:
        user_state["last_budget"] = int(budget.group(1) or budget.group(2))


def _stop_tags(stop: dict) -> list[str]:
    text = " ".join([
        stop.get("name", ""),
        stop.get("reason", ""),
        stop.get("poi_type", ""),
        " ".join(stop.get("evidence", [])[:2]),
    ])
    tags = []
    for tag, words in {**TAG_KEYWORDS, **TASTE_KEYWORDS}.items():
        if any(word in text for word in words):
            tags.append(tag)
    if stop.get("poi_type") == "food":
        tags.append("美食")
    return list(dict.fromkeys(tags))


def _bump(weights: dict, tag: str, delta: int) -> None:
    weights[tag] = max(-5, min(10, weights.get(tag, 0) + delta))
    if weights[tag] == 0:
        weights.pop(tag, None)


def _merge_weighted(base: list[str], weights: dict) -> list[str]:
    ranked = sorted(weights.items(), key=lambda item: item[1], reverse=True)
    merged = [tag for tag, weight in ranked if weight > 0]
    for tag in base:
        if tag not in merged:
            merged.append(tag)
    return merged[:8]


def _build_summary(user_state: dict) -> str:
    prefers = _top(user_state.get("prefer_weights", {}))
    tastes = _top(user_state.get("taste_weights", {}))
    avoids = _top(user_state.get("avoid_weights", {}))
    pieces = []
    if prefers:
        pieces.append(f"近期更偏好{', '.join(prefers)}")
    if tastes:
        pieces.append(f"口味更接近{', '.join(tastes)}")
    if avoids:
        pieces.append(f"应减少{', '.join(avoids)}")
    return "；".join(pieces) or "暂无反馈历史"


def _top(weights: dict) -> list[str]:
    return [tag for tag, weight in sorted(weights.items(), key=lambda item: item[1], reverse=True) if weight > 0][:3]


def _load_all_state() -> dict:
    return _load_json(STATE_PATH, {})


def _load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save_all_state(state: dict) -> None:
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")
