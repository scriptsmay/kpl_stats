# main.py — 入口，注册路由 + CORS + 健康检查

from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import THIRD_PARTY_API_URL, CACHE_TTL_HOURS, DATA_DIR, SEASON_TYPES
from services.cache import load_from_cache, is_cache_valid
from routers import halo, player

app = FastAPI(title="KPL 选手数据代理 API", version="1.0.0")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(halo.router)
app.include_router(player.router)


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
