# GitHub Secrets 配置说明

## 必需的 Secrets

在 GitHub 仓库 Settings → Secrets and variables → Actions 中添加以下 secrets：

### 服务器配置
| Secret 名称 | 说明 | 示例 |
|------------|------|------|
| `SSH_PRIVATE_KEY` | SSH 私钥（用于连接服务器） | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `SERVER_HOST` | 服务器 IP 地址 | `123.123.123.123` |
| `SERVER_USER` | SSH 用户名 | `root` |
| `SERVER_PORT` | SSH 端口（可选，默认 22） | `22` |
| `DEPLOY_PATH` | 后端代码部署路径 | `/root/docker/kpl_stats` |
| `FRONTEND_TARGET` | 前端静态文件部署目标路径 | `/opt/1panel/www/sites/data.kplwuyan.site/index` |

### 后端环境变量
| Secret 名称 | 说明 | 默认值 | 必填 |
|------------|------|------|------|
| `THIRD_PARTY_API_URL` | 第三方 API 地址（选手生涯数据） | - | ✅ |
| `API_KEY` | API 密钥（如需要） | - | ❌ |
| `CACHE_TTL_HOURS` | 缓存有效期（小时） | `24` | ❌ |

### Halo 博客 API 配置（新增）
| Secret 名称 | 说明 | 默认值 | 必填 |
|------------|------|------|------|
| `HALO_API_BASE` | Halo 博客基础 URL | `https://blog.kplwuyan.site` | ✅ |
| `HALO_API_TOKEN` | Halo API 认证 Token | - | ✅ |
| `HALO_POSTS_CACHE_TTL_HOURS` | 文章列表缓存时间（小时） | `1` | ❌ |

### Halo 视频 API 配置（新增）
| Secret 名称 | 说明 | 默认值 | 必填 |
|------------|------|------|------|
| `HALO_VIDEO_GROUP_ID` | 视频附件分组 ID | `attachment-group-25ptmssm` | ✅ |
| `HALO_VIDEO_CACHE_TTL_SECONDS` | 视频列表缓存时间（秒） | `600` | ❌ |

---

## 配置示例

### 1. 获取 Halo API Token

登录 Halo 博客后台：
1. 进入 **设置 → 开发者设置 → API Token**
2. 创建新的 Token
3. 复制 Token 值，添加到 GitHub Secrets：`HALO_API_TOKEN`

### 2. 获取视频分组 ID

在 Halo 后台查看视频附件分组：
1. 进入 **附件 → 分组**
2. 找到存放视频的分组
3. 查看分组 ID（如：`attachment-group-25ptmssm`）
4. 添加到 GitHub Secrets：`HALO_VIDEO_GROUP_ID`

### 3. 完整的 Secrets 配置

```bash
# 服务器配置
SSH_PRIVATE_KEY=-----BEGIN OPENSSH PRIVATE KEY-----...
SERVER_HOST=123.123.123.123
SERVER_USER=root
SERVER_PORT=22
DEPLOY_PATH=/root/docker/kpl_stats
FRONTEND_TARGET=/opt/1panel/www/sites/data.kplwuyan.site/index

# 后端环境变量
THIRD_PARTY_API_URL=https://api.example.com/player/career
API_KEY=your_api_key  # 可选
CACHE_TTL_HOURS=24

# Halo 博客 API
HALO_API_BASE=https://blog.kplwuyan.site
HALO_API_TOKEN=pat_eyJraWQiOiI0MDByMkZPYTJsVFNKNE1SOVIxS21jdkJfcnp3QURYX0NhWDctZlNMQmZnIiwiYWxnIjoiUlMyNTYifQ...
HALO_POSTS_CACHE_TTL_HOURS=1

# Halo 视频 API
HALO_VIDEO_GROUP_ID=attachment-group-25ptmssm
HALO_VIDEO_CACHE_TTL_SECONDS=600
```

---

## 前端部署路径

当前配置的前端部署目标由 `FRONTEND_TARGET` Secret 指定，例如：
```
/opt/1panel/www/sites/data.kplwuyan.site/index
```

这是 1Panel 的默认网站目录结构，请确保：
1. 1Panel 中已创建网站 `data.kplwuyan.site`
2. 网站运行目录指向正确

---

## OpenResty 配置

确保 OpenResty 容器名为 `openresty`，且已挂载配置文件：
```bash
# 检查容器名称
docker ps | grep openresty

# 如果名称不同，请修改 .github/workflows/deploy.yml 中的：
# docker exec openresty nginx -s reload
# 改为实际容器名
```

---

## 首次部署步骤

1. **配置 GitHub Secrets**（见上）

2. **在服务器上创建部署目录**：
   ```bash
   mkdir -p /root/kpl_stats
   ```

3. **配置 OpenResty**：
   ```bash
   # 将 openresty/conf.d/kpl-stats.conf 复制到服务器
   scp openresty/conf.d/kpl-stats.conf root@your.server.ip:/path/to/openresty/conf.d/

   # 重启 OpenResty
   docker exec openresty nginx -s reload
   ```

4. **推送代码到 GitHub**：
   ```bash
   git add .
   git commit -m "feat: 添加部署配置"
   git push origin main
   ```

5. **检查部署日志**：
   - GitHub Actions → Deploy to Server → 查看日志

---

## 验证部署

```bash
# SSH 登录服务器
ssh root@your.server.ip

# 检查后端容器
docker ps | grep kpl-stats-backend

# 检查端口监听
netstat -tlnp | grep 8001

# 查看后端日志
docker logs kpl-stats-backend

# 检查前端文件
ls -la /opt/1panel/www/sites/data.kplwuyan.site/index

# 测试 API
curl http://localhost:8001/api/health
curl http://localhost:8001/api/blog/posts?size=3
curl http://localhost:8001/api/video/random
```

---

## 安全提示

⚠️ **重要**：
- `HALO_API_TOKEN` 是敏感信息，**绝对不能**提交到代码仓库
- 所有 Secrets 都存储在 GitHub 加密存储中
- 部署过程中通过环境变量传递，不会出现在日志中
- 定期轮换 API Token 以提高安全性

---

**更新时间**：2026-03-25
