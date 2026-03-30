<template>
  <div class="compare-card">
    <div class="compare-label">{{ label }}</div>
    <div class="compare-values">
      <div class="compare-value win-side">
        <span class="compare-tag win">胜</span>
        <span class="compare-num">{{ formatValue(win) }}</span>
      </div>
      <div class="compare-value lose-side">
        <span class="compare-tag lose">负</span>
        <span class="compare-num">{{ formatValue(lose) }}</span>
      </div>
    </div>
    <div class="compare-diff" :class="diffClass">
      {{ diffText }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  label: { type: String, required: true },
  win: { type: [Number, String], default: 0 },
  lose: { type: [Number, String], default: 0 },
  reverse: { type: Boolean, default: false }, // true 表示败方值越小越好（如死亡）
});

function formatValue(v) {
  const n = Number(v);
  if (isNaN(n)) return v;
  if (n >= 10000) return (n / 1000).toFixed(1) + 'k';
  if (n % 1 !== 0) return n.toFixed(2);
  return n.toString();
}

const diff = computed(() => {
  return Number(props.win) - Number(props.lose);
});

const diffText = computed(() => {
  const d = diff.value;
  if (isNaN(d) || d === 0) return '持平';
  const sign = d > 0 ? '+' : '';
  const formatted = Math.abs(d) >= 100 ? Math.round(d).toLocaleString() : d.toFixed(2);
  return `${sign}${d > 0 ? formatted : formatted}`;
});

const diffClass = computed(() => {
  const d = diff.value;
  if (isNaN(d) || d === 0) return 'neutral';
  const isGood = props.reverse ? d < 0 : d > 0;
  return isGood ? 'positive' : 'negative';
});
</script>

<style scoped>
.compare-card {
  background: var(--bg-card);
  border-radius: var(--border-radius-md);
  padding: var(--spacing-md);
  box-shadow: var(--shadow-sm);
}

.compare-label {
  font-size: var(--font-size-sm);
  color: var(--gray-500);
  margin-bottom: 8px;
}

.compare-values {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-sm);
  margin-bottom: 6px;
}

.compare-value {
  display: flex;
  align-items: center;
  gap: 6px;
}

.compare-tag {
  font-size: var(--font-size-xs);
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: var(--font-weight-bold);
}

.compare-tag.win {
  background: var(--success-bg);
  color: var(--success-text);
}

.compare-tag.lose {
  background: var(--danger-bg);
  color: var(--danger-text);
}

.compare-num {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--gray-800);
}

.compare-diff {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  text-align: right;
}

.compare-diff.positive { color: var(--success-color); }
.compare-diff.negative { color: var(--danger-color); }
.compare-diff.neutral { color: var(--gray-400); }
</style>
