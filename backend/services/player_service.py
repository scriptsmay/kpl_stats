# player_service.py — 选手数据 API 调用 + 缓存逻辑

import json
from datetime import datetime, timedelta
from pathlib import Path

import httpx
from fastapi import HTTPException

from config import (
    DATA_DIR, THIRD_PARTY_API_URL, API_KEY,
    SEASONS_API_URL, RECORDS_API_URL, RECORDS_CACHE_TTL_HOURS,
)
from services.cache import load_from_cache


# 赛季名称缓存（内存缓存）
season_name_cache = {
    "data": None,
    "timestamp": None,
    "ttl_seconds": 86400  # 24 小时缓存
}


# ============= 赛季缓存函数 =============

def is_season_cache_valid():
    """检查赛季名称缓存是否有效"""
    if not season_name_cache["data"] or not season_name_cache["timestamp"]:
        return False
    cache_time = datetime.fromisoformat(season_name_cache["timestamp"])
    return (datetime.now() - cache_time).total_seconds() < season_name_cache["ttl_seconds"]


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


# ============= 高光记录缓存 =============

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


# ============= 选手数据 =============

def get_player_seasons_from_cache() -> list:
    """从缓存的生涯数据中提取选手参加的所有赛季 ID"""
    cache_data = load_from_cache('all')
    if not cache_data or not cache_data.get('data'):
        return []

    data = cache_data['data']
    seasons = []

    season_stats = data.get('season_stats', [])
    for season in season_stats:
        season_id = season.get('season_id')
        if season_id and season_id not in seasons:
            seasons.append(season_id)

    match_details = data.get('match_details', [])
    for match in match_details:
        season_id = match.get('season_id')
        if season_id and season_id not in seasons:
            seasons.append(season_id)

    print(f"从缓存中提取到 {len(seasons)} 个赛季：{seasons}")
    return seasons


async def fetch_from_third_party(season_type: str = 'all'):
    """从第三方 API 获取数据"""
    try:
        async with httpx.AsyncClient() as client:
            headers = {}
            if API_KEY:
                headers["Authorization"] = f"Bearer {API_KEY}"

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


async def fetch_season_records(season: str = 'all') -> list:
    """获取指定赛季（或所有赛季）的高光记录并合并"""
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
