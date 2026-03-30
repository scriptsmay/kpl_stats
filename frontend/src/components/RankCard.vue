<template>
  <div class="rank-card" :class="{ reverse: reverse }">
    <div class="rank-card-label">{{ label }}</div>
    <div class="rank-card-value">{{ value }}</div>
    <div class="rank-card-bar">
      <div class="rank-card-fill" :style="{ width: percentile + '%' }" :class="rankClass"></div>
    </div>
    <div class="rank-card-meta">
      <span class="rank-number" :class="rankClass">#{{ rank }}</span>
      <span class="rank-total">/ {{ total }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  rank: { type: [Number, String], default: '-' },
  total: { type: Number, default: 114 },
  reverse: { type: Boolean, default: false }, // 排名越小越好（默认），reverse 表示排名越大越好
});

const percentile = computed(() => {
  const r = Number(props.rank);
  if (!r || isNaN(r)) return 0;
  return Math.round(((props.total - r) / props.total) * 100);
});

const rankClass = computed(() => {
  const p = percentile.value;
  if (p >= 90) return 'rank-top';
  if (p >= 70) return 'rank-good';
  if (p >= 40) return 'rank-mid';
  return 'rank-low';
});
</script>

<style scoped>
.rank-card {
  background: var(--bg-card);
  border-radius: var(--border-radius-md);
  padding: var(--spacing-md);
  box-shadow: var(--shadow-sm);
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
}

.rank-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.rank-card-label {
  font-size: var(--font-size-sm);
  color: var(--gray-500);
  margin-bottom: 4px;
}

.rank-card-value {
  font-size: 22px;
  font-weight: var(--font-weight-bold);
  color: var(--gray-800);
  margin-bottom: 8px;
}

.rank-card-bar {
  height: 4px;
  background: var(--gray-100);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 8px;
}

.rank-card-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.8s ease;
}

.rank-card-fill.rank-top { background: #ee5a24; }
.rank-card-fill.rank-good { background: #ff9f43; }
.rank-card-fill.rank-mid { background: #0abde3; }
.rank-card-fill.rank-low { background: #c8d6e5; }

.rank-card-meta {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.rank-number {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
}

.rank-number.rank-top { color: #ee5a24; }
.rank-number.rank-good { color: #ff9f43; }
.rank-number.rank-mid { color: #0abde3; }
.rank-number.rank-low { color: var(--gray-400); }

.rank-total {
  font-size: var(--font-size-xs);
  color: var(--gray-400);
}
</style>
