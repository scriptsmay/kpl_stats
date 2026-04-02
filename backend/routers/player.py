# player.py — 选手数据相关接口（career, seasons, match records, admin）

import json
import os
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from config import (
    SEASON_TYPES, CACHE_TTL_HOURS, RECORDS_CACHE_TTL_HOURS,
    THIRD_PARTY_API_URL, DATA_DIR,
)
from services.cache import (
    get_cache_file, load_from_cache, is_cache_valid, save_to_cache,
    get_archive_list,
)
from services.player_service import (
    # 选手数据
    fetch_from_third_party, get_player_seasons_from_cache,
    # 赛季
    fetch_seasons_from_api, is_season_cache_valid,
    get_season_name_map, season_name_cache,
    # 高光记录
    fetch_match_records_from_api, save_match_records_cache,
    load_match_records_cache, is_match_records_cache_valid,
    get_match_records_cache_file,
    fetch_season_records,
)

router = APIRouter()


@router.get("/api/player/career")
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


@router.get("/api/player/seasons")
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


# ============= 赛季列表接口 =============

@router.get("/api/seasons/list")
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


@router.get("/api/seasons/name_map")
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


# ============= 高光记录 API 接口 =============

@router.get("/api/match/records")
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


@router.get("/api/match/records/cache_info")
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


@router.delete("/api/match/records/cache")
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


# ============= Admin 接口 =============

@router.post("/api/admin/refresh")
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


@router.get("/api/admin/cache_info")
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


@router.get("/api/admin/cache_list")
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


@router.get("/api/admin/archive_list")
async def list_archives():
    """
    获取历史存档列表（已废弃：存档功能已移除）
    """
    return {
        "code": 200,
        "message": "存档功能已移除",
        "data": {
            "archives": [],
            "total": 0
        }
    }


@router.get("/api/admin/archive/{date}")
async def get_archive(
    date: str,
    season_type: str = Query('all', description="赛季类型 (all/league/cup)")
):
    """
    获取指定日期的存档数据（已废弃：存档功能已移除）
    """
    raise HTTPException(status_code=410, detail="存档功能已移除，历史数据不再保留")


@router.delete("/api/admin/cache")
async def clear_cache(
    season_type: str = Query('all', description="赛季类型 (all/league/cup)，all 表示清除所有类型")
):
    """
    清除缓存文件
    """
    if season_type == 'all':
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
