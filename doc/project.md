# 《KPL无言选手生涯数据》项目文档

## 一、项目概述

### 1.1 项目简介

为电竞选手“KSG.无言”搭建生涯数据展示页面，通过代理第三方API获取数据，前端使用Vue进行纯JSON渲染。

### 1.2 技术栈

| 层级     | 技术          | 版本   | 用途           |
| -------- | ------------- | ------ | -------------- |
| **前端** | Vue 3         | 3.4+   | 数据绑定与渲染 |
|          | Vite          | 5.0+   | 构建工具       |
|          | Axios         | 1.6+   | HTTP请求       |
|          | 原生CSS       | -      | 页面样式       |
| **后端** | FastAPI       | 0.110+ | API代理服务    |
|          | Uvicorn       | 0.28+  | ASGI服务器     |
|          | HTTPX         | 0.27+  | 异步HTTP客户端 |
|          | Python-dotenv | 1.0+   | 环境变量管理   |

---

## 二、系统架构

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (Vue 3)                          │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  选手信息卡 │ 战队统计 │ 赛季统计 │ 英雄统计 │ 比赛列表 │  │
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
│                    第三方数据API                            │
│                  (选手生涯数据接口)                          │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据流程

```
1. 前端请求数据
        ↓
2. 后端检查本地缓存
   ├── 缓存有效 → 直接返回
   └── 缓存无效 → 请求第三方API
        ↓
3. 第三方API返回数据
        ↓
4. 保存到本地缓存
        ↓
5. 返回JSON给前端
        ↓
6. Vue渲染页面
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
│       ├── api/
│       │   └── stats.js     # API请求封装
│       └── style/
│           └── main.css     # 样式文件
├── backend/                  # 后端项目
│   ├── main.py              # FastAPI主程序
│   ├── requirements.txt     # Python依赖
│   ├── .env                 # 环境变量
│   ├── cache.json           # 缓存文件（自动生成）
│   └── .gitignore
└── README.md
```

---

## 四、API接口文档

### 4.1 获取选手数据

```
GET /api/player/career
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| force_refresh | boolean | 否 | 是否强制刷新（默认false） |

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

### 4.2 手动刷新缓存

```
POST /api/admin/refresh
```

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| force | boolean | 否 | 是否强制刷新（默认true） |

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

### 4.3 查看缓存信息

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
    "expires_in": "23.5小时"
  }
}
```

### 4.4 清除缓存

```
DELETE /api/admin/cache
```

### 4.5 健康检查

```
GET /api/health
```

---

## 五、快速开始

### 5.1 环境要求

- Python 3.8+
- Node.js 16+
- npm 或 yarn

### 5.2 后端启动

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
# 编辑 .env，填入第三方API地址

# 5. 启动服务
uvicorn main:app --reload --port 8000
```

### 5.3 前端启动

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev
```

### 5.4 访问页面

- 前端：http://localhost:3000
- 后端API：http://localhost:8000/docs（自动生成文档）

---

## 六、环境变量配置

**backend/.env**：

```env
# 第三方API地址
THIRD_PARTY_API_URL=https://your-api.com/player/career

# API密钥（如需要）
API_KEY=your_api_key

# 缓存有效期（小时），默认24
CACHE_TTL_HOURS=24
```

---

## 七、核心代码

### 7.1 后端核心（main.py）

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

    # 请求第三方API
    async with httpx.AsyncClient() as client:
        resp = await client.get("YOUR_API_URL")
        data = resp.json()

    # 保存缓存
    with open(CACHE_FILE, "w") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "data": data}, f)

    return {"code": 200, "data": data, "from_cache": False}
```

### 7.2 前端核心（App.vue）

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

## 八、部署说明

### 8.1 生产环境部署

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

### 8.2 Nginx配置示例

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

### 8.3 Docker部署

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

## 九、开发计划

| 阶段     | 任务               | 时间   |
| -------- | ------------------ | ------ |
| Day 1    | 后端搭建、API对接  | 2h     |
| Day 1    | 前端页面搭建       | 2h     |
| Day 2    | 数据绑定、样式调整 | 2h     |
| Day 2    | 测试、部署         | 1h     |
| **总计** |                    | **7h** |

---

## 十、常见问题

### Q1: 跨域问题怎么解决？

后端已配置CORS中间件，允许所有来源访问。

### Q2: 数据更新不及时怎么办？

调用 `POST /api/admin/refresh` 接口手动刷新缓存。

### Q3: 第三方API挂了怎么办？

系统会返回过期缓存数据，并标记为过期状态。

### Q4: 如何修改缓存时间？

修改环境变量 `CACHE_TTL_HOURS`。

---

## 十一、项目特点

✅ **零数据库**：无需安装和配置数据库  
✅ **极简架构**：前后端分离，代码量少  
✅ **自动缓存**：减少第三方API调用  
✅ **手动刷新**：支持强制更新数据  
✅ **快速部署**：一键启动，配置简单  
✅ **跨域支持**：开箱即用

---

**文档版本**：2.0  
**更新日期**：2026-03-24
