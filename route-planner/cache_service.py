# ================================================================
# Redis缓存服务
#
# 职责：
# - 缓存Agent规划结果，相同输入直接返回，不重复调用LLM
# - 降低token消耗，提升响应速度
# - 默认缓存1天，每天刷新
# ================================================================

import json
import os
import hashlib

try:
    import redis
except ImportError:
    redis = None

# Redis连接
r = None
if redis is not None and os.getenv("ENABLE_REDIS_CACHE", "").lower() == "true":
    r = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=True,
        socket_connect_timeout=0.2,
        socket_timeout=0.2,
    )

DEFAULT_TTL = 86400  # 1天


def _make_key(user_input: str) -> str:
    """
    把用户输入转成缓存key。
    用md5哈希避免key太长，相同输入永远得到相同key。
    """
    hash_str = hashlib.md5(user_input.strip().encode()).hexdigest()
    return f"route:{hash_str}"


def get_cached_route(user_input: str) -> dict | None:
    """
    查缓存。
    命中返回dict，未命中返回None。
    """
    if r is None:
        return None
    try:
        key = _make_key(user_input)
        cached = r.get(key)
        if cached:
            return json.loads(cached)
        return None
    except Exception:
        # Redis连接失败不影响主流程，直接返回None走正常规划
        return None


def set_cached_route(user_input: str, result: dict, ttl: int = DEFAULT_TTL):
    """
    写缓存。
    result是PlanResponse.model_dump()的结果。
    """
    if r is None:
        return
    try:
        key = _make_key(user_input)
        r.set(key, json.dumps(result, ensure_ascii=False), ex=ttl)
    except Exception:
        # Redis写入失败不影响主流程，静默处理
        pass


def delete_cached_route(user_input: str):
    """手动删除某个缓存，用于调试或强制刷新"""
    if r is None:
        return
    try:
        key = _make_key(user_input)
        r.delete(key)
    except Exception:
        pass
