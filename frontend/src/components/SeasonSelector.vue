<template>
  <div
    class="season-selector text-white"
    :class="{ 'is-mobile': isMobile }"
    ref="containerRef"
  >
    <button
      class="season-trigger"
      :class="{ open: isOpen, loading: loading }"
      :disabled="loading"
      @click="toggle"
    >
      <span class="season-trigger-text">
        {{ loading ? '加载中...' : currentLabel }}
      </span>
      <svg class="season-chevron" viewBox="0 0 16 16" fill="currentColor">
        <path
          d="M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z"
        />
      </svg>
    </button>
    <Transition name="dropdown">
      <div v-if="isOpen" class="season-dropdown">
        <div
          class="season-option"
          :class="{ active: isSelectedCurrent }"
          @click="selectSeason('current')"
        >
          <span class="season-option-name">{{
            currentSeasonName || '当前赛季'
          }}</span>
          <span class="season-tag latest">最新</span>
        </div>
        <div class="season-divider" v-if="historicalSeasons.length"></div>
        <div
          v-for="s in historicalSeasons"
          :key="s.tournament_id"
          class="season-option"
          :class="{
            active: !isSelectedCurrent && selectedSeason === s.tournament_id,
          }"
          @click="selectSeason(s.tournament_id)"
        >
          <span class="season-option-name">{{
            s.display_name || s.tournament_name
          }}</span>
          <span class="season-tag history">历史</span>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue';
import { useSeason } from '../composables/useSeason.js';

defineProps({
  isMobile: { type: Boolean, default: false },
});

const {
  selectedSeason,
  availableSeasons,
  resolvedSeasonId,
  resolvedSeasonName,
  isSelectedCurrent,
  currentSeasonName,
  seasonLoading: loading,
  setSeason,
  initSeasons,
} = useSeason();

const isOpen = ref(false);
const containerRef = ref(null);

const historicalSeasons = computed(() =>
  availableSeasons.value.filter((s) => !s.is_current),
);

const currentLabel = computed(() => {
  if (isSelectedCurrent.value) return currentSeasonName.value || '当前赛季';
  const found = availableSeasons.value.find(
    (s) => s.tournament_id === resolvedSeasonId.value,
  );
  return (
    found?.display_name || resolvedSeasonName.value || selectedSeason.value
  );
});

function toggle() {
  isOpen.value = !isOpen.value;
}

function selectSeason(id) {
  setSeason(id);
  isOpen.value = false;
}

function handleClickOutside(e) {
  if (containerRef.value && !containerRef.value.contains(e.target)) {
    isOpen.value = false;
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
  initSeasons();
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<style scoped>
.season-selector {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.season-trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  color: inherit;
  font-size: 13px;
  font-weight: 500;
  padding: 5px 12px;
  cursor: pointer;
  outline: none;
  transition:
    background 0.2s,
    border-color 0.2s,
    box-shadow 0.2s;
  white-space: nowrap;
  max-width: 180px;
}

.season-trigger:hover {
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(255, 255, 255, 0.28);
}

.season-trigger:focus-visible,
.season-trigger.open {
  border-color: #4a9eff;
  box-shadow: 0 0 0 2px rgba(74, 158, 255, 0.2);
}

.season-trigger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.season-trigger-text {
  overflow: hidden;
  text-overflow: ellipsis;
}

.season-chevron {
  width: 12px;
  height: 12px;
  flex-shrink: 0;
  transition: transform 0.2s ease;
  opacity: 0.6;
}

.season-trigger.open .season-chevron {
  transform: rotate(180deg);
}

.season-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  min-width: 180px;
  max-height: 320px;
  overflow-y: auto;
  background: #1e1e2e;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  z-index: 1000;
  padding: 4px;
}

.season-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 7px;
  cursor: pointer;
  font-size: 13px;
  color: #d0d0e0;
  transition: background 0.15s;
}

.season-option:hover {
  background: rgba(255, 255, 255, 0.08);
}

.season-option.active {
  background: rgba(74, 158, 255, 0.15);
  color: #fff;
}

.season-option-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.season-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  flex-shrink: 0;
  line-height: 1.4;
}

.season-tag.latest {
  background: #22c55e;
  color: #fff;
}

.season-tag.history {
  background: #f59e0b;
  color: #000;
}

.season-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.08);
  margin: 4px 8px;
}

/* 下拉动画 */
.dropdown-enter-active {
  transition:
    opacity 0.15s ease,
    transform 0.15s ease;
}
.dropdown-leave-active {
  transition:
    opacity 0.1s ease,
    transform 0.1s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.is-mobile .season-trigger {
  font-size: 12px;
  max-width: 130px;
  padding: 4px 10px;
}

.is-mobile .season-dropdown {
  min-width: 150px;
}
</style>
