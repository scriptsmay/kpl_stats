<!--
 * EvidenceList.vue - 证据列表组件
 * 可折叠的证据条目列表，默认展开前 3 条
 -->
<template>
  <div class="evidence-list" v-if="items && items.length">
    <div
      class="evidence-item"
      v-for="(item, idx) in visibleItems"
      :key="idx"
    >
      <span class="evidence-dot"></span>
      <span class="evidence-text">{{ item }}</span>
    </div>
    <button
      v-if="items.length > defaultShow"
      class="evidence-toggle"
      @click="expanded = !expanded"
    >
      {{ expanded ? '收起' : `展开全部 ${items.length} 条` }}
    </button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  items: { type: Array, default: () => [] },
  defaultShow: { type: Number, default: 3 },
});

const expanded = ref(false);

const visibleItems = computed(() => {
  if (expanded.value || props.items.length <= props.defaultShow) return props.items;
  return props.items.slice(0, props.defaultShow);
});
</script>

<style scoped>
.evidence-list {
  margin-top: var(--spacing-sm);
}

.evidence-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-xs);
  padding: 3px 0;
  font-size: var(--font-size-sm);
  color: var(--gray-600);
  line-height: 1.5;
}

.evidence-dot {
  flex-shrink: 0;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--gray-400);
  margin-top: 7px;
}

.evidence-text {
  flex: 1;
}

.evidence-toggle {
  background: none;
  border: none;
  color: var(--primary-medium);
  font-size: var(--font-size-sm);
  cursor: pointer;
  padding: 4px 0;
  margin-top: 2px;
}

.evidence-toggle:hover {
  text-decoration: underline;
}
</style>
