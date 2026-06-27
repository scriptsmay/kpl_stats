<template>
  <div class="season-selector" :class="{ 'is-mobile': isMobile }">
    <select
      v-model="selectedSeason.value"
      :disabled="loading"
      class="season-select"
      @change="onChange"
    >
      <option v-if="loading" value="current" disabled>加载中...</option>
      <template v-else>
        <option value="current">
          {{ currentSeasonName || '当前赛季' }}
        </option>
        <option
          v-for="s in historicalSeasons"
          :key="s.tournament_id"
          :value="s.tournament_id"
        >
          {{ s.display_name || s.tournament_name }}
        </option>
      </template>
    </select>
    <span v-if="!isCurrentSeason && !loading" class="historical-badge">历史</span>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { useSeason } from '../composables/useSeason.js';

defineProps({
  isMobile: { type: Boolean, default: false },
});

const {
  selectedSeason,
  availableSeasons,
  currentSeasonName,
  isCurrentSeason,
  seasonLoading: loading,
  setSeason,
  initSeasons,
} = useSeason();

const historicalSeasons = computed(() =>
  availableSeasons.value.filter((s) => !s.is_current)
);

function onChange(e) {
  setSeason(e.target.value);
}

onMounted(() => initSeasons());
</script>

<style scoped>
.season-selector {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.season-select {
  appearance: none;
  -webkit-appearance: none;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  color: inherit;
  font-size: 13px;
  padding: 4px 28px 4px 10px;
  cursor: pointer;
  outline: none;
  transition: background 0.2s, border-color 0.2s;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='white' viewBox='0 0 16 16'%3E%3Cpath d='M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  background-size: 12px;
  max-width: 160px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.season-select:hover {
  background-color: rgba(255, 255, 255, 0.18);
  border-color: rgba(255, 255, 255, 0.35);
}

.season-select:focus {
  border-color: #4a9eff;
  box-shadow: 0 0 0 2px rgba(74, 158, 255, 0.2);
}

.season-select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.season-select option {
  background: #1a1a2e;
  color: #e0e0e0;
}

.historical-badge {
  display: inline-block;
  background: #f59e0b;
  color: #000;
  font-size: 10px;
  font-weight: 600;
  padding: 1px 5px;
  border-radius: 3px;
  line-height: 1.4;
}

.is-mobile .season-select {
  font-size: 12px;
  max-width: 120px;
}
</style>
