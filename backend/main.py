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

app = FastAPI(title="KPL选手数据代理API", version="1.0.0")

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
CACHE_FILE = Path(__file__).parent / "cache.json"
CACHE_TTL_HOURS = int(os.getenv("CACHE_TTL_HOURS", "24"))  # 默认缓存24小时

def save_to_cache(data: dict, from_force: bool = False):
    """保存数据到本地文件缓存"""
    cache_data = {
        "timestamp": datetime.now().isoformat(),
        "data": data,
        "from_force": from_force  # 标记是否为强制刷新
    }
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    print(f"[{datetime.now()}] 缓存已保存，来源: {'强制刷新' if from_force else '自动更新'}")

def load_from_cache():
    """从本地文件加载缓存"""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"读取缓存失败: {e}")
            return None
    return None

def is_cache_valid(cache_data: dict) -> bool:
    """检查缓存是否有效"""
    if not cache_data:
        return False
    
    try:
        cache_time = datetime.fromisoformat(cache_data["timestamp"])
        # 检查是否过期
        return datetime.now() - cache_time < timedelta(hours=CACHE_TTL_HOURS)
    except (KeyError, ValueError):
        return False

async def fetch_from_third_party():
    """从第三方API获取数据"""
    try:
        async with httpx.AsyncClient() as client:
            headers = {}
            if API_KEY:
                headers["Authorization"] = f"Bearer {API_KEY}"
            
            print(f"[{datetime.now()}] 开始请求第三方API: {THIRD_PARTY_API_URL}")
            response = await client.get(
                THIRD_PARTY_API_URL,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            third_party_data = response.json()
            print(f"[{datetime.now()}] 第三方API请求成功")
                        # 如果第三方返回 { code: 200, data: {...} } 格式，解包返回 data 部分
            if isinstance(third_party_data, dict) and "data" in third_party_data:
                return third_party_data["data"]
            return third_party_data
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="第三方API请求超时")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"第三方API错误: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")

# ============= API 接口 =============

@app.get("/api/player/career")
async def get_career_data(
    force_refresh: bool = Query(False, description="是否强制刷新数据（忽略缓存）")
):
    """
    获取选手生涯数据
    
    参数：
    - force_refresh: 设置为 true 时强制从第三方API获取最新数据
    """
    
    # 如果强制刷新，直接请求第三方API
    if force_refresh:
        try:
            data = await fetch_from_third_party()
            # 保存到缓存（标记为强制刷新）
            save_to_cache(data, from_force=True)
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
            raise HTTPException(status_code=500, detail=f"强制刷新失败: {str(e)}")
    
    # 非强制刷新，尝试使用缓存
    cache_data = load_from_cache()
    
    # 检查缓存是否有效
    if cache_data and is_cache_valid(cache_data):
        print(f"[{datetime.now()}] 使用缓存数据，缓存时间: {cache_data['timestamp']}")
        return {
            "code": 200,
            "message": "数据来自缓存",
            "data": cache_data["data"],
            "from_cache": True,
            "cache_time": cache_data["timestamp"],
            "from_force": cache_data.get("from_force", False)
        }
    
    # 缓存无效，从第三方API获取
    try:
        print(f"[{datetime.now()}] 缓存无效，从第三方API获取数据")
        data = await fetch_from_third_party()
        # 保存到缓存
        save_to_cache(data, from_force=False)
        return {
            "code": 200,
            "message": "数据已更新",
            "data": data,
            "from_cache": False,
            "refresh_time": datetime.now().isoformat()
        }
    except HTTPException:
        # 如果第三方API失败，尝试返回过期缓存
        if cache_data:
            print(f"[{datetime.now()}] API失败，返回过期缓存")
            return {
                "code": 200,
                "message": "数据来自过期缓存（第三方API暂时不可用）",
                "data": cache_data["data"],
                "from_cache": True,
                "cache_time": cache_data["timestamp"],
                "is_expired": True
            }
        raise

@app.post("/api/admin/refresh")
async def refresh_cache(
    force: bool = Query(True, description="是否强制刷新")
):
    """
    手动刷新缓存数据
    
    参数：
    - force: 设置为 true 时强制从第三方API获取（忽略缓存）
    """
    try:
        print(f"[{datetime.now()}] 收到手动刷新请求，force={force}")
        
        # 直接从第三方API获取
        data = await fetch_from_third_party()
        
        # 保存到缓存
        save_to_cache(data, from_force=True)
        
        # 获取缓存文件信息
        cache_stat = CACHE_FILE.stat() if CACHE_FILE.exists() else None
        
        return {
            "code": 200,
            "message": "缓存刷新成功",
            "data": {
                "refresh_time": datetime.now().isoformat(),
                "cache_file": str(CACHE_FILE),
                "cache_size": cache_stat.st_size if cache_stat else 0,
                "data_keys": list(data.get("data", {}).keys()) if "data" in data else list(data.keys())
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刷新缓存失败: {str(e)}")

@app.get("/api/admin/cache_info")
async def get_cache_info():
    """
    获取缓存信息
    """
    cache_data = load_from_cache()
    
    if not cache_data:
        return {
            "code": 200,
            "message": "缓存不存在",
            "data": {
                "exists": False,
                "cache_file": str(CACHE_FILE)
            }
        }
    
    cache_time = datetime.fromisoformat(cache_data["timestamp"])
    is_valid = is_cache_valid(cache_data)
    
    return {
        "code": 200,
        "message": "缓存信息",
        "data": {
            "exists": True,
            "cache_file": str(CACHE_FILE),
            "cache_time": cache_data["timestamp"],
            "is_valid": is_valid,
            "expires_in": f"{CACHE_TTL_HOURS - (datetime.now() - cache_time).total_seconds() / 3600:.1f}小时" if is_valid else "已过期",
            "from_force": cache_data.get("from_force", False),
            "file_size": CACHE_FILE.stat().st_size if CACHE_FILE.exists() else 0
        }
    }

@app.delete("/api/admin/cache")
async def clear_cache():
    """
    清除缓存文件
    """
    if CACHE_FILE.exists():
        try:
            os.remove(CACHE_FILE)
            return {
                "code": 200,
                "message": "缓存已清除",
                "data": {
                    "cache_file": str(CACHE_FILE),
                    "cleared_at": datetime.now().isoformat()
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")
    else:
        return {
            "code": 200,
            "message": "缓存文件不存在",
            "data": {
                "cache_file": str(CACHE_FILE)
            }
        }

@app.get("/api/health")
async def health_check():
    """
    健康检查
    """
    cache_data = load_from_cache()
    
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "cache": {
            "exists": cache_data is not None,
            "valid": is_cache_valid(cache_data) if cache_data else False
        },
        "config": {
            "api_url": THIRD_PARTY_API_URL,
            "cache_ttl_hours": CACHE_TTL_HOURS
        }
    }