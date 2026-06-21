<!--
 * InsightCard.vue - 单条洞察卡片
 * 展示一个分析结论的完整信息：标题、类型、摘要、证据、风险提示
 -->
<template>
  <div class="insight-card" :class="`type-${section.conclusion_type}`">
    <div class="insight-card-header">
      <div class="insight-card-title">{{ section.title }}</div>
      <div class="insight-card-tags">
        <span class="conclusion-tag" :class="conclusionClass">{{ conclusionLabel }}</span>
      </div>
    </div>

    <div class="insight-card-summary">{{ section.summary }}</div>

    <EvidenceList :items="section.evidence" />

    <RiskNote
      :notes="section.risk_notes"
      :confidence="section.confidence"
      :sampleSize="section.sample_size"
      :sampleUnit="section.sample_unit"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue';
import EvidenceList from './EvidenceList.vue';
import RiskNote from './RiskNote.vue';

const props = defineProps({
  section: {
    type: Object,
    required: true,
    default: () => ({
      id: '',
      title: '',
      summary: '',
      conclusion_type: 'fact',
      confidence: 'medium',
      sample_size: 0,
      sample_unit: 'games',
      evidence: [],
      risk_notes: [],
    }),
  },
});

const CONCLUSION_MAP = {
  fact: { label: '事实', class: 'tag-fact' },
  signal: { label: '信号', class: 'tag-signal' },
  hypothesis: { label: '待验证', class: 'tag-hypothesis' },
};

const conclusionLabel = computed(() => CONCLUSION_MAP[props.section.conclusion_type]?.label || props.section.conclusion_type);
const conclusionClass = computed(() => CONCLUSION_MAP[props.section.conclusion_type]?.class || '');
</script>

<style scoped>
.insight-card {
  background: var(--bg-card);
  border-radius: var(--border-radius-md);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-sm);
  border-left: 4px solid var(--primary-medium);
  transition: box-shadow var(--transition-base);
}

.insight-card:hover {
  box-shadow: var(--shadow-hover);
}

.insight-card.type-signal {
  border-left-color: var(--success-color);
}

.insight-card.type-hypothesis {
  border-left-color: var(--orange-color);
}

.insight-card.type-fact {
  border-left-color: var(--info-color);
}

.insight-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-sm);
}

.insight-card-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--gray-800);
}

.conclusion-tag {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  padding: 2px 10px;
  border-radius: 10px;
}

.tag-fact {
  background: rgba(13, 110, 253, 0.1);
  color: #0a58ca;
}

.tag-signal {
  background: rgba(40, 167, 69, 0.1);
  color: #1a7431;
}

.tag-hypothesis {
  background: rgba(253, 126, 20, 0.12);
  color: #b35c00;
}

.insight-card-summary {
  font-size: var(--font-size-base);
  color: var(--gray-700);
  line-height: 1.6;
}

@media (max-width: 768px) {
  .insight-card {
    padding: var(--spacing-md);
  }

  .insight-card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }
}
</style>
