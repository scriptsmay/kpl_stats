# KPL Stats 数据站 - 开发进展

## 2026-03-30

### 项目现状
- **数据平台** (frontend): Vue 3 + Vite，已上线 `data.kplwuyan.site`
- **后端 API** (backend): FastAPI，包含 halo 代理 + 数据代理
- **粉丝站** (homepage): 静态 HTML/CSS/JS，已上线 `kplwuyan.site`
- **数据源**: kpl_data_daily GitHub Actions 每日抓取，JSON 文件托管在 GitHub

### 当前功能
- ✅ 生涯总览（总对局/胜率/KDA）
- ✅ 大场记录列表（分页、赛季筛选）
- ✅ 效力战队统计 / 赛季统计 / 英雄统计
- ✅ 比赛高光记录
- ✅ Halo 博客/视频/图库集成
- ✅ 管理面板（缓存刷新）

### 今日工作

#### 1. 后端拆分重构
- 目标：halo 代理和数据 API 分文件维护
- 结构：main.py + routers/ + services/ + config.py
- 状态：✅ 完成

#### 2. 前端数据展示增强
- 目标：基于 kpl_data_daily 数据源建设可视化页面
- 数据源：`https://raw.githubusercontent.com/scriptsmay/kpl_data_daily/main/data/`
- 技术方案：前端直接从 GitHub raw 获取 + ECharts 图表 + localStorage 缓存
- 新增依赖：`echarts`
- 状态：✅ 全部完成

##### 新增文件：
| 文件 | 用途 | 状态 |
|------|------|------|
| `api/github-data.js` | GitHub 数据源 API 模块（localStorage 缓存） | ✅ |
| `components/Abilities.vue` | 能力雷达图 + 12 维能力条 + 位置对比 | ✅ |
| `components/Ranking.vue` | 联盟排名（百分位雷达 + 排名卡片） | ✅ |
| `components/RankCard.vue` | 排名卡片组件 | ✅ |
| `components/Heroes.vue` | 英雄池分析（使用排行 + 胜率对比） | ✅ |
| `components/WinLose.vue` | 胜负对比（KDA/伤害/经济/洞察） | ✅ |
| `components/CompareCard.vue` | 对比卡片组件 | ✅ |

##### 新增路由：
| 路由 | 组件 | 说明 |
|------|------|------|
| `/abilities` | Abilities | 能力画像 |
| `/ranking` | Ranking | 联盟排名 |
| `/heroes` | Heroes | 英雄池分析 |
| `/win-lose` | WinLose | 胜负对比 |

##### 后端拆分：
| 文件 | 说明 |
|------|------|
| `config.py` | 环境变量集中管理 |
| `services/cache.py` | 通用缓存工具 |
| `services/halo_service.py` | Halo API + 缓存 |
| `services/player_service.py` | 选手数据 API + 缓存 |
| `routers/halo.py` | 9 个 Halo 相关接口 |
| `routers/player.py` | 13 个选手数据接口 |
| `main.py` | 精简为 ~40 行入口 |

---

## 待办
- [ ] 更新 README 文档
- [ ] 生产环境部署测试
- [ ] ECharts 动态 import 拆包（减少主 bundle 体积）
