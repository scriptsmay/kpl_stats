<!--
 * Heroes.vue - 英雄池分析页面
 * 数据源：player-hero-summary（英雄统计）+ player-hero-battles（对局详情）
 -->
<template>
  <div class="result-section heroes-page">
    <div class="result-header">
      <h1 class="result-title">⚔️ 英雄池分析</h1>
      <p class="result-subtitle">对抗路选手英雄使用数据与联盟胜率对比 · {{ seasonName }}</p>
    </div>

    <div class="loading" v-if="loading">
      <div class="loading-spinner"></div>
      <div class="loading-text">正在加载英雄池数据...</div>
    </div>

    <div class="error-message" v-else-if="error">
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="loadData">重试</button>
    </div>

    <div v-else-if="heroStats.length">
      <!-- 概览 -->
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

      <!-- AI 洞察 -->
      <InsightSection :sections="aiInsights?.sections" filterId="hero_pool" title="英雄池洞察" />

      <!-- 使用排行柱状图 -->
      <div class="chart-container">
        <div class="chart-title">英雄使用次数排行</div>
        <canvas ref="barChartRef" class="bar-canvas"></canvas>
      </div>

      <!-- 英雄详情表格 -->
      <div class="hero-table-section">
        <div class="section-title">英雄详情</div>
        <div class="hero-table-wrapper">
          <table class="hero-table">
            <thead>
              <tr>
                <th class="col-rank">#</th>
                <th class="col-hero">英雄</th>
                <th class="col-maturity">成熟度</th>
                <th class="col-num">使用</th>
                <th class="col-num">胜场</th>
                <th class="col-num">负场</th>
                <th class="col-num">胜率</th>
                <th class="col-action">详情</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="(hero, index) in heroStatsSorted" :key="hero.hero_id">
                <tr :class="{ 'is-expanded': expandedHero === hero.hero_name }">
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
                  <td class="col-maturity">
                    <HeroMaturityBadge :maturity="hero.maturity" />
                  </td>
                  <td class="col-num">{{ hero.total_matches }}</td>
                  <td class="col-num text-success">{{ hero.win_matches }}</td>
                  <td class="col-num text-danger">{{ hero.total_matches - hero.win_matches }}</td>
                  <td class="col-num">
                    <span :class="winRateClass(hero.win_rate)">{{ hero.win_rate }}</span>
                  </td>
                  <td class="col-action">
                    <button
                      v-if="heroBattles[hero.hero_name]"
                      class="detail-btn"
                      :class="{ active: expandedHero === hero.hero_name }"
                      type="button"
                      :aria-expanded="expandedHero === hero.hero_name"
                      @click="toggleDetail(hero.hero_name)"
                    >
                      {{ expandedHero === hero.hero_name ? '收起' : '查看' }}
                      <span class="detail-chevron" aria-hidden="true"></span>
                    </button>
                    <span v-else class="no-data">-</span>
                  </td>
                </tr>
                <tr v-if="expandedHero === hero.hero_name && heroBattles[hero.hero_name]" class="hero-detail-row">
                  <td colspan="8">
                    <div class="hero-detail-panel">
                      <div class="hero-detail-header">
                        <div>
                          <div class="hero-detail-title">{{ hero.hero_name }} 对局详情</div>
                          <div class="hero-detail-meta">{{ heroBattles[hero.hero_name].total }} 局记录</div>
                        </div>
                        <button class="detail-close" type="button" @click="expandedHero = null">收起</button>
                      </div>
                      <div class="inline-battles-list">
                        <div
                          v-for="(battle, idx) in heroBattles[hero.hero_name].battles"
                          :key="idx"
                          class="inline-battle"
                          :class="{ win: battle.is_win, lose: !battle.is_win, mvp: battle.is_mvp }"
                        >
                          <div class="inline-battle-main">
                            <span class="battle-result" :class="battle.is_win ? 'win' : 'lose'">{{
                              battle.is_win ? '胜' : '负'
                            }}</span>
                            <span v-if="battle.is_mvp" class="battle-mvp">MVP</span>
                            <span class="battle-kda">{{ battle.kda }}</span>
                            <span class="battle-vs">{{ battle.versus_info }}</span>
                            <span class="battle-date">{{ formatMatchDate(battle.match_date) }}</span>
                          </div>
                          <div class="inline-battle-detail">
                            <span v-if="battle.equip_ids?.length">
                              <span class="equip-label">出装：</span>{{ battle.equip_ids.join(' / ') }}
                            </span>
                            <span v-if="battle.rune">
                              <span class="rune-label">铭文：</span>{{ formatRune(battle.rune) }}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 胜率 vs 联盟 -->
      <div class="chart-container" v-if="compareData.length">
        <div class="chart-title">胜率 vs 联盟对抗路平均</div>
        <canvas ref="compareChartRef" class="bar-canvas"></canvas>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onUnmounted, watch } from 'vue';
import { Chart, BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js';
import {
  getPlayerHeroSummary,
  getPlayerHeroBattles,
  getHeroWinRate,
  getSeasonNameMap,
  getAiInsights,
  getInsights,
} from '../api/github-data';
import { useSeason } from '../composables/useSeason.js';
import InsightSection from './insights/InsightSection.vue';
import HeroMaturityBadge from './insights/HeroMaturityBadge.vue';

const { selectedSeason, resolvedSeasonName, resolveCurrent } = useSeason();

Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

const loading = ref(false);
const error = ref(null);
const heroStats = ref([]);
const leagueHeroes = ref([]);
const heroBattles = ref({});
const expandedHero = ref(null);
const seasonName = ref(resolvedSeasonName.value || '当前赛季');
const aiInsights = ref(null);

const barChartRef = ref(null);
const compareChartRef = ref(null);
let barChart = null;
let compareChart = null;

const heroAvatar = (id) => `https://game.gtimg.cn/images/yxzj/img201606/heroimg/${id}/${id}.jpg`;
const handleAvatarError = (e) => {
  e.target.style.display = 'none';
};

const totalMatches = computed(() => heroStats.value.reduce((s, h) => s + (h.total_matches || 0), 0));
const totalWins = computed(() => heroStats.value.reduce((s, h) => s + (h.win_matches || 0), 0));
const overallWinRate = computed(() =>
  totalMatches.value ? Math.round((totalWins.value / totalMatches.value) * 1000) / 10 : 0,
);
const overallWinRateText = computed(() => overallWinRate.value + '%');
const overallWinRateClass = computed(() =>
  overallWinRate.value >= 60 ? 'win' : overallWinRate.value < 45 ? 'lose' : '',
);
const heroStatsSorted = computed(() => [...heroStats.value].sort((a, b) => b.total_matches - a.total_matches));
const winRateClass = (rate) => {
  const v = parseFloat(rate);
  return v >= 60 ? 'text-success' : v < 45 ? 'text-danger' : '';
};

const compareData = computed(() => {
  if (!heroStats.value.length || !leagueHeroes.value.length) return [];
  const map = {};
  leagueHeroes.value.forEach((h) => {
    map[h.hero_id] = h;
  });
  return heroStats.value
    .filter((h) => map[h.hero_id])
    .map((h) => ({
      hero_name: h.hero_name,
      player_rate: parseFloat(h.win_rate),
      league_rate: parseFloat(map[h.hero_id].win_rate),
      total_matches: h.total_matches,
    }))
    .sort((a, b) => b.total_matches - a.total_matches)
    .slice(0, 15);
});

function formatMatchDate(d) {
  if (!d || d.length < 8) return d;
  return `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`;
}

function formatRune(rune) {
  if (!rune || typeof rune !== 'object') return '';
  return Object.values(rune)
    .map((r) => `${r.name}×${r.totalnumber}`)
    .join(' ');
}

function toggleDetail(heroName) {
  expandedHero.value = expandedHero.value === heroName ? null : heroName;
}

async function loadData() {
  loading.value = true;
  error.value = null;
  const season = selectedSeason.value;
  try {
    const [heroRes, leagueRes, nameMap, battlesRes] = await Promise.all([
      getPlayerHeroSummary(season),
      getHeroWinRate(season),
      getSeasonNameMap(),
      getPlayerHeroBattles(season).catch(() => null),
    ]);

    if (heroRes.code === 200 && Array.isArray(heroRes.data)) {
      heroStats.value = heroRes.data;
    }

    if (leagueRes.code === 200 && Array.isArray(leagueRes.data)) {
      leagueHeroes.value = leagueRes.data.filter((h) => h.position === '对抗路');
    }

    if (battlesRes) {
      heroBattles.value = battlesRes.heroes || {};
    }

    seasonName.value = nameMap[season] || resolvedSeasonName.value || season;
  } catch (err) {
    console.error('英雄池数据加载失败:', err);
    error.value = '数据加载失败，请检查网络后重试';
  } finally {
    loading.value = false;
    await nextTick();
    setTimeout(() => {
      initBarChart();
      if (compareData.value.length) initCompareChart();
    }, 50);
  }
}

function initBarChart() {
  if (!barChartRef.value || !heroStatsSorted.value.length) return;
  if (barChart) barChart.destroy();
  const top = heroStatsSorted.value.slice(0, 15);
  barChart = new Chart(barChartRef.value, {
    type: 'bar',
    data: {
      labels: top.map((h) => h.hero_name),
      datasets: [
        {
          label: '使用次数',
          data: top.map((h) => h.total_matches),
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
        y: { grid: { display: false }, ticks: { font: { size: 12 } } },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const h = top[ctx.dataIndex];
              return [
                `使用: ${h.total_matches} 场`,
                `胜场: ${h.win_matches} / 负场: ${h.total_matches - h.win_matches}`,
                `胜率: ${h.win_rate}`,
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
        x: { grid: { display: false }, ticks: { font: { size: 11 }, maxRotation: 45 } },
        y: {
          beginAtZero: true,
          max: 100,
          title: { display: true, text: '胜率 (%)', font: { size: 12 } },
          grid: { color: 'rgba(0,0,0,0.04)' },
        },
      },
      plugins: {
        legend: { position: 'top', labels: { usePointStyle: true, padding: 16, font: { size: 12 } } },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const d = data[ctx.dataIndex];
              return ctx.datasetIndex === 0
                ? `无言胜率: ${d.player_rate}% (${d.total_matches} 场)`
                : `联盟对抗路平均: ${d.league_rate}%`;
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
  barChart?.destroy();
  compareChart?.destroy();
});
</script>

<style scoped>
.heroes-page {
  padding: 20px;
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

/* 表格 */
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
.hero-table tbody tr.is-expanded {
  background: #f5f7ff;
  box-shadow: inset 3px 0 0 #4361ee;
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
.col-maturity {
  width: 80px;
}
.col-action {
  width: 120px;
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
.detail-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-width: 68px;
  padding: 4px 10px;
  border: 1px solid #4361ee;
  background: transparent;
  color: #4361ee;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}
.detail-btn:hover {
  background: #4361ee;
  color: #fff;
}
.detail-btn.active {
  background: #4361ee;
  color: #fff;
}
.detail-chevron {
  width: 6px;
  height: 6px;
  border-right: 1.5px solid currentColor;
  border-bottom: 1.5px solid currentColor;
  transform: rotate(45deg);
  transition: transform 0.2s ease;
}
.detail-btn.active .detail-chevron {
  transform: rotate(225deg);
}
.no-data {
  color: var(--gray-300);
}

/* 表格内联对局详情 */
.hero-detail-row:hover {
  background: transparent !important;
}
.hero-detail-row td {
  padding: 0 12px 16px;
  background: #f5f7ff;
  border-bottom: 1px solid #dfe5ff;
}
.hero-detail-panel {
  border: 1px solid #dfe5ff;
  border-radius: 8px;
  background: #fff;
  padding: 14px;
  text-align: left;
}
.hero-detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.hero-detail-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--gray-800);
}
.hero-detail-meta {
  margin-top: 2px;
  font-size: 12px;
  color: var(--gray-400);
}
.detail-close {
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 4px;
  background: #fff;
  color: var(--gray-500);
  cursor: pointer;
  font-size: 12px;
  padding: 4px 10px;
  white-space: nowrap;
}
.detail-close:hover {
  border-color: #4361ee;
  color: #4361ee;
}
.inline-battles-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 420px;
  overflow-y: auto;
  padding-right: 4px;
}
.inline-battle {
  border: 1px solid var(--border-color, #f0f0f0);
  border-left: 4px solid var(--gray-300);
  border-radius: 6px;
  padding: 10px 12px;
  background: #fff;
}
.inline-battle.win {
  border-left-color: var(--success-color);
}
.inline-battle.lose {
  border-left-color: var(--danger-color);
}
.inline-battle.mvp {
  background: rgba(255, 193, 7, 0.04);
}
.inline-battle-main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.battle-result {
  font-weight: 700;
  font-size: 14px;
  padding: 2px 8px;
  border-radius: 4px;
}
.battle-result.win {
  color: #fff;
  background: var(--success-color);
}
.battle-result.lose {
  color: #fff;
  background: var(--danger-color);
}
.battle-mvp {
  font-size: 13px;
  font-weight: 600;
  color: #e67e22;
  white-space: nowrap;
}
.battle-kda {
  font-weight: 700;
  font-size: 15px;
  color: var(--gray-800);
  white-space: nowrap;
}
.battle-vs {
  font-size: 13px;
  color: var(--gray-600);
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.battle-date {
  font-size: 12px;
  color: var(--gray-400);
  margin-left: auto;
  white-space: nowrap;
}
.inline-battle-detail {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin-top: 6px;
  font-size: 13px;
  color: var(--gray-600);
  line-height: 1.6;
}
.equip-label,
.rune-label {
  font-weight: 600;
  color: var(--gray-500);
}

/* 加载/错误 */
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
  .hero-detail-row td {
    padding: 0 8px 12px;
  }
  .hero-detail-header {
    align-items: flex-start;
  }
  .inline-battle-main {
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 8px;
  }
  .battle-date {
    margin-left: 0;
  }
  .battle-vs {
    flex-basis: 100%;
    white-space: normal;
  }
  .inline-battle-detail {
    gap: 4px;
  }
  .inline-battle-detail span {
    flex-basis: 100%;
  }
}
</style>
