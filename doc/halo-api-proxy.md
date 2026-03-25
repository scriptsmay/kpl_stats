# Halo 博客 API 配置指南

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
```

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `HALO_API_URL` | Halo API 基础地址 | - |
| `HALO_API_TOKEN` | Halo API 认证 Token | - |
| `HALO_POSTS_CACHE_TTL_HOURS` | 文章列表缓存时间（小时） | 1 |

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

**更新时间**：2026-03-25
