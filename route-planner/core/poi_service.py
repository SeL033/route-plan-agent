# ================================================================
# POI数据服务
#
# 职责：
# - 读取和管理 mock_data/pois.json（Demo阶段）
# - 提供POI查询、筛选的底层方法
# - 供 tools.py 中的 search_poi 调用
# ================================================================

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ================================================================
# 【落地版】调用美团POI真实接口
# 实际部署时取消注释，注释掉下方Mock版本
# ================================================================
# import httpx
#
# MEITUAN_POI_API = "https://api.meituan.com/v1/poi/search"  # 接入美团内部POI服务（需申请权限）
# MEITUAN_API_KEY = os.getenv("MEITUAN_API_KEY")
#
# async def fetch_pois_from_api(city: str, category: str, budget_max: int) -> list:
#     """调用美团POI接口获取真实数据"""
#     async with httpx.AsyncClient() as client:
#         response = await client.get(
#             MEITUAN_POI_API,
#             params={
#                 "city": city,
#                 "category": category,
#                 "price_max": budget_max,
#                 "page_size": 20,
#             },
#             headers={"Authorization": f"Bearer {MEITUAN_API_KEY}"}
#         )
#         data = response.json()
#         return data["pois"]


# ================================================================
# 【Demo版】读取本地Mock数据
# ================================================================

def load_pois() -> list:
    """读取pois.json，返回所有POI列表"""
    with open(os.path.join(BASE_DIR, "mock_data/pois.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def filter_by_category(pois: list, category: str) -> list:
    """按类型筛选POI"""
    return [p for p in pois if category in p.get("category", [])]


def filter_by_budget(pois: list, budget_max: int) -> list:
    """按最高费用筛选POI"""
    return [p for p in pois if p.get("cost", 0) <= budget_max]


def filter_by_group(pois: list, suitable_for: str) -> list:
    """按适合人群筛选POI"""
    return [p for p in pois if suitable_for in p.get("suitable_for", [])]


def filter_by_exclude(pois: list, exclude_ids: list) -> list:
    """排除指定POI"""
    return [p for p in pois if p["id"] not in exclude_ids]