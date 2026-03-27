import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

// 获取选手生涯数据
export const getCareerData = (seasonType = 'all', forceRefresh = false) =>
  api.get('/player/career', { 
    params: { 
      season_type: seasonType,
      force_refresh: forceRefresh 
    } 
  });

// 手动刷新缓存
export const refreshCache = (seasonType = 'all', force = true) => 
  api.post('/admin/refresh', null, { 
    params: { 
      season_type: seasonType,
      force 
    } 
  });

// 查看单个缓存信息
export const getCacheInfo = (seasonType = 'all') => 
  api.get('/admin/cache_info', { 
    params: { season_type: seasonType } 
  });

// 查看所有缓存状态
export const getAllCacheInfo = () => 
  api.get('/admin/cache_list');

// 清除缓存
export const clearCache = (seasonType = 'all') => 
  api.delete('/admin/cache', { 
    params: { season_type: seasonType } 
  });

// 获取存档列表
export const getArchiveList = () => 
  api.get('/admin/archive_list');

// 获取指定日期存档
export const getArchive = (date, seasonType = 'all') => 
  api.get(`/admin/archive/${date}`, { 
    params: { season_type: seasonType } 
  });

// 获取赛季列表
export const getSeasonsList = (project = 'KPL') => 
  api.get('/seasons/list', { 
    params: { project } 
  });

// 获取赛季名称映射
export const getSeasonNameMap = () =>
  api.get('/seasons/name_map');

// 获取比赛高光记录
export const getMatchRecords = () =>
  api.get('/match/records');
