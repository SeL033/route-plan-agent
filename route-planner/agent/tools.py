# ================================================================
# Agent工具函数
# 负责人：AI同学
#
# 职责：
# - 封装所有LLM可以调用的工具
# - 每个工具对应一个函数，负责查询数据并返回结构化结果
# - TOOLS_SCHEMA 告诉LLM有哪些工具可以用
# - TOOLS_MAP 供Agent执行实际函数调用
#
# 工具列表：
# - search_poi: 按条件搜索POI
# - get_ugc_info: 获取POI的排队和口碑信息
# - calculate_route_time: 计算路线时间安排
# - check_budget: 校验POI组合是否超预算
# ================================================================


def search_poi(
    city: str,
    category: str = None,
    budget_max: int = None,
    suitable_for: str = None,
    exclude_ids: list = None
) -> list:
    """
    根据条件搜索POI列表。
    返回：符合条件的POI列表，按评分降序排列，最多8条
    """
    # TODO: 读取 data/pois.json，按参数筛选
    pass


def get_ugc_info(poi_id: str) -> dict:
    """
    获取某个POI的用户评价摘要。
    返回：crowd_level / avg_wait_minutes / best_time / avoid_time / sample_reviews
    """
    # TODO: 读取 data/ugc_reviews.json，返回对应POI的评价数据
    pass


def calculate_route_time(poi_ids: list, start_time: str = "09:00") -> dict:
    """
    根据POI顺序计算路线的时间安排。
    返回：schedule（每个POI的到达/离开时间） / total_duration_minutes / end_time
    """
    # TODO: 根据每个POI的duration和相邻POI的距离估算交通时间
    pass


def check_budget(poi_ids: list, total_budget: int) -> dict:
    """
    检查选定POI组合的总费用是否超出预算。
    返回：total_cost / over_budget / over_amount / breakdown
    """
    # TODO: 累加各POI门票费用，与total_budget比较
    pass


# LLM可调用的工具描述（function calling schema）
TOOLS_SCHEMA = [
    # TODO: 按OpenAI function calling格式描述每个工具
]

# 工具名称 → 函数映射（Agent执行tool_call时用）
TOOLS_MAP = {
    "search_poi": search_poi,
    "get_ugc_info": get_ugc_info,
    "calculate_route_time": calculate_route_time,
    "check_budget": check_budget,
}
