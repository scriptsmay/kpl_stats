# 选手能力值变化可视化 — 实现总结

> 版本：v2.0（实现完成版）
> 日期：2026-07-26
> 状态：已实现，进入维护期

---

## 一、概述

### 1.1 功能定位

**能力趋势**是选手能力画像的延伸视图，以时间序列折线图形式展示选手能力值随赛季进行的变化轨迹。每个数据点对应一场比赛后能力值的更新结果，配合赛程联动标注，让用户直观看到"打完这场比赛后能力值变成了多少"。

**关键决策**：能力趋势属于**数据可视化**范畴，不属于 AI 分析。已于 v2.0 从 AI 分析页面迁移到 [Abilities.vue](file:///d:/code/projects/cheer.wuyan/kpl_stats/frontend/src/components/Abilities.vue) 选手能力画像页面底部，作为独立区块呈现。AI 分析页面回归纯 AI 洞察语义。

### 1.2 整体架构

项目采用**前后端分离 + 静态数据驱动**的架构：

| 层级 | 项目 | 说明 |
|------|------|------|
| 前端展示 | kpl_stats | Vue 3 + Chart.js，数据平台 |
| 数据仓库 | kpl_data_daily | 每日采集 + 后处理派生数据 |
| 后端代理 | FastAPI | 生涯数据、管理接口、Halo 代理 |

**数据流向**：
```
KPL官方API → kpl_data_daily (每日采集) → 静态JSON (GitHub)
                                              ↓
                                       kpl_stats 前端
                                  (直接读取 GitHub 原始文件)
```

### 1.3 文件清单

| 文件 | 职责 |
|------|------|
| [trends.py](file:///d:/code/projects/cheer.wuyan/kpl_data_daily/src/analysis/trends.py) | 数据仓库侧：`generate_ability_timeline()` 生成时间序列 |
| [post_process.py](file:///d:/code/projects/cheer.wuyan/kpl_data_daily/post_process.py) | 数据仓库侧：调用生成函数，写入 `ability-timeline.json` |
| [fetch-schedule.py](file:///d:/code/projects/cheer.wuyan/kpl_data_daily/scripts/fetch-schedule.py) | 数据仓库侧：生成 `schedule.json`，使用 `wrap_derived_payload()` 标准包装 |
| [github-data.js](file:///d:/code/projects/cheer.wuyan/kpl_stats/frontend/src/api/github-data.js) | 前端 API：`getAbilityTimeline()` / `getSchedule()` |
| [useAbilityTrend.js](file:///d:/code/projects/cheer.wuyan/kpl_stats/frontend/src/composables/useAbilityTrend.js) | 前端 composable：赛程对齐、数据组装 |
| [AbilityTrendChart.vue](file:///d:/code/projects/cheer.wuyan/kpl_stats/frontend/src/components/AbilityTrendChart.vue) | 前端图表组件 |
| [Abilities.vue](file:///d:/code/projects/cheer.wuyan/kpl_stats/frontend/src/components/Abilities.vue) | 容器页面，底部承载能力趋势区块 |

---

## 二、数据仓库实现

### 2.1 派生数据文件

`post_process.py` 每日生成以下派生文件，位于 `derived/{season}/`：

| 文件 | 内容 |
|------|------|
| `ability-timeline.json` | 能力值绝对值时间序列（核心数据） |
| `schedule.json` | KSG 全部赛程 |
| `trend-summary.json` | 趋势摘要 deltas（已存在，前端可复用） |
| `growth-path.json` | 成长路径 milestones（已存在） |
| `ai-insights.json` | AI 洞察文案（已存在） |

### 2.2 `ability-timeline.json` 结构

由 [trends.py `generate_ability_timeline()`](file:///d:/code/projects/cheer.wuyan/kpl_data_daily/src/analysis/trends.py#L325-L422) 生成，输出包装格式：

```json
{
  "schema_version": 1,
  "season": "KPL2026S2",
  "generated_at": "2026-07-25T19:00:02+00:00",
  "build_id": "...",
  "data": {
    "snapshot_count": 31,
    "reference_date": "20260725",
    "player_position": "对抗路",
    "position_averages": {
      "damage_output": 84,
      "teamfight": 90,
      ...
    },
    "position_averages_by_position": {
      "对抗路": { "damage_output": 84, ... },
      "中路": { ... }
    },
    "season_final_data": {
      "status": "complete | pending | missing",
      "last_match_id": "...",
      "expected_total": 37,
      "actual_total": 34
    },
    "snapshots": [
      {
        "date": "20260625",
        "last_updated": "2026-06-25 06:03:46",
        "total_matches": 10,
        "overall_rating": 94.87,
        "overall_rank": 5,
        "position_rank": 1,
        "abilities": {
          "damage_output": 85.0,
          "teamfight": 94.0,
          "initiation": 100.0,
          "early_game": 79.0,
          "mid_game": 91.0,
          "late_game": 95.0,
          "map_control": 85.0,
          "invasion_ability": 92.0,
          "support_ability": 91.0,
          "economy": 78.0,
          "tankiness": 100.0,
          "durability": 62.0
        }
      }
    ]
  }
}
```

### 2.3 关键设计点

#### `position_averages` 展平
原始数据按位置嵌套（`{对抗路: {damage_output: 84, ...}, 中路: {...}}`），但前端只需"该选手所在位置"的均值。因此 trends.py 从快照中提取 `player_position`，将对应位置的均值展平为 `{damage_output: 84, ...}`，前端可直接 `positionAverages[dimKey]` 取值。原始嵌套结构保留在 `position_averages_by_position` 字段供调试参考。

#### `season_final_data` 状态判定
由 [`_determine_season_final_data()`](file:///d:/code/projects/cheer.wuyan/kpl_data_daily/src/analysis/trends.py#L425-L512) 计算：

1. 加载 `schedule.json`
2. 累计所有已结束（`status === 4`）KSG 比赛的小局数 → `expected_total`
3. 取最新快照的 `total_matches` → `actual_total`
4. 判定状态：
   - `complete`：`actual_total >= expected_total`，决赛数据已到位
   - `missing`：赛季最后一场已结束 > 7 天，且 `actual_total < expected_total`，决赛数据超时缺失
   - `pending`：赛季未结束或最后一场结束 ≤ 7 天，数据待更新

#### `total_matches` 处理
原始数据可能是浮点数（`34.0`），trends.py 统一 `int(round(float()))` 转为整数，防御性处理 None / 异常字符串。

### 2.4 `schedule.json` 结构

由 [fetch-schedule.py](file:///d:/code/projects/cheer.wuyan/kpl_data_daily/scripts/fetch-schedule.py#L119-L136) 生成，使用 `wrap_derived_payload()` 标准包装。`schedule.json` 与 `post_process` 异步生成，`build_id` 天然不同步，因此前端 `getSchedule()` 绕过 `fetchDerived` 的严格 build_id 校验，改走直接 fetch + 手动缓存。

```json
{
  "schedule_id": "KPL2026S2M1W1D3",
  "start_ts": 1781697600,
  "date": "06-17 20:00",
  "team_a": "重庆狼队",
  "team_b": "KSG",
  "is_ksg": true,
  "location": "重庆",
  "stage": "常规赛第一轮",
  "bo": 5,
  "status": 4,
  "score_a": 0,
  "score_b": 3
}
```

| 字段 | 说明 |
|------|------|
| `schedule_id` | 赛程唯一标识（注意不是 `match_id`） |
| `start_ts` | Unix 时间戳（秒） |
| `date` | 人类可读日期，格式 `MM-DD HH:MM` |
| `team_a` / `team_b` | 对战双方队伍全名 |
| `is_ksg` | 恒为 true，表示"这是 KSG 的比赛"（**不是**"KSG 是否主场"） |
| `status` | 数字：0=未开始，1=进行中，4=已结束 |
| `score_a` / `score_b` | team_a / team_b 的得分 |

> **关键**：判断 KSG 主客场需检查 `team_a === 'KSG'`，而非 `is_ksg` 字段。判断胜负根据 KSG 是 team_a 还是 team_b 来比较 score。

---

## 三、赛程-能力值对齐方案

### 3.1 对齐原理：对局数锚定法

```
能力快照.total_matches = N
          ↕ 精确对应
赛程中累计达到 N 局的那场比赛
```

能力值是"基于截至某场比赛的累计数据计算的"，用 `total_matches` 可以精确知道这份能力数据反映了哪几场比赛之后的水平。

KPL2026S2 赛季对齐示例：

| 场次 | 比赛日期 | 对手 | KSG比分 | 胜负 | 累计小局 | 能力数据文件日期 | total_matches |
|------|---------|------|---------|------|---------|-----------------|---------------|
| 第1场 | 06-17 | 重庆狼队 | 3:0 | 胜 | 3 | 06-18 | 3 |
| 第2场 | 06-19 | 成都AG超玩会 | 1:3 | 负 | 7 | 06-20 | 7 |
| 第3场 | 06-24 | 济南RW侠 | 3:0 | 胜 | 10 | 06-25 | 10 |
| ... | ... | ... | ... | ... | ... | ... | ... |
| 第9场 | 07-22 | 杭州LGD.NBW | 3:1 | 胜 | 34 | 07-23 | 34 |

### 3.2 前端对齐实现

由 [useAbilityTrend.js](file:///d:/code/projects/cheer.wuyan/kpl_stats/frontend/src/composables/useAbilityTrend.js#L29-L77) 实现：

```javascript
function buildMatchCumulative(scheduleData) {
  // 按 status === 4 过滤已结束比赛，按 start_ts 排序
  // 通过 team_a === 'KSG' 判断主客场
  // 累计小局数 = score_a + score_b
  // 返回 [{ match_id, date, start_ts, opponent, score, is_win, stage,
  //         game_count, cumulative_matches }]
}

function alignAbilityToMatch(snapshot, matchCumulative) {
  const totalMatches = Math.round(snapshot.total_matches);
  // 找到 cumulative_matches >= totalMatches 的第一场比赛
  // 误差 > 2 局时回退到 last_updated 日期对齐
}
```

### 3.3 边界情况处理

| 情况 | 处理方式 |
|------|---------|
| `total_matches` 为 0 或 null | 跳过该快照，不计入趋势线 |
| 对齐误差 > 2 局（替补/转会等） | 回退到 `last_updated` 日期对齐，console.warn 告警 |
| 多场比赛在同一天 | 都标注在同一天，tooltip 中列出全部比赛 |
| 赛季末决赛数据滞后 | 通过 `season_final_data` 字段驱动前端提示 |

### 3.4 数据滞后规律

- **实际更新时间**：比赛结束后当晚（约赛后 2-5 小时）第三方 API 更新
- **数据采集延迟**：kpl_data_daily 每日采集一次，文件日期 = 比赛日期 + 1天
- **赛季末延迟**：决赛后 API 可能延迟 2~5 天，由 `season_final_data` 状态机处理

---

## 四、前端实现

### 4.1 页面布局

能力趋势作为 [Abilities.vue](file:///d:/code/projects/cheer.wuyan/kpl_stats/frontend/src/components/Abilities.vue) 底部独立区块呈现：

```
┌──────────────────────────────────────────────┐
│  📊 选手能力画像            [赛季选择器]       │
├──────────────────────────────────────────────┤
│  综合评分卡片 / 雷达图 / 维度详情 / 位置对比  │
├──────────────────────────────────────────────┤
│  📈 能力趋势                                  │
│  [7天] [14天] [30天] [全部]                   │
│  [折线] [阶梯]  [值] [Delta]                  │
│  维度选择: [综合评分 ▼]  + 添加对比           │
├──────────────────────────────────────────────┤
│        能力趋势折线图（主图）                 │
│    · 折线：能力值变化                         │
│    · 数据点：胜=红 / 负=绿                    │
│    · 悬停tooltip：日期+数值+比赛详情          │
└──────────────────────────────────────────────┘
```

> AI 分析页面 [AIAnalysis.vue](file:///d:/code/projects/cheer.wuyan/kpl_stats/frontend/src/components/AIAnalysis.vue) 已移除 Tab 结构，回归纯 AI 洞察。

### 4.2 数据流

```
useSeason() ──seasonId──┬─→ getAbilityTimeline(seasonId) ──→ ability-timeline.json
                        │
                        └─→ getSchedule(seasonId) ─────────→ schedule.json

useAbilityTrend(seasonId)
  ├─ 并行加载两个数据源
  ├─ buildMatchCumulative(schedule)
  ├─ alignAbilityToMatch(snapshot, matchCumulative)
  └─ 输出 { snapshots, dimensions, timeRanges, ... }

AbilityTrendChart.vue
  └─ Chart.js 渲染折线/阶梯图
```

### 4.3 图表交互设计

#### 工具栏（3 组按钮）
- **时间范围**：7天 / 14天 / 30天 / 全部
- **图表模式**：折线 / 阶梯
- **值显示模式**：值 / Delta（相对起点的变化量）

#### 颜色语义（三处色块各司其职）

| 位置 | 颜色来源 | 含义 |
|------|---------|------|
| **图表数据点** | `pointBackgroundColor` 数组 | 胜=红 / 负=绿 |
| **Legend 图例** | `dataset.borderColor` | 标识"这是哪条指标线" |
| **Tooltip 色块** | `dataset.borderColor`（通过 `labelColor` 回调） | 标识"这一行属于哪条线" |

> Chart.js 4.x 中，legend `usePointStyle: true` 会取 `pointBackgroundColor` 数组首元素，导致所有指标显示成同一颜色。已改用 `usePointStyle: false` + 矩形色块（`boxWidth: 16, boxHeight: 3`）读取 `borderColor`。Tooltip 同理添加 `labelColor` 回调。

#### 胜负颜色约定（中国电竞惯例）
- **涨=红**（正向变化）
- **跌=绿**（负向变化）

CSS `.stat-delta.positive { color: red }` / `.stat-delta.negative { color: green }`。

#### Tooltip 内容（按数据点类型）

**正常情况**（`aligned_match` 存在）：
```
📍 常规赛第一轮
🎮 累计 14 局
🕐 比赛: 06-27 20:00
```

**降级兜底**（对齐误差 > 2 局，`aligned_match` 为 null）：
```
ℹ️ 对齐误差较大，使用数据更新日期兜底
🕐 数据更新: 2026-06-28 06:03:46
```

> 能力值更新本质上都是因为比赛，只有对齐失败时才需要降级。"非比赛日微调"措辞已弃用，避免误导用户。

### 4.4 多维度对比的 Y 轴归一化

- **单维度**：使用单一 Y 轴，显示绝对值
- **多维度叠加**：启用双 Y 轴（`yAxisID`），左轴对应第一个维度，右轴对应第二个维度
- 提供"值 / Delta"切换开关，Delta 模式显示相对起点的变化量

### 4.5 赛季切换

- `seasonId` 由 `useSeason` 提供，所有 API 必填参数
- `useAbilityTrend` 内部 watch seasonId 自动重载
- 缓存 key 含 seasonId，赛季切换自动隔离，二次访问秒开
- 切换时清空上一赛季趋势数据 ref，避免视觉残留

---

## 五、容错与降级策略

### 5.1 数据容错

| Case | 处理 |
|------|------|
| 脚本断网未采集 | ability-timeline.json 中该日期无快照，折线不中断 |
| `total_matches` 浮点数 | `Math.round()` 取整后对齐 |
| 对齐误差 > 2 局 | 回退到 `last_updated` 日期，console.warn |
| 缺失 seasonId | 抛出 `seasonId is required` 错误，不发起请求 |
| 缓存赛季隔离 | 缓存 key 含 seasonId，切回秒开且无串档 |

### 5.2 赛季末决赛数据状态机

由 `season_final_data.status` 字段驱动前端提示：

| 状态 | 条件 | 前端提示 |
|------|------|---------|
| `complete` | `actual_total >= expected_total` | 绿色徽标"赛季数据完整" |
| `pending` | 赛季未结束或最后一场结束 ≤ 7 天 | 橙色 Alert"赛季已结束，决赛数据等待更新中（预计 1~3 天）" |
| `missing` | 最后一场结束 > 7 天且未追平 | 灰色提示"本赛季决赛数据未能获取，趋势图展示至半决赛" |

### 5.3 跨赛季隔离

- 数据仓库按 `season` 字段过滤，不混用不同赛季的 `total_matches`
- 赛季切换时 `total_matches` 重置从 0 开始，趋势图在新赛季重新起线
- 前端按 `seasonId` 隔离缓存与 ref

---

## 六、未实现 / 后续迭代项

按 review 文档标注，以下为低优先级或后续迭代项，当前版本未实现：

| 项 | 严重性 | 说明 |
|----|--------|------|
| 垂直线标注比赛日 | P2 | 当前用数据点颜色区分胜负，未画垂直线 |
| `hero_first_use` 关键节点标注 | P2 | growth-path.json 已有数据，未在图表上标注 |
| QA-3 选手未上场检测 | P2 | 当前用战队累计小局近似选手出场，误差 > 2 局时降级兜底 |
| 休赛期断轴 ⌇ | P2 | 当前 `bounds: 'data'` 自适应，未做非线性截断 |
| 数据表格视图 | P3 | |
| 跨赛季对比 | P3 | |
| 选手个人出场数据采集 | P3 | 解决替补/轮换对齐精度 |

---

## 七、验收标准对照

### 7.1 已通过

| Case | 状态 |
|------|------|
| QA-1 脚本断网未采集 | ✅ 折线不中断 |
| QA-4 跨赛季切换 | ✅ total_matches 重新起线 |
| QA-4b 缺失 seasonId | ✅ 抛错不发起请求 |
| QA-4c 缓存赛季隔离 | ✅ 缓存 key 含 seasonId |
| QA-5 对齐误差回退 | ✅ 降级到 last_updated |
| QA-6 total_matches 浮点数 | ✅ Math.round 取整 |
| QA-6b 决赛数据待更新 | ✅ 橙色 Alert |
| QA-6c 决赛数据补全 | ✅ 自动补全末尾点 |
| QA-6d 决赛数据超时缺失 | ✅ 灰色提示 |
| QA-7 单文件加载 | ✅ 1 个请求 ~10-15KB |
| QA-8 二次访问缓存 | ✅ localStorage 秒开 |
| QA-9 数据仓库生成 | ✅ 与 trend-summary 同源 |
| QA-12 阶梯/折线切换 | ✅ 工具栏切换按钮 |
| QA-13 胜负色标 | ✅ 胜红负绿 |
| QA-16 schedule 字段解析 | ✅ team_a/team_b 正确识别 |
| QA-17 status 数字判断 | ✅ status === 4 |
| QA-18 完整10场比赛 | ✅ X 轴全标注 |

### 7.2 未实现（见第六章）

QA-3 选手未上场、QA-10 双 Y 轴多维度叠加、QA-11 休赛期截断、QA-14 关键节点、QA-15 变化统计面板

---

## 八、维护注意事项

1. **`position_averages` 结构**：trends.py 已展平为该选手位置的均值，前端直接 `positionAverages[dimKey]` 取值。若需展示其他位置均值，从 `position_averages_by_position` 取。
2. **`schedule.json` build_id 不同步**：fetch-schedule.py 与 post_process 异步生成，前端 `getSchedule()` 已绕过 `fetchDerived` 严格校验。修改 schedule 包装格式时注意兼容性。
3. **赛季末延迟采集**：数据仓库应在赛季最后一场比赛结束后继续采集 7 天，直到决赛 `total_matches` 出现或超时。
4. **服务器内存约束**：2G 服务器跑 Playwright + Chromium 需使用 headless + 单进程 + 禁用 GPU 等内存优化参数。
5. **第三方 API Origin 校验**：直接调用 47.102.210.150 系列 API 会被 403，必须通过浏览器上下文或代理服务器（http://www.jungushiyan.cn/）访问。
