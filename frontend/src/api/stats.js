import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

// 正常获取数据（使用缓存）
export const getCareerData = (forceRefresh = false) =>
  api.get('/player/career', { params: { force_refresh: forceRefresh } });

// 手动刷新缓存
export const refreshCache = (force = true) => api.post('/admin/refresh', null, { params: { force } });

// 查看缓存信息
export const getCacheInfo = () => api.get('/admin/cache_info');

// 清除缓存
export const clearCache = () => api.delete('/admin/cache');
