<!--
 * HeroMaturityBadge.vue - 英雄成熟度标签
 * 显示英雄在当前赛季的使用成熟度分类
 -->
<template>
  <span class="maturity-badge" :class="maturityClass">{{ label }}</span>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  maturity: { type: String, default: '' },
});

const MATURITY_MAP = {
  core: { label: '核心', class: 'maturity-core' },
  rotation: { label: '轮换', class: 'maturity-rotation' },
  trial: { label: '尝试', class: 'maturity-trial' },
  watch_only: { label: '待观察', class: 'maturity-watch' },
};

const label = computed(() => MATURITY_MAP[props.maturity]?.label || props.maturity || '-');
const maturityClass = computed(() => MATURITY_MAP[props.maturity]?.class || '');
</script>

<style scoped>
.maturity-badge {
  display: inline-block;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  padding: 1px 8px;
  border-radius: 10px;
  line-height: 1.6;
  vertical-align: middle;
}

.maturity-core {
  background: rgba(30, 60, 114, 0.12);
  color: var(--primary-dark);
}

.maturity-rotation {
  background: rgba(40, 167, 69, 0.1);
  color: #1a7431;
}

.maturity-trial {
  background: rgba(253, 126, 20, 0.12);
  color: #b35c00;
}

.maturity-watch {
  background: var(--gray-100);
  color: var(--gray-500);
}
</style>
