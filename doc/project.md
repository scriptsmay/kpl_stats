# 《KPL 无言选手生涯数据》项目文档

## 一、项目概述

### 1.1 项目简介

为电竞选手"KSG.无言"搭建生涯数据展示页面，通过代理第三方 API 获取数据，前端使用 Vue 进行纯 JSON 渲染。

### 1.2 技术栈

| 层级     | 技术          | 版本   | 用途           |
| -------- | ------------- | ------ | -------------- |
| **前端** | Vue 3         | 3.4+   | 数据绑定与渲染 |
|          | Vue Router    | 4.x    | 路由管理       |
|          | Vite          | 5.0+   | 构建工具       |
|          | Axios         | 1.6+   | HTTP 请求       |
|          | 原生 CSS      | -      | 页面样式       |
| **后端** | FastAPI       | 0.110+ | API 代理服务    |
|          | Uvicorn       | 0.28+  | ASGI 服务器     |
|          | HTTPX         | 0.27+  | 异步 HTTP 客户端 |
|          | Python-dotenv | 1.0+   | 环境变量管理   |

---

## 二、系统架构

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (Vue 3)                          │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  首页 │ 战队统计 │ 赛季统计 │ 英雄统计 │ 比赛记录 │ 管理面板 │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP / JSON
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   后端代理 (FastAPI)                        │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  GET /api/player/career    - 获取数据（支持缓存）    │  │
│  │  POST /api/admin/refresh   - 手动刷新缓存           │  │
│  │  GET /api/admin/cache_info - 查看缓存信息           │  │
│  │  DELETE /api/admin/cache   - 清除缓存               │  │
│  │  GET /api/health           - 健康检查               │  │
│  └─────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              本地文件缓存 (cache.json)              │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP / JSON
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    第三方数据 API                            │
│                  (选手生涯数据接口)                          │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据流程

```
1. 前端请求数据
        ↓
2. 后端检查本地缓存
   ├── 缓存有效 → 直接返回
   └── 缓存无效 → 请求第三方 API
        ↓
3. 第三方 API 返回数据
        ↓
4. 保存到本地缓存
        ↓
5. 返回 JSON 给前端
        ↓
6. Vue 渲染页面
```

---

## 三、项目结构

```
kpl-player-stats/
├── frontend/                 # 前端项目
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js          # 入口文件
│       ├── App.vue          # 主页面
│       ├── router/
│       │   └── index.js     # 路由配置
│       ├── api/
│       │   └── stats.js     # API 请求封装
│       ├── components/
│       │   ├── Home.vue         # 首页组件
│       │   ├── AdminPanel.vue   # 管理面板组件
│       │   ├── MatchRecords.vue # 比赛记录页面
│       │   └── BackToTop.vue    # 回到顶部组件
│       └── style/
│           └── main.css     # 样式文件
├── backend/                  # 后端项目
│   ├── main.py              # FastAPI 主程序
│   ├── requirements.txt     # Python 依赖
│   ├── .env                 # 环境变量
│   ├── cache.json           # 缓存文件（自动生成）
│   └── .gitignore
└── README.md
```

---

## 四、路由配置

前端使用 Vue Router 进行路由管理，当前配置的路由如下：

| 路由      | 组件名称         | 说明           |
| --------- | ---------------- | -------------- |
| `/`       | Home.vue         | 首页           |
| `/admin`  | AdminPanel.vue   | 数据管理面板   |
| `/records`| MatchRecords.vue | 比赛记录页面   |

路由配置文件位于 `frontend/src/router/index.js`。

---

## 五、API 接口文档

### 5.1 获取选手数据

```
GET /api/player/career
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| force_refresh | boolean | 否 | 是否强制刷新（默认 false） |

**响应示例**：

```json
{
  "code": 200,
  "message": "数据来自缓存",
  "data": {
    "player_info": {...},
    "career_summary": {...},
    "hero_stats": [...],
    "season_stats": [...],
    "team_stats": [...],
    "match_details": [...]
  },
  "from_cache": true,
  "cache_time": "2026-03-24T10:30:00"
}
```

### 5.2 手动刷新缓存

```
POST /api/admin/refresh
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| force | boolean | 否 | 是否强制刷新（默认 true） |

**响应**：

```json
{
  "code": 200,
  "message": "缓存刷新成功",
  "data": {
    "refresh_time": "2026-03-24T12:00:00",
    "cache_file": "/path/to/cache.json"
  }
}
```

### 5.3 查看缓存信息

```
GET /api/admin/cache_info
```

**响应**：

```json
{
  "code": 200,
  "data": {
    "exists": true,
    "cache_time": "2026-03-24T10:30:00",
    "is_valid": true,
    "expires_in": "23.5 小时"
  }
}
```

### 5.4 清除缓存

```
DELETE /api/admin/cache
```

### 5.5 健康检查

```
GET /api/health
```

---

## 六、快速开始

### 6.1 环境要求

- Python 3.8+
- Node.js 16+
- npm 或 yarn

### 6.2 后端启动

```bash
# 1. 进入后端目录
cd backend

# 2. 创建虚拟环境（可选）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，填入第三方 API 地址

# 5. 启动服务
uvicorn main:app --reload --port 8000
```

### 6.3 前端启动

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev
```

### 6.4 访问页面

- 前端：http://localhost:3000
- 后端 API：http://localhost:8000/docs（自动生成文档）
- 首页：http://localhost:3000/
- 管理面板：http://localhost:3000/admin
- 比赛记录：http://localhost:3000/records

---

## 七、环境变量配置

**backend/.env**：

```env
# 第三方 API 地址
THIRD_PARTY_API_URL=https://your-api.com/player/career

# API 密钥（如需要）
API_KEY=your_api_key

# 缓存有效期（小时），默认 24
CACHE_TTL_HOURS=24
```

---

## 八、核心代码

### 8.1 后端核心（main.py）

```python
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx
import json
from pathlib import Path
from datetime import datetime, timedelta

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

CACHE_FILE = Path("cache.json")
CACHE_TTL_HOURS = 24

@app.get("/api/player/career")
async def get_career_data(force_refresh: bool = False):
    # 检查缓存
    if not force_refresh and CACHE_FILE.exists():
        with open(CACHE_FILE) as f:
            cache = json.load(f)
        cache_time = datetime.fromisoformat(cache["timestamp"])
        if datetime.now() - cache_time < timedelta(hours=CACHE_TTL_HOURS):
            return {"code": 200, "data": cache["data"], "from_cache": True}

    # 请求第三方 API
    async with httpx.AsyncClient() as client:
        resp = await client.get("YOUR_API_URL")
        data = resp.json()

    # 保存缓存
    with open(CACHE_FILE, "w") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "data": data}, f)

    return {"code": 200, "data": data, "from_cache": False}
```

### 8.2 前端核心（App.vue）

```vue
<template>
  <div class="container" v-if="data">
    <!-- 选手信息 -->
    <div class="player-card">
      <h2>{{ data.player_info.latest_nickname }}</h2>
      <p>职业生涯：{{ data.career_summary.date_range }}</p>
      <p>
        总比赛：{{ data.career_summary.total_matches }}场 | 胜率：{{ data.career_summary.match_win_rate }} | KDA：{{
          data.career_summary.kda_ratio
        }}
      </p>
    </div>

    <!-- 英雄统计 -->
    <div class="stats-section">
      <h3>英雄使用统计</h3>
      <table class="data-table">
        <thead>
          <tr>
            <th>英雄</th>
            <th>对局数</th>
            <th>胜局</th>
            <th>败局</th>
            <th>胜率</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="hero in data.hero_stats" :key="hero.hero_id">
            <td>{{ hero.hero_name }}</td>
            <td>{{ hero.battles }}</td>
            <td>{{ hero.wins }}</td>
            <td>{{ hero.loses }}</td>
            <td>{{ hero.win_rate }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const data = ref(null);

onMounted(async () => {
  const res = await axios.get('/api/player/career');
  data.value = res.data.data;
});
</script>
```

---

## 九、部署说明

### 9.1 生产环境部署

**后端部署**：

```bash
# 使用 gunicorn + uvicorn
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

**前端部署**：

```bash
# 构建静态文件
npm run build
# 将 dist 目录部署到 Nginx
```

### 9.2 Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        root /var/www/kpl-stats/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
}
```

### 9.3 Docker 部署

**docker-compose.yml**：

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - '8000:8000'
    environment:
      - THIRD_PARTY_API_URL=${THIRD_PARTY_API_URL}
    volumes:
      - ./backend/cache.json:/app/cache.json

  frontend:
    build: ./frontend
    ports:
      - '80:80'
```

---

## 十、开发计划

| 阶段     | 任务               | 时间   |
| -------- | ------------------ | ------ |
| Day 1    | 后端搭建、API 对接  | 2h     |
| Day 1    | 前端页面搭建       | 2h     |
| Day 2    | 数据绑定、样式调整 | 2h     |
| Day 2    | 测试、部署         | 1h     |
| **总计** |                    | **7h** |

---

## 十一、常见问题

### Q1: 跨域问题怎么解决？

后端已配置 CORS 中间件，允许所有来源访问。

### Q2: 数据更新不及时怎么办？

调用 `POST /api/admin/refresh` 接口手动刷新缓存。

### Q3: 第三方 API 挂了怎么办？

系统会返回过期缓存数据，并标记为过期状态。

### Q4: 如何修改缓存时间？

修改环境变量 `CACHE_TTL_HOURS`。

---

## 十二、项目特点

✅ **零数据库**：无需安装和配置数据库
✅ **极简架构**：前后端分离，代码量少
✅ **自动缓存**：减少第三方 API 调用
✅ **手动刷新**：支持强制更新数据
✅ **快速部署**：一键启动，配置简单
✅ **跨域支持**：开箱即用
✅ **路由管理**：使用 Vue Router 进行前端路由管理
✅ **组件化**：模块化设计，易于维护和扩展
✅ **Halo 博客集成**：自动同步博客文章
✅ **Halo 视频集成**：随机视频展示
✅ **Halo 图库集成**：照片墙展示，支持懒加载和缩略图

---

**文档版本**：2.2
**更新日期**：2026-03-28
