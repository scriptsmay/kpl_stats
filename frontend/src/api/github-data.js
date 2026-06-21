/**
 * kpl_data_daily static JSON data source.
 * Reads stable latest/derived URLs instead of scanning GitHub Contents API.
 */
import axios from 'axios';

const GITHUB_PROXY = 'https://github.matishare.com/proxy/';
const GITHUB_BASE = `${GITHUB_PROXY}https://raw.githubusercontent.com/scriptsmay/kpl_data_daily/main/data`;
const CACHE_PREFIX = 'kpl_data_';
const CACHE_TTL = 24 * 60 * 60 * 1000;
const SUPPORTED_SCHEMA_VERSION = 1;

export const DEFAULT_SEASON = 'current';

let currentSeasonCache = null;
let seasonNameMap = null;

function getLocalCache(key) {
  try {
    const raw = localStorage.getItem(CACHE_PREFIX + key);
    if (!raw) return null;
    const { data, timestamp } = JSON.parse(raw);
    if (Date.now() - timestamp > CACHE_TTL) return null;
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

function isCurrentSeasonPayload(payload) {
  return payload?.schema_version === SUPPORTED_SCHEMA_VERSION && payload?.current && payload?.build_id;
}

function validateDerivedPayload(payload, currentSeason) {
  return (
    payload?.schema_version === SUPPORTED_SCHEMA_VERSION &&
    payload?.season === currentSeason.current &&
    payload?.build_id === currentSeason.build_id
  );
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

async function resolveSeason(season) {
  if (season && season !== DEFAULT_SEASON) return season;
  const current = await getCurrentSeason();
  return current.current;
}

async function fetchLatest(namespace, season = DEFAULT_SEASON) {
  const resolvedSeason = await resolveSeason(season);
  const cacheKey = `latest.${resolvedSeason}.${namespace}.v${SUPPORTED_SCHEMA_VERSION}`;
  return fetchJson(`latest/${resolvedSeason}/${namespace}.json`, cacheKey);
}

async function fetchLatestGlobal(namespace) {
  const cacheKey = `latest.global.${namespace}.v${SUPPORTED_SCHEMA_VERSION}`;
  return fetchJson(`latest/${namespace}.json`, cacheKey);
}

export async function fetchDerived(pageKey, season = DEFAULT_SEASON) {
  const current = await getCurrentSeason();
  const resolvedSeason = await resolveSeason(season);
  const cacheKey = `derived.${resolvedSeason}.${pageKey}.v${SUPPORTED_SCHEMA_VERSION}.${current.build_id}`;
  const cachePrefix = `derived.${resolvedSeason}.${pageKey}.v${SUPPORTED_SCHEMA_VERSION}.`;

  const cached = getLocalCache(cacheKey);
  if (cached && validateDerivedPayload(cached, { ...current, current: resolvedSeason })) {
    return cached;
  }

  const payload = await fetchRemoteJson(`derived/${resolvedSeason}/${pageKey}.json`);
  if (!validateDerivedPayload(payload, { ...current, current: resolvedSeason })) {
    const fallback = getLastValidDerivedCache(cachePrefix, resolvedSeason, current.build_id);
    if (fallback) return fallback;
    throw new Error(`${pageKey} 派生数据正在发布或版本不兼容`);
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
    console.warn(`读取 derived/${pageKey} 失败，降级到 latest`, err);
    return fallbackFn();
  }
}

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

export const getPlayerCareer = () => fetchLatestGlobal('player-career-wuyan');

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
