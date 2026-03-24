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

def is_season_cache_valid():
    """检查赛季名称缓存是否有效"""
    if not season_name_cache["data"] or not season_name_cache["timestamp"]:
        return False
    cache_time = datetime.fromisoformat(season_name_cache["timestamp"])
    return (datetime.now() - cache_time).total_seconds() < season_name_cache["ttl_seconds"]

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
