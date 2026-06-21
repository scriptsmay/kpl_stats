<template>
  <div class="result-section ai-analysis-page">
    <div class="result-header">
      <h1 class="result-title">AI 分析</h1>
      <p class="result-subtitle">个人成长路径观察 · {{ seasonName }}</p>
    </div>

    <div class="loading" v-if="loading">
      <div class="loading-spinner"></div>
      <div class="loading-text">正在加载 AI 分析...</div>
    </div>

    <div class="error-message" v-else-if="error">
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="loadData">重试</button>
    </div>

    <div v-else-if="insights">
      <section class="ai-hero">
        <div>
          <div class="ai-stage" v-if="insights.growth_stage">{{ insights.growth_stage }}</div>
          <h2>{{ insights.headline }}</h2>
          <p>{{ insights.summary }}</p>
        </div>
      </section>

      <div class="summary-cards">
        <div class="summary-card">
          <div class="summary-card-value">{{ sectionCount }}</div>
          <div class="summary-card-label">分析主题</div>
        </div>
        <div class="summary-card">
          <div class="summary-card-value">{{ primarySampleSize }}</div>
          <div class="summary-card-label">本赛季样本</div>
        </div>
        <div class="summary-card">
          <div class="summary-card-value">{{ confidenceText }}</div>
          <div class="summary-card-label">当前置信度</div>
        </div>
        <div class="summary-card">
          <div class="summary-card-value">{{ trendSnapshots }}</div>
          <div class="summary-card-label">趋势快照</div>
        </div>
      </div>

      <InsightSection :sections="insights.sections" title="全部洞察" />

      <section class="growth-section" v-if="growthPath">
        <div class="section-title">成长路径</div>
        <div class="growth-summary">{{ growthPath.summary }}</div>

        <div class="milestone-list" v-if="growthPath.milestones?.length">
          <div class="milestone-item" v-for="item in growthPath.milestones.slice(0, 8)" :key="item.type + item.date + item.description">
            <div class="milestone-date">{{ item.date || '-' }}</div>
            <div class="milestone-content">
              <div class="milestone-type">{{ milestoneLabel(item.type) }}</div>
              <div class="milestone-desc">{{ item.description }}</div>
            </div>
          </div>
        </div>
      </section>

      <section class="trend-section" v-if="heroPoolTrend">
        <div class="section-title">英雄池趋势</div>
        <div class="trend-grid">
          <div class="trend-item">
            <span class="trend-label">时间范围</span>
            <span class="trend-value">{{ heroPoolTrend.date_range }}</span>
          </div>
          <div class="trend-item">
            <span class="trend-label">英雄数变化</span>
            <span class="trend-value">{{ heroPoolTrend.hero_count_oldest }} → {{ heroPoolTrend.hero_count_latest }}</span>
          </div>
          <div class="trend-item">
            <span class="trend-label">新增英雄</span>
            <span class="trend-value">{{ heroPoolTrend.new_heroes?.join('、') || '-' }}</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import {
  DEFAULT_SEASON,
  getAiInsights,
  getCurrentSeason,
  getGrowthPath,
  getInsights,
  getTrendSummary,
} from '../api/github-data';
import InsightSection from './insights/InsightSection.vue';

const loading = ref(false);
const error = ref(null);
const insights = ref(null);
const growthPath = ref(null);
const trendSummary = ref(null);
const seasonName = ref(DEFAULT_SEASON);

const sectionCount = computed(() => insights.value?.sections?.length || 0);
const primarySampleSize = computed(() => {
  const size = insights.value?.sections?.[0]?.sample_size;
  return size == null ? '-' : `${size} 局`;
});
const confidenceText = computed(() => {
  const confidence = insights.value?.sections?.[0]?.confidence;
  return { low: '低', medium: '中', high: '高' }[confidence] || '-';
});
const trendSnapshots = computed(() => trendSummary.value?.snapshots_available || '-');
const heroPoolTrend = computed(() => trendSummary.value?.trends?.hero_pool?.['7d'] || trendSummary.value?.trends?.hero_pool?.['3d']);

function milestoneLabel(type) {
  return {
    first_appear: '首秀',
    season_start: '赛季',
    hero_pool: '英雄池',
    role_signal: '角色信号',
    ability_signal: '能力信号',
  }[type] || '节点';
}

async function loadData() {
  loading.value = true;
  error.value = null;
  try {
    const current = await getCurrentSeason();
    seasonName.value = current.season_name || current.current;

    const [aiData, ruleData, growthData, trendData] = await Promise.all([
      getAiInsights(DEFAULT_SEASON),
      getInsights(DEFAULT_SEASON).catch(() => null),
      getGrowthPath(DEFAULT_SEASON).catch(() => null),
      getTrendSummary(DEFAULT_SEASON).catch(() => null),
    ]);

    insights.value = aiData || ruleData;
    growthPath.value = growthData;
    trendSummary.value = trendData;

    if (!insights.value) {
      throw new Error('AI 分析数据暂不可用');
    }
  } catch (err) {
    console.error('加载 AI 分析失败:', err);
    error.value = `加载失败：${err.message}`;
  } finally {
    loading.value = false;
  }
}

onMounted(loadData);
</script>

<style scoped>
.ai-analysis-page {
  max-width: 1400px;
}

.ai-hero {
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-xl);
  background: linear-gradient(135deg, rgba(30, 60, 114, 0.08), rgba(78, 205, 196, 0.08));
  border: 1px solid var(--gray-200);
  border-radius: var(--border-radius-md);
}

.ai-stage {
  display: inline-flex;
  align-items: center;
  margin-bottom: var(--spacing-sm);
  padding: 2px 10px;
  border-radius: 999px;
  background: rgba(40, 167, 69, 0.1);
  color: #1a7431;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.ai-hero h2 {
  margin: 0 0 var(--spacing-sm);
  color: var(--gray-800);
  font-size: var(--font-size-xxl);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0;
}

.ai-hero p,
.growth-summary {
  margin: 0;
  color: var(--gray-600);
  line-height: 1.7;
}

.growth-section,
.trend-section {
  margin-top: var(--spacing-xl);
}

.milestone-list {
  margin-top: var(--spacing-md);
  border-top: 1px solid var(--gray-200);
}

.milestone-item {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: var(--spacing-md);
  padding: var(--spacing-md) 0;
  border-bottom: 1px solid var(--gray-200);
}

.milestone-date {
  color: var(--gray-500);
  font-size: var(--font-size-sm);
}

.milestone-type {
  color: var(--gray-800);
  font-weight: var(--font-weight-semibold);
}

.milestone-desc {
  margin-top: 2px;
  color: var(--gray-600);
  line-height: 1.6;
}

.trend-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--spacing-md);
}

.trend-item {
  padding: var(--spacing-md);
  border: 1px solid var(--gray-200);
  border-radius: var(--border-radius-md);
  background: var(--bg-card);
}

.trend-label {
  display: block;
  color: var(--gray-500);
  font-size: var(--font-size-sm);
}

.trend-value {
  display: block;
  margin-top: 4px;
  color: var(--gray-800);
  font-weight: var(--font-weight-semibold);
}

@media (max-width: 768px) {
  .ai-hero {
    padding: var(--spacing-lg);
  }

  .milestone-item {
    grid-template-columns: 1fr;
    gap: 4px;
  }
}
</style>
