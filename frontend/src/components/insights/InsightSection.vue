<!--
 * InsightSection.vue - 洞察区块组件
 * 按 filterId 筛选 sections 数组，渲染匹配的 InsightCard
 -->
<template>
  <div class="insight-section" v-if="filteredSections.length">
    <div class="insight-section-title" v-if="title">{{ title }}</div>
    <div class="insight-section-cards">
      <InsightCard
        v-for="section in displaySections"
        :key="section.id"
        :section="section"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import InsightCard from './InsightCard.vue';

const props = defineProps({
  sections: { type: Array, default: () => [] },
  filterId: { type: String, default: '' },
  title: { type: String, default: '' },
  limit: { type: Number, default: 0 },
});

const filteredSections = computed(() => {
  if (!props.sections) return [];
  if (!props.filterId) return props.sections;
  return props.sections.filter((s) => s.id === props.filterId);
});

const displaySections = computed(() => {
  if (props.limit > 0) return filteredSections.value.slice(0, props.limit);
  return filteredSections.value;
});
</script>

<style scoped>
.insight-section {
  margin-top: var(--spacing-xl);
}

.insight-section-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--gray-700);
  margin-bottom: var(--spacing-md);
}

.insight-section-cards {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}
</style>
