<template>
  <div class="result-section ai-analysis-page">
    <div class="result-header">
      <h1 class="result-title">AI分析</h1>
      <p class="result-subtitle">个人成长路径观察 · {{ seasonName }}</p>
    </div>

    <div class="loading" v-if="loading">
      <div class="loading-spinner"></div>
      <div class="loading-text">正在加载 AI分析...</div>
    </div>

    <div class="error-message" v-else-if="error">
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="loadData">重试</button>
    </div>

    <div v-else-if="insights">
      <section class="ai-hero">
        <div>
          <div class="ai-stage" v-if="insights.growth_stage">
            {{ insights.growth_stage }}
          </div>
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
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import {
  getAiInsights,
  getGrowthPath,
  getInsights,
  getTrendSummary,
} from '../api/github-data';
import { useSeason } from '../composables/useSeason.js';
import InsightSection from './insights/InsightSection.vue';

const { selectedSeason, resolvedSeasonName, resolveCurrent } = useSeason();

const loading = ref(false);
const error = ref(null);
const insights = ref(null);
const growthPath = ref(null);
const trendSummary = ref(null);
const seasonName = computed(() => resolvedSeasonName.value || '当前赛季');

const sectionCount = computed(() => insights.value?.sections?.length || 0);
const primarySampleSize = computed(() => {
  const size = insights.value?.sections?.[0]?.sample_size;
  return size == null ? '-' : `${size} 局`;
});
const confidenceText = computed(() => {
  const confidence = insights.value?.sections?.[0]?.confidence;
  return { low: '低', medium: '中', high: '高' }[confidence] || '-';
});
const trendSnapshots = computed(
  () => trendSummary.value?.snapshots_available || '-',
);

async function loadData() {
  loading.value = true;
  error.value = null;
  const season = selectedSeason.value;
  try {
    const [aiData, ruleData, growthData, trendData] = await Promise.all([
      getAiInsights(season),
      getInsights(season).catch(() => null),
      getGrowthPath(season).catch(() => null),
      getTrendSummary(season).catch(() => null),
    ]);

    insights.value = aiData || ruleData;
    growthPath.value = growthData;
    trendSummary.value = trendData;

    if (!insights.value) {
      throw new Error('AI分析数据暂不可用');
    }
  } catch (err) {
    console.error('加载 AI分析失败:', err);
    error.value = `加载失败：${err.message}`;
  } finally {
    loading.value = false;
  }
}

onMounted(loadData);

watch(selectedSeason, async () => {
  await resolveCurrent();
  loadData();
});
</script>

<style scoped>
.ai-analysis-page {
  max-width: 1400px;
}

.ai-hero {
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-xl);
  background: linear-gradient(
    135deg,
    rgba(30, 60, 114, 0.08),
    rgba(78, 205, 196, 0.08)
  );
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

@media (max-width: 768px) {
  .ai-hero {
    padding: var(--spacing-lg);
  }
}
</style>
