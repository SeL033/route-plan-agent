# ================================================================
# Agent核心
# 负责人：AI同学
#
# 职责：
# - 接收用户原始输入
# - 注册工具（来自 tools.py）
# - 调用 DeepSeek function calling，让LLM自主决定调用哪些工具
# - 收集工具调用结果，驱动LLM持续推理直到生成完整路线
# - 最终返回 PlanResponse.model_dump()
#
# 输入：user_input: str
# 输出：PlanResponse.model_dump() -> dict
# ================================================================

from models.schemas import PlanResponse


async def run(user_input: str) -> PlanResponse:
    # TODO: 实现Agent主循环
    # 1. 初始化DeepSeek client
    # 2. 注册 TOOLS_SCHEMA（来自tools.py）
    # 3. 启动function calling循环
    # 4. 每次LLM返回tool_call，用TOOLS_MAP执行对应函数
    # 5. 把结果塞回messages继续推理
    # 6. 直到LLM输出最终路线，构建PlanResponse返回
    pass
