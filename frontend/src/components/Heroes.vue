<!--
 * Heroes.vue - 英雄池分析页面
 * 展示选手（KSG.无言）的英雄使用数据与联盟英雄胜率对比
 * 包含：英雄池概览、使用排行柱状图、详情表格、胜率vs联盟平均对比
 -->
<template>
  <div class="result-section heroes-page">
    <div class="result-header">
      <h1 class="result-title">⚔️ 英雄池分析</h1>
      <p class="result-subtitle">对抗路选手英雄使用数据与联盟胜率对比</p>
    </div>

    <!-- 加载状态 -->
    <div class="loading" v-if="loading">
      <div class="loading-spinner"></div>
      <div class="loading-text">正在加载英雄池数据...</div>
    </div>

    <!-- 错误状态 -->
    <div class="error-message" v-else-if="error">
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="loadData">重试</button>
    </div>

    <!-- 数据内容 -->
    <div v-else-if="heroStats.length">
      <!-- 1. 英雄池概览 -->
      <div class="summary-cards">
        <div class="summary-card">
          <div class="summary-card-value">{{ heroStats.length }}</div>
          <div class="summary-card-label">使用英雄数</div>
        </div>
        <div class="summary-card">
          <div class="summary-card-value">{{ totalMatches }}</div>
          <div class="summary-card-label">总使用场次</div>
        </div>
        <div class="summary-card">
          <div class="summary-card-value win">{{ totalWins }}</div>
          <div class="summary-card-label">获胜场次</div>
        </div>
        <div class="summary-card">
          <div class="summary-card-value" :class="overallWinRateClass">{{ overallWinRateText }}</div>
          <div class="summary-card-label">综合胜率</div>
        </div>
      </div>

      <!-- 2. 英雄使用排行柱状图 -->
      <div class="chart-container">
        <div class="chart-title">英雄使用次数排行 TOP 15</div>
        <div ref="barChartRef" class="chart-box chart-box-tall"></div>
      </div>

      <!-- 3. 英雄详情表格 -->
      <div class="hero-table-section">
        <div class="section-title">英雄详情</div>
        <div class="hero-table-wrapper">
          <table class="hero-table">
            <thead>
              <tr>
                <th class="col-rank">#</th>
                <th class="col-hero">英雄</th>
                <th class="col-num">使用</th>
                <th class="col-num">胜场</th>
                <th class="col-num">负场</th>
                <th class="col-num">胜率</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(hero, index) in heroStatsSorted" :key="hero.hero_id">
                <td class="col-rank">{{ index + 1 }}</td>
                <td class="col-hero">
                  <div class="hero-info">
                    <img
                      :src="heroAvatar(hero.hero_id)"
                      :alt="hero.hero_name"
                      class="hero-avatar"
                      @error="handleAvatarError($event)"
                    />
                    <span class="hero-name">{{ hero.hero_name }}</span>
                  </div>
                </td>
                <td class="col-num">{{ hero.total_matches }}</td>
                <td class="col-num text-success">{{ hero.win_matches }}</td>
                <td class="col-num text-danger">{{ hero.total_matches - hero.win_matches }}</td>
                <td class="col-num">
                  <span :class="winRateClass(hero.win_rate)">{{ hero.win_rate }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 4. 英雄胜率 vs 联盟平均 -->
      <div class="chart-container" v-if="compareData.length">
        <div class="chart-title">胜率 vs 联盟对抗路平均</div>
        <div ref="compareChartRef" class="chart-box chart-box-tall"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onUnmounted } from 'vue';
import * as echarts from 'echarts';
import { getPlayerHeroSummary, getHeroWinRate, DEFAULT_SEASON } from '../api/github-data';

// 状态
const loading = ref(false);
const error = ref(null);
const heroStats = ref([]);
const leagueHeroes = ref([]);

// 图表引用
const barChartRef = ref(null);
const compareChartRef = ref(null);
let barChart = null;
let compareChart = null;

// 英雄头像 URL
const heroAvatar = (id) =>
  `https://game.gtimg.cn/images/yxzj/img201606/heroimg/${id}/${id}.jpg`;

// 头像加载失败 fallback
const handleAvatarError = (e) => {
  e.target.style.display = 'none';
};

// ====== 计算属性 ======

const totalMatches = computed(() =>
  heroStats.value.reduce((sum, h) => sum + (h.total_matches || 0), 0)
);

const totalWins = computed(() =>
  heroStats.value.reduce((sum, h) => sum + (h.win_matches || 0), 0)
);

const overallWinRate = computed(() => {
  if (!totalMatches.value) return 0;
  return Math.round((totalWins.value / totalMatches.value) * 1000) / 10;
});

const overallWinRateText = computed(() => overallWinRate.value + '%');

const overallWinRateClass = computed(() => {
  if (overallWinRate.value >= 60) return 'win';
  if (overallWinRate.value < 45) return 'lose';
  return '';
});

// 按使用次数降序
const heroStatsSorted = computed(() =>
  [...heroStats.value].sort((a, b) => b.total_matches - a.total_matches)
);

// 胜率样式
const winRateClass = (rate) => {
  const v = parseFloat(rate);
  if (v >= 60) return 'text-success';
  if (v < 45) return 'text-danger';
  return '';
};

// 对比数据：无言使用过的英雄 vs 联盟对抗路该英雄胜率
const compareData = computed(() => {
  if (!heroStats.value.length || !leagueHeroes.value.length) return [];

  const leagueMap = {};
  leagueHeroes.value.forEach(h => {
    leagueMap[h.hero_id] = h;
  });

  return heroStats.value
    .filter(h => leagueMap[h.hero_id])
    .map(h => ({
      hero_name: h.hero_name,
      player_rate: parseFloat(h.win_rate),
      league_rate: parseFloat(leagueMap[h.hero_id].win_rate),
      total_matches: h.total_matches
    }))
    .sort((a, b) => b.total_matches - a.total_matches)
    .slice(0, 15);
});

// ====== 数据加载 ======

async function loadData() {
  loading.value = true;
  error.value = null;
  try {
    const [heroRes, leagueRes] = await Promise.all([
      getPlayerHeroSummary(DEFAULT_SEASON),
      getHeroWinRate(DEFAULT_SEASON)
    ]);

    // 处理选手英雄数据 — 可能是单条或数组
    if (heroRes.code === 200) {
      heroStats.value = Array.isArray(heroRes.data) ? heroRes.data : [heroRes.data];
    }

    // 处理联盟英雄胜率 — 筛选对抗路
    if (leagueRes.code === 200 && Array.isArray(leagueRes.data)) {
      leagueHeroes.value = leagueRes.data.filter(h => h.position === '对抗路');
    }

    await nextTick();
    initBarChart();
    if (compareData.value.length) {
      await nextTick();
      initCompareChart();
    }
  } catch (err) {
    console.error('英雄池数据加载失败:', err);
    error.value = '数据加载失败，请检查网络后重试';
  } finally {
    loading.value = false;
  }
}

// ====== 图表初始化 ======

function initBarChart() {
  if (!barChartRef.value) return;
  if (barChart) barChart.dispose();

  barChart = echarts.init(barChartRef.value);

  const top15 = heroStatsSorted.value.slice(0, 15).reverse();

  barChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const p = params[0];
        const hero = top15[p.dataIndex];
        return `<strong>${hero.hero_name}</strong><br/>
          使用: ${hero.total_matches} 场<br/>
          胜场: ${hero.win_matches} / 负场: ${hero.total_matches - hero.win_matches}<br/>
          胜率: ${hero.win_rate}`;
      }
    },
    grid: { left: 100, right: 40, top: 20, bottom: 30 },
    xAxis: { type: 'value', name: '使用次数' },
    yAxis: {
      type: 'category',
      data: top15.map(h => h.hero_name),
      axisLabel: { fontSize: 13 }
    },
    series: [
      {
        type: 'bar',
        data: top15.map(h => h.total_matches),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#667eea' },
            { offset: 1, color: '#764ba2' }
          ]),
          borderRadius: [0, 4, 4, 0]
        },
        barMaxWidth: 24,
        label: {
          show: true,
          position: 'right',
          formatter: '{c} 场',
          fontSize: 12
        }
      }
    ]
  });
}

function initCompareChart() {
  if (!compareChartRef.value) return;
  if (compareChart) compareChart.dispose();

  compareChart = echarts.init(compareChartRef.value);

  const data = compareData.value;

  compareChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const d = data[params[0].dataIndex];
        return `<strong>${d.hero_name}</strong><br/>
          无言胜率: ${d.player_rate}% (${d.total_matches} 场)<br/>
          联盟对抗路平均: ${d.league_rate}%`;
      }
    },
    legend: {
      data: ['无言胜率', '联盟对抗路平均'],
      top: 5
    },
    grid: { left: 80, right: 40, top: 50, bottom: 30 },
    xAxis: {
      type: 'category',
      data: data.map(d => d.hero_name),
      axisLabel: { rotate: 30, fontSize: 12 }
    },
    yAxis: { type: 'value', name: '胜率 (%)', max: 100 },
    series: [
      {
        name: '无言胜率',
        type: 'bar',
        data: data.map(d => d.player_rate),
        itemStyle: {
          color: '#4ecdc4',
          borderRadius: [4, 4, 0, 0]
        },
        barMaxWidth: 20
      },
      {
        name: '联盟对抗路平均',
        type: 'bar',
        data: data.map(d => d.league_rate),
        itemStyle: {
          color: '#e0e0e0',
          borderRadius: [4, 4, 0, 0]
        },
        barMaxWidth: 20
      }
    ]
  });
}

// 响应式 resize
function handleResize() {
  barChart?.resize();
  compareChart?.resize();
}

onMounted(() => {
  loadData();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  barChart?.dispose();
  compareChart?.dispose();
});
</script>

<style scoped>
.heroes-page {
  padding: 20px;
}

/* 概览卡片复用项目已有样式 (.summary-cards) */

/* 图表容器 */
.chart-container {
  background: var(--card-bg, #fff);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: var(--shadow-sm, 0 1px 3px rgba(0, 0, 0, 0.08));
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-primary, #333);
}

.chart-box {
  width: 100%;
  height: 400px;
}

.chart-box-tall {
  height: 480px;
}

/* 区域标题 */
.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-primary, #333);
}

/* 英雄详情表格 */
.hero-table-section {
  background: var(--card-bg, #fff);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: var(--shadow-sm, 0 1px 3px rgba(0, 0, 0, 0.08));
}

.hero-table-wrapper {
  overflow-x: auto;
}

.hero-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.hero-table th,
.hero-table td {
  padding: 10px 12px;
  text-align: center;
  border-bottom: 1px solid var(--border-color, #f0f0f0);
}

.hero-table thead th {
  font-weight: 600;
  color: var(--text-secondary, #888);
  background: var(--bg-secondary, #fafafa);
  position: sticky;
  top: 0;
}

.hero-table tbody tr:hover {
  background: var(--bg-hover, #f5f7ff);
}

.col-rank {
  width: 48px;
  color: var(--text-secondary, #999);
}

.col-hero {
  text-align: left !important;
  min-width: 120px;
}

.col-num {
  width: 72px;
}

.hero-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.hero-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--primary-color, #667eea);
  flex-shrink: 0;
}

.hero-name {
  font-weight: 500;
  white-space: nowrap;
}

.text-success {
  color: var(--success-color, #52c41a);
  font-weight: 600;
}

.text-danger {
  color: var(--danger-color, #ff4d4f);
  font-weight: 600;
}

/* 加载 & 错误 */
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 0;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--border-color, #f0f0f0);
  border-top-color: var(--primary-color, #667eea);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  margin-top: 12px;
  color: var(--text-secondary, #999);
}

.error-message {
  text-align: center;
  padding: 40px 0;
  color: var(--danger-color, #ff4d4f);
}

.error-message .btn {
  margin-top: 12px;
  padding: 8px 24px;
  border: none;
  border-radius: 6px;
  background: var(--primary-gradient, linear-gradient(135deg, #667eea, #764ba2));
  color: #fff;
  cursor: pointer;
  font-size: 14px;
}

/* 响应式 */
@media (max-width: 768px) {
  .heroes-page {
    padding: 12px;
  }

  .chart-box {
    height: 300px;
  }

  .chart-box-tall {
    height: 360px;
  }

  .hero-table {
    font-size: 12px;
  }

  .hero-avatar {
    width: 28px;
    height: 28px;
  }

  .hero-table th,
  .hero-table td {
    padding: 8px 6px;
  }
}
</style>
