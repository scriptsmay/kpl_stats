# cache.py — 通用缓存工具（文件读写、有效性检查、存档管理）

import json
from datetime import datetime, timedelta
from pathlib import Path

from config import DATA_DIR, CACHE_TTL_HOURS


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
