# KPL Stats - 项目上下文

## 项目概述

**KPL Stats** 是一个用于展示电竞选手"KSG.无言"职业生涯数据的 Web 应用（KPL - 王者荣耀职业联赛）。系统采用代理架构从第三方 API 获取数据，并使用本地文件缓存来减少 API 调用次数。

### 架构

- **前端**: Vue 3 + Vite + Axios（运行在端口 3000）
- **后端**: FastAPI + Uvicorn + HTTPX（运行在端口 8000）
- **缓存**: 本地 JSON 文件缓存（`backend/cache.json`）
- **无数据库**: 使用文件缓存替代传统数据库

### 数据流

```
前端 (Vue 3) → 后端 (FastAPI) → 缓存检查 → 第三方 API → JSON 响应 → Vue 渲染
```

---

## 项目结构

```
kpl_stats/
├── backend/
│   ├── main.py              # FastAPI 应用，包含缓存逻辑
│   ├── requirements.txt     # Python 依赖
│   ├── .env                 # 环境变量（API 地址、缓存 TTL）
│   └── cache.json           # 自动生成的缓存文件
├── frontend/
│   ├── src/
│   │   ├── App.vue          # Vue 主组件，展示选手数据 UI
│   │   └── api/
│   │       └── stats.js     # API 客户端封装
│   └── .env.development     # 前端环境配置
├── doc/
│   └── project.md           # 详细项目文档（中文）
├── test/
│   └── ...                  # 测试数据文件（JSON 样本、测试脚本）
└── .vscode/
    └── settings.json        # VS Code 工作区设置
```

---

## 构建与运行

### 前置要求

- Python 3.8+（推荐使用 Conda 管理环境）
- Node.js 16+
- npm 或 yarn

### 后端设置

```bash
cd backend

# 使用 Conda 安装依赖（如已配置 conda 环境）
conda activate your-env
pip install -r requirements.txt

# 配置环境变量
# 编辑 .env 填入第三方 API 地址

# 启动服务
uvicorn main:app --reload --port 8000
```

### 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 访问地址

- **前端**: http://localhost:3000
- **后端 API 文档**: http://localhost:8000/docs

---

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/player/career` | GET | 获取选手生涯数据（支持缓存） |
| `/api/admin/refresh` | POST | 手动刷新缓存 |
| `/api/admin/cache_info` | GET | 查看缓存信息 |
| `/api/admin/cache` | DELETE | 清除缓存 |
| `/api/health` | GET | 健康检查 |

### 查询参数

- `GET /api/player/career?force_refresh=true` - 强制从第三方 API 刷新
- `POST /api/admin/refresh?force=true` - 强制刷新缓存

---

## 环境变量配置

### 后端（`.env`）

```env
THIRD_PARTY_API_URL=https://your-api.com/player/career
API_KEY=your_api_key
CACHE_TTL_HOURS=24
```

### 前端（`.env.development`）

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

---

## 开发规范

### 代码风格

- **Python**: 遵循 Python 标准规范（PEP 8）
- **Vue**: 使用组合式 API 和 `<script setup>` 语法
- **CSS**: Vue 组件使用 scoped 样式

### 测试实践

- 测试数据样本位于 `test/` 目录
- 可通过 API 文档手动测试：http://localhost:8000/docs

### 核心模式

1. **缓存策略**: 默认 24 小时缓存 TTL，支持手动刷新
2. **降级行为**: 第三方 API 不可用时返回过期缓存
3. **CORS**: 后端允许所有来源访问（开发环境）

---

## 关键文件参考

| 文件 | 用途 |
|------|------|
| `backend/main.py` | FastAPI 服务器，包含缓存逻辑 |
| `backend/requirements.txt` | Python 依赖列表 |
| `backend/.env` | 后端配置 |
| `frontend/src/App.vue` | 主 UI 组件 |
| `frontend/src/api/stats.js` | API 客户端封装 |
| `doc/project.md` | 详细文档（中文） |

---

## 常用操作

### 强制刷新数据

```bash
curl -X POST "http://localhost:8000/api/admin/refresh?force=true"
```

### 查看缓存状态

```bash
curl "http://localhost:8000/api/admin/cache_info"
```

### 清除缓存

```bash
curl -X DELETE "http://localhost:8000/api/admin/cache"
```

---

## 注意事项

- 项目使用 **Conda** 作为默认 Python 环境管理器（见 `.vscode/settings.json`）
- 缓存文件位于 `backend/cache.json`（自动生成）
- 运行前必须在 `backend/.env` 中配置第三方 API 地址

## Qwen Added Memories
- 用户手动修正了 Home.vue 中的数据显示字段，以后修改代码时不要改动用户已修正的 JS 字段映射
