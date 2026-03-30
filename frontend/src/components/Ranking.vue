<template>
  <div class="result-section ranking-page">
    <div class="result-header">
      <h1 class="result-title">📊 联盟数据排名</h1>
      <p class="result-subtitle">无言在 KPL {{ seasonName }} 中的全方位数据对比</p>
    </div>

    <!-- 加载状态 -->
    <div class="loading" v-if="loading">
      <div class="loading-spinner"></div>
      <div class="loading-text">正在加载排名数据...</div>
    </div>

    <div class="error-message" v-else-if="error">
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="loadData">重试</button>
    </div>

    <div v-else-if="statsData">
      <!-- 选手概览 -->
      <div class="player-overview-card">
        <div class="player-overview-left">
          <div class="player-name-big">{{ statsData.player_name }}</div>
          <div class="player-meta">
            {{ statsData.team_name }} · {{ statsData.player_position }} · {{ statsData.total_matches }}场
          </div>
        </div>
        <div class="player-overview-right">
          <div class="overview-stat">
            <span class="overview-value win">{{ statsData.win_rate }}</span>
            <span class="overview-label">胜率</span>
          </div>
          <div class="overview-stat">
            <span class="overview-value">{{ statsData.kda_ratio }}</span>
            <span class="overview-label">KDA</span>
          </div>
          <div class="overview-stat">
            <span class="overview-value">{{ statsData.avg_kill_participation }}</span>
            <span class="overview-label">参团率</span>
          </div>
        </div>
      </div>

      <!-- 排名雷达图 (Chart.js) -->
      <div class="chart-container">
        <div class="chart-title">核心指标排名百分位</div>
        <div class="chart-hint">数值越高表示排名越靠前（百分位）</div>
        <canvas ref="rankRadarRef" class="radar-canvas"></canvas>
      </div>

      <!-- KDA 数据 -->
      <div class="ranking-section">
        <div class="section-title">⚔️ KDA 数据</div>
        <div class="ranking-cards">
          <RankCard
            label="场均击杀"
            :value="statsData.avg_kills"
            :rank="statsData.avg_kills_rank"
            :total="totalPlayers"
          />
          <RankCard
            label="场均死亡"
            :value="statsData.avg_deaths"
            :rank="statsData.avg_deaths_rank"
            :total="totalPlayers"
            reverse
          />
          <RankCard
            label="场均助攻"
            :value="statsData.avg_assists"
            :rank="statsData.avg_assists_rank"
            :total="totalPlayers"
          />
          <RankCard label="KDA" :value="statsData.kda_ratio" :rank="statsData.kda_ratio_rank" :total="totalPlayers" />
          <RankCard
            label="参团率"
            :value="statsData.avg_kill_participation"
            :rank="statsData.avg_kill_participation_rank"
            :total="totalPlayers"
          />
        </div>
      </div>

      <!-- 伤害数据 -->
      <div class="ranking-section">
        <div class="section-title">🔥 伤害数据</div>
        <div class="ranking-cards">
          <RankCard
            label="每分钟伤害"
            :value="statsData.damage_per_minute"
            :rank="statsData.damage_per_minute_rank"
            :total="totalPlayers"
          />
          <RankCard
            label="伤害占比"
            :value="statsData.damage_share"
            :rank="statsData.damage_share_rank"
            :total="totalPlayers"
          />
          <RankCard
            label="每分钟承伤"
            :value="statsData.damage_taken_per_minute"
            :rank="statsData.damage_taken_per_minute_rank"
            :total="totalPlayers"
          />
          <RankCard
            label="承伤占比"
            :value="statsData.damage_taken_share"
            :rank="statsData.damage_taken_share_rank"
            :total="totalPlayers"
          />
          <RankCard
            label="每次死亡伤害"
            :value="statsData.damage_per_death"
            :rank="statsData.damage_per_death_rank"
            :total="totalPlayers"
          />
        </div>
      </div>

      <!-- 经济数据 -->
      <div class="ranking-section">
        <div class="section-title">💰 经济数据</div>
        <div class="ranking-cards">
          <RankCard
            label="每分钟经济"
            :value="statsData.economy_per_minute"
            :rank="statsData.economy_per_minute_rank"
            :total="totalPlayers"
          />
          <RankCard
            label="经济占比"
            :value="statsData.economy_share"
            :rank="statsData.economy_share_rank"
            :total="totalPlayers"
          />
          <RankCard
            label="经济转化率"
            :value="statsData.avg_economy_to_damage"
            :rank="statsData.avg_economy_to_damage_rank"
            :total="totalPlayers"
          />
        </div>
      </div>

      <!-- 中立资源 -->
      <div class="ranking-section">
        <div class="section-title">🐉 资源控制</div>
        <div class="ranking-cards">
          <RankCard
            label="主宰控制率"
            :value="statsData.master_control_rate"
            :rank="statsData.master_control_rate_rank"
            :total="totalPlayers"
          />
          <RankCard
            label="暴君控制率"
            :value="statsData.baron_control_rate"
            :rank="statsData.baron_control_rate_rank"
            :total="totalPlayers"
          />
          <RankCard
            label="中立资源控制率"
            :value="statsData.neutral_resource_control_rate"
            :rank="statsData.neutral_resource_control_rate_rank"
            :total="totalPlayers"
          />
        </div>
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
  Tooltip,
  Legend,
} from 'chart.js';
import { getAllPlayerStats, DEFAULT_SEASON } from '../api/github-data';
import RankCard from './RankCard.vue';

// 注册 Chart.js 组件
Chart.register(RadarController, RadialLinearScale, LineElement, PointElement, Filler, Tooltip, Legend);

const loading = ref(false);
const error = ref(null);
const statsData = ref(null);
const rankRadarRef = ref(null);
let rankChart = null;

const seasonName = '2026 春季赛';

const totalPlayers = computed(() => statsData.value?.total_players || 114);

const RANK_INDICATORS = [
  { key: 'avg_kill_participation_rank', label: '参团率' },
  { key: 'damage_per_minute_rank', label: '分均伤害' },
  { key: 'damage_per_death_rank', label: '每次死亡伤害' },
  { key: 'economy_per_minute_rank', label: '分均经济' },
  { key: 'avg_economy_to_damage_rank', label: '经济转化' },
  { key: 'kda_ratio_rank', label: 'KDA' },
];

async function loadData() {
  loading.value = true;
  error.value = null;
  try {
    const res = await getAllPlayerStats(DEFAULT_SEASON);
    statsData.value = res.data;
  } catch (err) {
    console.error('加载排名数据失败:', err);
    error.value = `加载失败：${err.message}`;
  } finally {
    loading.value = false;
    await nextTick();
    setTimeout(() => renderRankRadar(), 50);
  }
}

// Chart.js 雷达图
function renderRankRadar() {
  if (!rankRadarRef.value || !statsData.value) return;

  if (rankChart) rankChart.destroy();

  const total = totalPlayers.value;
  const labels = RANK_INDICATORS.map((r) => r.label);
  const values = RANK_INDICATORS.map((r) => {
    const rank = statsData.value[r.key];
    if (!rank) return 0;
    return Math.round(((total - rank) / total) * 100);
  });

  rankChart = new Chart(rankRadarRef.value, {
    type: 'radar',
    data: {
      labels,
      datasets: [
        {
          label: statsData.value.player_name,
          data: values,
          backgroundColor: 'rgba(67, 97, 238, 0.2)',
          borderColor: '#4361ee',
          borderWidth: 2.5,
          pointBackgroundColor: '#4361ee',
          pointBorderColor: '#fff',
          pointBorderWidth: 1,
          pointRadius: 5,
          pointHoverRadius: 7,
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
            stepSize: 25,
            font: { size: 10 },
            color: '#999',
            backdropColor: 'transparent',
          },
          pointLabels: {
            font: { size: 12, weight: '500' },
            color: '#555',
          },
          grid: { color: 'rgba(0,0,0,0.06)' },
          angleLines: { color: 'rgba(0,0,0,0.06)' },
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
              const indicator = RANK_INDICATORS[ctx.dataIndex];
              const rank = statsData.value[indicator.key] || '-';
              return `${indicator.label}: #${rank} / ${total}（百分位 ${ctx.raw}%）`;
            },
          },
        },
      },
    },
  });
}

onMounted(() => loadData());

onUnmounted(() => {
  rankChart?.destroy();
});
</script>

<style scoped>
.ranking-page {
  max-width: 1400px;
  margin: 0 auto;
}

.player-overview-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-card);
  border-radius: var(--border-radius-lg);
  padding: 24px 30px;
  margin-bottom: var(--spacing-xl);
  box-shadow: var(--shadow-sm);
}

.player-name-big {
  font-size: 28px;
  font-weight: var(--font-weight-bold);
  color: var(--gray-800);
}

.player-meta {
  font-size: var(--font-size-sm);
  color: var(--gray-500);
  margin-top: 4px;
}

.player-overview-right {
  display: flex;
  gap: 30px;
}

.overview-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.overview-value {
  font-size: 24px;
  font-weight: var(--font-weight-bold);
  color: var(--gray-800);
}

.overview-value.win {
  color: var(--success-color);
}

.overview-label {
  font-size: var(--font-size-xs);
  color: var(--gray-500);
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
}

.chart-hint {
  font-size: var(--font-size-xs);
  color: var(--gray-400);
  margin-bottom: var(--spacing-sm);
}

.radar-canvas {
  width: 100% !important;
  max-height: 400px;
}

.ranking-section {
  margin-bottom: var(--spacing-xl);
}

.section-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--gray-700);
  margin-bottom: var(--spacing-md);
}

.ranking-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: var(--spacing-md);
}

@media (max-width: 768px) {
  .player-overview-card {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  .player-overview-right {
    gap: 20px;
  }
  .radar-canvas {
    max-height: 300px;
  }
}
</style>
