/**
 * Cloudflare Worker for kpl-wuyan-stats
 *
 * Responsibilities:
 * 1. Serves Vue SPA frontend static assets via env.ASSETS (run_worker_first = true)
 * 2. Proxies Halo API requests (/api/photo/list, /api/blog/posts, /api/timeline/list, /api/video/*) with Bearer token
 * 3. Serves player data from kpl_data_daily (/api/player/career, /api/match/records, etc.) for homepage & legacy consumers
 */

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS, HEAD',
  'Access-Control-Allow-Headers': '*',
  'Access-Control-Max-Age': '86400',
};

const DEFAULT_HALO_BASE = 'https://blog.kplwuyan.site';
const DEFAULT_VIDEO_GROUP = 'attachment-group-25ptmssm';
const GITHUB_RAW_BASE = 'https://raw.githubusercontent.com/scriptsmay/kpl_data_daily/main/data';
const GITHUB_PROXY_BASE = 'https://github.matishare.com/proxy/raw.githubusercontent.com/scriptsmay/kpl_data_daily/main/data';

function jsonResponse(data, status = 200, cacheTtlSeconds = 0) {
  const headers = {
    ...CORS_HEADERS,
    'Content-Type': 'application/json; charset=utf-8',
  };
  if (cacheTtlSeconds > 0) {
    headers['Cache-Control'] = `public, max-age=${Math.min(cacheTtlSeconds, 300)}, s-maxage=${cacheTtlSeconds}`;
  } else {
    headers['Cache-Control'] = 'no-cache, no-store, must-revalidate';
  }
  return new Response(JSON.stringify(data), { status, headers });
}

function errorResponse(message, status = 500) {
  return jsonResponse({ code: status, message, data: null }, status);
}

/**
 * Fetch helper with fallback from GitHub Raw to CF Worker proxy
 */
async function fetchGithubData(path) {
  const primaryUrl = `${GITHUB_RAW_BASE}/${path}`;
  try {
    const res = await fetch(primaryUrl);
    if (res.ok) return await res.json();
  } catch (e) {
    console.warn(`Primary fetch failed for ${primaryUrl}:`, e);
  }

  // Fallback to proxy
  const fallbackUrl = `${GITHUB_PROXY_BASE}/${path}`;
  const res = await fetch(fallbackUrl);
  if (!res.ok) {
    throw new Error(`Failed to fetch ${path}: status ${res.status}`);
  }
  return await res.json();
}

/**
 * Helper to fetch from Halo with authentication check and redirect protection
 */
async function fetchHaloApi(apiUrl, token) {
  if (!token) {
    throw {
      status: 401,
      message: 'HALO_API_TOKEN 未配置，请在 Cloudflare 后台设置 Secrets 或本地 .dev.vars 中配置',
    };
  }

  const headers = {
    Accept: 'application/json',
    Authorization: `Bearer ${token}`,
  };

  const res = await fetch(apiUrl, { headers, redirect: 'manual' });

  if (res.status === 302 || res.status === 401 || res.status === 403) {
    throw {
      status: 401,
      message: `Halo API 鉴权失败 (HTTP ${res.status})，请检查 HALO_API_TOKEN 是否正确或已过期`,
    };
  }

  if (!res.ok) {
    throw {
      status: res.status,
      message: `Halo API 请求异常 (HTTP ${res.status})`,
    };
  }

  const contentType = res.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    throw {
      status: 502,
      message: `Halo API 返回了非 JSON 响应 (HTTP ${res.status})`,
    };
  }

  return await res.json();
}

/**
 * Wrap GET handlers with Cloudflare edge cache (caches.default)
 */
async function withEdgeCache(request, ctx, ttlSeconds, fetcher) {
  const url = new URL(request.url);
  const forceRefresh = url.searchParams.get('force_refresh') === 'true';
  const cache = caches.default;
  const cacheKey = new Request(url.toString(), { method: 'GET' });

  if (!forceRefresh && ttlSeconds > 0) {
    try {
      const cached = await cache.match(cacheKey);
      if (cached) {
        const response = new Response(cached.body, cached);
        response.headers.set('X-CF-Cache-Status', 'HIT');
        return response;
      }
    } catch (e) {
      console.warn('Cache lookup failed:', e);
    }
  }

  const response = await fetcher();

  if (response.status === 200 && ttlSeconds > 0 && ctx && ctx.waitUntil) {
    try {
      const responseToCache = response.clone();
      ctx.waitUntil(cache.put(cacheKey, responseToCache));
    } catch (e) {
      console.warn('Cache put failed:', e);
    }
  }

  return response;
}

// ==================== Halo API Handlers ====================

async function handlePhotoList(request, env) {
  const haloBase = (env.HALO_API_BASE || DEFAULT_HALO_BASE).replace(/\/+$/, '');
  const token = env.HALO_API_TOKEN || '';

  const apiUrl = `${haloBase}/apis/console.api.photo.halo.run/v1alpha1/photos?page=1&size=20&keyword=`;
  const data = await fetchHaloApi(apiUrl, token);
  const items = data.items || [];

  const photos = items.map((item) => {
    const spec = item.spec || {};
    const metadata = item.metadata || {};
    let url = spec.url || '';
    if (url && !url.startsWith('http')) {
      url = `${haloBase}${url.startsWith('/') ? '' : '/'}${url}`;
    }
    const thumbUrl = url ? `${url}?width=800` : '';
    const labels = metadata.labels || {};

    return {
      title: spec.displayName || spec.filename || '未命名',
      url,
      thumb_url: thumbUrl,
      mediaType: spec.mediaType || 'image/jpeg',
      size: spec.size || 0,
      creationTimestamp: metadata.creationTimestamp || '',
      groupName: labels['photo.halo.run/group-name'] || '',
    };
  });

  // Sort descending by creation timestamp
  photos.sort((a, b) => (b.creationTimestamp || '').localeCompare(a.creationTimestamp || ''));
  const latestPhotos = photos.slice(0, 10);

  return jsonResponse(
    {
      code: 200,
      message: '照片列表获取成功',
      data: latestPhotos,
      from_cache: false,
      refresh_time: new Date().toISOString(),
    },
    200,
    3600 // 1 hour cache
  );
}

async function handleBlogPosts(request, env) {
  const url = new URL(request.url);
  const size = parseInt(url.searchParams.get('size') || '3', 10);
  const haloBase = (env.HALO_API_BASE || DEFAULT_HALO_BASE).replace(/\/+$/, '');
  const token = env.HALO_API_TOKEN || '';

  const apiUrl = `${haloBase}/apis/api.console.halo.run/v1alpha1/posts?size=${size}&publishPhase=PUBLISHED&sort=spec.publishTime,desc`;
  const data = await fetchHaloApi(apiUrl, token);
  const items = (data.items || []).map((item) => {
    const post = item.post || {};
    const spec = post.spec || {};
    const status = post.status || {};
    let cover = spec.cover || '';
    if (cover && !cover.startsWith('http')) {
      cover = `${haloBase}${cover.startsWith('/') ? '' : '/'}${cover}`;
    }

    let excerpt = spec.excerpt;
    if (excerpt && typeof excerpt === 'object') {
      excerpt = excerpt.raw || '';
    }
    if (!excerpt) {
      excerpt = status.excerpt || '';
    }

    return {
      title: spec.title || '无标题',
      cover,
      excerpt: excerpt || '',
      publishTime: spec.publishTime || '',
      permalink: status.permalink || '#',
    };
  });

  return jsonResponse(
    {
      code: 200,
      message: '文章列表获取成功',
      data: { items },
    },
    200,
    3600 // 1 hour cache
  );
}

async function handleTimelineList(request, env) {
  const url = new URL(request.url);
  const group = url.searchParams.get('group');
  if (!group) {
    return errorResponse('必须指定时间轴分组 ID', 400);
  }

  const haloBase = (env.HALO_API_BASE || DEFAULT_HALO_BASE).replace(/\/+$/, '');
  const token = env.HALO_API_TOKEN || '';

  const apiUrl = `${haloBase}/apis/api.timeline.xhhao.com/v1alpha1/timelines?group=${encodeURIComponent(group)}`;
  const haloData = await fetchHaloApi(apiUrl, token);

  return jsonResponse(
    {
      code: 200,
      message: '时间轴列表获取成功',
      data: haloData,
    },
    200,
    3600 // 1 hour cache
  );
}

async function fetchHaloVideos(env) {
  const haloBase = (env.HALO_API_BASE || DEFAULT_HALO_BASE).replace(/\/+$/, '');
  const token = env.HALO_API_TOKEN || '';
  const groupId = env.HALO_VIDEO_GROUP_ID || DEFAULT_VIDEO_GROUP;

  const apiUrl = `${haloBase}/apis/api.console.halo.run/v1alpha1/attachments?fieldSelector=spec.groupName%3D${encodeURIComponent(groupId)}&accepts=video%2F*&size=100`;
  const data = await fetchHaloApi(apiUrl, token);
  const items = data.items || [];

  return items.map((video) => {
    const spec = video.spec || {};
    const status = video.status || {};
    const permalink = status.permalink || '';

    let fullUrl = permalink;
    if (permalink && permalink.startsWith('/')) {
      fullUrl = `${haloBase}${permalink}`;
    }

    let coverUrl = '';
    if (permalink) {
      const lastDot = permalink.lastIndexOf('.');
      const basePath = lastDot > 0 ? permalink.substring(0, lastDot) : permalink;
      coverUrl = `${haloBase}${basePath.startsWith('/') ? '' : '/'}${basePath}-cover.jpg`;
    }

    return {
      title: spec.displayName || '未命名视频',
      url: fullUrl,
      poster: coverUrl,
    };
  });
}

async function handleVideoList(request, env) {
  const videos = await fetchHaloVideos(env);
  return jsonResponse(
    {
      code: 200,
      message: '视频列表获取成功',
      data: videos,
      meta: {
        total: videos.length,
      },
    },
    200,
    600 // 10 minutes cache
  );
}

async function handleVideoRandom(request, env) {
  const videos = await fetchHaloVideos(env);
  if (videos.length === 0) {
    return errorResponse('暂无视频', 404);
  }
  const randomVideo = videos[Math.floor(Math.random() * videos.length)];
  return jsonResponse({
    code: 200,
    message: '随机视频获取成功',
    data: randomVideo,
  });
}

// ==================== Player / Career Handlers ====================

async function handlePlayerCareer(request) {
  const url = new URL(request.url);
  const seasonType = url.searchParams.get('season_type') || 'all';

  let suffix = '';
  if (seasonType === 'league') suffix = '-league';
  if (seasonType === 'cup') suffix = '-cup';

  const data = await fetchGithubData(`latest/player-career-wuyan${suffix}.json`);
  return jsonResponse(data, 200, 3600);
}

async function handlePlayerSeasons() {
  const data = await fetchGithubData('latest/player-career-wuyan.json');
  const seasonsCovered = data?.data?.career_summary?.seasons_covered || [];
  const seasons = seasonsCovered.map((s) => ({
    season_id: s.tournament_id,
    season_name: s.tournament_name || s.tournament_id,
  }));
  return jsonResponse(
    {
      code: 200,
      message: '赛季列表获取成功',
      data: seasons,
    },
    200,
    3600
  );
}

async function handleSeasonsList() {
  const data = await fetchGithubData('latest/seasons-list.json');
  return jsonResponse(data, 200, 3600);
}

async function handleMatchRecords(request) {
  const url = new URL(request.url);
  const season = url.searchParams.get('season') || 'all';

  let records = await fetchGithubData('latest/player-match-records.json');
  if (!Array.isArray(records)) {
    records = [];
  }

  if (season !== 'all') {
    records = records.filter(
      (r) => r.tournament === season || r.tournament_id === season || r.season_id === season
    );
  }

  return jsonResponse(
    {
      code: 200,
      message: '比赛记录获取成功',
      data: records,
    },
    200,
    3600
  );
}

// ==================== Router ====================

async function handleApiRequest(request, env, ctx) {
  const url = new URL(request.url);
  const path = url.pathname.replace(/\/+$/, '');

  // OPTIONS preflight
  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: CORS_HEADERS });
  }

  try {
    switch (path) {
      // Halo Photo
      case '/api/photo/list':
        return await withEdgeCache(request, ctx, 3600, () => handlePhotoList(request, env));
      case '/api/photo/cache_info':
        return jsonResponse({ code: 200, message: '缓存信息', data: { exists: true, is_valid: true } });
      case '/api/photo/cache':
        return jsonResponse({ code: 200, message: '缓存已清除', data: null });

      // Halo Blog
      case '/api/blog/posts':
        return await withEdgeCache(request, ctx, 3600, () => handleBlogPosts(request, env));
      case '/api/blog/cache_info':
        return jsonResponse({ code: 200, message: '缓存信息', data: { exists: true, is_valid: true } });
      case '/api/blog/cache':
        return jsonResponse({ code: 200, message: '缓存已清除', data: null });

      // Halo Timeline
      case '/api/timeline/list':
        return await withEdgeCache(request, ctx, 3600, () => handleTimelineList(request, env));

      // Halo Video
      case '/api/video/list':
        return await withEdgeCache(request, ctx, 600, () => handleVideoList(request, env));
      case '/api/video/random':
        return await handleVideoRandom(request, env);
      case '/api/video/cache_info':
        return jsonResponse({ code: 200, message: '缓存信息', data: { exists: true, is_valid: true } });
      case '/api/video/cache':
        return jsonResponse({ code: 200, message: '缓存已清除', data: null });

      // Player & Records (kpl_data_daily backed)
      case '/api/player/career':
        return await withEdgeCache(request, ctx, 3600, () => handlePlayerCareer(request));
      case '/api/player/seasons':
        return await withEdgeCache(request, ctx, 3600, () => handlePlayerSeasons());
      case '/api/seasons/list':
        return await withEdgeCache(request, ctx, 3600, () => handleSeasonsList());
      case '/api/match/records':
        return await withEdgeCache(request, ctx, 3600, () => handleMatchRecords(request));
      case '/api/match/records/cache_info':
        return jsonResponse({ code: 200, message: '缓存信息', data: { exists: true, is_valid: true } });
      case '/api/match/records/cache':
        return jsonResponse({ code: 200, message: '缓存已清除', data: null });

      // Admin generic
      case '/api/admin/cache_info':
      case '/api/admin/cache_list':
        return jsonResponse({ code: 200, message: '缓存信息', data: {} });
      case '/api/admin/refresh':
      case '/api/admin/cache':
        return jsonResponse({ code: 200, message: '操作成功', data: null });

      default:
        return errorResponse(`接口不存在: ${path}`, 404);
    }
  } catch (error) {
    console.error(`API handler error [${path}]:`, error);
    const status = error.status || 500;
    const message = error.message || String(error);
    return errorResponse(`接口请求失败: ${message}`, status);
  }
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Any request to /api/* is handled by our API proxy
    if (url.pathname.startsWith('/api/') || url.pathname === '/api') {
      return handleApiRequest(request, env, ctx);
    }

    // All other requests serve SPA static assets
    return env.ASSETS.fetch(request);
  },
};
