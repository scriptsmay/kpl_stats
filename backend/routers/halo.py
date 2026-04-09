# halo.py — Halo 博客/视频/图库相关接口

import os
import random
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from config import HALO_API_BASE, HALO_POSTS_CACHE_TTL_HOURS, HALO_VIDEO_CACHE_TTL_SECONDS, HALO_PHOTO_CACHE_TTL_SECONDS
from services.halo_service import (
    # 博客
    fetch_halo_posts_from_api, save_halo_posts_cache,
    load_halo_posts_cache, is_halo_posts_cache_valid, get_halo_posts_cache_file,
    # 时间轴
    fetch_halo_timelines_from_api, save_halo_timeline_cache,
    load_halo_timeline_cache, is_halo_timeline_cache_valid,
    # 视频
    fetch_halo_videos_from_api, save_halo_video_cache,
    load_halo_video_cache, is_halo_video_cache_valid, get_halo_video_cache_file,
    generate_video_cover_url,
    # 图库
    fetch_halo_photos_from_api, save_halo_photo_cache,
    load_halo_photo_cache, is_halo_photo_cache_valid, get_halo_photo_cache_file,
)

router = APIRouter()


# ============= Halo 博客 API 接口 =============

@router.get("/api/blog/posts")
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


@router.get("/api/blog/cache_info")
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


@router.delete("/api/blog/cache")
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


@router.get("/api/timeline/list")
async def get_halo_timeline_list(
    group: str = Query(..., description="时间轴分组 ID"),
    force_refresh: bool = Query(False, description="是否强制刷新缓存")
):
    """
    获取 Halo 时间轴指定分组记录（带缓存）
    """
    # 如果没有指定分组，直接返回错误
    if not group:
        raise HTTPException(status_code=400, detail="必须指定时间轴分组 ID")
    
    cache_data = load_halo_timeline_cache(group)

    if force_refresh:
        try:
            data = await fetch_halo_timelines_from_api(group)
            save_halo_timeline_cache(data, group)
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

    if cache_data and is_halo_timeline_cache_valid(cache_data):
        print(f"[{datetime.now()}] 使用 Halo 时间轴缓存数据，缓存时间：{cache_data['timestamp']}")
        return {
            "code": 200,
            "message": "数据来自缓存",
            "data": cache_data["data"],
            "from_cache": True,
            "cache_time": cache_data["timestamp"]
        }

    try:
        print(f"[{datetime.now()}] Halo 时间轴缓存无效，从 API 获取数据")
        data = await fetch_halo_timelines_from_api(group)
        save_halo_timeline_cache(data, group)
        return {
            "code": 200,
            "message": "数据已更新",
            "data": data,
            "from_cache": False,
            "refresh_time": datetime.now().isoformat()
        }
    except HTTPException:
        if cache_data:
            print(f"[{datetime.now()}] Halo 时间轴 API 失败，返回过期缓存")
            return {
                "code": 200,
                "message": "数据来自过期缓存（Halo API 暂时不可用）",
                "data": cache_data["data"],
                "from_cache": True,
                "cache_time": cache_data["timestamp"],
                "is_expired": True
            }
        raise


# ============= Halo 视频 API 接口 =============

@router.get("/api/video/random")
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


@router.get("/api/video/list")
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


@router.get("/api/video/cache_info")
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


@router.delete("/api/video/cache")
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


# ============= Halo 图库 API 接口 =============

@router.get("/api/photo/list")
async def get_photo_list(
    force_refresh: bool = Query(False, description="是否强制刷新缓存")
):
    """
    获取 Halo 图库照片列表

    参数：
    - force_refresh: 设置为 true 时强制从 Halo API 获取最新数据
    """
    cache_data = load_halo_photo_cache()

    # 如果强制刷新，直接从 API 获取
    if force_refresh:
        try:
            photos = await fetch_halo_photos_from_api()
            save_halo_photo_cache(photos)
            return {
                "code": 200,
                "message": "照片列表已强制刷新",
                "data": photos,
                "from_cache": False,
                "refresh_time": datetime.now().isoformat()
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"强制刷新失败：{str(e)}")

    # 非强制刷新，尝试使用缓存
    if cache_data and is_halo_photo_cache_valid(cache_data):
        print(f"[{datetime.now()}] 使用缓存数据，缓存时间：{cache_data['timestamp']}")
        return {
            "code": 200,
            "message": "数据来自缓存",
            "data": cache_data.get("items", []),
            "from_cache": True,
            "cache_time": cache_data["timestamp"]
        }

    # 缓存无效，从 API 获取
    try:
        photos = await fetch_halo_photos_from_api()
        save_halo_photo_cache(photos)
        return {
            "code": 200,
            "message": "数据已更新",
            "data": photos,
            "from_cache": False,
            "refresh_time": datetime.now().isoformat()
        }
    except HTTPException as e:
        # API 失败时，如果有过期缓存，使用过期缓存
        if cache_data and cache_data.get("items"):
            print(f"[{datetime.now()}] Halo API 失败，使用过期缓存")
            return {
                "code": 200,
                "message": "数据来自过期缓存（Halo API 暂时不可用）",
                "data": cache_data.get("items", []),
                "from_cache": True,
                "cache_time": cache_data["timestamp"],
                "is_expired": True
            }
        raise


@router.get("/api/photo/cache_info")
async def get_halo_photo_cache_info():
    """
    获取 Halo 图库缓存信息
    """
    cache_data = load_halo_photo_cache()
    cache_file = get_halo_photo_cache_file()

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
    is_valid = is_halo_photo_cache_valid(cache_data)
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
            "expires_in": f"{HALO_PHOTO_CACHE_TTL_SECONDS - (datetime.now() - cache_time).total_seconds():.0f}秒" if is_valid else "已过期",
            "file_size": cache_file.stat().st_size if cache_file.exists() else 0
        }
    }


@router.delete("/api/photo/cache")
async def clear_halo_photo_cache():
    """
    清除 Halo 图库缓存
    """
    cache_file = get_halo_photo_cache_file()
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
