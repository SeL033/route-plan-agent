# ================================================================
# UGC评价数据服务
# 负责人：AI同学
#
# 职责：
# - 读取和管理 mock_data/ugc_reviews.json
# - 提供评价查询的底层方法
# - 供 tools.py 中的 get_ugc_info 调用
# ================================================================

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ================================================================
# 【落地版】调用大众点评UGC真实接口
# 实际部署时取消注释，注释掉下方Mock版本
# ================================================================
# import httpx
#
# DIANPING_REVIEW_API = "https://api.dianping.com/v1/reviews"
# DIANPING_API_KEY = "YOUR_API_KEY"
#
# async def fetch_reviews_from_api(poi_id: str) -> dict:
#     """调用大众点评接口获取真实UGC评价"""
#     async with httpx.AsyncClient() as client:
#         response = await client.get(
#             DIANPING_REVIEW_API,
#             params={
#                 "poi_id": poi_id,
#                 "page_size": 20,
#                 "sort": "helpful",      # 按有用数排序，质量更高
#             },
#             headers={"Authorization": f"Bearer {DIANPING_API_KEY}"}
#         )
#         data = response.json()
#         return data["reviews"]


# ================================================================
# 【Demo版】读取本地Mock数据
# ================================================================

def load_reviews() -> dict:
    """读取ugc_reviews.json，返回所有评价数据"""
    with open(os.path.join(BASE_DIR, "mock_data/ugc_reviews.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def get_reviews_by_poi(poi_id: str) -> dict:
    """根据POI id获取评价摘要"""
    # TODO
    pass