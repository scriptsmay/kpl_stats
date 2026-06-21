<!--
 * RiskNote.vue - 风险提示组件
 * 显示样本量、置信度和风险备注
 -->
<template>
  <div class="risk-note" v-if="hasContent">
    <div class="risk-meta">
      <span class="risk-sample" v-if="sampleSize != null">
        样本：{{ sampleSize }} {{ displayUnit }}
      </span>
      <span class="risk-confidence" :class="confidenceClass" v-if="confidence">
        {{ confidenceLabel }}
      </span>
    </div>
    <div class="risk-texts" v-if="notes && notes.length">
      <div class="risk-text" v-for="(note, idx) in notes" :key="idx">
        {{ note }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  notes: { type: Array, default: () => [] },
  confidence: { type: String, default: '' },
  sampleSize: { type: Number, default: null },
  sampleUnit: { type: String, default: '局' },
});

const hasContent = computed(() => {
  return (props.notes && props.notes.length) || props.sampleSize != null || props.confidence;
});

const UNIT_MAP = {
  games: '局',
  matches: '场',
  heroes: '英雄',
};

const displayUnit = computed(() => UNIT_MAP[props.sampleUnit] || props.sampleUnit);

const confidenceLabel = computed(() => {
  const map = { low: '低置信', medium: '中置信', high: '高置信' };
  return map[props.confidence] || props.confidence;
});

const confidenceClass = computed(() => {
  return `confidence-${props.confidence}`;
});
</script>

<style scoped>
.risk-note {
  margin-top: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: rgba(255, 193, 7, 0.08);
  border: 1px solid rgba(255, 193, 7, 0.2);
  border-radius: var(--border-radius-sm);
}

.risk-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: 4px;
}

.risk-sample {
  font-size: var(--font-size-xs);
  color: var(--gray-500);
}

.risk-confidence {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  padding: 1px 8px;
  border-radius: 10px;
}

.confidence-low {
  background: rgba(253, 126, 20, 0.12);
  color: #b35c00;
}

.confidence-medium {
  background: rgba(13, 110, 253, 0.1);
  color: #0a58ca;
}

.confidence-high {
  background: rgba(40, 167, 69, 0.1);
  color: #1a7431;
}

.risk-texts {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.risk-text {
  font-size: var(--font-size-xs);
  color: var(--gray-500);
  line-height: 1.5;
}
</style>
