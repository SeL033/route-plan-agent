# 逛逛 · AI 路线规划系统

一句话输入出行意图，后端结合本地 POI、UGC 评价和外部地图数据，自动生成 3 条可执行路线，前端展示路线方案与地图标注。

---

## 目录

- [功能概览](#功能概览)
- [系统架构](#系统架构)
- [目录结构](#目录结构)
- [快速开始](#快速开始)
  - [后端启动](#后端启动)
  - [前端启动](#前端启动)
- [环境变量说明](#环境变量说明)
- [API 接口](#api-接口)
- [示例请求](#示例请求)
- [用户画像](#用户画像)
- [数据说明](#数据说明)
- [部署](#部署)
- [计划功能（受 API 费用限制暂未实现）](#计划功能受-api-费用限制暂未实现)
- [落地版扩展点](#落地版扩展点)

---

## 功能概览

| 功能 | 说明 |
|------|------|
| 多风格路线 | 每次生成 3 条路线：平衡推荐、省钱少排队、经典打卡 |
| 分层规划 | 先快速返回初步方案（`/api/plan/initial`），再异步触发大模型精修（`/api/plan`） |
| LLM 集成 | `USE_LLM_API=true` 时调用 LongCat（OpenAI 兼容接口）生成路线；无 Key 时自动使用本地规划兜底 |
| 外部 POI | 配置 `AMAP_KEY` 后接入高德地图 Place API 补充坐标、地址和营业信息；超时自动回退本地 mock |
| Citation 证据链 | 每个推荐点附带引用式证据：UGC 评价数、高频关键词、时间费用成本、相似用户偏好、榜单/品牌 |
| Last-50-Meter Guidance | 为隐藏店、商场店、地铁口附近店提供最后 50 米到店提示 |
| 外卖口感衰减判断 | 根据 RAG 常识库判断餐厅适合堂食、预约、外卖或自取，并提示口感风险 |
| 用户自进化画像 | 记录搜索意图与点赞/踩反馈，动态调整偏好标签，下次规划自动参考 |
| Redis 缓存 | 可选，相同输入直接返回缓存结果，不重复调用 LLM |
| 多日游支持 | 自动解析"两日游"/"3天"，按 day 字段拆分路线 |
| 多城市支持 | 支持上海、北京、成都、广州、悉尼、珀斯、东京、首尔等城市 |

---

## 系统架构

```
用户输入
    │
    ▼
前端 (React + Vite)
    │   POST /api/plan/initial  → 快速草案（秒级响应）
    │   POST /api/plan          → 大模型精修（异步，最多 45s）
    ▼
FastAPI 后端
    ├── api/routes.py           HTTP 路由
    │
    ├── agent/planner_agent.py  规划核心
    │       ├── run()           大模型路径（LongCat）
    │       ├── run_initial()   快速路径（外部搜索 + 本地组装）
    │       └── _run_local_demo()  无 Key 兜底
    │
    ├── agent/tools.py          LLM 可调用工具
    │       ├── search_poi      搜索景点/美食
    │       ├── get_ugc_info    获取评价/排队信息
    │       ├── calculate_route_time  时间安排
    │       ├── check_budget    预算校验
    │       └── retrieve_external_context  外部 POI + RAG 常识
    │
    ├── core/
    │       ├── poi_service.py      读取本地 POI mock 数据
    │       ├── ugc_service.py      读取本地 UGC mock 数据
    │       ├── external_knowledge.py  高德地图 API + RAG 常识库
    │       └── profile_evolution.py   用户自进化画像
    │
    ├── cache_service.py        Redis 缓存（可选）
    ├── db_service.py           MySQL 数据库（落地版扩展点）
    └── models/schemas.py       Pydantic 数据结构定义
```

---

## 目录结构

```
route-planner/
├── main.py                     FastAPI 入口，注册路由与 CORS
├── requirements.txt            Python 依赖
├── Procfile                    Heroku/Render 启动命令
├── render.yaml                 Render 部署配置
├── .env.example                环境变量模板
│
├── api/
│   └── routes.py               HTTP 路由：/api/plan、/api/plan/initial、/api/feedback
│
├── agent/
│   ├── planner_agent.py        规划核心（LLM 路径 + 本地兜底）
│   └── tools.py                LLM 工具函数 + TOOLS_SCHEMA + TOOLS_MAP
│
├── core/
│   ├── poi_service.py          POI 数据服务（Demo: 读 mock_data/pois.json）
│   ├── ugc_service.py          UGC 评价服务（Demo: 读 mock_data/ugc_reviews.json）
│   ├── external_knowledge.py   高德地图 Place API + 外卖口感 RAG 常识库
│   └── profile_evolution.py    用户画像自进化（搜索意图 + 反馈加权）
│
├── models/
│   └── schemas.py              Pydantic 数据结构：PlanRequest/Response、Route、Stop 等
│
├── cache_service.py            Redis 缓存服务（ENABLE_REDIS_CACHE=true 时生效）
├── db_service.py               MySQL 服务（含建表 SQL，落地版扩展点）
│
├── mock_data/
│   ├── pois.json               模拟景点 POI 数据
│   ├── food_pois.json          模拟美食 POI 数据（含外卖质量、预约信息）
│   ├── ugc_reviews.json        模拟 UGC 用户评价（拥挤度、排队时间、评论）
│   └── user_profiles.json      预设用户画像（demo_user、user_family、user_spicy）
│
└── frontend/
    ├── index.html
    ├── vite.config.js          开发代理：/api → 后端服务
    ├── package.json
    └── src/
        ├── main.jsx
        ├── App.jsx             应用入口，管理双阶段请求和状态
        ├── index.css           全局样式
        ├── cityContent.js      各城市特色美食内容
        └── components/
            ├── SearchPanel.jsx     搜索输入、用户画像选择、出发地输入
            ├── RoutePanel.jsx      路线展示、证据链、反馈按钮
            ├── MapView.jsx         地图视图（高德/自定义渲染）
            ├── LoadingScreen.jsx   规划中加载动画
            └── OpeningAnimation.jsx  首屏开场动画
```

---

## 快速开始

### 后端启动

```bash
cd route-planner
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # 按需填写 KEY
uvicorn main:app --reload --port 8011
```

**最小运行**（无需任何 API Key）：保持 `.env` 中 `USE_LLM_API=false`，系统会用本地 mock 数据规划路线。

### 前端启动

```bash
cd route-planner/frontend
npm install
npm run dev
```

访问：`http://localhost:5173`

> 如遇 Rollup 原生依赖报错（通常是 `node_modules` 来自其他系统），删除 `frontend/node_modules` 后重新执行 `npm install`。

---

## 环境变量说明

### 后端（`route-planner/.env`）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `USE_LLM_API` | `false` | 是否调用 LongCat 大模型。`false` 时使用本地规划兜底 |
| `LONGCAT_API_KEY` | — | LongCat API Key（OpenAI 兼容接口）。`USE_LLM_API=true` 时必填 |
| `LLM_TIMEOUT` | `45` | LLM 请求超时秒数 |
| `LLM_MAX_TOOL_ROUNDS` | `1` | Agent 工具调用最大轮次 |
| `AMAP_KEY` | — | 高德地图 Web 服务 Key。填写后启用外部 POI 检索 |
| `EXTERNAL_API_TIMEOUT` | `0.6` | 高德 API 超时秒数（超时自动回退本地 mock） |
| `ENABLE_REDIS_CACHE` | `false` | 是否启用 Redis 缓存 |
| `REDIS_HOST` | `localhost` | Redis 主机 |
| `REDIS_PORT` | `6379` | Redis 端口 |

### 前端（`route-planner/frontend/.env`）

| 变量 | 说明 |
|------|------|
| `VITE_AMAP_KEY` | 高德地图 JS API Key（前端地图渲染使用） |

---

## API 接口

### `POST /api/plan`

完整规划请求，调用 LLM 或本地兜底，返回 3 条路线。

**请求体**
```json
{
  "user_input": "我和朋友在上海玩两天，预算500，想吃本地美食，不想排队",
  "start_location": "上海人民广场",
  "user_id": "demo_user"
}
```

**响应**
```json
{
  "status": "success",
  "user_input": "...",
  "routes": [
    {
      "style": "平衡推荐",
      "description": "...",
      "total_cost": 220,
      "total_duration_minutes": 480,
      "start_time": "09:00",
      "end_time": "17:00",
      "stops": [
        {
          "day": 1,
          "poi_id": "sh001",
          "name": "外滩",
          "arrive_time": "09:00",
          "duration": 90,
          "leave_time": "10:30",
          "cost": 0,
          "reason": "...",
          "poi_type": "attraction",
          "evidence": ["UGC：约120条评价...", "高频关键词：夜景、免费", "..."],
          "last_50m_guidance": "从地铁出口沿南京东路步行到江边...",
          "dining_advice": null,
          "location": { "lat": 31.2397, "lng": 121.4901 }
        }
      ]
    }
  ]
}
```

### `POST /api/plan/initial`

快速初步规划（秒级响应），基于外部搜索结果组装草案。前端先展示此结果，再异步触发 `/api/plan` 精修。

请求体与 `/api/plan` 相同，响应中 `status` 为 `"partial"`。

### `POST /api/feedback`

提交用户对某条路线的反馈，更新自进化用户画像。

```json
{
  "user_id": "demo_user",
  "route_style": "平衡推荐",
  "liked": true,
  "stops": [...],
  "comment": "路线很顺，美食推荐不错"
}
```

---

## 用户画像

`user_id` 对应 `mock_data/user_profiles.json` 中的预设画像，也会被 `profile_evolution.py` 根据搜索和反馈动态更新。

| user_id | 特征 |
|---------|------|
| `demo_user` | 华东用户，偏清淡、甜口、咖啡，喜欢文化、室内、免费和美食点 |
| `user_family` | 亲子/家庭用户，偏清淡、早茶、甜品，重视可预约、室内和少排队 |
| `user_spicy` | 川渝重口味用户，偏辣味、火锅、夜景和网红点 |

**自进化逻辑**：每次搜索和反馈后，系统会提取意图关键词，动态调整 `prefer_weights`、`taste_weights`、`avoid_weights`，并生成 `history_summary` 摘要，供下次规划参考。状态持久化在 `mock_data/user_state.json`。

---

## 数据说明

`mock_data/` 下的文件仅供开发和 Demo 演示。

| 文件 | 说明 |
|------|------|
| `pois.json` | 模拟景点 POI，含坐标、评分、标签、适合人群、停留时长等 |
| `food_pois.json` | 模拟美食 POI，额外含外卖质量（`takeout_quality`）、是否可预约、口味标签 |
| `ugc_reviews.json` | 模拟 UGC 评价，含拥挤度、平均排队时间、最佳游览时段 |
| `user_profiles.json` | 预设用户画像（静态基础，运行时与 `user_state.json` 合并） |

落地时可替换为：
- `poi_service.py` → 美团 POI 内部接口（文件内已有注释模板）
- `ugc_service.py` → 大众点评 UGC 接口（文件内已有注释模板）
- `db_service.py` → MySQL 存储用户偏好与历史记录（建表 SQL 已在文件末尾）

---

## 部署

项目已配置 `render.yaml`，支持一键部署到 [Render](https://render.com)：

```bash
# render.yaml 中已定义：
# - Python Web 服务
# - uvicorn 启动命令
# - 所有环境变量（LONGCAT_API_KEY、AMAP_KEY 等需手动在 Render 面板填写）
```

前端开发模式下，`vite.config.js` 将 `/api` 代理到 `https://route-plan-agent.onrender.com`，可修改为本地后端地址。

---

## 计划功能（受 API 费用限制暂未实现）

以下功能已完成设计，因 API 额度/费用问题未能在 Demo 阶段集成，保留此处供后续开发参考。

---

### 1. 真实路径绘制 + 多交通方式导航

**期望效果**：地图上按实际道路绘制路线折线，而非直线连点；支持步行、骑行、公交、驾车四种模式，显示每段预计耗时和换乘提示。

**所需 API**：
- 国内：高德路径规划 API（`/v3/direction/walking`、`/v3/direction/transit/integrated` 等）
- 海外：Google Routes API 或 Directions API

**实现思路**：

路线规划完成后，对相邻两个 stop 的坐标调用路径规划接口，拿到 `polyline` 编码的路段坐标串，在 `MapView.jsx` 中解码后叠加到地图上。`Stop` schema 可增加 `transit_to_next` 字段存储交通建议。

```python
# 后端新增工具（agent/tools.py）
def get_directions(origin: dict, destination: dict, mode: str = "walking") -> dict:
    """
    调用高德/Google 路径规划，返回 polyline 和分段时间。
    mode: walking / transit / driving / cycling
    """
    # 高德示例：
    # GET https://restapi.amap.com/v3/direction/walking
    #   ?origin=121.49,31.23&destination=121.50,31.24&key=AMAP_KEY
    ...
```

```jsx
// 前端 MapView.jsx 中解码 polyline 并绘制
// 高德：AMap.PolylineEditor / map.add(polyline)
// Google：google.maps.Polyline + google.maps.geometry.encoding.decodePath
```

**需要的 Key**：`AMAP_KEY`（路径规划权限）或 Google Maps Platform 账号（Routes API 已启用）

---

### 2. 景点图片实时搜索展示

**期望效果**：每个 stop 卡片上展示 2–3 张该景点/餐厅的真实图片，点击可放大预览。

**所需 API**（任选其一）：

| 方案 | 接口 | 费用 |
|------|------|------|
| 高德地图照片 | Place API `extensions=all` 返回的 `photos[].url` | 含在现有 `AMAP_KEY` 权限内，**已部分实现**，见 `external_knowledge.py` 中 `photo_url` 字段 |
| Google Places Photos | `Place Details → photos[].photo_reference → Place Photo API` | 按请求计费 |
| Unsplash | `GET /search/photos?query=外滩+上海` | 免费套餐 50 req/hour |
| Pexels | `GET /v1/search?query=...` | 免费，200 req/hour |

**实现思路**：

高德路径已经在 `_normalize_amap_poi()` 里解析了 `photo_url`，目前只存在 POI 数据里，前端 `RoutePanel.jsx` 的 stop 卡片里尚未渲染。最小改动只需前端读取 `stop.photo_url`（需后端把该字段透传到 `Stop` schema）。

海外景点可对接 Unsplash/Pexels，用景点名称做关键词搜索，成本可控。

```python
# models/schemas.py 中 Stop 增加字段
class Stop(BaseModel):
    ...
    photo_urls: list[str] = []   # 新增
```

```jsx
// RoutePanel.jsx stop 卡片中渲染
{stop.photo_urls?.length > 0 && (
  <div className="stop-photos">
    {stop.photo_urls.slice(0, 2).map(url => <img key={url} src={url} />)}
  </div>
)}
```

**需要的 Key**：`UNSPLASH_ACCESS_KEY` 或 `PEXELS_API_KEY`（海外景点）；国内景点已有高德图片，只差前端渲染。

---

### 3. 景点附近美食在线搜索

**期望效果**：在每个景点 stop 下方显示"附近推荐美食"入口，点击后异步拉取该坐标 500m 内评分最高的 3–5 家餐厅，直接插入当日路线或供用户手动添加。

**所需 API**：
- 国内：高德 Place API 周边搜索（`/v3/place/around`）
- 海外：Google Places Nearby Search API

**实现思路**：

新增一个轻量接口，接受 `poi_id` 或坐标，返回附近美食列表：

```python
# api/routes.py 新增
@router.get("/api/nearby_food")
async def nearby_food(lat: float, lng: float, radius: int = 500) -> list:
    """
    根据坐标搜索附近美食 POI。
    国内调高德 /v3/place/around，海外调 Google Places Nearby Search。
    """
    ...
```

```python
# core/external_knowledge.py 新增
def fetch_nearby_food(lat: float, lng: float, radius: int = 500, city: str = "") -> list[dict]:
    params = {
        "key": AMAP_KEY,
        "location": f"{lng},{lat}",
        "radius": radius,
        "types": "050000",   # 高德餐饮大类 code
        "sortrule": "rating",
        "offset": "5",
    }
    # GET https://restapi.amap.com/v3/place/around
    ...
```

前端在 `RoutePanel.jsx` 的每个 stop 底部加"附近美食"按钮，点击后调用 `/api/nearby_food?lat=...&lng=...`，结果渲染为可添加的小卡片。

**需要的 Key**：`AMAP_KEY`（周边搜索权限）或 Google Places API Key

---

### 4. 海外地点 Google 地图渲染

**期望效果**：当用户输入悉尼、珀斯、东京、首尔、新加坡等海外城市时，地图底图自动切换为 Google Maps，支持街景、卫星图和路线绘制；国内城市继续使用高德地图。

**原因**：高德地图海外覆盖质量有限，POI 数据和底图精度明显弱于 Google Maps；且国内坐标系（GCJ-02）与国际坐标系（WGS-84）存在偏移，直接混用会导致标注错位。

**所需 API**：Google Maps JavaScript API（需启用 Maps JS API + Places API）

**实现思路**：

`App.jsx` 中已有 `detectIsForeign()` 函数识别海外城市，目前只用于前端 UI 判断，可以直接扩展为地图实例切换逻辑：

```jsx
// frontend/src/components/MapView.jsx
// 当前：统一用高德地图
// 改造后：根据 isForeign 动态加载不同地图 SDK

useEffect(() => {
  if (isForeign) {
    // 动态注入 Google Maps JS SDK
    loadGoogleMapsScript(import.meta.env.VITE_GOOGLE_MAPS_KEY).then(() => {
      initGoogleMap(containerRef.current, stops)
    })
  } else {
    initAmapMap(containerRef.current, stops)  // 现有逻辑
  }
}, [isForeign, stops])
```

坐标系注意事项：
- 高德 Place API 返回的坐标是 **GCJ-02**（火星坐标系），只能用于高德地图
- 海外 POI 坐标应保持 **WGS-84**，直接传给 Google Maps
- `_normalize_amap_poi()` 中海外城市的坐标需确认来源，避免错位

```python
# .env.example 新增
GOOGLE_MAPS_KEY=        # 后端 Directions/Places API 使用
```

```
# frontend/.env.example 新增
VITE_GOOGLE_MAPS_KEY=   # 前端地图渲染使用
```

**需要的 Key**：Google Maps Platform 账号，启用 Maps JavaScript API 和（可选）Places API、Routes API

---

以下模块已预留落地接口，代码中有注释说明：

| 模块 | 当前状态 | 落地方案 |
|------|----------|---------|
| `core/poi_service.py` | 读本地 `pois.json` | 接入美团 POI 内部 API |
| `core/ugc_service.py` | 读本地 `ugc_reviews.json` | 接入大众点评 UGC API |
| `db_service.py` | 接口已定义，函数体为 TODO | 补充 MySQL 实现，用于用户偏好和历史记录持久化 |
| `cache_service.py` | Redis 可选，默认关闭 | 生产环境设 `ENABLE_REDIS_CACHE=true` |
| 外部 POI | 高德地图（需 `AMAP_KEY`） | 可扩展接入其他地图服务 |
| LLM | LongCat（OpenAI 兼容） | 修改 `planner_agent.py` 中的 `base_url` 和 `MODEL` 即可切换 |