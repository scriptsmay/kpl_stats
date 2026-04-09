# halo_service.py — Halo 相关的 API 调用函数 + 缓存逻辑

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath

import httpx
from fastapi import HTTPException

from config import (
    DATA_DIR, HALO_API_BASE, HALO_API_URL, HALO_API_TOKEN,
    HALO_POSTS_CACHE_TTL_HOURS, HALO_VIDEO_GROUP_ID,
    HALO_VIDEO_CACHE_TTL_SECONDS, HALO_PHOTO_CACHE_TTL_SECONDS,
)


# ============= Halo 博客缓存 =============

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


# ============= Halo 时间轴缓存 =============

def _build_halo_timeline_cache_file(group: str) -> Path:
    """根据 group 生成 Halo 时间轴缓存文件路径"""
    group_key = ''.join(ch if ch.isalnum() or ch in ('-', '_') else '_' for ch in group)[:64] or 'timeline'
    return DATA_DIR / f"cache.halo.timeline.{group_key}.json"


def save_halo_timeline_cache(data: dict, group: str):
    """保存 Halo 时间轴查询结果到缓存"""
    now = datetime.now()
    cache_data = {
        "timestamp": now.isoformat(),
        "query": {
            "group": group,
        },
        "data": data
    }
    cache_file = _build_halo_timeline_cache_file(group)
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    print(f"[{now}] Halo 时间轴缓存已保存，group={group}")


def load_halo_timeline_cache(group: str):
    """从本地文件加载 Halo 时间轴缓存"""
    cache_file = _build_halo_timeline_cache_file(group)
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"读取 Halo 时间轴缓存失败：{e}")
            return None
    return None


def is_halo_timeline_cache_valid(cache_data: dict) -> bool:
    """检查 Halo 时间轴缓存是否有效"""
    if not cache_data:
        return False
    try:
        cache_time = datetime.fromisoformat(cache_data["timestamp"])
        return datetime.now() - cache_time < timedelta(hours=HALO_POSTS_CACHE_TTL_HOURS)
    except (KeyError, ValueError):
        return False


async def fetch_halo_timelines_from_api(group: str):
    """从 Halo API 获取时间轴指定分组记录"""
    try:
        async with httpx.AsyncClient() as client:
            headers = {}
            if HALO_API_TOKEN:
                headers["Authorization"] = f"Bearer {HALO_API_TOKEN}"

            request_url = f"{HALO_API_BASE.rstrip('/')}/apis/api.timeline.xhhao.com/v1alpha1/timelines"
            params = {
                "group": group
            }

            print(f"[{datetime.now()}] 开始请求 Halo 时间轴 API: {request_url} group={group}")
            response = await client.get(
                request_url,
                headers=headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            halo_data = response.json()

            print(f"[{datetime.now()}] Halo 时间轴 API 请求成功，group={group}")
            return halo_data
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Halo 时间轴 API 请求超时")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Halo 时间轴 API 错误：{e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 Halo 时间轴失败：{str(e)}")


# ============= Halo 视频缓存 =============

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


# ============= Halo 图库缓存 =============

def get_halo_photo_cache_file() -> Path:
    """获取 Halo 图库照片列表缓存文件路径"""
    return DATA_DIR / "cache.halo.photos.json"


def save_halo_photo_cache(data: list):
    """保存 Halo 图库照片列表到缓存"""
    now = datetime.now()
    cache_data = {
        "timestamp": now.isoformat(),
        "items": data
    }
    cache_file = get_halo_photo_cache_file()
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    print(f"[{now}] Halo 图库照片列表缓存已保存，共 {len(data)} 张")


def load_halo_photo_cache():
    """从本地文件加载 Halo 图库照片列表缓存"""
    cache_file = get_halo_photo_cache_file()
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"读取 Halo 图库缓存失败：{e}")
            return None
    return None


def is_halo_photo_cache_valid(cache_data: dict) -> bool:
    """检查 Halo 图库照片列表缓存是否有效"""
    if not cache_data:
        return False
    try:
        cache_time = datetime.fromisoformat(cache_data["timestamp"])
        return (datetime.now() - cache_time).total_seconds() < HALO_PHOTO_CACHE_TTL_SECONDS
    except (KeyError, ValueError):
        return False


async def fetch_halo_photos_from_api():
    """从 Halo API 获取图库照片列表（获取所有分组的最新 N 张）"""
    try:
        async with httpx.AsyncClient() as client:
            headers = {}
            if HALO_API_TOKEN:
                headers["Authorization"] = f"Bearer {HALO_API_TOKEN}"

            photos_url = f"{HALO_API_BASE}/apis/console.api.photo.halo.run/v1alpha1/photos"
            params = {
                "page": 1,
                "size": 20,
                "keyword": ""
            }

            print(f"[{datetime.now()}] 开始请求 Halo 图库照片列表：{photos_url}")
            photos_response = await client.get(photos_url, headers=headers, params=params, timeout=30.0)
            photos_response.raise_for_status()
            photos_data = photos_response.json()

            items = photos_data.get('items', [])
            print(f"[{datetime.now()}] 获取到 {len(items)} 张照片")

            # 提取照片信息
            all_photos = []
            for item in items:
                spec = item.get('spec', {})
                metadata = item.get('metadata', {})
                url = spec.get('url', '')

                creation_timestamp = metadata.get('creationTimestamp', '')

                if url and not url.startswith('http'):
                    url = f"{HALO_API_BASE.rstrip('/')}{url}"

                thumb_url = f"{url}?width=800" if url else ''

                labels = metadata.get('labels', {})
                group_name = labels.get('photo.halo.run/group-name', '')

                all_photos.append({
                    "title": spec.get('displayName', spec.get('filename', '未命名')),
                    "url": url,
                    "thumb_url": thumb_url,
                    "mediaType": spec.get('mediaType', 'image/jpeg'),
                    "size": spec.get('size', 0),
                    "creationTimestamp": creation_timestamp,
                    "groupName": group_name
                })

            # 按创建时间倒序排序（新照片在前）
            all_photos.sort(key=lambda x: x.get('creationTimestamp', ''), reverse=True)

            # 取最新 10 张
            latest_photos = all_photos[:10]

            print(f"[{datetime.now()}] Halo 图库 API 请求完成，返回最新 {len(latest_photos)} 张照片")
            return latest_photos

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Halo 图库 API 请求超时")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Halo 图库 API 错误：{e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 Halo 图库失败：{str(e)}")


def generate_video_cover_url(permalink: str) -> str:
    """根据视频 permalink 自动生成封面图 URL

    规则：/upload/test.mp4 -> /upload/test-cover.jpg
    """
    path = PurePosixPath(permalink)
    dirname = str(path.parent) if path.parent != PurePosixPath('.') else ''
    filename = path.stem  # 不带后缀的文件名

    cover_path = f"{dirname}/{filename}-cover.jpg" if dirname else f"/{filename}-cover.jpg"
    return f"{HALO_API_BASE.rstrip('/')}{cover_path}"
