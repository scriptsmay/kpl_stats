/**
 * GitHub 数据源 API 模块
 * 直接从 kpl_data_daily 仓库读取 JSON 数据
 * 数据源: https://github.com/scriptsmay/kpl_data_daily
 */
import axios from 'axios';

// GitHub 代理（解决国内网络问题）
const GITHUB_PROXY = 'https://github.matishare.com/proxy/';
const GITHUB_BASE = `${GITHUB_PROXY}https://raw.githubusercontent.com/scriptsmay/kpl_data_daily/main/data`;

// 没有指定文件时读取目录列表
const GITHUB_API_FILELIST = `https://api.github.com/repos/scriptsmay/kpl_data_daily/contents/data`;

// localStorage 缓存键前缀
const CACHE_PREFIX = 'kpl_data_';
const CACHE_TTL = 24 * 60 * 60 * 1000; // 24 小时

/**
 * 从 localStorage 读取缓存
 */
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

/**
 * 写入 localStorage 缓存
 */
function setLocalCache(key, data) {
  try {
    localStorage.setItem(CACHE_PREFIX + key, JSON.stringify({ data, timestamp: Date.now() }));
  } catch {
    // storage 满了就忽略
  }
}

/**
 * 通用 GitHub 数据获取
 * 支持三种文件名格式：
 *   - namespace.season.date.json（有赛季有日期）
 *   - namespace.date.json（无赛季有日期）
 *   - namespace.json（无赛季无日期，固定文件）
 * @param {string} namespace - 数据命名空间
 * @param {string} season - 赛季 ID，空字符串表示无赛季
 * @param {string} [date] - 可选日期 YYYYMMDD
 */
async function fetchData(namespace, season, date) {
  const cacheKey = `${namespace}.${season || 'noseason'}.${date || 'latest'}`;

  // 1. 检查缓存
  const cached = getLocalCache(cacheKey);
  if (cached) return cached;

  // 2. 文件名
  let filename;
  if (date) {
    filename = season
      ? `${namespace}.${season}.${date}.json`
      : `${namespace}.${date}.json`;
  } else {
    // 通过 GitHub API 列出目录，找到最新的文件
    try {
      const { data: files } = await axios.get(GITHUB_API_FILELIST, { timeout: 10000 });

      let matched;

      if (season) {
        // 有赛季：namespace.season.date.json
        const pattern = new RegExp(`^${namespace.replace('.', '\\.')}.${season.replace('.', '\\.')}.(\\d{8})\\.json$`);
        matched = files
          .filter((f) => f.type === 'file' && pattern.test(f.name))
          .map((f) => ({ name: f.name, date: f.name.match(pattern)?.[1] }))
          .filter((f) => f.date)
          .sort((a, b) => b.date.localeCompare(a.date));
      } else {
        // 无赛季：先尝试 namespace.date.json，再尝试 namespace.json
        const datedPattern = new RegExp(`^${namespace.replace('.', '\\.')}.(\\d{8})\\.json$`);
        matched = files
          .filter((f) => f.type === 'file' && datedPattern.test(f.name))
          .map((f) => ({ name: f.name, date: f.name.match(datedPattern)?.[1] }))
          .filter((f) => f.date)
          .sort((a, b) => b.date.localeCompare(a.date));

        // 没有带日期的文件，尝试固定文件名 namespace.json
        if (matched.length === 0) {
          const fixedFile = files.find((f) => f.name === `${namespace}.json`);
          if (fixedFile) {
            filename = fixedFile.name;
          }
        }
      }

      if (!filename) {
        if (matched && matched.length > 0) {
          filename = matched[0].name;
        } else {
          throw new Error(`未找到 ${namespace}${season ? '.' + season : ''} 的数据文件`);
        }
      }
    } catch (err) {
      console.error('GitHub API 查询失败:', err);
      throw err;
    }
  }

  // 3. 获取数据
  const url = `${GITHUB_BASE}/${filename}`;
  try {
    const { data } = await axios.get(url, { timeout: 15000 });
    setLocalCache(cacheKey, data);
    return data;
  } catch (err) {
    console.error(`获取数据失败: ${url}`, err);
    throw err;
  }
}

// ====== 具体数据接口 ======

/** 选手能力数据（有赛季） */
export const getPlayerAbilities = (season) => fetchData('player-abilities', season);

/** 全选手统计数据（有赛季） */
export const getAllPlayerStats = (season) => fetchData('all-player-stats', season);

/** 联盟英雄胜率（有赛季） */
export const getHeroWinRate = (season) => fetchData('hero-win-rate', season);

/** 选手英雄胜场统计（有赛季，返回数组） */
export const getPlayerHeroSummary = (season) => fetchData('player-hero-summary', season);

/** 英雄对局详情（有赛季，无日期取最新） */
export const getPlayerHeroBattles = (season) => fetchData('player-hero-battles', season);

/** 选手胜场数据（有赛季） */
export const getPlayerWinStats = (season) => fetchData('player-win-stats', season);

/** 选手负场数据（有赛季） */
export const getPlayerLoseStats = (season) => fetchData('player-lose-stats', season);

/** 战队伤害分布（有赛季） */
export const getTeamDamageDistribution = (season) => fetchData('team-damage-distribution', season);

/** 获胜亲近度分析（有赛季） */
export const getWinAffinityAnalysis = (season) => fetchData('win-affinity-analysis', season);

/** 选手生涯数据（无赛季，跨赛季累计） */
export const getPlayerCareer = () => fetchData('player-career-wuyan', '');

/** 清除所有本地缓存 */
export const clearDataCache = () => {
  const keys = Object.keys(localStorage).filter((k) => k.startsWith(CACHE_PREFIX));
  keys.forEach((k) => localStorage.removeItem(k));
};

/** 默认赛季 */
export const DEFAULT_SEASON = 'KPL2026S1';

// 赛季名称映射（缓存）
let seasonNameMap = null;

/**
 * 获取赛季名称映射 { KPL2026S1: 'KPL2026春季赛', ... }
 */
export async function getSeasonNameMap() {
  if (seasonNameMap) return seasonNameMap;
  try {
    const res = await fetchData('seasons-list', '');
    const list = Array.isArray(res) ? res : (res.data || []);
    seasonNameMap = {};
    list.forEach(s => {
      seasonNameMap[s.tournament_id] = s.tournament_name;
    });
    return seasonNameMap;
  } catch (err) {
    console.error('获取赛季列表失败:', err);
    // 降级
    return { KPL2026S1: 'KPL2026春季赛', KCC2025: '2025挑战者杯' };
  }
}
