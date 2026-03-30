<!--
 * Abilities.vue - 选手能力画像页面
 * 雷达图使用 Chart.js，柱状图使用 ECharts
 -->
<template>
  <div class="result-section abilities-page">
    <div class="result-header">
      <h1 class="result-title">🎯 选手能力画像</h1>
      <p class="result-subtitle">基于 KPL 官方数据的 12 维能力评估 · {{ seasonName }}</p>
    </div>

    <!-- 加载状态 -->
    <div class="loading" v-if="loading">
      <div class="loading-spinner"></div>
      <div class="loading-text">正在加载能力数据...</div>
    </div>

    <!-- 错误状态 -->
    <div class="error-message" v-else-if="error">
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="loadData">重试</button>
    </div>

    <!-- 数据内容 -->
    <div v-else-if="abilityData">
      <!-- 综合评分卡片 -->
      <div class="rating-overview">
        <div class="rating-main">
          <div class="rating-score">{{ abilityData.overall_rating }}</div>
          <div class="rating-label">综合评分</div>
        </div>
        <div class="rating-details">
          <div class="rating-item">
            <span class="rating-value">{{ abilityData.overall_rank }}</span>
            <span class="rating-desc">联盟排名</span>
          </div>
          <div class="rating-item">
            <span class="rating-value" :class="{ 'text-primary': abilityData.position_rank < 11 }">
              {{ abilityData.position_rank }}
            </span>
            <span class="rating-desc">{{ abilityData.player_position }}排名</span>
          </div>
        </div>
      </div>

      <!-- 雷达图 (Chart.js) -->
      <div class="chart-container">
        <div class="chart-title">能力雷达图</div>
        <canvas ref="radarChartRef" class="radar-canvas"></canvas>
      </div>

      <!-- 能力维度详情 -->
      <div class="ability-bars">
        <div class="section-title">能力维度详情</div>
        <div class="ability-bar-list">
          <div class="ability-bar-item" v-for="item in abilityDimensions" :key="item.key">
            <div class="ability-bar-header">
              <span class="ability-name">{{ item.label }}</span>
              <span class="ability-score">{{ item.value }}</span>
            </div>
            <div class="ability-bar-track">
              <div
                class="ability-bar-fill"
                :style="{ width: item.value + '%', background: getBarColor(item.value) }"
              ></div>
              <div class="ability-bar-avg" :style="{ left: item.avg + '%' }" :title="`位置平均: ${item.avg}`"></div>
            </div>
            <div class="ability-bar-meta">
              <span>联盟 #{{ item.overallRank }}</span>
              <span>{{ abilityData.player_position }} #{{ item.positionRank }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 位置对比图 (Chart.js) -->
      <div class="chart-container">
        <div class="chart-title">vs {{ abilityData.player_position }}平均</div>
        <canvas ref="compareChartRef" class="compare-canvas"></canvas>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onUnmounted } from 'vue';
import {
  Chart,
  RadarController,
  RadialLinearScale,
  LineElement,
  PointElement,
  Filler,
  BarController,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from 'chart.js';
import { getPlayerAbilities, getSeasonNameMap, DEFAULT_SEASON } from '../api/github-data';

// 注册 Chart.js 组件
Chart.register(
  RadarController,
  RadialLinearScale,
  LineElement,
  PointElement,
  Filler,
  BarController,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
);

const loading = ref(false);
const error = ref(null);
const abilityData = ref(null);
const positionAverages = ref(null);
const radarChartRef = ref(null);
const compareChartRef = ref(null);
const seasonName = ref(DEFAULT_SEASON);

let radarChart = null;
let compareChart = null;

// 能力维度配置
const DIMENSION_MAP = {
  damage_output: { label: '输出能力' },
  teamfight: { label: '团战能力' },
  initiation: { label: '开团能力' },
  early_game: { label: '前期能力' },
  mid_game: { label: '中期能力' },
  late_game: { label: '后期能力' },
  map_control: { label: '地图控制' },
  invasion_ability: { label: '入侵能力' },
  support_ability: { label: '支援能力' },
  economy: { label: '经济能力' },
  tankiness: { label: '抗伤能力' },
  durability: { label: '生存能力' },
};

const DIMENSION_ORDER = [
  'damage_output',
  'teamfight',
  'initiation',
  'early_game',
  'mid_game',
  'late_game',
  'map_control',
  'invasion_ability',
  'support_ability',
  'economy',
  'tankiness',
  'durability',
];

const abilityDimensions = computed(() => {
  if (!abilityData.value) return [];
  return DIMENSION_ORDER.map((key) => {
    const cfg = DIMENSION_MAP[key];
    const avg = positionAverages.value?.[key] || 0;
    return {
      key,
      label: cfg.label,
      value: abilityData.value[key] || 0,
      avg,
      overallRank: abilityData.value[`${key}_overall_rank`] || '-',
      positionRank: abilityData.value[`${key}_position_rank`] || '-',
    };
  });
});

function getBarColor(value) {
  if (value >= 90) return 'linear-gradient(90deg, #ff6b6b, #ee5a24)';
  if (value >= 80) return 'linear-gradient(90deg, #feca57, #ff9f43)';
  if (value >= 70) return 'linear-gradient(90deg, #48dbfb, #0abde3)';
  if (value >= 60) return 'linear-gradient(90deg, #1dd1a1, #10ac84)';
  return 'linear-gradient(90deg, #c8d6e5, #8395a7)';
}

async function loadData() {
  loading.value = true;
  error.value = null;
  try {
    const [abilitiesRes, nameMap] = await Promise.all([
      getPlayerAbilities(DEFAULT_SEASON),
      getSeasonNameMap(),
    ]);
    abilityData.value = abilitiesRes.data;
    positionAverages.value = abilitiesRes.position_averages?.[abilitiesRes.data?.player_position] || null;
    seasonName.value = nameMap[DEFAULT_SEASON] || DEFAULT_SEASON;
  } catch (err) {
    console.error('加载能力数据失败:', err);
    error.value = `加载失败：${err.message}`;
  } finally {
    loading.value = false;
    await nextTick();
    setTimeout(() => {
      renderRadarChart();
      renderCompareChart();
    }, 50);
  }
}

// Chart.js 雷达图
function renderRadarChart() {
  if (!radarChartRef.value || !abilityData.value) return;

  if (radarChart) radarChart.destroy();

  const labels = DIMENSION_ORDER.map((k) => DIMENSION_MAP[k].label);
  const playerValues = DIMENSION_ORDER.map((k) => abilityData.value[k] || 0);
  const avgValues = DIMENSION_ORDER.map((k) => positionAverages.value?.[k] || 0);

  radarChart = new Chart(radarChartRef.value, {
    type: 'radar',
    data: {
      labels,
      datasets: [
        {
          label: abilityData.value.player_name,
          data: playerValues,
          backgroundColor: 'rgba(67, 97, 238, 0.2)',
          borderColor: '#4361ee',
          borderWidth: 2.5,
          pointBackgroundColor: '#4361ee',
          pointBorderColor: '#fff',
          pointBorderWidth: 1,
          pointRadius: 4,
          pointHoverRadius: 6,
          fill: true,
        },
        {
          label: `${abilityData.value.player_position}平均`,
          data: avgValues,
          backgroundColor: 'rgba(173, 181, 189, 0.1)',
          borderColor: '#adb5bd',
          borderWidth: 1.5,
          borderDash: [5, 5],
          pointBackgroundColor: '#adb5bd',
          pointBorderColor: '#fff',
          pointBorderWidth: 1,
          pointRadius: 3,
          pointHoverRadius: 5,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        r: {
          min: 0,
          max: 100,
          ticks: {
            stepSize: 20,
            font: { size: 10 },
            color: '#999',
            backdropColor: 'transparent',
          },
          pointLabels: {
            font: { size: 12, weight: '500' },
            color: '#555',
          },
          grid: {
            color: 'rgba(0,0,0,0.06)',
          },
          angleLines: {
            color: 'rgba(0,0,0,0.06)',
          },
        },
      },
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            padding: 20,
            usePointStyle: true,
            font: { size: 13 },
          },
        },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const idx = ctx.dataIndex;
              const pv = playerValues[idx];
              const av = avgValues[idx];
              const diff = pv - av;
              const sign = diff >= 0 ? '+' : '';
              return `${ctx.dataset.label}: ${ctx.raw} (均${av}, ${sign}${diff})`;
            },
          },
        },
      },
    },
  });
}

// Chart.js 柱状图（位置对比）
function renderCompareChart() {
  if (!compareChartRef.value || !abilityData.value || !positionAverages.value) return;
  if (compareChart) compareChart.destroy();

  const labels = DIMENSION_ORDER.map((k) => DIMENSION_MAP[k].label);
  const playerValues = DIMENSION_ORDER.map((k) => abilityData.value[k] || 0);
  const avgValues = DIMENSION_ORDER.map((k) => positionAverages.value[k] || 0);

  compareChart = new Chart(compareChartRef.value, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: abilityData.value.player_name,
          data: playerValues,
          backgroundColor: 'rgba(67, 97, 238, 0.75)',
          borderColor: '#4361ee',
          borderWidth: 1,
          borderRadius: 4,
        },
        {
          label: '位置平均',
          data: avgValues,
          backgroundColor: 'rgba(222, 226, 230, 0.8)',
          borderColor: '#dee2e6',
          borderWidth: 1,
          borderRadius: 4,
        },
      ],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          max: 100,
          ticks: { font: { size: 11 } },
          grid: { color: 'rgba(0,0,0,0.04)' },
        },
        y: {
          grid: { display: false },
          ticks: { font: { size: 11 } },
        },
      },
      plugins: {
        legend: {
          position: 'top',
          labels: { usePointStyle: true, padding: 16, font: { size: 13 } },
        },
      },
    },
  });
}

onMounted(() => {
  loadData();
});

onUnmounted(() => {
  radarChart?.destroy();
  compareChart?.destroy();
});
</script>

<style scoped>
.abilities-page {
  /* padding: 20px; */
}

.rating-overview {
  display: flex;
  align-items: center;
  gap: 40px;
  background: var(--bg-card);
  border-radius: var(--border-radius-lg);
  padding: 30px;
  margin-bottom: var(--spacing-xl);
  box-shadow: var(--shadow-sm);
}

.rating-main {
  text-align: center;
  min-width: 120px;
}

.rating-score {
  font-size: 56px;
  font-weight: var(--font-weight-bold);
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.1;
}

.rating-label {
  font-size: var(--font-size-sm);
  color: var(--gray-500);
  margin-top: 4px;
}

.rating-details {
  display: flex;
  gap: 30px;
}

.rating-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.rating-value {
  font-size: var(--font-size-xxxl);
  font-weight: var(--font-weight-bold);
}

.rating-desc {
  font-size: var(--font-size-xs);
  color: var(--gray-500);
}

.text-primary {
  color: var(--primary-medium);
}

.chart-container {
  background: var(--bg-card);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
  box-shadow: var(--shadow-sm);
}

.chart-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--gray-700);
  margin-bottom: var(--spacing-md);
}

.compare-canvas {
  width: 100% !important;
  height: 420px !important;
}

.radar-canvas {
  width: 100% !important;
  max-height: 420px;
}

.ability-bars {
  margin-bottom: var(--spacing-xl);
}

.ability-bar-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  background: var(--bg-card);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-sm);
}

.ability-bar-item {
  padding: var(--spacing-xs) 0;
}

.ability-bar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.ability-name {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--gray-700);
}

.ability-score {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--gray-800);
}

.ability-bar-track {
  position: relative;
  height: 10px;
  background: var(--gray-100);
  border-radius: 5px;
  overflow: visible;
}

.ability-bar-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.8s ease;
}

.ability-bar-avg {
  position: absolute;
  top: -3px;
  width: 2px;
  height: 16px;
  background: var(--gray-400);
  border-radius: 1px;
  transform: translateX(-1px);
}

.ability-bar-avg::after {
  content: '均';
  position: absolute;
  top: -14px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 9px;
  color: var(--gray-400);
}

.ability-bar-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  font-size: var(--font-size-xs);
  color: var(--gray-400);
}

.section-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--gray-700);
  margin-bottom: var(--spacing-md);
}

@media (max-width: 768px) {
  .rating-overview {
    flex-direction: column;
    gap: 20px;
  }
  .chart-box {
    height: 350px;
  }
  .radar-canvas {
    max-height: 350px;
  }
}
</style>
