# Intern Match 实习岗位抓取与匹配系统

Intern Match 是一个面向实习、New Grad 和早期职业机会的岗位聚合与推荐系统。后端使用 FastAPI 抓取公开岗位数据、解析 Markdown 表格、提取技能、去重入库，并基于用户画像返回可解释的岗位匹配结果。前端提供一个 React + TypeScript + Vite + Tailwind CSS 的 SaaS 风格仪表盘。

## 功能概览

- 岗位抓取：从公开 GitHub Markdown/README 数据源增量抓取岗位。
- 岗位解析：提取公司、岗位、地点、申请链接、岗位类型、season 和技能标签。
- 岗位搜索：支持关键词、地点、岗位类型筛选，并支持分页。
- 岗位详情：查看单个岗位的完整后端数据。
- 匹配推荐：根据技能、目标地点、方向、远程偏好和黑名单关键词生成推荐。
- 数据源状态：查看默认数据源的抓取状态，并手动触发抓取。
- 趋势统计：查看岗位总数、活跃岗位、热门技能、热门地点、来源分布等。
- 申请跟踪：保存岗位、收藏岗位、记录申请状态和备注。
- 前端仪表盘：React Router、TanStack Query、Tailwind CSS、卡片、表格、筛选器、骨架屏、空状态、错误状态和 toast 通知。

## 技术栈

### 后端

- Python 3.11+
- FastAPI
- SQLAlchemy
- Pydantic v2
- SQLite 默认开发数据库，可切换 PostgreSQL
- Alembic 数据库迁移
- APScheduler 可选定时抓取
- pytest 测试

### 前端

- React
- TypeScript
- Vite
- Tailwind CSS
- React Router
- TanStack Query
- shadcn/ui 风格的本地组件封装

## 项目结构

```text
app/
  main.py                 FastAPI 应用与 API 路由
  schemas.py              Pydantic 请求/响应模型
  models.py               SQLAlchemy 数据模型
  core/config.py          配置与环境变量
  db/session.py           数据库连接与 Session
  crawlers/               抓取器
  services/               抓取、解析、匹配、仓储等业务服务

frontend/
  src/lib/api.ts          前端 API client 与 TypeScript 类型
  src/layouts/            应用布局
  src/pages/              Dashboard、Jobs、Match、Sources 页面
  src/components/ui/      本地 UI 组件

ui/
  streamlit_app.py        旧版 Streamlit UI

tests/                    后端测试
alembic/                  数据库迁移
sample_data/              示例数据
```

## 环境变量

复制后端环境变量示例：

```powershell
Copy-Item .env.example .env
```

常用后端变量：

```env
APP_NAME=Intern Match
DATABASE_URL=sqlite:///./intern_match.db
SCHEDULER_ENABLED=false
CRAWL_INTERVAL_HOURS=12
```

复制前端环境变量示例：

```powershell
Copy-Item frontend\.env.example frontend\.env
```

前端通过 `VITE_API_BASE_URL` 指向 FastAPI：

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 本地运行

### 1. 启动后端

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

后端地址：

- API: `http://localhost:8000`
- Swagger 文档: `http://localhost:8000/docs`
- 健康检查: `http://localhost:8000/health`

### 2. 启动 React 前端

```powershell
cd frontend
npm install
npm run dev
```

前端地址：

- `http://localhost:5173`
- 或 `http://127.0.0.1:5173`

如果 PowerShell 阻止 `npm.ps1`，可以使用：

```powershell
npm.cmd install
npm.cmd run dev
```

### 3. 可选：启动旧版 Streamlit UI

```powershell
streamlit run ui/streamlit_app.py
```

默认地址：

- `http://localhost:8501`

## Docker 运行

```powershell
Copy-Item .env.example .env
docker compose up --build
```

默认服务：

- API: `http://localhost:8000`
- Streamlit UI: `http://localhost:8501`
- PostgreSQL: `localhost:5432`

PostgreSQL 示例配置：

```env
DATABASE_URL=postgresql+psycopg2://intern_match:change-me@postgres:5432/intern_match
POSTGRES_PASSWORD=change-me
```

生产环境不要硬编码数据库密码或 API Key，应通过环境变量、密钥管理系统或部署平台注入。

## 数据源

默认数据源定义在 `app/services/sources.py`：

- SimplifyJobs Summer 2026 Tech Internships
- SimplifyJobs New Grad Positions
- speedyapply 2026 SWE College Jobs
- jobright-ai 2026 Internship New Grad

抓取器只读取公开 raw Markdown 内容，不绕过登录、验证码、访问限制或反爬机制。使用时应遵守目标站点的 robots.txt、服务条款和合理频率限制。

## API 概览

### 健康检查

- `GET /health`

返回：

```json
{
  "status": "ok",
  "app": "Intern Match"
}
```

### 岗位

- `GET /jobs?skip=0&limit=50&q=python&location=remote&job_type=internship`
- `GET /jobs/{job_id}`

`GET /jobs` 返回：

```json
{
  "total": 100,
  "items": []
}
```

### 匹配推荐

- `POST /match`

请求示例：

```json
{
  "name": "default",
  "skills": ["Python", "SQL", "FastAPI"],
  "target_locations": ["Remote", "New York"],
  "target_directions": ["backend", "data engineering"],
  "remote_preference": "prefer_remote",
  "blacklist_keywords": ["unpaid"],
  "min_score": 0.35,
  "limit": 20
}
```

返回包含岗位、匹配分数和推荐原因：

```json
{
  "items": [
    {
      "job": {},
      "score": 0.82,
      "reasons": ["匹配 Python"]
    }
  ]
}
```

### 用户画像

- `POST /profile`

用于保存或更新用户画像。

### 岗位跟踪

- `POST /jobs/{job_id}/tracking`
- `GET /tracking?profile_name=default&status=applied&favorites_only=false`
- `DELETE /tracking/{tracking_id}`

支持状态：

- `saved`
- `interested`
- `applied`
- `interview`
- `offer`
- `rejected`
- `archived`

### 数据源与抓取

- `GET /sources`
- `POST /crawl/run?force=true`

### 趋势统计

- `GET /analytics/trends?limit=10`

返回岗位数量、来源分布、岗位类型、热门地点、热门技能和申请状态统计。

## 匹配评分逻辑

当前匹配服务综合以下因素：

```text
score = 技能匹配分 * 0.6
      + 地点匹配分 * 0.15
      + 岗位方向匹配分 * 0.15
      + 新鲜度分 * 0.1
```

匹配结果会按分数降序返回，并附带可解释的推荐原因。

## 前端页面

React 前端目前包含：

- Dashboard：岗位趋势、活跃岗位、热门技能、热门地点、来源分布。
- Jobs：真实连接 `GET /jobs`，支持筛选、分页和 `GET /jobs/{id}` 岗位详情。
- Match：真实连接 `POST /match`，展示推荐结果、分数和原因。
- Sources：真实连接 `GET /sources` 和 `POST /crawl/run`，展示数据源状态并支持手动抓取。
- 顶部状态：真实连接 `GET /health`，展示后端健康状态。

## 开发命令

后端测试：

```powershell
pytest
```

前端构建：

```powershell
cd frontend
npm.cmd run build
```

数据库迁移：

```powershell
alembic upgrade head
```

手动触发抓取：

```powershell
Invoke-RestMethod -Method Post "http://localhost:8000/crawl/run?force=true"
```

## 注意事项

- 默认开发数据库是项目根目录下的 `intern_match.db`。
- 后端启动时会执行 `create_all` 并种子化默认数据源。
- 前端只使用后端真实 API 字段；如果字段为空，会在 UI 中显示兜底文案。
- 本项目适合用于作品集展示、岗位数据聚合原型、推荐算法演示和 FastAPI + React 全栈练习。
