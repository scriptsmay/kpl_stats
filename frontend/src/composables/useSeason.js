/**
 * Global season state composable.
 * Single shared reactive state across all pages.
 * Persistence: URL ?season= > localStorage > 'current'.
 */
import { ref, computed, watch } from 'vue';
import { DEFAULT_SEASON, resolveSeasonId, getAvailableSeasons, getCurrentSeason } from '../api/github-data.js';
import { getPlayerSeasons } from '../api/stats.js';

const STORAGE_KEY = 'kpl_selected_season';

// ─── Shared singleton state ─────────────────────────────────
const selectedSeason = ref(loadInitialSeason());
const availableSeasons = ref([]);
const resolvedInfo = ref(null);
const seasonLoading = ref(false);
const seasonError = ref(null);

let initPromise = null;

function loadInitialSeason() {
  // 1. URL param
  if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search);
    const urlSeason = params.get('season');
    if (urlSeason) return urlSeason;
  }
  // 2. localStorage
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) return stored;
  } catch {}
  // 3. Default
  return DEFAULT_SEASON;
}

function persistSeason(season) {
  try {
    localStorage.setItem(STORAGE_KEY, season);
  } catch {}
}

export function useSeason() {
  // ─── Load available seasons (once) ──────────────────────
  async function initSeasons() {
    if (initPromise) return initPromise;
    if (availableSeasons.value.length > 0) return;

    seasonLoading.value = true;
    seasonError.value = null;
    initPromise = (async () => {
      try {
        const [playerSeasonsRes, currentSeason] = await Promise.all([
          getPlayerSeasons().catch(() => ({ data: { data: [] } })),
          getCurrentSeason().catch(() => null),
        ]);
        const playerSeasonData = playerSeasonsRes.data?.data || [];
        const currentId = currentSeason?.current || null;

        availableSeasons.value = playerSeasonData.map((s) => ({
          tournament_id: s.season_id,
          tournament_name: s.season_name || s.season_id,
          display_name: s.season_name || s.season_id,
          is_current: currentId ? s.season_id === currentId : s.season_id === DEFAULT_SEASON,
        }));
      } catch (err) {
        seasonError.value = err.message;
        console.warn('初始化赛季列表失败:', err);
      } finally {
        seasonLoading.value = false;
        initPromise = null;
      }
    })();

    return initPromise;
  }

  // ─── Resolve current selection ──────────────────────────
  async function resolveCurrent() {
    try {
      resolvedInfo.value = await resolveSeasonId(selectedSeason.value);
    } catch (err) {
      console.warn('解析赛季失败:', err);
      resolvedInfo.value = {
        seasonId: selectedSeason.value,
        seasonName: selectedSeason.value,
        buildId: null,
        sourceType: 'historical',
        manifest: null,
      };
    }
  }

  // ─── Computed ───────────────────────────────────────────
  const currentSeasonId = computed(() => resolvedInfo.value?.seasonId || selectedSeason.value);
  const currentSeasonName = computed(() => {
    if (resolvedInfo.value?.sourceType === 'current') {
      return resolvedInfo.value.seasonName;
    }
    const found = availableSeasons.value.find((s) => s.tournament_id === selectedSeason.value);
    return found?.display_name || resolvedInfo.value?.seasonName || selectedSeason.value;
  });
  const isCurrentSeason = computed(() => resolvedInfo.value?.sourceType === 'current');
  const seasonBuildId = computed(() => resolvedInfo.value?.buildId || null);

  // ─── Actions ────────────────────────────────────────────
  function setSeason(season) {
    selectedSeason.value = season;
    persistSeason(season);
    resolveCurrent();
  }

  // Watch for external changes
  watch(selectedSeason, (val) => {
    persistSeason(val);
    resolveCurrent();
  });

  // Initialize on first use
  initSeasons().then(() => resolveCurrent());

  return {
    // State
    selectedSeason,
    availableSeasons,
    resolvedInfo,
    seasonLoading,
    seasonError,
    // Computed
    currentSeasonId,
    currentSeasonName,
    isCurrentSeason,
    seasonBuildId,
    // Actions
    setSeason,
    initSeasons,
    resolveCurrent,
  };
}
