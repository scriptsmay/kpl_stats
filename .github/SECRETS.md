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
| Secret 名称 | 说明 | 示例 |
|------------|------|------|
| `THIRD_PARTY_API_URL` | 第三方 API 地址（必填） | `https://api.example.com/player/career` |
| `API_KEY` | API 密钥（如需要） | `your_api_key` |
| `CACHE_TTL_HOURS` | 缓存有效期（小时，可选） | `24` |

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
```
