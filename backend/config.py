# config.py — 所有配置项（环境变量读取）

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 数据目录
DATA_DIR = Path(__file__).parent / "data"

# 选手数据 API 配置
THIRD_PARTY_API_URL = os.getenv("THIRD_PARTY_API_URL", "https://api.example.com/player/career")
API_KEY = os.getenv("API_KEY", "")
CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))  # 默认缓存 24 小时

# 赛季列表 API 配置
SEASONS_API_URL = os.getenv("SEASONS_API_URL", "http://47.102.210.150:5006/seasons/list")

# 高光记录 API 配置
RECORDS_API_URL = os.getenv("RECORDS_API_URL", "http://47.102.210.150:5022/api/records")
RECORDS_CACHE_TTL_HOURS = int(os.getenv("RECORDS_CACHE_TTL_HOURS", "24"))  # 默认缓存 24 小时（每天 0 点更新）

# Halo 博客 API 配置
HALO_API_BASE = os.getenv("HALO_API_BASE", "https://blog.kplwuyan.site")
HALO_API_URL = f"{HALO_API_BASE}/apis/api.console.halo.run/v1alpha1"
HALO_API_TOKEN = os.getenv("HALO_API_TOKEN", "")
HALO_POSTS_CACHE_TTL_HOURS = int(os.getenv("HALO_POSTS_CACHE_TTL_HOURS", "1"))  # 默认缓存 1 小时

# Halo 视频 API 配置
HALO_VIDEO_GROUP_ID = os.getenv("HALO_VIDEO_GROUP_ID", "attachment-group-25ptmssm")
HALO_VIDEO_CACHE_TTL_SECONDS = int(os.getenv("HALO_VIDEO_CACHE_TTL_SECONDS", "600"))  # 默认缓存 10 分钟

# Halo 图库 API 配置
HALO_PHOTO_CACHE_TTL_SECONDS = int(os.getenv("HALO_PHOTO_CACHE_TTL_SECONDS", "3600"))  # 默认缓存 1 小时

# 赛季类型常量
SEASON_TYPES = ['all', 'league', 'cup']

# 确保 data 目录存在
DATA_DIR.mkdir(exist_ok=True)
