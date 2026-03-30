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
const GITHUB_API_FILELIST = `${GITHUB_PROXY}https://api.github.com/repos/scriptsmay/kpl_data_daily/contents/data`;

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
 * @param {string} namespace - 数据命名空间，如 'player-abilities'
 * @param {string} season - 赛季 ID，如 'KPL2026S1'
 * @param {string} [date] - 可选日期 YYYYMMDD，不传则取最新
 */
async function fetchData(namespace, season, date) {
  const cacheKey = `${namespace}.${season}.${date || 'latest'}`;

  // 1. 检查缓存
  const cached = getLocalCache(cacheKey);
  if (cached) return cached;

  // 2. 如果没有指定日期，先查 GitHub 目录找最新文件
  let filename;
  if (date) {
    filename = `${namespace}.${season}.${date}.json`;
  } else {
    // 通过 GitHub API 列出目录，找到最新的文件

    try {
      const { data: files } = await axios.get(GITHUB_API_FILELIST, { timeout: 10000 });
      // 筛选匹配的文件
      const pattern = new RegExp(`^${namespace.replace('.', '\\.')}.${season.replace('.', '\\.')}.(\\d{8})\\.json$`);
      const matched = files
        .filter((f) => f.type === 'file' && pattern.test(f.name))
        .map((f) => ({ name: f.name, date: f.name.match(pattern)?.[1] }))
        .filter((f) => f.date)
        .sort((a, b) => b.date.localeCompare(a.date));

      if (matched.length === 0) {
        throw new Error(`未找到 ${namespace}.${season} 的数据文件`);
      }
      filename = matched[0].name;
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

/**
 * 获取选手能力数据
 * @param {string} season - 赛季 ID
 */
export const getPlayerAbilities = (season) => fetchData('player-abilities', season);

/**
 * 获取全选手统计数据
 * @param {string} season - 赛季 ID
 */
export const getAllPlayerStats = (season) => fetchData('all-player-stats', season);

/**
 * 获取联盟英雄胜率
 * @param {string} season - 赛季 ID
 */
export const getHeroWinRate = (season) => fetchData('hero-win-rate', season);

/**
 * 获取选手英雄胜场统计
 * @param {string} season - 赛季 ID
 */
export const getPlayerHeroSummary = (season) => fetchData('player-hero-summary', season);

/**
 * 获取选手胜场数据
 * @param {string} season - 赛季 ID
 */
export const getPlayerWinStats = (season) => fetchData('player-win-stats', season);

/**
 * 获取选手负场数据
 * @param {string} season - 赛季 ID
 */
export const getPlayerLoseStats = (season) => fetchData('player-lose-stats', season);

/**
 * 获取战队伤害分布
 * @param {string} season - 赛季 ID
 */
export const getTeamDamageDistribution = (season) => fetchData('team-damage-distribution', season);

/**
 * 获取获胜亲近度分析
 * @param {string} season - 赛季 ID
 */
export const getWinAffinityAnalysis = (season) => fetchData('win-affinity-analysis', season);

/**
 * 获取选手生涯数据
 * @param {string} season - 赛季 ID
 */
export const getPlayerCareer = (season) => fetchData('player-career-wuyan', season);

/**
 * 清除所有本地缓存
 */
export const clearDataCache = () => {
  const keys = Object.keys(localStorage).filter((k) => k.startsWith(CACHE_PREFIX));
  keys.forEach((k) => localStorage.removeItem(k));
};

/**
 * 获取当前最新赛季 ID（默认）
 */
export const DEFAULT_SEASON = 'KPL2026S1';
