<!--
 * Heroes.vue - 英雄池分析页面
 * 展示选手（KSG.无言）的英雄使用数据与联盟英雄胜率对比
 * 图表使用 Chart.js
 -->
<template>
  <div class="result-section heroes-page">
    <div class="result-header">
      <h1 class="result-title">⚔️ 英雄池分析</h1>
      <p class="result-subtitle">对抗路选手英雄使用数据与联盟胜率对比 · {{ seasonName }}</p>
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
        <canvas ref="barChartRef" class="bar-canvas"></canvas>
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
        <canvas ref="compareChartRef" class="bar-canvas"></canvas>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onUnmounted } from 'vue';
import { Chart, BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend, Colors } from 'chart.js';
import { getPlayerCareer, getHeroWinRate, getSeasonNameMap, DEFAULT_SEASON } from '../api/github-data';

// 注册 Chart.js 组件
Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend, Colors);
// Chart.register(Colors);

// 状态
const loading = ref(false);
const error = ref(null);
const heroStats = ref([]);
const leagueHeroes = ref([]);
const seasonName = ref(DEFAULT_SEASON);

// 图表引用
const barChartRef = ref(null);
const compareChartRef = ref(null);
let barChart = null;
let compareChart = null;

// 英雄头像 URL
const heroAvatar = (id) => `https://game.gtimg.cn/images/yxzj/img201606/heroimg/${id}/${id}.jpg`;

const handleAvatarError = (e) => {
  e.target.style.display = 'none';
};

// ====== 计算属性 ======

const totalMatches = computed(() => heroStats.value.reduce((sum, h) => sum + (h.total_matches || 0), 0));

const totalWins = computed(() => heroStats.value.reduce((sum, h) => sum + (h.win_matches || 0), 0));

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

const heroStatsSorted = computed(() => [...heroStats.value].sort((a, b) => b.total_matches - a.total_matches));

const winRateClass = (rate) => {
  const v = parseFloat(rate);
  if (v >= 60) return 'text-success';
  if (v < 45) return 'text-danger';
  return '';
};

const compareData = computed(() => {
  if (!heroStats.value.length || !leagueHeroes.value.length) return [];
  const leagueMap = {};
  leagueHeroes.value.forEach((h) => {
    leagueMap[h.hero_id] = h;
  });
  return heroStats.value
    .filter((h) => leagueMap[h.hero_id])
    .map((h) => ({
      hero_name: h.hero_name,
      player_rate: parseFloat(h.win_rate),
      league_rate: parseFloat(leagueMap[h.hero_id].win_rate),
      total_matches: h.total_matches,
    }))
    .sort((a, b) => b.total_matches - a.total_matches)
    .slice(0, 15);
});

// ====== 数据加载 ======

async function loadData() {
  loading.value = true;
  error.value = null;
  try {
    const [careerRes, leagueRes, nameMap] = await Promise.all([
      getPlayerCareer(),
      getHeroWinRate(DEFAULT_SEASON),
      getSeasonNameMap(),
    ]);

    // 从 career 数据中获取英雄列表
    if (careerRes.code === 200 && careerRes.data?.hero_stats) {
      heroStats.value = careerRes.data.hero_stats.map((h) => ({
        hero_id: h.hero_id,
        hero_name: h.hero_name,
        total_matches: h.battles,
        win_matches: h.wins,
        win_rate: h.win_rate,
      }));
    }

    // 联盟英雄胜率 — 筛选对抗路
    if (leagueRes.code === 200 && Array.isArray(leagueRes.data)) {
      leagueHeroes.value = leagueRes.data.filter((h) => h.position === '对抗路');
    }

    seasonName.value = nameMap[DEFAULT_SEASON] || DEFAULT_SEASON;
  } catch (err) {
    console.error('英雄池数据加载失败:', err);
    error.value = '数据加载失败，请检查网络后重试';
  } finally {
    loading.value = false;
    await nextTick();
    setTimeout(() => {
      initBarChart();
      if (compareData.value.length) {
        initCompareChart();
      }
    }, 50);
  }
}

// ====== Chart.js 图表 ======

function initBarChart() {
  if (!barChartRef.value || !heroStatsSorted.value.length) return;
  if (barChart) barChart.destroy();

  const top15 = heroStatsSorted.value.slice(0, 15);

  barChart = new Chart(barChartRef.value, {
    type: 'bar',
    data: {
      labels: top15.map((h) => h.hero_name),
      datasets: [
        {
          label: '使用次数',
          data: top15.map((h) => h.total_matches),
          backgroundColor: 'rgba(67, 97, 238, 0.7)',
          borderColor: '#4361ee',
          borderWidth: 1,
          borderRadius: 4,
          barThickness: 20,
        },
      ],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          beginAtZero: true,
          title: { display: true, text: '使用次数', font: { size: 12 } },
          grid: { color: 'rgba(0,0,0,0.04)' },
        },
        y: {
          grid: { display: false },
          ticks: { font: { size: 12 } },
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const hero = top15[ctx.dataIndex];
              return [
                `使用: ${hero.total_matches} 场`,
                `胜场: ${hero.win_matches} / 负场: ${hero.total_matches - hero.win_matches}`,
                `胜率: ${hero.win_rate}`,
              ];
            },
          },
        },
      },
    },
  });
}

function initCompareChart() {
  if (!compareChartRef.value || !compareData.value.length) return;
  if (compareChart) compareChart.destroy();

  const data = compareData.value;

  compareChart = new Chart(compareChartRef.value, {
    type: 'bar',
    data: {
      labels: data.map((d) => d.hero_name),
      datasets: [
        {
          label: '无言胜率',
          data: data.map((d) => d.player_rate),
          backgroundColor: 'rgba(78, 205, 196, 0.8)',
          borderColor: '#4ecdc4',
          borderWidth: 1,
          borderRadius: 4,
          barPercentage: 0.7,
        },
        {
          label: '联盟对抗路平均',
          data: data.map((d) => d.league_rate),
          backgroundColor: 'rgba(224, 224, 224, 0.8)',
          borderColor: '#ccc',
          borderWidth: 1,
          borderRadius: 4,
          barPercentage: 0.7,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { size: 11 }, maxRotation: 45 },
        },
        y: {
          beginAtZero: true,
          max: 100,
          title: { display: true, text: '胜率 (%)', font: { size: 12 } },
          grid: { color: 'rgba(0,0,0,0.04)' },
        },
      },
      plugins: {
        legend: {
          position: 'top',
          labels: { usePointStyle: true, padding: 16, font: { size: 12 } },
        },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const d = data[ctx.dataIndex];
              if (ctx.datasetIndex === 0) {
                return `无言胜率: ${d.player_rate}% (${d.total_matches} 场)`;
              }
              return `联盟对抗路平均: ${d.league_rate}%`;
            },
          },
        },
      },
    },
  });
}

onMounted(() => loadData());

onUnmounted(() => {
  barChart?.destroy();
  compareChart?.destroy();
});
</script>

<style scoped>
.heroes-page {
  /* padding: 20px; */
}

.chart-container {
  background: var(--bg-card, #fff);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: var(--shadow-sm);
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--gray-700);
}

.bar-canvas {
  width: 100% !important;
  height: 420px !important;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--gray-700);
}

.hero-table-section {
  background: var(--bg-card, #fff);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: var(--shadow-sm);
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
  color: var(--gray-500);
  background: var(--gray-50, #fafafa);
  position: sticky;
  top: 0;
}

.hero-table tbody tr:hover {
  background: #f5f7ff;
}

.col-rank {
  width: 48px;
  color: var(--gray-400);
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
  border: 2px solid #4361ee;
  flex-shrink: 0;
}

.hero-name {
  font-weight: 500;
  white-space: nowrap;
}

.text-success {
  color: var(--success-color);
  font-weight: 600;
}

.text-danger {
  color: var(--danger-color);
  font-weight: 600;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 0;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--gray-200);
  border-top-color: #4361ee;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  margin-top: 12px;
  color: var(--gray-400);
}

.error-message {
  text-align: center;
  padding: 40px 0;
  color: var(--danger-color);
}

.error-message .btn {
  margin-top: 12px;
  padding: 8px 24px;
  border: none;
  border-radius: 6px;
  background: var(--primary-gradient);
  color: #fff;
  cursor: pointer;
  font-size: 14px;
}

@media (max-width: 768px) {
  .heroes-page {
    padding: 12px;
  }
  .bar-canvas {
    height: 360px !important;
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
