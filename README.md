# KPL Stats - KSG.无言 生涯数据展示

KPL 选手生涯数据展示平台，为电竞选手"KSG.无言"打造的个人数据展示页面。

## 项目预览

![Preview](doc/preview.png)

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| **前端** | Vue 3 | 3.4+ |
| | Vue Router | 4.x |
| | Vite | 5.0+ |
| | Axios | 1.6+ |
| **后端** | FastAPI | 0.110+ |
| | Uvicorn | 0.28+ |
| | HTTPX | 0.27+ |
| | Python-dotenv | 1.0+ |

## 项目结构

```
kpl_stats/
├── backend/                 # 后端服务
│   ├── main.py              # FastAPI 主程序
│   ├── requirements.txt     # Python 依赖
│   ├── .env                 # 环境变量配置
│   ├── .env.example         # 环境变量模板
│   └── data/                # 数据目录（自动生成）
│       ├── cache.all.json       # 全部赛季缓存
│       ├── cache.league.json    # 联赛缓存
│       ├── cache.cup.json       # 杯赛缓存
│       ├── cache.all.YYYY-MM-DD.json    # 全部赛季存档
│       ├── cache.league.YYYY-MM-DD.json # 联赛存档
│       └── cache.cup.YYYY-MM-DD.json    # 杯赛存档
├── frontend/                # 前端应用
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── .env.development
│   └── src/
│       ├── main.js
│       ├── App.vue          # 主布局组件（导航栏 + router-view）
│       ├── router/
│       │   └── index.js     # 路由配置
│       ├── api/
│       │   └── stats.js     # API 请求封装
│       ├── components/
│       │   ├── Home.vue         # 首页组件
│       │   └── AdminPanel.vue   # 管理面板组件
│       └── styles/
│           ├── index.css        # 样式入口
│           ├── variables.css    # CSS 变量
│           ├── components.css   # 通用组件样式
│           ├── layouts.css      # 布局样式
│           ├── pages.css        # 页面样式
│           └── admin.css        # 管理面板样式
├── doc/                     # 项目文档
├── test/                    # 测试数据
└── README.md
```

## 快速开始

### 环境要求

- Python 3.8+（推荐使用 Conda 管理环境）
- Node.js 16+
- npm 或 yarn

### 后端启动

```bash
# 进入后端目录
cd backend

# 激活 Conda 环境（如已配置）
conda activate your-env

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env  # 或编辑 .env 文件
# 设置 THIRD_PARTY_API_URL 为实际 API 地址

# 启动服务
uvicorn main:app --reload --port 8001
```

### 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 访问应用

- **前端页面**: http://localhost:3000
- **数据管理**: http://localhost:3000/admin
- **后端 API 文档**: http://localhost:8001/docs

## API 接口

### 获取选手数据

```
GET /api/player/career?season_type=all&force_refresh=false
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| season_type | string | 否 | 赛季类型：all=全部，league=联赛，cup=杯赛 |
| force_refresh | boolean | 否 | 是否强制刷新缓存 |

**响应示例：**
```json
{
  "code": 200,
  "message": "数据来自缓存",
  "data": { ... },
  "season_type": "all",
  "from_cache": true,
  "cache_time": "2026-03-24T10:30:00"
}
```

### 手动刷新缓存

```
POST /api/admin/refresh?season_type=all&force=true
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| season_type | string | 否 | 赛季类型：all/league/cup |
| force | boolean | 否 | 是否强制刷新 |

### 查看缓存信息

```
GET /api/admin/cache_info?season_type=all
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| season_type | string | 否 | 赛季类型：all/league/cup |

### 查看所有缓存状态

```
GET /api/admin/cache_list
```

返回所有赛季类型的缓存状态。

### 清除缓存

```
DELETE /api/admin/cache?season_type=all
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| season_type | string | 否 | 赛季类型：all=清除所有，league/cup=清除指定类型 |

### 获取存档列表

```
GET /api/admin/archive_list
```

### 获取指定日期存档

```
GET /api/admin/archive/{date}?season_type=all
```

**参数：**
- `date`: 日期，格式 YYYY-MM-DD
- `season_type`: 赛季类型：all/league/cup

### 健康检查

```
GET /api/health
```

### 获取赛季列表

```
GET /api/seasons/list?project=KPL
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project | string | 否 | 项目名称，默认 KPL |

**响应示例：**
```json
{
  "code": 200,
  "message": "数据来自缓存",
  "data": [
    {
      "tournament_id": "KPL2026S1",
      "tournament_name": "KPL2026 春季赛",
      "project": "KPL",
      "season_type": "联赛",
      "is_latest": 1
    }
  ],
  "from_cache": true
}
```

### 获取赛季名称映射

```
GET /api/seasons/name_map
```

返回赛季 ID 到名称的映射，方便前端使用。

**响应示例：**
```json
{
  "code": 200,
  "message": "赛季名称映射",
  "data": {
    "KPL2026S1": "KPL2026 春季赛",
    "KCC2025": "2025 挑战者杯"
  }
}
```

## 环境变量配置

### 后端 (backend/.env)

```env
# 第三方 API 地址
THIRD_PARTY_API_URL=https://your-api.com/player/career

# API 密钥（如需要）
API_KEY=your_api_key

# 缓存有效期（小时），默认 24 小时
CACHE_TTL_HOURS=24
```

### 前端 (frontend/.env.development)

```env
# 后端 API 地址
VITE_API_BASE_URL=http://localhost:8001/api
```

## 核心功能

- ✅ **自动缓存** - 24 小时本地缓存，减少第三方 API 调用
- ✅ **手动刷新** - 支持强制更新数据
- ✅ **降级处理** - API 不可用时返回过期缓存
- ✅ **跨域支持** - Vite 代理，开发环境开箱即用
- ✅ **零数据库** - 文件缓存，无需额外配置

## 开发说明

### 代码风格

- **Python**: PEP 8 规范
- **Vue**: 组合式 API + `<script setup>` 语法
- **CSS**: Scoped 样式

### 常用命令

```bash
# 后端
cd backend
uvicorn main:app --reload --port 8001

# 前端
cd frontend
npm run dev      # 开发模式
npm run build    # 构建生产版本
npm run preview  # 预览构建结果
```

## 部署

### 生产环境部署

**后端：**

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

**前端：**

```bash
npm run build
# 将 dist 目录部署到 Nginx 或其他静态服务器
```

### Docker 部署

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - '8001:8001'
    environment:
      - THIRD_PARTY_API_URL=${THIRD_PARTY_API_URL}
  
  frontend:
    build: ./frontend
    ports:
      - '80:80'
```

## 常见问题

### Q: 跨域问题怎么解决？

前端开发环境已配置 Vite 代理，生产环境需配置 Nginx 反向代理。

### Q: 数据更新不及时怎么办？

调用 `POST /api/admin/refresh?force=true` 手动刷新缓存。

### Q: 第三方 API 不可用怎么办？

系统会自动返回过期缓存数据，并标记为过期状态。

### Q: 如何修改缓存时间？

修改环境变量 `CACHE_TTL_HOURS` 的值。

## 许可证

MIT License

## 联系方式

项目维护者：virola

---

**文档版本**: 1.0  
**更新日期**: 2026-03-24
