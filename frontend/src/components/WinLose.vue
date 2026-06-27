<!--
 * WinLose.vue - 胜负对比分析页面
 * 图表使用 Chart.js
 -->
<template>
  <div class="result-section winlose-page">
    <div class="result-header">
      <h1 class="result-title">⚔️ 胜负对比分析</h1>
      <p class="result-subtitle">赢和输的时候，无言的表现有什么不同？ · {{ seasonName }}</p>
    </div>

    <div class="loading" v-if="loading">
      <div class="loading-spinner"></div>
      <div class="loading-text">正在加载数据...</div>
    </div>

    <div class="error-message" v-else-if="error">
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="loadData">重试</button>
    </div>

    <div v-else-if="winData && loseData && !hasData" class="empty-state">
      <div class="empty-icon">📊</div>
      <p class="empty-text">该赛季暂无胜负数据</p>
      <p class="empty-hint">数据正在收集中，请稍后再来...</p>
    </div>

    <div v-else-if="winData && loseData && hasData">
      <!-- 概览卡片 -->
      <div class="summary-cards winlose-overview">
        <div class="summary-card">
          <div class="summary-card-value win">{{ overview.totalWins }}</div>
          <div class="summary-card-label">胜利对局</div>
        </div>
        <div class="summary-card">
          <div class="summary-card-value lose">{{ overview.totalLosses }}</div>
          <div class="summary-card-label">失败对局</div>
        </div>
        <div class="summary-card">
          <div class="summary-card-value">{{ overview.totalMatches }}</div>
          <div class="summary-card-label">总对局数</div>
        </div>
        <div class="summary-card">
          <div class="summary-card-value" :class="overview.winRateClass">{{ overview.winRate }}</div>
          <div class="summary-card-label">胜率</div>
        </div>
      </div>

      <!-- KDA 对比 -->
      <div class="compare-section">
        <div class="section-title">📊 KDA 对比</div>
        <div class="compare-grid">
          <CompareCard label="场均击杀" :win="winData.avg_kills" :lose="loseData.avg_kills" />
          <CompareCard label="场均死亡" :win="winData.avg_deaths" :lose="loseData.avg_deaths" reverse />
          <CompareCard label="场均助攻" :win="winData.avg_assists" :lose="loseData.avg_assists" />
          <CompareCard label="场均 KDA" :win="winData.avg_kda" :lose="loseData.avg_kda" />
        </div>
      </div>

      <!-- 伤害对比 -->
      <div class="compare-section">
        <div class="section-title">🔥 伤害对比</div>
        <div class="chart-container">
          <canvas ref="damageChartRef" class="chart-canvas"></canvas>
        </div>
      </div>

      <!-- 经济对比 -->
      <div class="compare-section">
        <div class="section-title">💰 经济对比</div>
        <div class="chart-container">
          <canvas ref="economyChartRef" class="chart-canvas"></canvas>
        </div>
      </div>

      <!-- 团战对比 -->
      <div class="compare-section">
        <div class="section-title">🎯 团战对比</div>
        <div class="compare-grid">
          <CompareCard
            label="大型团战平均伤害"
            :win="winData.avg_big_fight_damage"
            :lose="loseData.avg_big_fight_damage"
          />
          <CompareCard
            label="大型团战平均承伤"
            :win="winData.avg_big_fight_damage_taken"
            :lose="loseData.avg_big_fight_damage_taken"
          />
          <CompareCard
            label="大型团战核心伤害"
            :win="winData.avg_big_fight_carry_damage"
            :lose="loseData.avg_big_fight_carry_damage"
          />
          <CompareCard
            label="大型团战核心击杀"
            :win="winData.avg_big_fight_carry_kills"
            :lose="loseData.avg_big_fight_carry_kills"
          />
        </div>
      </div>

      <!-- 资源控制 -->
      <div class="compare-section">
        <div class="section-title">🗺️ 资源控制</div>
        <div class="compare-grid">
          <CompareCard label="平均蓝 buff" :win="winData.avg_blue_buff" :lose="loseData.avg_blue_buff" />
          <CompareCard label="平均红 buff" :win="winData.avg_red_buff" :lose="loseData.avg_red_buff" />
          <CompareCard label="平均入侵次数" :win="winData.avg_invasion_jungle" :lose="loseData.avg_invasion_jungle" />
          <CompareCard
            label="平均入侵时长"
            :win="winData.avg_invasion_duration"
            :lose="loseData.avg_invasion_duration"
          />
          <CompareCard label="平均河道时长" :win="winData.avg_river_duration" :lose="loseData.avg_river_duration" />
          <CompareCard label="平均控制时长" :win="winData.avg_control_duration" :lose="loseData.avg_control_duration" />
        </div>
      </div>

      <!-- 10分钟数据 -->
      <div class="compare-section">
        <div class="section-title">⏱️ 10 分钟数据</div>
        <div class="compare-grid">
          <CompareCard label="10分钟平均伤害" :win="winData.avg_ten_min_damage" :lose="loseData.avg_ten_min_damage" />
          <CompareCard
            label="10分钟伤害占比"
            :win="winData.avg_damage_10min_ratio"
            :lose="loseData.avg_damage_10min_ratio"
          />
          <CompareCard label="10分钟平均经济" :win="winData.avg_economy_10min" :lose="loseData.avg_economy_10min" />
          <CompareCard
            label="10分钟经济差"
            :win="winData.avg_economy_diff_10min"
            :lose="loseData.avg_economy_diff_10min"
          />
        </div>
      </div>

      <!-- AI 洞察 / 关键洞察 -->
      <div class="compare-section">
        <InsightSection v-if="aiInsights" :sections="aiInsights.sections" filterId="win_lose" title="胜负洞察" />
        <template v-else>
          <div class="section-title">💡 关键洞察</div>
          <div class="insight-cards">
            <div class="insight-card" v-for="insight in insights" :key="insight.label">
              <div class="insight-icon">{{ insight.icon }}</div>
              <div class="insight-text">{{ insight.text }}</div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onUnmounted, watch } from 'vue';
import { Chart, BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js';
import { getPlayerWinStats, getPlayerLoseStats, getSeasonNameMap, getAiInsights, getInsights } from '../api/github-data';
import { useSeason } from '../composables/useSeason.js';
import CompareCard from './CompareCard.vue';
import InsightSection from './insights/InsightSection.vue';

const { selectedSeason, currentSeasonName, resolveCurrent } = useSeason();

Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

const loading = ref(false);
const error = ref(null);
const winData = ref(null);
const loseData = ref(null);
const damageChartRef = ref(null);
const economyChartRef = ref(null);
const seasonName = ref(currentSeasonName.value || '当前赛季');
const aiInsights = ref(null);

let damageChart = null;
let economyChart = null;

// 判断是否有实际数据
const hasData = computed(() => {
  if (!winData.value || !loseData.value) return false;
  const w = winData.value;
  const l = loseData.value;
  // 至少有一个有效数值字段才认为有数据
  return (w.total_matches > 0) || (l.total_matches > 0) || (w.avg_kills > 0) || (l.avg_kills > 0);
});

// 概览统计
const overview = computed(() => {
  const w = winData.value || {};
  const l = loseData.value || {};
  const totalWins = w.total_matches || 0;
  const totalLosses = l.total_matches || 0;
  const totalMatches = totalWins + totalLosses;
  const winRate = totalMatches > 0 ? ((totalWins / totalMatches) * 100).toFixed(1) + '%' : '-';
  const winRateNum = totalMatches > 0 ? (totalWins / totalMatches) * 100 : 0;
  const winRateClass = winRateNum >= 50 ? 'win' : 'lose';
  return { totalWins, totalLosses, totalMatches, winRate, winRateClass };
});

const insights = computed(() => {
  if (!winData.value || !loseData.value) return [];
  const w = winData.value;
  const l = loseData.value;
  const result = [];

  const kdaDiff = (w.avg_kda || 0) - (l.avg_kda || 0);
  if (kdaDiff > 0) {
    result.push({ icon: '📈', text: `获胜时 KDA 比失败时高 ${kdaDiff.toFixed(1)}，稳定性是关键` });
  }

  const deathDiff = (l.avg_deaths || 0) - (w.avg_deaths || 0);
  if (deathDiff > 0.5) {
    result.push({ icon: '💀', text: `失败时场均死亡多 ${deathDiff.toFixed(1)} 次，减少失误能显著提升胜率` });
  }

  if ((w.avg_economy_diff_10min || 0) > 0 && (l.avg_economy_diff_10min || 0) < 0) {
    result.push({
      icon: '💰',
      text: `获胜时 10 分钟经济领先 ${Math.round(w.avg_economy_diff_10min)}，失败时经济落后 ${Math.round(Math.abs(l.avg_economy_diff_10min))}`,
    });
  }

  const fightDiff = (w.avg_big_fight_damage || 0) - (l.avg_big_fight_damage || 0);
  if (fightDiff > 0) {
    result.push({
      icon: '🔥',
      text: `获胜时大型团战平均伤害多 ${Math.round(fightDiff).toLocaleString()}，团战表现直接影响胜负`,
    });
  }

  if (result.length === 0) {
    result.push({ icon: '📊', text: '数据持续积累中，更多分析即将到来...' });
  }

  return result;
});

async function loadData() {
  loading.value = true;
  error.value = null;
  const season = selectedSeason.value;
  try {
    const [winRes, loseRes, nameMap] = await Promise.all([
      getPlayerWinStats(season),
      getPlayerLoseStats(season),
      getSeasonNameMap(),
    ]);
    winData.value = (winRes.data && winRes.data[0]) || {};
    loseData.value = (loseRes.data && loseRes.data[0]) || {};
    seasonName.value = nameMap[season] || currentSeasonName.value || season;
  } catch (err) {
    console.error('加载胜负数据失败:', err);
    error.value = `加载失败：${err.message}`;
  } finally {
    loading.value = false;
    await nextTick();
    setTimeout(() => {
      renderDamageChart();
      renderEconomyChart();
    }, 50);
  }
}

function renderDamageChart() {
  if (!damageChartRef.value || !winData.value || !loseData.value) return;
  if (damageChart) damageChart.destroy();

  const labels = ['场均英雄伤害', '场均承伤', '场均治疗量', '团战平均伤害', '团战平均承伤'];
  const damageFields = ['avg_hurt_to_hero', 'avg_be_hurt_by_hero', 'avg_heal_count', 'avg_big_fight_damage', 'avg_big_fight_damage_taken'];

  damageChart = new Chart(damageChartRef.value, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: '胜利',
          data: damageFields.map(f => winData.value[f] || 0),
          backgroundColor: 'rgba(40, 167, 69, 0.75)',
          borderColor: '#28a745',
          borderWidth: 1,
          borderRadius: 4,
        },
        {
          label: '失败',
          data: damageFields.map(f => loseData.value[f] || 0),
          backgroundColor: 'rgba(220, 53, 69, 0.75)',
          borderColor: '#dc3545',
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
          beginAtZero: true,
          ticks: {
            callback: (v) => v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v,
            font: { size: 11 },
          },
          grid: { color: 'rgba(0,0,0,0.04)' },
        },
        y: { grid: { display: false }, ticks: { font: { size: 12 } } },
      },
      plugins: {
        legend: {
          position: 'top',
          labels: { usePointStyle: true, padding: 16, font: { size: 12 } },
        },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const val = ctx.raw;
              const field = damageFields[ctx.dataIndex];
              const other = ctx.datasetIndex === 0
                ? (loseData.value[field] || 0)
                : (winData.value[field] || 0);
              const diff = val - other;
              const pct = other > 0 ? ((diff / other) * 100).toFixed(1) : '—';
              return `${ctx.dataset.label}: ${val.toLocaleString()} (${diff >= 0 ? '+' : ''}${pct}%)`;
            },
          },
        },
      },
    },
  });
}

function renderEconomyChart() {
  if (!economyChartRef.value || !winData.value || !loseData.value) return;
  if (economyChart) economyChart.destroy();

  const labels = ['场均经济', '10分钟经济', '10分钟经济差', '分均经济'];
  const economyFields = ['avg_gold', 'avg_economy_10min', 'avg_economy_diff_10min', null]; // null = computed

  economyChart = new Chart(economyChartRef.value, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: '胜利',
          data: [
            winData.value.avg_gold || 0,
            winData.value.avg_economy_10min || 0,
            winData.value.avg_economy_diff_10min || 0,
            Math.round((winData.value.avg_gold || 0) / ((winData.value.avg_game_duration || 600) / 60)),
          ],
          backgroundColor: 'rgba(40, 167, 69, 0.75)',
          borderColor: '#28a745',
          borderWidth: 1,
          borderRadius: 4,
        },
        {
          label: '失败',
          data: [
            loseData.value.avg_gold || 0,
            loseData.value.avg_economy_10min || 0,
            loseData.value.avg_economy_diff_10min || 0,
            Math.round((loseData.value.avg_gold || 0) / ((loseData.value.avg_game_duration || 600) / 60)),
          ],
          backgroundColor: 'rgba(220, 53, 69, 0.75)',
          borderColor: '#dc3545',
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
          ticks: {
            callback: (v) => {
              if (Math.abs(v) >= 1000) return (v / 1000).toFixed(1) + 'k';
              return v;
            },
            font: { size: 11 },
          },
          grid: { color: 'rgba(0,0,0,0.04)' },
        },
        y: { grid: { display: false }, ticks: { font: { size: 12 } } },
      },
      plugins: {
        legend: {
          position: 'top',
          labels: { usePointStyle: true, padding: 16, font: { size: 12 } },
        },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const val = ctx.raw;
              const other = ctx.datasetIndex === 0
                ? (loseData.value[economyFields[ctx.dataIndex]] || 0)
                : (winData.value[economyFields[ctx.dataIndex]] || 0);
              // 分均经济是计算值，不做对比
              if (ctx.dataIndex === 3) {
                return `${ctx.dataset.label}: ${val.toLocaleString()}/min`;
              }
              const diff = val - other;
              const pct = other > 0 ? ((diff / other) * 100).toFixed(1) : '—';
              return `${ctx.dataset.label}: ${val.toLocaleString()} (${diff >= 0 ? '+' : ''}${pct}%)`;
            },
          },
        },
      },
    },
  });
}

onMounted(async () => {
  loadData();
  try {
    aiInsights.value = await getAiInsights(selectedSeason.value);
    if (!aiInsights.value) {
      aiInsights.value = await getInsights(selectedSeason.value);
    }
  } catch { /* insights unavailable */ }
});

watch(selectedSeason, async () => {
  await resolveCurrent();
  loadData();
  try {
    aiInsights.value = await getAiInsights(selectedSeason.value);
    if (!aiInsights.value) {
      aiInsights.value = await getInsights(selectedSeason.value);
    }
  } catch { /* insights unavailable */ }
});

onUnmounted(() => {
  damageChart?.destroy();
  economyChart?.destroy();
});
</script>

<style scoped>
.winlose-page {
  /* padding: 20px; */
}

.compare-section {
  margin-bottom: var(--spacing-xl);
}

.section-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--gray-700);
  margin-bottom: var(--spacing-md);
}

.compare-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--spacing-md);
}

.chart-container {
  background: var(--bg-card);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-sm);
}

.chart-canvas {
  width: 100% !important;
  height: 320px !important;
}

.insight-cards {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.insight-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  background: var(--bg-card);
  border-radius: var(--border-radius-md);
  padding: var(--spacing-md) var(--spacing-lg);
  box-shadow: var(--shadow-sm);
  border-left: 4px solid var(--primary-medium);
}

.insight-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.insight-text {
  font-size: var(--font-size-base);
  color: var(--gray-700);
  line-height: 1.5;
}

@media (max-width: 768px) {
  .compare-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .chart-canvas {
    height: 260px !important;
  }
}

@media (max-width: 480px) {
  .compare-grid {
    grid-template-columns: 1fr;
  }
  .chart-canvas {
    height: 220px !important;
  }
}

.winlose-overview {
  margin-bottom: var(--spacing-xl);
}

.empty-state {
  text-align: center;
  padding: var(--spacing-xxxl) var(--spacing-lg);
  color: var(--gray-500);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: var(--spacing-md);
}

.empty-text {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--gray-600);
  margin-bottom: var(--spacing-sm);
}

.empty-hint {
  font-size: var(--font-size-sm);
  color: var(--gray-400);
}
</style>
