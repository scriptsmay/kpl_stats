<!--
 * WinLose.vue - 胜负对比分析页面
 * 图表使用 Chart.js
 -->
<template>
  <div class="result-section winlose-page">
    <div class="result-header">
      <h1 class="result-title">⚔️ 胜负对比分析</h1>
      <p class="result-subtitle">赢和输的时候，无言的表现有什么不同？</p>
    </div>

    <div class="loading" v-if="loading">
      <div class="loading-spinner"></div>
      <div class="loading-text">正在加载数据...</div>
    </div>

    <div class="error-message" v-else-if="error">
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="loadData">重试</button>
    </div>

    <div v-else-if="winData && loseData">
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
          <CompareCard label="大型团战平均伤害" :win="winData.avg_big_fight_damage" :lose="loseData.avg_big_fight_damage" />
          <CompareCard label="大型团战平均承伤" :win="winData.avg_big_fight_damage_taken" :lose="loseData.avg_big_fight_damage_taken" />
          <CompareCard label="大型团战核心伤害" :win="winData.avg_big_fight_carry_damage" :lose="loseData.avg_big_fight_carry_damage" />
          <CompareCard label="大型团战核心击杀" :win="winData.avg_big_fight_carry_kills" :lose="loseData.avg_big_fight_carry_kills" />
        </div>
      </div>

      <!-- 资源控制 -->
      <div class="compare-section">
        <div class="section-title">🗺️ 资源控制</div>
        <div class="compare-grid">
          <CompareCard label="平均蓝 buff" :win="winData.avg_blue_buff" :lose="loseData.avg_blue_buff" />
          <CompareCard label="平均红 buff" :win="winData.avg_red_buff" :lose="loseData.avg_red_buff" />
          <CompareCard label="平均入侵次数" :win="winData.avg_invasion_jungle" :lose="loseData.avg_invasion_jungle" />
          <CompareCard label="平均入侵时长" :win="winData.avg_invasion_duration" :lose="loseData.avg_invasion_duration" />
          <CompareCard label="平均河道时长" :win="winData.avg_river_duration" :lose="loseData.avg_river_duration" />
          <CompareCard label="平均控制时长" :win="winData.avg_control_duration" :lose="loseData.avg_control_duration" />
        </div>
      </div>

      <!-- 10分钟数据 -->
      <div class="compare-section">
        <div class="section-title">⏱️ 10 分钟数据</div>
        <div class="compare-grid">
          <CompareCard label="10分钟平均伤害" :win="winData.avg_ten_min_damage" :lose="loseData.avg_ten_min_damage" />
          <CompareCard label="10分钟伤害占比" :win="winData.avg_damage_10min_ratio" :lose="loseData.avg_damage_10min_ratio" />
          <CompareCard label="10分钟平均经济" :win="winData.avg_economy_10min" :lose="loseData.avg_economy_10min" />
          <CompareCard label="10分钟经济差" :win="winData.avg_economy_diff_10min" :lose="loseData.avg_economy_diff_10min" />
        </div>
      </div>

      <!-- 关键洞察 -->
      <div class="compare-section">
        <div class="section-title">💡 关键洞察</div>
        <div class="insight-cards">
          <div class="insight-card" v-for="insight in insights" :key="insight.label">
            <div class="insight-icon">{{ insight.icon }}</div>
            <div class="insight-text">{{ insight.text }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onUnmounted } from 'vue';
import {
  Chart, BarController, BarElement, CategoryScale, LinearScale,
  Tooltip, Legend
} from 'chart.js';
import { getPlayerWinStats, getPlayerLoseStats, DEFAULT_SEASON } from '../api/github-data';
import CompareCard from './CompareCard.vue';

Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

const loading = ref(false);
const error = ref(null);
const winData = ref(null);
const loseData = ref(null);
const damageChartRef = ref(null);
const economyChartRef = ref(null);

let damageChart = null;
let economyChart = null;

const insights = computed(() => {
  if (!winData.value || !loseData.value) return [];
  const w = winData.value;
  const l = loseData.value;
  const result = [];

  const kdaDiff = ((w.avg_kda || 0) - (l.avg_kda || 0)).toFixed(1);
  if (kdaDiff > 0) {
    result.push({ icon: '📈', text: `获胜时 KDA 比失败时高 ${kdaDiff}，稳定性是关键` });
  }

  const deathDiff = ((l.avg_deaths || 0) - (w.avg_deaths || 0)).toFixed(1);
  if (deathDiff > 0.5) {
    result.push({ icon: '💀', text: `失败时场均死亡多 ${deathDiff} 次，减少失误能显著提升胜率` });
  }

  if ((w.avg_economy_diff_10min || 0) > 0 && (l.avg_economy_diff_10min || 0) < 0) {
    result.push({
      icon: '💰',
      text: `获胜时 10 分钟经济领先 ${Math.round(w.avg_economy_diff_10min)}，失败时经济落后 ${Math.round(Math.abs(l.avg_economy_diff_10min))}`,
    });
  }

  const fightDiff = ((w.avg_big_fight_damage || 0) - (l.avg_big_fight_damage || 0)).toFixed(0);
  if (fightDiff > 0) {
    result.push({ icon: '🔥', text: `获胜时大型团战平均伤害多 ${Number(fightDiff).toLocaleString()}，团战表现直接影响胜负` });
  }

  if (result.length === 0) {
    result.push({ icon: '📊', text: '数据持续积累中，更多分析即将到来...' });
  }

  return result;
});

async function loadData() {
  loading.value = true;
  error.value = null;
  try {
    const [winRes, loseRes] = await Promise.all([
      getPlayerWinStats(DEFAULT_SEASON),
      getPlayerLoseStats(DEFAULT_SEASON),
    ]);
    winData.value = winRes.data;
    loseData.value = loseRes.data;
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

  damageChart = new Chart(damageChartRef.value, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: '胜利',
          data: [
            winData.value.avg_hurt_to_hero || 0,
            winData.value.avg_be_hurt_by_hero || 0,
            winData.value.avg_heal_count || 0,
            winData.value.avg_big_fight_damage || 0,
            winData.value.avg_big_fight_damage_taken || 0,
          ],
          backgroundColor: 'rgba(40, 167, 69, 0.75)',
          borderColor: '#28a745',
          borderWidth: 1,
          borderRadius: 4,
        },
        {
          label: '失败',
          data: [
            loseData.value.avg_hurt_to_hero || 0,
            loseData.value.avg_be_hurt_by_hero || 0,
            loseData.value.avg_heal_count || 0,
            loseData.value.avg_big_fight_damage || 0,
            loseData.value.avg_big_fight_damage_taken || 0,
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
          beginAtZero: true,
          ticks: {
            callback: (v) => (v / 1000).toFixed(0) + 'k',
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
            label: (ctx) => `${ctx.dataset.label}: ${ctx.raw.toLocaleString()}`,
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
          beginAtZero: true,
          ticks: { font: { size: 11 } },
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
            label: (ctx) => `${ctx.dataset.label}: ${ctx.raw.toLocaleString()}`,
          },
        },
      },
    },
  });
}

onMounted(() => loadData());

onUnmounted(() => {
  damageChart?.destroy();
  economyChart?.destroy();
});
</script>

<style scoped>
.winlose-page {
  max-width: 1000px;
  margin: 0 auto;
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
  .compare-grid { grid-template-columns: repeat(2, 1fr); }
  .chart-canvas { height: 260px !important; }
}
</style>
