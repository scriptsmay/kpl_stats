<template>
  <div class="result-section abilities-page">
    <div class="result-header">
      <h1 class="result-title">🎯 选手能力画像</h1>
      <p class="result-subtitle">基于 KPL 官方数据的 12 维能力评估</p>
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
            <!-- <span
              v-if="abilityData.overall_rank_change"
              :class="['rank-change', abilityData.overall_rank_trend === 'UP' ? 'up' : 'down']"
            >
              {{ abilityData.overall_rank_trend === 'UP' ? '↑' : '↓' }}{{ Math.abs(abilityData.overall_rank_change) }}
            </span> -->
          </div>
          <div class="rating-item">
            <span class="rating-value" :class="{ 'text-primary': abilityData.position_rank < 11 }">{{
              abilityData.position_rank
            }}</span>
            <span class="rating-desc">{{ abilityData.player_position }}排名</span>
            <!-- <span
              v-if="abilityData.position_rank_change"
              :class="['rank-change', abilityData.position_rank_trend === 'UP' ? 'up' : 'down']"
            >
              {{ abilityData.position_rank_trend === 'UP' ? '↑' : '↓' }}{{ Math.abs(abilityData.position_rank_change) }}
            </span> -->
          </div>
        </div>
      </div>

      <!-- 雷达图 -->
      <div class="chart-container">
        <div class="chart-title">能力雷达图</div>
        <div ref="radarChartRef" class="chart-box"></div>
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

      <!-- 位置对比图 -->
      <div class="chart-container">
        <div class="chart-title">vs {{ abilityData.player_position }}平均</div>
        <div ref="compareChartRef" class="chart-box"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue';
import * as echarts from 'echarts';
import { getPlayerAbilities, DEFAULT_SEASON } from '../api/github-data';

const loading = ref(false);
const error = ref(null);
const abilityData = ref(null);
const positionAverages = ref(null);
const radarChartRef = ref(null);
const compareChartRef = ref(null);

let radarChart = null;
let compareChart = null;

// 能力维度配置
const DIMENSION_MAP = {
  damage_output: { label: '输出能力', icon: '⚔️' },
  teamfight: { label: '团战能力', icon: '🔥' },
  initiation: { label: '开团能力', icon: '🎯' },
  early_game: { label: '前期能力', icon: '🌅' },
  mid_game: { label: '中期能力', icon: '☀️' },
  late_game: { label: '后期能力', icon: '🌙' },
  map_control: { label: '地图控制', icon: '🗺️' },
  invasion_ability: { label: '入侵能力', icon: '🏴' },
  support_ability: { label: '支援能力', icon: '🤝' },
  economy: { label: '经济能力', icon: '💰' },
  tankiness: { label: '抗伤能力', icon: '🛡️' },
  durability: { label: '生存能力', icon: '❤️' },
};

// 维度排序（雷达图用）
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

// 能力维度列表（用于柱状图展示）
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

// 颜色映射
function getBarColor(value) {
  if (value >= 90) return 'linear-gradient(90deg, #ff6b6b, #ee5a24)';
  if (value >= 80) return 'linear-gradient(90deg, #feca57, #ff9f43)';
  if (value >= 70) return 'linear-gradient(90deg, #48dbfb, #0abde3)';
  if (value >= 60) return 'linear-gradient(90deg, #1dd1a1, #10ac84)';
  return 'linear-gradient(90deg, #c8d6e5, #8395a7)';
}

// 加载数据
async function loadData() {
  loading.value = true;
  error.value = null;
  try {
    const res = await getPlayerAbilities(DEFAULT_SEASON);
    abilityData.value = res.data;
    positionAverages.value = res.position_averages?.[res.data?.player_position] || null;
  } catch (err) {
    console.error('加载能力数据失败:', err);
    error.value = `加载失败：${err.message}`;
  } finally {
    loading.value = false;
    // 等 DOM 渲染完成后再初始化图表
    await nextTick();
    setTimeout(() => {
      renderRadarChart();
      renderCompareChart();
    }, 50);
  }
}

// 渲染雷达图
function renderRadarChart() {
  if (!radarChartRef.value || !abilityData.value) return;

  if (radarChart) radarChart.dispose();
  radarChart = echarts.init(radarChartRef.value);

  const playerValues = DIMENSION_ORDER.map((k) => abilityData.value[k] || 0);
  const avgValues = DIMENSION_ORDER.map((k) => positionAverages.value?.[k] || 0);
  const indicators = DIMENSION_ORDER.map((k) => ({
    name: DIMENSION_MAP[k].label,
    max: 100,
  }));

  radarChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const lines = indicators.map((ind, i) => {
          const pv = params.value[i];
          const av = avgValues[i];
          const diff = pv - av;
          const sign = diff >= 0 ? '+' : '';
          return `${ind.name}: ${pv} (均${av}, ${sign}${diff})`;
        });
        return `<strong>${params.name}</strong><br/>${lines.join('<br/>')}`;
      },
    },
    legend: {
      data: [abilityData.value.player_name, `${abilityData.value.player_position}平均`],
      bottom: 0,
      textStyle: { fontSize: 14 },
    },
    radar: {
      indicator: indicators,
      radius: '76%',
      center: ['50%', '48%'],
      splitNumber: 10,
      shape: 'polygon',
      axisName: {
        color: '#666',
        fontSize: 11,
      },
      splitArea: {
        areaStyle: {
          color: [
            'rgba(30,60,114,0.01)',
            'rgba(30,60,114,0.01)',
            'rgba(30,60,114,0.01)',
            'rgba(30,60,114,0.01)',
            'rgba(30,60,114,0.01)',
          ],
        },
      },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: playerValues,
            name: abilityData.value.player_name,
            symbol: 'circle',
            symbolSize: 5,
            lineStyle: { color: '#4361ee', width: 3 },
            areaStyle: { color: 'rgba(42,82,152,0.25)' },
            itemStyle: { color: '#4361ee' },
          },
          {
            value: avgValues,
            name: `${abilityData.value.player_position}平均`,
            symbol: 'circle',
            symbolSize: 3,
            lineStyle: { color: '#adb5bd', width: 1, type: 'dashed' },
            areaStyle: { color: 'rgba(173,181,189,0.1)' },
            itemStyle: { color: '#adb5bd' },
          },
        ],
      },
    ],
  });

  // 响应式
  window.addEventListener('resize', () => radarChart?.resize());
}

// 渲染位置对比柱状图
function renderCompareChart() {
  if (!compareChartRef.value || !abilityData.value || !positionAverages.value) return;

  if (compareChart) compareChart.dispose();
  compareChart = echarts.init(compareChartRef.value);

  const labels = DIMENSION_ORDER.map((k) => DIMENSION_MAP[k].label);
  const playerValues = DIMENSION_ORDER.map((k) => abilityData.value[k] || 0);
  const avgValues = DIMENSION_ORDER.map((k) => positionAverages.value[k] || 0);

  compareChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    legend: {
      data: [abilityData.value.player_name, '位置平均'],
      bottom: 0,
      textStyle: { fontSize: 14 },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '12%',
      top: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'value',
      max: 100,
      axisLabel: { fontSize: 11 },
    },
    yAxis: {
      type: 'category',
      data: labels,
      axisLabel: { fontSize: 11 },
    },
    series: [
      {
        name: abilityData.value.player_name,
        type: 'bar',
        data: playerValues,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#4361ee' },
            { offset: 1, color: '#2a5298' },
          ]),
          borderRadius: [0, 4, 4, 0],
        },
        barGap: '10%',
      },
      {
        name: '位置平均',
        type: 'bar',
        data: avgValues,
        itemStyle: {
          color: '#dee2e6',
          borderRadius: [0, 4, 4, 0],
        },
      },
    ],
  });

  window.addEventListener('resize', () => compareChart?.resize());
}

onMounted(() => {
  loadData();
});
</script>

<style scoped>
.abilities-page {
  max-width: 1000px;
  margin: 0 auto;
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
  /* color: var(--gray-800); */
}

.rating-desc {
  font-size: var(--font-size-xs);
  color: var(--gray-500);
}

.rating-total {
  font-size: var(--font-size-sm);
  color: var(--gray-400);
}

.rank-change {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-bold);
  padding: 1px 6px;
  border-radius: 4px;
}

.rank-change.up {
  color: var(--success-color);
  background: var(--success-bg);
}

.rank-change.down {
  color: var(--danger-color);
  background: var(--danger-bg);
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

.chart-box {
  width: 100%;
  height: 420px;
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
}
</style>
