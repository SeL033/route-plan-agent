# ================================================================
# 数据结构定义（契约文件）
#
# 职责：
# - 定义所有模块之间传递的数据结构
# - 所有人import这个文件，不要自己定义dict格式
# - 改字段只改这里，Pydantic会在其他地方报错提示
# ================================================================

from pydantic import BaseModel
from typing import Optional


class PlanRequest(BaseModel):
    """前端 → 后端：用户请求"""
    user_input: str
    user_id: Optional[str] = None
    start_location: Optional[str] = None   # 出发地，如"上海虹桥火车站"


class Location(BaseModel):
    """地理坐标"""
    lat: float
    lng: float


class POI(BaseModel):
    """单个POI数据结构"""
    id: str
    name: str
    category: list[str]
    cost: int
    duration: int
    score: float
    tags: list[str]
    open_time: str
    location: Location


class UGCInfo(BaseModel):
    """POI的用户评价摘要"""
    poi_id: str
    poi_name: str
    crowd_level: str
    avg_wait_minutes: int
    best_time: Optional[str] = None
    avoid_time: Optional[str] = None
    sample_reviews: list[str] = []


class Stop(BaseModel):
    """路线中的单个停留点"""
    poi_id: str
    name: str
    arrive_time: str
    duration: int
    leave_time: str
    cost: int
    reason: str
    location: Location             # 真实坐标，供地图使用


class Route(BaseModel):
    """单条路线方案"""
    style: str
    description: str
    total_cost: int
    total_duration_minutes: int
    start_time: str
    end_time: str
    stops: list[Stop]


class PlanResponse(BaseModel):
    """后端 → 前端：最终返回结构（所有人对齐这个）"""
    status: str
    user_input: str
    routes: list[Route]
    error_msg: Optional[str] = None


class AgentContext(BaseModel):
    """Agent内部流转的上下文（不暴露给前端）"""
    user_input: str
    city: Optional[str] = None
    duration: int = 1
    budget: int = 500
    group: list[str] = []
    avoid: list[str] = []
    prefer: list[str] = []
    start_time: str = "09:00"
    start_location: Optional[str] = None
    candidate_pois: list[POI] = []
    routes: list[Route] = []
    