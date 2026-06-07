# AI Route Planner

本项目是一个本地智能路线规划 Demo。用户输入游玩目标后，后端结合本地 POI 和 UGC mock 数据生成路线，前端展示路线方案和地图点位。

## 当前能力

- FastAPI 后端接口：`POST /api/plan`
- React + Vite 前端页面
- 本地 mock POI/UGC 数据
- 用户历史偏好画像与美食 POI 推荐
- Citation-style Explainability：每个推荐点展示评论、关键词、榜单、相似地区用户偏好、预约/外卖等证据链
- Last-50-Meter Guidance：为隐藏店、商场店、地铁口附近店提供最后 50 米到店提示
- Takeout Quality Decay：判断餐厅更适合到店、预约、外卖或打包，并提示口感衰减风险
- 设置 `USE_LLM_API=true` 且有 `LONGCAT_API_KEY` 时调用 LongCat/OpenAI 兼容接口生成路线
- 有 `AMAP_KEY` 时，后端会调用高德 Place API 补充外部 POI、坐标、地址和营业信息
- `retrieve_external_context` 工具会把外部 POI 样例与本地 RAG 常识一起提供给大模型，用于证据链、最后 50 米指引和外卖口感判断
- 外部 API 设置短超时和内存缓存，外部请求失败时自动回退本地 mock 数据，保证响应速度
- 没有 API key 时自动使用本地 demo 规划逻辑，保证项目可以本地跑通
- 输出 3 类路线：平衡推荐、省钱少排队、经典打卡

## 后端启动

```bash
cd route-planner
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

如果暂时没有 `LONGCAT_API_KEY`，可以留空并设置 `USE_LLM_API=false` 使用本地规划。`USE_LLM_API=true` 时必须调用 LongCat；系统会先做分层外部搜索：无反馈时只取少量POI快速生成初步方案，有反馈后再加入餐饮/RAG/偏好深搜。LongCat精修会在一分钟内返回结果或明确超时提示。

如果配置了 `AMAP_KEY`，系统会优先尝试外部 POI 检索；如果外部地图接口超时或不可用，会快速回退到本地 mock，不影响主流程。

## 前端启动

```bash
cd route-planner/frontend
npm install
npm run dev
```

如果遇到 Rollup 原生依赖报错，通常是因为 `node_modules` 来自其他系统。删除 `frontend/node_modules` 后重新执行 `npm install` 即可。

默认访问：

```text
http://localhost:5173
```

## 示例请求

```bash
curl -X POST http://127.0.0.1:8000/api/plan \
  -H "Content-Type: application/json" \
  -d '{"user_input":"我和朋友在上海玩两天，预算500，想吃本地美食，不想排队","start_location":"上海人民广场","user_id":"demo_user"}'
```

可切换的本地用户画像：

- `demo_user`：华东用户，偏清淡、甜口、咖啡，喜欢文化、室内、免费和美食点
- `user_family`：亲子/家庭用户，偏清淡、早茶、甜品，重视可预约、室内和少排队
- `user_spicy`：川渝重口味用户，偏辣味、火锅、夜景和网红点

## 目录结构

```text
route-planner/
  main.py                 FastAPI 入口
  api/routes.py           HTTP API
  agent/planner_agent.py  AI Agent 与本地兜底规划
  agent/tools.py          POI/UGC/时间/预算工具
  core/                   数据读取与筛选
  models/schemas.py       Pydantic 数据结构
  mock_data/              本地 POI 和 UGC 数据
  frontend/               React 前端
```
