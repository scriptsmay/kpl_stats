from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

app = FastAPI(title="KPL 选手数据代理 API", version="1.0.0")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置
THIRD_PARTY_API_URL = os.getenv("THIRD_PARTY_API_URL", "https://api.example.com/player/career")
API_KEY = os.getenv("API_KEY", "")
DATA_DIR = Path(__file__).parent / "data"
CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))  # 默认缓存 24 小时
SEASONS_API_URL = os.getenv("SEASONS_API_URL", "http://47.102.210.150:5006/seasons/list")

# Halo 博客 API 配置
HALO_API_BASE = os.getenv("HALO_API_BASE", "https://blog.kplwuyan.site")
HALO_API_URL = f"{HALO_API_BASE}/apis/api.console.halo.run/v1alpha1"
HALO_API_TOKEN = os.getenv("HALO_API_TOKEN", "")
HALO_POSTS_CACHE_TTL_HOURS = int(os.getenv("HALO_POSTS_CACHE_TTL_HOURS", "1"))  # 默认缓存 1 小时

# Halo 视频 API 配置
HALO_VIDEO_GROUP_ID = os.getenv("HALO_VIDEO_GROUP_ID", "attachment-group-25ptmssm")
HALO_VIDEO_CACHE_TTL_SECONDS = int(os.getenv("HALO_VIDEO_CACHE_TTL_SECONDS", "600"))  # 默认缓存 10 分钟

# 高光记录 API 配置
RECORDS_API_URL = os.getenv("RECORDS_API_URL", "http://47.102.210.150:5022/api/records")
RECORDS_CACHE_TTL_HOURS = int(os.getenv("RECORDS_CACHE_TTL_HOURS", "24"))  # 默认缓存 24 小时（每天 0 点更新）

# 确保 data 目录存在
DATA_DIR.mkdir(exist_ok=True)

# 赛季类型常量
SEASON_TYPES = ['all', 'league', 'cup']

# 赛季名称缓存（内存缓存）
season_name_cache = {
    "data": None,
    "timestamp": None,
    "ttl_seconds": 86400  # 24 小时缓存
}

# 高光记录缓存（内存缓存）
match_records_cache = {
    "data": None,
    "timestamp": None,
    "ttl_hours": RECORDS_CACHE_TTL_HOURS
}

def get_cache_file(season_type: str = 'all') -> Path:
    """获取指定赛季类型的缓存文件路径"""
    return DATA_DIR / f"cache.{season_type}.json"

def get_archive_filename(season_type: str = 'all'):
    """获取指定赛季类型的今日存档文件名"""
    today = datetime.now().strftime("%Y-%m-%d")
    return DATA_DIR / f"cache.{season_type}.{today}.json"

def save_to_cache(data: dict, season_type: str = 'all', from_force: bool = False):
    """保存数据到本地文件缓存，并创建每日存档"""
    now = datetime.now()
    cache_data = {
        "timestamp": now.isoformat(),
        "season_type": season_type,
        "data": data,
        "from_force": from_force
    }

    # 保存主缓存文件
    cache_file = get_cache_file(season_type)
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)

    # 保存每日存档
    archive_file = get_archive_filename(season_type)
    with open(archive_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)

    print(f"[{now}] 缓存已保存 [{season_type}]，来源：{'强制刷新' if from_force else '自动更新'}")
    print(f"[{now}] 存档已保存 [{season_type}]：{archive_file}")

def load_from_cache(season_type: str = 'all'):
    """从本地文件加载缓存"""
    cache_file = get_cache_file(season_type)
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"读取缓存失败 [{season_type}]: {e}")
            return None
    return None

def is_cache_valid(cache_data: dict) -> bool:
    """检查缓存是否有效"""
    if not cache_data:
        return False

    try:
        cache_time = datetime.fromisoformat(cache_data["timestamp"])
        return datetime.now() - cache_time < timedelta(hours=CACHE_TTL_HOURS)
    except (KeyError, ValueError):
        return False

def get_archive_list():
    """获取所有存档文件列表"""
    if not DATA_DIR.exists():
        return []

    archives = []
    for f in DATA_DIR.glob("cache.*.*.json"):
        # 跳过主缓存文件
        if f.name.startswith('cache.') and f.name.count('.') == 2:
            continue
        try:
            stat = f.stat()
            # 解析文件名：cache.{season_type}.{date}.json
            parts = f.stem.split('.')
            if len(parts) >= 3:
                season_type = parts[1]
                date = parts[2]
                archives.append({
                    "filename": f.name,
                    "season_type": season_type,
                    "date": date,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        except Exception as e:
            print(f"读取存档文件失败：{e}")

    # 按日期降序排序
    return sorted(archives, key=lambda x: x["date"], reverse=True)

# ============= Halo 博客缓存函数 =============

def get_halo_posts_cache_file() -> Path:
    """获取 Halo 文章列表缓存文件路径"""
    return DATA_DIR / "cache.halo.posts.json"

def save_halo_posts_cache(data: dict):
    """保存 Halo 文章列表到缓存"""
    now = datetime.now()
    cache_data = {
        "timestamp": now.isoformat(),
        "data": data
    }
    cache_file = get_halo_posts_cache_file()
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    print(f"[{now}] Halo 文章列表缓存已保存")

def load_halo_posts_cache():
    """从本地文件加载 Halo 文章列表缓存"""
    cache_file = get_halo_posts_cache_file()
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"读取 Halo 缓存失败：{e}")
            return None
    return None

def is_halo_posts_cache_valid(cache_data: dict) -> bool:
    """检查 Halo 文章列表缓存是否有效"""
    if not cache_data:
        return False
    try:
        cache_time = datetime.fromisoformat(cache_data["timestamp"])
        return datetime.now() - cache_time < timedelta(hours=HALO_POSTS_CACHE_TTL_HOURS)
    except (KeyError, ValueError):
        return False

async def fetch_halo_posts_from_api(size: int = 3):
    """从 Halo API 获取文章列表"""
    try:
        async with httpx.AsyncClient() as client:
            headers = {}
            if HALO_API_TOKEN:
                headers["Authorization"] = f"Bearer {HALO_API_TOKEN}"

            # Halo 控制台 API 端点：获取已发布的文章
            request_url = f"{HALO_API_URL}/posts"
            params = {
                "size": size,
                "publishPhase": "PUBLISHED",
                "sort": "spec.publishTime,desc"
            }

            print(f"[{datetime.now()}] 开始请求 Halo API: {request_url}")
            response = await client.get(
                request_url,
                headers=headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            halo_data = response.json()

            # 精简数据，只返回前端需要的字段
            simplified_items = []
            for item in halo_data.get('items', []):
                post = item.get('post', {})
                spec = post.get('spec', {})
                status = post.get('status', {})

                # 处理封面图
                cover = spec.get('cover', '')
                if cover and not cover.startswith('http'):
                    cover = f"{HALO_API_BASE}{cover}"

                # 处理摘要
                excerpt_obj = spec.get('excerpt', {})
                excerpt = excerpt_obj.get('raw', '') if isinstance(excerpt_obj, dict) else excerpt_obj
                if not excerpt:
                    excerpt = status.get('excerpt', '')

                simplified_items.append({
                    "title": spec.get('title', '无标题'),
                    "cover": cover,
                    "excerpt": excerpt,
                    "publishTime": spec.get('publishTime', ''),
                    "permalink": status.get('permalink', '#')
                })

            print(f"[{datetime.now()}] Halo API 请求成功，共 {len(simplified_items)} 篇文章")
            return {"items": simplified_items}
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Halo API 请求超时")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Halo API 错误：{e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 Halo 文章失败：{str(e)}")

# ============= Halo 视频缓存函数 =============

def get_halo_video_cache_file() -> Path:
    """获取 Halo 视频列表缓存文件路径"""
    return DATA_DIR / "cache.halo.videos.json"

def save_halo_video_cache(data: list):
    """保存 Halo 视频列表到缓存"""
    now = datetime.now()
    cache_data = {
        "timestamp": now.isoformat(),
        "items": data
    }
    cache_file = get_halo_video_cache_file()
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    print(f"[{now}] Halo 视频列表缓存已保存")

def load_halo_video_cache():
    """从本地文件加载 Halo 视频列表缓存"""
    cache_file = get_halo_video_cache_file()
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"读取 Halo 视频缓存失败：{e}")
            return None
    return None

def is_halo_video_cache_valid(cache_data: dict) -> bool:
    """检查 Halo 视频列表缓存是否有效"""
    if not cache_data:
        return False
    try:
        cache_time = datetime.fromisoformat(cache_data["timestamp"])
        return (datetime.now() - cache_time).total_seconds() < HALO_VIDEO_CACHE_TTL_SECONDS
    except (KeyError, ValueError):
        return False

async def fetch_halo_videos_from_api():
    """从 Halo API 获取视频附件列表"""
    try:
        async with httpx.AsyncClient() as client:
            headers = {}
            if HALO_API_TOKEN:
                headers["Authorization"] = f"Bearer {HALO_API_TOKEN}"
            
            # Halo 控制台 API 端点：获取指定分组的视频附件
            request_url = f"{HALO_API_URL}/attachments"
            params = {
                "fieldSelector": f"spec.groupName={HALO_VIDEO_GROUP_ID}",
                "accepts": "video/*",
                "size": 100
            }
            
            print(f"[{datetime.now()}] 开始请求 Halo 视频 API: {request_url}")
            response = await client.get(
                request_url,
                headers=headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            halo_data = response.json()
            items = halo_data.get('items', [])
            print(f"[{datetime.now()}] Halo 视频 API 请求成功，共 {len(items)} 个视频")
            return items
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Halo 视频 API 请求超时")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Halo 视频 API 错误：{e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 Halo 视频失败：{str(e)}")

def generate_video_cover_url(permalink: str) -> str:
    """根据视频 permalink 自动生成封面图 URL
    
    规则：/upload/test.mp4 -> /upload/test-cover.jpg
    """
    from pathlib import PurePosixPath
    
    path = PurePosixPath(permalink)
    dirname = str(path.parent) if path.parent != PurePosixPath('.') else ''
    filename = path.stem  # 不带后缀的文件名
    
    cover_path = f"{dirname}/{filename}-cover.jpg" if dirname else f"/{filename}-cover.jpg"
    return f"{HALO_API_BASE.rstrip('/')}{cover_path}"

# ============= 赛季缓存函数 =============

def is_season_cache_valid():
    """检查赛季名称缓存是否有效"""
    if not season_name_cache["data"] or not season_name_cache["timestamp"]:
        return False
    cache_time = datetime.fromisoformat(season_name_cache["timestamp"])
    return (datetime.now() - cache_time).total_seconds() < season_name_cache["ttl_seconds"]

# ============= 高光记录缓存函数 =============

def get_match_records_cache_file(season: str = 'all') -> Path:
    """获取高光记录缓存文件路径"""
    if season == 'all':
        return DATA_DIR / "cache.match_records.json"
    return DATA_DIR / f"cache.match_records.{season}.json"

def save_match_records_cache(data: list, season: str = 'all'):
    """保存高光记录到缓存"""
    now = datetime.now()
    cache_data = {
        "timestamp": now.isoformat(),
        "season": season,
        "data": data
    }
    cache_file = get_match_records_cache_file(season)
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    print(f"[{now}] 高光记录缓存已保存 [{season}]，共 {len(data)} 条")

def load_match_records_cache(season: str = 'all'):
    """从本地文件加载高光记录缓存"""
    cache_file = get_match_records_cache_file(season)
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"读取高光记录缓存失败 [{season}]：{e}")
            return None
    return None

def is_match_records_cache_valid(cache_data: dict) -> bool:
    """检查高光记录缓存是否有效"""
    if not cache_data:
        return False
    try:
        cache_time = datetime.fromisoformat(cache_data["timestamp"])
        return datetime.now() - cache_time < timedelta(hours=RECORDS_CACHE_TTL_HOURS)
    except (KeyError, ValueError):
        return False

async def fetch_match_records_from_api(season_id: str):
    """从第三方 API 获取指定赛季的高光记录"""
    try:
        async with httpx.AsyncClient() as client:
            params = {"season": season_id}
            print(f"[{datetime.now()}] 开始请求高光记录 API: {RECORDS_API_URL}, params: {params}")
            response = await client.get(
                RECORDS_API_URL,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            all_records = response.json()
            
            # 筛选出含有"无言"的记录
            wuyan_records = [
                record for record in all_records 
                if "无言" in record.get("content", "")
            ]
            
            print(f"[{datetime.now()}] 高光记录 API 请求成功 [{season_id}]，共 {len(all_records)} 条，筛选出无言相关 {len(wuyan_records)} 条")
            return wuyan_records
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="高光记录 API 请求超时")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"高光记录 API 错误：{e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取高光记录失败：{str(e)}")

async def fetch_seasons_from_api(project: str = 'KPL'):
    """从第三方 API 获取赛季列表"""
    try:
        async with httpx.AsyncClient() as client:
            params = {"project": project}
            print(f"[{datetime.now()}] 开始请求赛季列表：{SEASONS_API_URL}, params: {params}")
            response = await client.get(
                SEASONS_API_URL,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            seasons_data = response.json()
            print(f"[{datetime.now()}] 赛季列表请求成功，共 {len(seasons_data)} 个赛季")
            
            # 更新缓存
            season_name_cache["data"] = seasons_data
            season_name_cache["timestamp"] = datetime.now().isoformat()
            
            return seasons_data
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="赛季列表 API 请求超时")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"赛季列表 API 错误：{e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取赛季列表失败：{str(e)}")

def get_season_name_map():
    """获取赛季 ID 到名称的映射"""
    if not season_name_cache["data"]:
        return {}
    
    name_map = {}
    for season in season_name_cache["data"]:
        tournament_id = season.get("tournament_id", "")
        tournament_name = season.get("tournament_name", "")
        if tournament_id:
            name_map[tournament_id] = tournament_name
    return name_map

async def fetch_from_third_party(season_type: str = 'all'):
    """从第三方 API 获取数据"""
    try:
        async with httpx.AsyncClient() as client:
            headers = {}
            if API_KEY:
                headers["Authorization"] = f"Bearer {API_KEY}"

            # 构建请求 URL，添加赛季类型参数
            params = {"season_type": season_type}
            request_url = f"{THIRD_PARTY_API_URL}"
            
            print(f"[{datetime.now()}] 开始请求第三方 API: {request_url}, params: {params}")
            response = await client.get(
                request_url,
                headers=headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            third_party_data = response.json()
            print(f"[{datetime.now()}] 第三方 API 请求成功 [{season_type}]")
            
            # 如果第三方返回 { code: 200, data: {...} } 格式，解包返回 data 部分
            if isinstance(third_party_data, dict) and "data" in third_party_data:
                return third_party_data["data"]
            return third_party_data
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="第三方 API 请求超时")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"第三方 API 错误：{e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据失败：{str(e)}")

def get_player_seasons_from_cache() -> list:
    """从缓存的生涯数据中提取选手参加的所有赛季 ID"""
    # 尝试从全部赛季缓存中获取
    cache_data = load_from_cache('all')
    if not cache_data or not cache_data.get('data'):
        return []
    
    data = cache_data['data']
    seasons = []
    
    # 从赛季数据中提取
    season_stats = data.get('season_stats', [])
    for season in season_stats:
        season_id = season.get('season_id')
        if season_id and season_id not in seasons:
            seasons.append(season_id)
    
    # 从比赛详情中提取（作为补充）
    match_details = data.get('match_details', [])
    for match in match_details:
        season_id = match.get('season_id')
        if season_id and season_id not in seasons:
            seasons.append(season_id)
    
    print(f"从缓存中提取到 {len(seasons)} 个赛季：{seasons}")
    return seasons

@app.get("/api/player/seasons")
async def get_player_seasons():
    """
    获取选手参赛的所有赛季列表

    从生涯数据缓存中提取选手参加的所有赛季 ID 和名称
    """
    try:
        # 从缓存中提取选手参加的赛季
        seasons = get_player_seasons_from_cache()

        if not seasons:
            return {
                "code": 200,
                "message": "暂无赛季数据",
                "data": [],
                "from_cache": False
            }

        # 获取赛季名称映射
        if not is_season_cache_valid():
            await fetch_seasons_from_api('KPL')

        name_map = get_season_name_map()

        # 构建带名称的赛季列表
        season_list = [
            {
                "season_id": season_id,
                "season_name": name_map.get(season_id, season_id)
            }
            for season_id in seasons
        ]

        # 按赛季 ID 降序排序（新赛季在前）
        season_list.sort(key=lambda x: x["season_id"], reverse=True)

        return {
            "code": 200,
            "message": "赛季列表获取成功",
            "data": season_list,
            "from_cache": True
        }
    except Exception as e:
        print(f"获取选手赛季列表失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取赛季列表失败：{str(e)}")

# ============= API 接口 =============

@app.get("/api/player/career")
async def get_career_data(
    season_type: str = Query('all', description="赛季类型：all=全部，league=联赛，cup=杯赛"),
    force_refresh: bool = Query(False, description="是否强制刷新数据（忽略缓存）")
):
    """
    获取选手生涯数据

    参数：
    - season_type: 赛季类型 (all/league/cup)
    - force_refresh: 设置为 true 时强制从第三方 API 获取最新数据
    """
    
    # 验证赛季类型参数
    if season_type not in SEASON_TYPES:
        raise HTTPException(status_code=400, detail=f"无效的赛季类型，可选值：{SEASON_TYPES}")

    # 如果强制刷新，直接请求第三方 API
    if force_refresh:
        try:
            data = await fetch_from_third_party(season_type)
            save_to_cache(data, season_type, from_force=True)
            return {
                "code": 200,
                "message": "数据已强制刷新",
                "data": data,
                "season_type": season_type,
                "from_cache": False,
                "refresh_time": datetime.now().isoformat()
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"强制刷新失败：{str(e)}")

    # 非强制刷新，尝试使用缓存
    cache_data = load_from_cache(season_type)

    # 检查缓存是否有效
    if cache_data and is_cache_valid(cache_data):
        print(f"[{datetime.now()}] 使用缓存数据 [{season_type}]，缓存时间：{cache_data['timestamp']}")
        return {
            "code": 200,
            "message": "数据来自缓存",
            "data": cache_data["data"],
            "season_type": season_type,
            "from_cache": True,
            "cache_time": cache_data["timestamp"],
            "from_force": cache_data.get("from_force", False)
        }

    # 缓存无效，从第三方 API 获取
    try:
        print(f"[{datetime.now()}] 缓存无效，从第三方 API 获取数据 [{season_type}]")
        data = await fetch_from_third_party(season_type)
        save_to_cache(data, season_type, from_force=False)
        return {
            "code": 200,
            "message": "数据已更新",
            "data": data,
            "season_type": season_type,
            "from_cache": False,
            "refresh_time": datetime.now().isoformat()
        }
    except HTTPException:
        if cache_data:
            print(f"[{datetime.now()}] API 失败，返回过期缓存 [{season_type}]")
            return {
                "code": 200,
                "message": "数据来自过期缓存（第三方 API 暂时不可用）",
                "data": cache_data["data"],
                "season_type": season_type,
                "from_cache": True,
                "cache_time": cache_data["timestamp"],
                "is_expired": True
            }
        raise

@app.post("/api/admin/refresh")
async def refresh_cache(
    season_type: str = Query('all', description="赛季类型 (all/league/cup)"),
    force: bool = Query(True, description="是否强制刷新")
):
    """
    手动刷新缓存数据

    参数：
    - season_type: 赛季类型 (all/league/cup)，默认刷新全部
    - force: 设置为 true 时强制从第三方 API 获取
    """
    try:
        print(f"[{datetime.now()}] 收到手动刷新请求，season_type={season_type}, force={force}")

        data = await fetch_from_third_party(season_type)
        save_to_cache(data, season_type, from_force=True)

        cache_file = get_cache_file(season_type)
        cache_stat = cache_file.stat() if cache_file.exists() else None

        return {
            "code": 200,
            "message": "缓存刷新成功",
            "data": {
                "refresh_time": datetime.now().isoformat(),
                "season_type": season_type,
                "cache_file": str(cache_file),
                "cache_size": cache_stat.st_size if cache_stat else 0
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新缓存失败：{str(e)}")

@app.get("/api/admin/cache_info")
async def get_cache_info(
    season_type: str = Query('all', description="赛季类型 (all/league/cup)")
):
    """
    获取缓存信息
    """
    cache_data = load_from_cache(season_type)
    cache_file = get_cache_file(season_type)

    if not cache_data:
        return {
            "code": 200,
            "message": "缓存不存在",
            "data": {
                "exists": False,
                "season_type": season_type,
                "cache_file": str(cache_file)
            }
        }

    cache_time = datetime.fromisoformat(cache_data["timestamp"])
    is_valid = is_cache_valid(cache_data)

    return {
        "code": 200,
        "message": "缓存信息",
        "data": {
            "exists": True,
            "season_type": season_type,
            "cache_file": str(cache_file),
            "cache_time": cache_data["timestamp"],
            "is_valid": is_valid,
            "expires_in": f"{CACHE_TTL_HOURS - (datetime.now() - cache_time).total_seconds() / 3600:.1f}小时" if is_valid else "已过期",
            "from_force": cache_data.get("from_force", False),
            "file_size": cache_file.stat().st_size if cache_file.exists() else 0
        }
    }

@app.get("/api/admin/cache_list")
async def list_all_caches():
    """
    获取所有赛季类型的缓存状态
    """
    result = {}
    for st in SEASON_TYPES:
        cache_data = load_from_cache(st)
        cache_file = get_cache_file(st)
        
        if cache_data:
            cache_time = datetime.fromisoformat(cache_data["timestamp"])
            is_valid = is_cache_valid(cache_data)
            result[st] = {
                "exists": True,
                "cache_time": cache_data["timestamp"],
                "is_valid": is_valid,
                "expires_in": f"{CACHE_TTL_HOURS - (datetime.now() - cache_time).total_seconds() / 3600:.1f}小时" if is_valid else "已过期",
                "file_size": cache_file.stat().st_size if cache_file.exists() else 0
            }
        else:
            result[st] = {
                "exists": False,
                "cache_file": str(cache_file)
            }
    
    return {
        "code": 200,
        "message": "缓存列表",
        "data": result
    }

@app.get("/api/admin/archive_list")
async def list_archives():
    """
    获取历史存档列表
    """
    archives = get_archive_list()
    return {
        "code": 200,
        "message": "存档列表",
        "data": {
            "archives": archives,
            "total": len(archives)
        }
    }

@app.get("/api/admin/archive/{date}")
async def get_archive(
    date: str,
    season_type: str = Query('all', description="赛季类型 (all/league/cup)")
):
    """
    获取指定日期的存档数据

    参数：
    - date: 日期，格式 YYYY-MM-DD
    - season_type: 赛季类型
    """
    archive_file = DATA_DIR / f"cache.{season_type}.{date}.json"
    
    if not archive_file.exists():
        raise HTTPException(status_code=404, detail=f"日期 {date} 的存档不存在 (season_type={season_type})")
    
    try:
        with open(archive_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {
            "code": 200,
            "message": "存档数据",
            "data": data,
            "archive_date": date,
            "season_type": season_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取存档失败：{str(e)}")

@app.delete("/api/admin/cache")
async def clear_cache(
    season_type: str = Query('all', description="赛季类型 (all/league/cup)，all 表示清除所有类型")
):
    """
    清除缓存文件
    """
    if season_type == 'all':
        # 清除所有赛季类型的缓存
        cleared = []
        for st in SEASON_TYPES:
            cache_file = get_cache_file(st)
            if cache_file.exists():
                try:
                    os.remove(cache_file)
                    cleared.append(st)
                except Exception as e:
                    print(f"清除缓存失败 [{st}]: {e}")
        return {
            "code": 200,
            "message": "缓存已清除",
            "data": {
                "cleared_season_types": cleared,
                "cleared_at": datetime.now().isoformat()
            }
        }
    else:
        cache_file = get_cache_file(season_type)
        if cache_file.exists():
            try:
                os.remove(cache_file)
                return {
                    "code": 200,
                    "message": "缓存已清除",
                    "data": {
                        "season_type": season_type,
                        "cache_file": str(cache_file),
                        "cleared_at": datetime.now().isoformat()
                    }
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"清除缓存失败：{str(e)}")
        else:
            return {
                "code": 200,
                "message": "缓存文件不存在",
                "data": {
                    "season_type": season_type,
                    "cache_file": str(cache_file)
                }
            }

@app.get("/api/health")
async def health_check():
    """
    健康检查
    """
    cache_status = {}
    for st in SEASON_TYPES:
        cache_data = load_from_cache(st)
        cache_status[st] = {
            "exists": cache_data is not None,
            "valid": is_cache_valid(cache_data) if cache_data else False
        }

    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "cache": cache_status,
        "config": {
            "api_url": THIRD_PARTY_API_URL,
            "cache_ttl_hours": CACHE_TTL_HOURS,
            "data_dir": str(DATA_DIR),
            "season_types": SEASON_TYPES
        }
    }

@app.get("/api/seasons/list")
async def get_seasons_list(
    project: str = Query('KPL', description="项目名称，如 KPL")
):
    """
    获取赛季列表（带缓存）
    """
    try:
        # 检查缓存是否有效
        if is_season_cache_valid():
            return {
                "code": 200,
                "message": "数据来自缓存",
                "data": season_name_cache["data"],
                "from_cache": True
            }
        
        # 从第三方 API 获取
        data = await fetch_seasons_from_api(project)
        return {
            "code": 200,
            "message": "数据已更新",
            "data": data,
            "from_cache": False
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取赛季列表失败：{str(e)}")

@app.get("/api/seasons/name_map")
async def get_season_name_map_api():
    """
    获取赛季 ID 到名称的映射（方便前端使用）
    """
    try:
        # 检查缓存是否有效，无效则获取
        if not is_season_cache_valid():
            await fetch_seasons_from_api('KPL')

        name_map = get_season_name_map()
        return {
            "code": 200,
            "message": "赛季名称映射",
            "data": name_map
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取赛季名称映射失败：{str(e)}")

# ============= Halo 博客 API 接口 =============

@app.get("/api/blog/posts")
async def get_blog_posts(
    size: int = Query(3, description="获取文章数量"),
    force_refresh: bool = Query(False, description="是否强制刷新缓存")
):
    """
    获取博客文章列表（带缓存）
    
    参数：
    - size: 获取文章数量，默认 3 篇
    - force_refresh: 设置为 true 时强制从 Halo API 获取最新数据
    """
    # 如果强制刷新，直接请求 Halo API
    if force_refresh:
        try:
            data = await fetch_halo_posts_from_api(size)
            save_halo_posts_cache(data)
            return {
                "code": 200,
                "message": "数据已强制刷新",
                "data": data,
                "from_cache": False,
                "refresh_time": datetime.now().isoformat()
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"强制刷新失败：{str(e)}")

    # 非强制刷新，尝试使用缓存
    cache_data = load_halo_posts_cache()

    # 检查缓存是否有效
    if cache_data and is_halo_posts_cache_valid(cache_data):
        print(f"[{datetime.now()}] 使用 Halo 缓存数据，缓存时间：{cache_data['timestamp']}")
        return {
            "code": 200,
            "message": "数据来自缓存",
            "data": cache_data["data"],
            "from_cache": True,
            "cache_time": cache_data["timestamp"]
        }

    # 缓存无效，从 Halo API 获取
    try:
        print(f"[{datetime.now()}] 缓存无效，从 Halo API 获取数据")
        data = await fetch_halo_posts_from_api(size)
        save_halo_posts_cache(data)
        return {
            "code": 200,
            "message": "数据已更新",
            "data": data,
            "from_cache": False,
            "refresh_time": datetime.now().isoformat()
        }
    except HTTPException:
        if cache_data:
            print(f"[{datetime.now()}] Halo API 失败，返回过期缓存")
            return {
                "code": 200,
                "message": "数据来自过期缓存（Halo API 暂时不可用）",
                "data": cache_data["data"],
                "from_cache": True,
                "cache_time": cache_data["timestamp"],
                "is_expired": True
            }
        raise

@app.get("/api/blog/cache_info")
async def get_halo_cache_info():
    """
    获取 Halo 文章缓存信息
    """
    cache_data = load_halo_posts_cache()
    cache_file = get_halo_posts_cache_file()

    if not cache_data:
        return {
            "code": 200,
            "message": "缓存不存在",
            "data": {
                "exists": False,
                "cache_file": str(cache_file)
            }
        }

    cache_time = datetime.fromisoformat(cache_data["timestamp"])
    is_valid = is_halo_posts_cache_valid(cache_data)

    return {
        "code": 200,
        "message": "缓存信息",
        "data": {
            "exists": True,
            "cache_file": str(cache_file),
            "cache_time": cache_data["timestamp"],
            "is_valid": is_valid,
            "expires_in": f"{HALO_POSTS_CACHE_TTL_HOURS - (datetime.now() - cache_time).total_seconds() / 3600:.1f}小时" if is_valid else "已过期",
            "file_size": cache_file.stat().st_size if cache_file.exists() else 0
        }
    }

@app.delete("/api/blog/cache")
async def clear_halo_cache():
    """
    清除 Halo 文章缓存
    """
    cache_file = get_halo_posts_cache_file()
    if cache_file.exists():
        try:
            os.remove(cache_file)
            return {
                "code": 200,
                "message": "缓存已清除",
                "data": {
                    "cache_file": str(cache_file),
                    "cleared_at": datetime.now().isoformat()
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"清除缓存失败：{str(e)}")
    else:
        return {
            "code": 200,
            "message": "缓存文件不存在",
            "data": {
                "cache_file": str(cache_file)
            }
        }

# ============= Halo 视频 API 接口 =============

@app.get("/api/video/random")
async def get_random_video():
    """
    随机获取一个视频地址（带缓存）
    
    从 Halo 博客的视频附件分组中随机返回一个视频，包含：
    - title: 视频标题
    - url: 视频完整 URL
    - poster: 自动生成的封面图 URL
    
    缓存策略：
    - 视频列表缓存 10 分钟（可配置 HALO_VIDEO_CACHE_TTL_SECONDS）
    - 每次请求从缓存列表中随机选择一个视频
    """
    import random
    
    base_url = "https://blog.kplwuyan.site"
    items = []
    
    # 1. 检查缓存
    cache_data = load_halo_video_cache()
    if cache_data and is_halo_video_cache_valid(cache_data):
        print(f"[{datetime.now()}] 使用 Halo 视频缓存，缓存时间：{cache_data['timestamp']}")
        items = cache_data.get("items", [])
    
    # 2. 缓存无效或为空，从 API 获取
    if not items:
        try:
            print(f"[{datetime.now()}] 缓存无效，从 Halo API 获取视频列表")
            items = await fetch_halo_videos_from_api()
            if items:
                save_halo_video_cache(items)
        except HTTPException as e:
            # API 失败时，如果有过期缓存，使用过期缓存
            if cache_data and cache_data.get("items"):
                print(f"[{datetime.now()}] Halo API 失败，使用过期缓存")
                items = cache_data.get("items", [])
            else:
                raise HTTPException(status_code=500, detail=f"获取视频失败：{e.detail}")
        except Exception as e:
            if cache_data and cache_data.get("items"):
                print(f"[{datetime.now()}] Halo API 失败，使用过期缓存")
                items = cache_data.get("items", [])
            else:
                raise HTTPException(status_code=500, detail=f"获取视频失败：{str(e)}")
    
    # 3. 随机选择一个视频
    if not items:
        raise HTTPException(status_code=500, detail="视频列表为空，无法随机选择")
    
    video = random.choice(items)
    
    # 4. 解析字段
    display_name = video.get('spec', {}).get('displayName', '未命名视频')
    permalink = video.get('status', {}).get('permalink', '')

    # 拼接完整 URL
    full_url = permalink
    if permalink and permalink.startswith('/'):
        full_url = f"{HALO_API_BASE}{permalink}"

    # 5. 自动生成封面图 URL
    cover_url = ""
    if permalink:
        cover_url = generate_video_cover_url(permalink)

    return {
        "code": 200,
        "message": "随机视频获取成功",
        "data": {
            "title": display_name,
            "url": full_url,
            "poster": cover_url
        },
        "meta": {
            "total_videos": len(items),
            "cache_used": cache_data is not None and is_halo_video_cache_valid(cache_data)
        }
    }

@app.get("/api/video/list")
async def get_video_list():
    """
    获取所有视频列表（带缓存）
    
    返回缓存中的所有视频附件信息
    """
    items = []
    
    # 检查缓存
    cache_data = load_halo_video_cache()
    if cache_data and is_halo_video_cache_valid(cache_data):
        print(f"[{datetime.now()}] 使用 Halo 视频缓存，缓存时间：{cache_data['timestamp']}")
        items = cache_data.get("items", [])
    
    # 缓存无效或为空，从 API 获取
    if not items:
        try:
            print(f"[{datetime.now()}] 缓存无效，从 Halo API 获取视频列表")
            items = await fetch_halo_videos_from_api()
            if items:
                save_halo_video_cache(items)
        except HTTPException as e:
            if cache_data and cache_data.get("items"):
                print(f"[{datetime.now()}] Halo API 失败，使用过期缓存")
                items = cache_data.get("items", [])
            else:
                raise
        except Exception as e:
            if cache_data and cache_data.get("items"):
                print(f"[{datetime.now()}] Halo API 失败，使用过期缓存")
                items = cache_data.get("items", [])
            else:
                raise
    
    # 处理视频信息
    videos = []
    for video in items:
        display_name = video.get('spec', {}).get('displayName', '未命名视频')
        permalink = video.get('status', {}).get('permalink', '')

        full_url = permalink
        if permalink and permalink.startswith('/'):
            full_url = f"{HALO_API_BASE}{permalink}"

        cover_url = ""
        if permalink:
            cover_url = generate_video_cover_url(permalink)

        videos.append({
            "title": display_name,
            "url": full_url,
            "poster": cover_url
        })

    return {
        "code": 200,
        "message": "视频列表获取成功",
        "data": videos,
        "meta": {
            "total": len(videos),
            "cache_used": cache_data is not None and is_halo_video_cache_valid(cache_data)
        }
    }

@app.get("/api/video/cache_info")
async def get_halo_video_cache_info():
    """
    获取 Halo 视频缓存信息
    """
    cache_data = load_halo_video_cache()
    cache_file = get_halo_video_cache_file()

    if not cache_data:
        return {
            "code": 200,
            "message": "缓存不存在",
            "data": {
                "exists": False,
                "cache_file": str(cache_file)
            }
        }

    cache_time = datetime.fromisoformat(cache_data["timestamp"])
    is_valid = is_halo_video_cache_valid(cache_data)
    items_count = len(cache_data.get("items", []))

    return {
        "code": 200,
        "message": "缓存信息",
        "data": {
            "exists": True,
            "cache_file": str(cache_file),
            "cache_time": cache_data["timestamp"],
            "is_valid": is_valid,
            "items_count": items_count,
            "expires_in": f"{HALO_VIDEO_CACHE_TTL_SECONDS - (datetime.now() - cache_time).total_seconds():.0f}秒" if is_valid else "已过期",
            "file_size": cache_file.stat().st_size if cache_file.exists() else 0
        }
    }

@app.delete("/api/video/cache")
async def clear_halo_video_cache():
    """
    清除 Halo 视频缓存
    """
    cache_file = get_halo_video_cache_file()
    if cache_file.exists():
        try:
            os.remove(cache_file)
            return {
                "code": 200,
                "message": "缓存已清除",
                "data": {
                    "cache_file": str(cache_file),
                    "cleared_at": datetime.now().isoformat()
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"清除缓存失败：{str(e)}")
    else:
        return {
            "code": 200,
            "message": "缓存文件不存在",
            "data": {
                "cache_file": str(cache_file)
            }
        }

# ============= 高光记录 API 接口 =============

@app.get("/api/match/records")
async def get_match_records(
    season: str = Query('all', description="赛季 ID，all 表示所有赛季"),
    force_refresh: bool = Query(False, description="是否强制刷新缓存")
):
    """
    获取无言的比赛高光记录

    参数：
    - season: 赛季 ID，all 表示所有赛季
    - force_refresh: 设置为 true 时强制从第三方 API 获取最新数据
    """
    # 如果强制刷新，重新获取所有数据
    if force_refresh:
        try:
            all_records = await fetch_season_records(season)
            save_match_records_cache(all_records, season)
            return {
                "code": 200,
                "message": "数据已强制刷新",
                "data": all_records,
                "season": season,
                "from_cache": False,
                "refresh_time": datetime.now().isoformat()
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"强制刷新失败：{str(e)}")

    # 非强制刷新，尝试使用缓存
    cache_data = load_match_records_cache(season)

    # 检查缓存是否有效
    if cache_data and is_match_records_cache_valid(cache_data):
        print(f"[{datetime.now()}] 使用高光记录缓存 [{season}]，缓存时间：{cache_data['timestamp']}")
        return {
            "code": 200,
            "message": "数据来自缓存",
            "data": cache_data["data"],
            "season": season,
            "from_cache": True,
            "cache_time": cache_data["timestamp"]
        }

    # 缓存无效，重新获取
    try:
        print(f"[{datetime.now()}] 缓存无效，从第三方 API 获取高光记录 [{season}]")
        all_records = await fetch_season_records(season)
        save_match_records_cache(all_records, season)
        return {
            "code": 200,
            "message": "数据已更新",
            "data": all_records,
            "season": season,
            "from_cache": False,
            "refresh_time": datetime.now().isoformat()
        }
    except HTTPException:
        # API 失败时，如果有缓存则返回过期缓存
        if cache_data:
            print(f"[{datetime.now()}] API 失败，返回过期缓存 [{season}]")
            return {
                "code": 200,
                "message": "数据来自过期缓存（第三方 API 暂时不可用）",
                "data": cache_data["data"],
                "season": season,
                "from_cache": True,
                "cache_time": cache_data["timestamp"],
                "is_expired": True
            }
        raise

async def fetch_season_records(season: str = 'all') -> list:
    """获取指定赛季（或所有赛季）的高光记录并合并"""
    # 从缓存中提取选手参加的赛季
    all_seasons = get_player_seasons_from_cache()

    if not all_seasons:
        print("警告：未能从缓存中提取到赛季信息，使用默认赛季")
        all_seasons = ["KPL2026S1", "KCC2025"]  # 降级处理

    # 如果指定了赛季，只获取该赛季的记录
    if season != 'all':
        if season in all_seasons:
            all_seasons = [season]
        else:
            print(f"警告：指定赛季 {season} 不在选手参赛赛季列表中")
            return []

    records_list = []

    # 遍历每个赛季获取记录
    for season_id in all_seasons:
        try:
            print(f"[{datetime.now()}] 开始获取赛季 {season_id} 的高光记录")
            records = await fetch_match_records_from_api(season_id)
            records_list.extend(records)
        except HTTPException as e:
            print(f"获取赛季 {season_id} 的高光记录失败：{e.detail}")
            continue
        except Exception as e:
            print(f"获取赛季 {season_id} 的高光记录异常：{e}")
            continue

    # 按日期降序排序
    records_list.sort(key=lambda x: x.get("date", ""), reverse=True)

    print(f"[{datetime.now()}] 高光记录获取完成，共 {len(records_list)} 条")
    return records_list

# 兼容旧版本，保留 fetch_all_season_records 函数
async def fetch_all_season_records() -> list:
    """获取所有赛季的高光记录并合并（已废弃，使用 fetch_season_records）"""
    return await fetch_season_records('all')

@app.get("/api/match/records/cache_info")
async def get_match_records_cache_info(
    season: str = Query('all', description="赛季 ID")
):
    """
    获取高光记录缓存信息
    """
    cache_data = load_match_records_cache(season)
    cache_file = get_match_records_cache_file(season)

    if not cache_data:
        return {
            "code": 200,
            "message": "缓存不存在",
            "data": {
                "exists": False,
                "season": season,
                "cache_file": str(cache_file)
            }
        }

    cache_time = datetime.fromisoformat(cache_data["timestamp"])
    is_valid = is_match_records_cache_valid(cache_data)
    items_count = len(cache_data.get("data", []))

    return {
        "code": 200,
        "message": "缓存信息",
        "data": {
            "exists": True,
            "season": season,
            "cache_file": str(cache_file),
            "cache_time": cache_data["timestamp"],
            "is_valid": is_valid,
            "items_count": items_count,
            "expires_in": f"{RECORDS_CACHE_TTL_HOURS - (datetime.now() - cache_time).total_seconds() / 3600:.1f}小时" if is_valid else "已过期",
            "file_size": cache_file.stat().st_size if cache_file.exists() else 0
        }
    }

@app.delete("/api/match/records/cache")
async def clear_match_records_cache(
    season: str = Query('all', description="赛季 ID")
):
    """
    清除高光记录缓存
    """
    cache_file = get_match_records_cache_file(season)
    if cache_file.exists():
        try:
            os.remove(cache_file)
            return {
                "code": 200,
                "message": "缓存已清除",
                "data": {
                    "season": season,
                    "cache_file": str(cache_file),
                    "cleared_at": datetime.now().isoformat()
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"清除缓存失败：{str(e)}")
    else:
        return {
            "code": 200,
            "message": "缓存文件不存在",
            "data": {
                "season": season,
                "cache_file": str(cache_file)
            }
        }
