# Halo API 配置与使用指南

## 概述

为了安全地访问 Halo 博客 API，我们在后端实现了 API 代理层，避免将 Token 暴露在前端代码中。

## 架构

```
homepage (前端) → backend (FastAPI 代理) → Halo API
     无 Token            带 Token           安全调用
```

## 配置步骤

### 1. 获取 Halo API Token

登录你的 Halo 博客后台，在 **设置 → 开发者设置 → API Token** 中创建一个新的 Token。

### 2. 配置后端环境变量

编辑 `backend/.env` 文件（如不存在则复制 `.env.example`）：

```env
# Halo 博客 API 配置
HALO_API_URL=https://blog.kplwuyan.site/apis/api.content.halo.run/v1alpha1
HALO_API_TOKEN=your_actual_halo_api_token_here
HALO_POSTS_CACHE_TTL_HOURS=1

# Halo 视频 API 配置
HALO_VIDEO_GROUP_ID=attachment-group-25ptmssm
HALO_VIDEO_CACHE_TTL_SECONDS=600
```

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `HALO_API_URL` | Halo API 基础地址 | - |
| `HALO_API_TOKEN` | Halo API 认证 Token | - |
| `HALO_POSTS_CACHE_TTL_HOURS` | 文章列表缓存时间（小时） | 1 |
| `HALO_VIDEO_GROUP_ID` | 视频附件分组 ID | - |
| `HALO_VIDEO_CACHE_TTL_SECONDS` | 视频列表缓存时间（秒） | 600 |

**注意**：正确的 API 端点是 `/apis/api.content.halo.run/v1alpha1`（不是 `/apis/api.halo.run/v1alpha1`）

### 3. 重启后端服务

```bash
cd backend
uvicorn main:app --reload --port 8001
```

## API 接口

### 获取博客文章列表

```http
GET /api/blog/posts?size=3&force_refresh=false
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `size` | integer | 否 | 获取文章数量，默认 3 篇 |
| `force_refresh` | boolean | 否 | 是否强制刷新缓存 |

**响应示例：**
```json
{
  "code": 200,
  "message": "数据来自缓存",
  "data": {
    "items": [
      {
        "spec": {
          "title": "文章标题",
          "excerpt": "文章摘要",
          "cover": "https://...",
          "publishTime": "2026-03-25T10:00:00Z"
        },
        "status": {
          "permalink": "/posts/article-slug"
        }
      }
    ]
  },
  "from_cache": true,
  "cache_time": "2026-03-25T10:30:00"
}
```

### 查看缓存信息

```http
GET /api/blog/cache_info
```

### 清除缓存

```http
DELETE /api/blog/cache
```

## 缓存策略

- **默认缓存时间**：1 小时
- **降级处理**：Halo API 不可用时返回过期缓存
- **缓存文件**：`backend/data/cache.halo.posts.json`

## 安全说明

✅ **Token 存储位置**：只在后端 `backend/.env` 文件中
✅ **前端访问**：前端代码不包含任何敏感信息
✅ **跨域支持**：后端已配置 CORS 允许前端访问
✅ **日志记录**：所有 API 调用都有时间戳日志

## 故障排查

### 问题：前端无法加载博客文章

1. 检查后端日志，确认 Halo API 调用是否成功
2. 访问 `http://localhost:8001/api/blog/cache_info` 查看缓存状态
3. 尝试强制刷新：`curl -X POST "http://localhost:8001/api/blog/posts?force_refresh=true"`

### 问题：Halo API 返回 401 错误

1. 确认 `HALO_API_TOKEN` 配置正确
2. 检查 Token 是否已过期或被撤销
3. 在 Halo 后台重新生成 Token 并更新配置

### 问题：文章封面图显示失败

前端已配置 `onerror` 降级处理，会自动替换为随机占位图。如需自定义，可修改 `homepage/assets/js/index.js` 中的 `fetchPosts()` 函数。

---

## Halo 视频 API 接口

### 随机获取一个视频

```http
GET /api/video/random
```

**说明：**
- 从视频附件分组中随机返回一个视频
- 包含标题、URL、封面图
- 视频列表缓存 10 分钟，每次请求从缓存中随机选择

**响应示例：**
```json
{
  "code": 200,
  "message": "随机视频获取成功",
  "data": {
    "title": "训练日常.mp4",
    "url": "https://blog.kplwuyan.site/upload/video.mp4",
    "poster": "https://blog.kplwuyan.site/upload/video-cover.jpg"
  },
  "meta": {
    "total_videos": 25,
    "cache_used": true
  }
}
```

### 获取所有视频列表

```http
GET /api/video/list
```

**说明：**
- 返回缓存中的所有视频附件信息
- 适合用于视频 gallery 页面

**响应示例：**
```json
{
  "code": 200,
  "message": "视频列表获取成功",
  "data": [
    {
      "title": "训练日常.mp4",
      "url": "https://blog.kplwuyan.site/upload/video1.mp4",
      "poster": "https://blog.kplwuyan.site/upload/video1-cover.jpg"
    }
  ],
  "meta": {
    "total": 25,
    "cache_used": true
  }
}
```

### 查看视频缓存信息

```http
GET /api/video/cache_info
```

**响应示例：**
```json
{
  "code": 200,
  "message": "缓存信息",
  "data": {
    "exists": true,
    "cache_file": "/path/to/cache.halo.videos.json",
    "cache_time": "2026-03-25T12:00:00",
    "is_valid": true,
    "items_count": 25,
    "expires_in": "480 秒",
    "file_size": 10240
  }
}
```

### 清除视频缓存

```http
DELETE /api/video/cache
```

## 视频封面图生成规则

系统会根据视频 URL 自动生成封面图 URL：

```
视频 URL: /upload/training.mp4
封面 URL: /upload/training-cover.jpg
```

请确保你的视频文件命名符合此规则，或者手动上传对应的封面图。

---

## Halo 图库 API 接口

### 获取照片列表

```http
GET /api/photo/list?force_refresh=false
```

**说明：**
- 直接获取所有图库照片（不指定分组）
- 按创建时间倒序排序，返回最新 10 张
- 支持懒加载和缩略图（`?width=400`）
- 照片列表默认缓存 1 小时

**API 流程：**
1. 请求 `/apis/console.api.photo.halo.run/v1alpha1/photos?page=1&size=50` 获取所有照片
2. 按 `metadata.creationTimestamp` 倒序排序
3. 返回最新 10 张照片

**响应示例：**
```json
{
  "code": 200,
  "message": "照片列表获取成功",
  "data": [
    {
      "title": "Hi！KSG 无言",
      "url": "https://blog.kplwuyan.site/upload/photo.jpg",
      "thumb_url": "https://blog.kplwuyan.site/upload/photo.jpg?width=400",
      "mediaType": "image/jpeg",
      "size": 0,
      "creationTimestamp": "2026-03-28T15:18:58.691867357Z",
      "groupName": "photo-group-35subhyr"
    }
  ],
  "from_cache": false,
  "refresh_time": "2026-03-28T15:20:00"
}
```

### 查看图库缓存信息

```http
GET /api/photo/cache_info
```

**响应示例：**
```json
{
  "code": 200,
  "message": "缓存信息",
  "data": {
    "exists": true,
    "cache_file": "/path/to/cache.halo.photos.json",
    "cache_time": "2026-03-28T12:00:00",
    "is_valid": true,
    "items_count": 12,
    "expires_in": "3200 秒",
    "file_size": 20480
  }
}
```

### 清除图库缓存

```http
DELETE /api/photo/cache
```

## 照片墙配置

### 1. 在 Halo 后台创建照片分组

1. 登录 Halo 博客后台
2. 进入 **图库** → **分组管理**
3. 创建新分组（可选，系统会自动获取所有分组的照片）

### 2. 配置后端环境变量

编辑 `backend/.env` 文件：

```env
# Halo 图库 API 配置
HALO_PHOTO_CACHE_TTL_SECONDS=3600
```

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `HALO_PHOTO_CACHE_TTL_SECONDS` | 照片列表缓存时间（秒） | 3600（1 小时） |

### 3. 上传照片到 Halo

1. 在 Halo 后台进入 **图库**
2. 选择对应分组（或不分组）
3. 上传照片（支持批量上传）
4. 照片会自动在照片墙展示（最新 10 张）

### 4. 缩略图优化

系统会自动在照片 URL 后添加 `?width=400` 参数获取小尺寸缩略图，用于照片墙展示。

点击照片时会以灯箱形式展示原图。

---

**更新时间**：2026-03-28
