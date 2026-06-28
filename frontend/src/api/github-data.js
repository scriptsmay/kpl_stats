/**
 * kpl_data_daily static JSON data source.
 * Reads stable latest/derived URLs instead of scanning GitHub Contents API.
 *
 * Historical season path layout:
 *   Current season: derived/{season}/{page}.json, latest/{season}/{namespace}.json
 *   Historical:     seasons/{season}/derived/{page}.json,
 *                   seasons/{season}/latest/{season}/{namespace}.json,
 *                   seasons/{season}/latest/{namespace}.json (cross-season career)
 */
import axios from 'axios';

const GITHUB_PROXY = 'https://github.matishare.com/proxy/';
const GITHUB_BASE = `${GITHUB_PROXY}https://raw.githubusercontent.com/scriptsmay/kpl_data_daily/main/data`;
const CACHE_PREFIX = 'kpl_data_v2:';
const CACHE_TTL = 24 * 60 * 60 * 1000;
const HISTORICAL_CACHE_TTL = 7 * 24 * 60 * 60 * 1000; // 7 days for frozen historical data
const SUPPORTED_SCHEMA_VERSION = 1;

export const DEFAULT_SEASON = 'current';

let currentSeasonCache = null;
let seasonNameMap = null;

// ─── Cache Layer ────────────────────────────────────────────

function getLocalCache(key) {
  try {
    const raw = localStorage.getItem(CACHE_PREFIX + key);
    if (!raw) return null;
    const { data, timestamp } = JSON.parse(raw);
    const ttl = data?.season && data.season !== getCurrentSeasonIdSync() ? HISTORICAL_CACHE_TTL : CACHE_TTL;
    if (Date.now() - timestamp > ttl) return null;
    return data;
  } catch {
    return null;
  }
}

function setLocalCache(key, data) {
  try {
    localStorage.setItem(CACHE_PREFIX + key, JSON.stringify({ data, timestamp: Date.now() }));
  } catch {
    // Ignore storage quota errors.
  }
}

async function fetchJson(path, cacheKey) {
  const cached = getLocalCache(cacheKey);
  if (cached) return cached;

  const data = await fetchRemoteJson(path);
  setLocalCache(cacheKey, data);
  return data;
}

async function fetchRemoteJson(path) {
  const url = `${GITHUB_BASE}/${path}`;
  const { data } = await axios.get(url, { timeout: 15000 });
  return data;
}

async function fetchRemoteJsonOrNull(path) {
  try {
    return await fetchRemoteJson(path);
  } catch {
    return null;
  }
}

// ─── Validation ─────────────────────────────────────────────

function isCurrentSeasonPayload(payload) {
  return payload?.schema_version === SUPPORTED_SCHEMA_VERSION && payload?.current && payload?.build_id;
}

function validateDerivedPayload(payload, season, buildId) {
  return (
    payload?.schema_version === SUPPORTED_SCHEMA_VERSION &&
    payload?.season === season &&
    (!buildId || payload?.build_id === buildId)
  );
}

// ─── Season Resolution ──────────────────────────────────────

/** Synchronous helper — returns the last-known current season ID (may be null). */
function getCurrentSeasonIdSync() {
  return currentSeasonCache?.current || null;
}

export async function getCurrentSeason() {
  if (currentSeasonCache) return currentSeasonCache;

  const cacheKey = `current-season.v${SUPPORTED_SCHEMA_VERSION}`;
  const cached = getLocalCache(cacheKey);

  try {
    const data = await fetchRemoteJson('latest/current-season.json');
    if (!isCurrentSeasonPayload(data)) {
      throw new Error('当前赛季数据版本不兼容');
    }
    setLocalCache(cacheKey, data);
    currentSeasonCache = data;
    return currentSeasonCache;
  } catch (err) {
    if (isCurrentSeasonPayload(cached)) {
      console.warn('当前赛季远程数据不可用，使用本地缓存', err);
      currentSeasonCache = cached;
      return currentSeasonCache;
    }
    throw err;
  }
}

/**
 * Resolve season alias to real ID + metadata.
 * @param {string} season - 'current' or a real season ID like 'KPL2026S1'
 * @returns {{ seasonId: string, seasonName: string, buildId: string, sourceType: 'current'|'historical', manifest: object|null }}
 */
export async function resolveSeasonId(season) {
  if (season && season !== DEFAULT_SEASON) {
    // Historical season — fetch its manifest for build_id
    const manifest = await fetchSeasonManifest(season);
    return {
      seasonId: season,
      seasonName: manifest ? `${season}` : season,
      buildId: manifest?.build_id || null,
      sourceType: 'historical',
      manifest,
    };
  }
  const current = await getCurrentSeason();
  return {
    seasonId: current.current,
    seasonName: current.season_name || current.current,
    buildId: current.build_id,
    sourceType: 'current',
    manifest: null,
  };
}

async function resolveSeason(season) {
  if (season && season !== DEFAULT_SEASON) return season;
  const current = await getCurrentSeason();
  return current.current;
}

// ─── Historical Path Fallback ───────────────────────────────

/**
 * Fetch with fallback: try current-season path first, then historical path.
 * @param {string} currentPath - e.g. 'derived/KPL2026S2/abilities.json'
 * @param {string} historicalPath - e.g. 'seasons/KPL2026S1/derived/abilities.json'
 * @param {string} cacheKey
 */
async function fetchWithFallback(currentPath, historicalPath, cacheKey) {
  const cached = getLocalCache(cacheKey);
  if (cached) return cached;

  // Try current-season path first
  let data = await fetchRemoteJsonOrNull(currentPath);
  if (data) {
    setLocalCache(cacheKey, data);
    return data;
  }

  // Fallback to historical path
  data = await fetchRemoteJsonOrNull(historicalPath);
  if (data) {
    setLocalCache(cacheKey, data);
    return data;
  }

  throw new Error(`数据不可用: ${currentPath} 和 ${historicalPath} 均无法访问`);
}

// ─── Season Manifest & List ─────────────────────────────────

/**
 * Fetch the season manifest for historical data validation.
 * @param {string} seasonId
 * @returns {object|null}
 */
export async function fetchSeasonManifest(seasonId) {
  const cacheKey = `manifest.${seasonId}.v${SUPPORTED_SCHEMA_VERSION}`;
  try {
    return await fetchJson(`seasons/${seasonId}/manifest.json`, cacheKey);
  } catch {
    return null;
  }
}

/**
 * Get available seasons from seasons-list.json for the selector.
 * @returns {Array<{tournament_id: string, tournament_name: string, is_latest: number, season_type: string}>}
 */
export async function getAvailableSeasons() {
  const cacheKey = `seasons-list.v${SUPPORTED_SCHEMA_VERSION}`;
  try {
    const list = await fetchJson('latest/seasons-list.json', cacheKey);
    const seasons = Array.isArray(list) ? list : list?.data || [];
    const current = await getCurrentSeason();
    // Ensure current season is marked
    return seasons.map((s) => ({
      ...s,
      is_current: s.tournament_id === current.current,
    }));
  } catch (err) {
    console.warn('获取赛季列表失败，使用兜底列表', err);
    const current = await getCurrentSeason();
    return [
      { tournament_id: current.current, tournament_name: current.season_name || current.current, is_latest: 1, is_current: true, season_type: 'league' },
    ];
  }
}

// ─── Data Fetching (with historical path fallback) ──────────

export async function fetchLatest(namespace, season = DEFAULT_SEASON) {
  const resolvedSeason = await resolveSeason(season);
  const isHistorical = season && season !== DEFAULT_SEASON;
  const cacheKey = `latest.${resolvedSeason}.${namespace}.v${SUPPORTED_SCHEMA_VERSION}`;

  if (isHistorical) {
    // Historical: try current path first, then seasons/{season}/latest/{season}/{namespace}.json
    const currentPath = `latest/${resolvedSeason}/${namespace}.json`;
    const historicalPath = `seasons/${resolvedSeason}/latest/${resolvedSeason}/${namespace}.json`;
    return fetchWithFallback(currentPath, historicalPath, cacheKey);
  }

  // Current season: direct path
  return fetchJson(`latest/${resolvedSeason}/${namespace}.json`, cacheKey);
}

export async function fetchLatestGlobal(namespace) {
  const cacheKey = `latest.global.${namespace}.v${SUPPORTED_SCHEMA_VERSION}`;
  return fetchJson(`latest/${namespace}.json`, cacheKey);
}

export async function fetchDerived(pageKey, season = DEFAULT_SEASON) {
  const resolvedSeason = await resolveSeason(season);
  const isHistorical = season && season !== DEFAULT_SEASON;

  // For historical seasons, use manifest build_id; for current, use current-season build_id
  let buildId;
  if (isHistorical) {
    const manifest = await fetchSeasonManifest(resolvedSeason);
    buildId = manifest?.build_id || null;
  } else {
    const current = await getCurrentSeason();
    buildId = current.build_id;
  }

  const cacheKey = `derived.${resolvedSeason}.${pageKey}.v${SUPPORTED_SCHEMA_VERSION}.${buildId || 'nocache'}`;
  const cachePrefix = `derived.${resolvedSeason}.${pageKey}.v${SUPPORTED_SCHEMA_VERSION}.`;

  const cached = getLocalCache(cacheKey);
  if (cached && validateDerivedPayload(cached, resolvedSeason, buildId)) {
    return cached;
  }

  const derivedPath = isHistorical
    ? `seasons/${resolvedSeason}/derived/${pageKey}.json`
    : `derived/${resolvedSeason}/${pageKey}.json`;

  const payload = await fetchRemoteJsonOrNull(derivedPath);

  if (!payload) {
    // Try last valid cache as final fallback
    const fallback = getLastValidDerivedCache(cachePrefix, resolvedSeason, buildId);
    if (fallback) return fallback;
    throw new Error(`${pageKey} 派生数据不可用 (season=${resolvedSeason})`);
  }

  if (!validateDerivedPayload(payload, resolvedSeason, buildId)) {
    const fallback = getLastValidDerivedCache(cachePrefix, resolvedSeason, buildId);
    if (fallback) return fallback;
    throw new Error(`${pageKey} 派生数据版本不兼容 (season=${resolvedSeason})`);
  }

  setLocalCache(cacheKey, payload);
  return payload;
}

function getLastValidDerivedCache(cachePrefix, season, buildId) {
  try {
    const candidates = Object.keys(localStorage)
      .filter((key) => key.startsWith(CACHE_PREFIX + cachePrefix))
      .map((key) => getLocalCache(key.slice(CACHE_PREFIX.length)))
      .filter((payload) => payload?.schema_version === SUPPORTED_SCHEMA_VERSION && payload?.season === season);

    if (buildId) {
      const exact = candidates.find((p) => p?.build_id === buildId);
      if (exact) return exact;
    }

    return candidates
      .sort((a, b) => String(b.generated_at || '').localeCompare(String(a.generated_at || '')))[0] || null;
  } catch {
    return null;
  }
}

async function derivedData(pageKey, season, fallbackFn) {
  try {
    const payload = await fetchDerived(pageKey, season);
    return payload.data;
  } catch (err) {
    console.warn(`读取 derived/${pageKey} (season=${season}) 失败，降级到 latest`, err);
    return fallbackFn();
  }
}

// ─── Public API Functions ───────────────────────────────────

export const getPlayerAbilities = (season = DEFAULT_SEASON) =>
  derivedData('abilities', season, () => fetchLatest('player-abilities', season));

export const getAllPlayerStats = (season = DEFAULT_SEASON) =>
  derivedData('ranking', season, () => fetchLatest('all-player-stats', season));

export const getHeroWinRate = (season = DEFAULT_SEASON) => fetchLatest('hero-win-rate', season);

export const getPlayerHeroSummary = (season = DEFAULT_SEASON) =>
  derivedData('heroes', season, async () => fetchLatest('player-hero-summary', season)).then((data) => {
    if (data?.summary) return { code: 200, data: data.summary };
    return data;
  });

export const getPlayerHeroBattles = (season = DEFAULT_SEASON) =>
  derivedData('heroes', season, async () => fetchLatest('player-hero-battles', season)).then((data) => {
    if (data?.battles) return { heroes: data.battles };
    return data;
  });

export const getPlayerWinStats = (season = DEFAULT_SEASON) =>
  derivedData('win-lose', season, async () => fetchLatest('player-win-stats', season)).then((data) => {
    if (data?.win) return { code: 200, data: data.win ? [data.win] : [] };
    return data;
  });

export const getPlayerLoseStats = (season = DEFAULT_SEASON) =>
  derivedData('win-lose', season, async () => fetchLatest('player-lose-stats', season)).then((data) => {
    if (data?.lose) return { code: 200, data: data.lose && Object.keys(data.lose).length ? [data.lose] : [] };
    return data;
  });

export const getTeamDamageDistribution = (season = DEFAULT_SEASON) =>
  fetchLatest('team-damage-distribution', season);

export const getWinAffinityAnalysis = (season = DEFAULT_SEASON) =>
  fetchLatest('win-affinity-analysis', season);

export const getPlayerCareer = (season = DEFAULT_SEASON) => {
  // Career data: try season-specific first, then global
  if (season && season !== DEFAULT_SEASON) {
    return fetchLatest('player-career-wuyan', season).catch(() => fetchLatestGlobal('player-career-wuyan'));
  }
  return fetchLatestGlobal('player-career-wuyan');
};

export const getInsights = (season = DEFAULT_SEASON) =>
  fetchDerived('insights', season).then((payload) => payload.data);

export async function getAiInsights(season = DEFAULT_SEASON) {
  try {
    const payload = await fetchDerived('ai-insights', season);
    return payload.data;
  } catch (err) {
    if (import.meta.env.DEV) {
      console.warn('[getAiInsights] AI insights unavailable:', err.message);
    }
    return null;
  }
}

export const getGrowthPath = (season = DEFAULT_SEASON) =>
  fetchDerived('growth-path', season).then((payload) => payload.data);

export const getTrendSummary = (season = DEFAULT_SEASON) =>
  fetchDerived('trend-summary', season).then((payload) => payload.data);

export const clearDataCache = () => {
  const keys = Object.keys(localStorage).filter((k) => k.startsWith(CACHE_PREFIX));
  keys.forEach((k) => localStorage.removeItem(k));
  currentSeasonCache = null;
  seasonNameMap = null;
};

export async function getSeasonNameMap() {
  if (seasonNameMap) return seasonNameMap;
  try {
    const current = await getCurrentSeason();
    const list = await fetchLatestGlobal('seasons-list');
    seasonNameMap = {};
    (Array.isArray(list) ? list : list.data || []).forEach((s) => {
      seasonNameMap[s.tournament_id] = s.tournament_name;
    });
    seasonNameMap[DEFAULT_SEASON] = current.season_name || current.current;
    seasonNameMap[current.current] = current.season_name || current.current;
    return seasonNameMap;
  } catch (err) {
    console.error('获取赛季列表失败:', err);
    return { KPL2026S2: 'KPL2026夏季赛', KPL2026S1: 'KPL2026春季赛', KCC2025: '2025挑战者杯' };
  }
}

// ─── Debug Helpers ──────────────────────────────────────────

export function debugSeasonInfo() {
  return {
    currentSeasonCache: currentSeasonCache?.current,
    buildId: currentSeasonCache?.build_id,
    cachePrefix: CACHE_PREFIX,
    cachedKeys: Object.keys(localStorage).filter((k) => k.startsWith(CACHE_PREFIX)).length,
  };
}
