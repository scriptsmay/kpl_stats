#!/bin/bash

# KPL Stats 手动部署脚本
# 用法：./deploy.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}   KPL Stats 部署脚本${NC}"
echo -e "${GREEN}================================${NC}"

# 配置（请根据实际情况修改）
SERVER_USER="root"
SERVER_HOST="your.server.ip"
SERVER_PORT="22"  # 如果不是 22，请修改
DEPLOY_PATH="/root/kpl_stats"
FRONTEND_TARGET="/var/www/kpl-stats/dist"

# 1. 构建前端
echo -e "${YELLOW}[1/5] 构建前端...${NC}"
cd frontend
npm install
npm run build
cd ..

# 2. 复制文件到服务器
echo -e "${YELLOW}[2/5] 上传文件到服务器...${NC}"
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST "mkdir -p $DEPLOY_PATH $FRONTEND_TARGET"
scp -P $SERVER_PORT -r frontend/dist/* $SERVER_USER@$SERVER_HOST:$FRONTEND_TARGET
scp -P $SERVER_PORT -r backend $SERVER_USER@$SERVER_HOST:$DEPLOY_PATH/
scp -P $SERVER_PORT docker-compose.backend.yml $SERVER_USER@$SERVER_HOST:$DEPLOY_PATH/

# 3. 部署后端
echo -e "${YELLOW}[3/5] 部署后端服务...${NC}"
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST << 'ENDSSH'
  cd /root/kpl_stats
  
  # 复制环境变量（如果不存在）
  if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "请编辑 backend/.env 配置环境变量"
  fi
  
  # 构建并启动容器
  docker compose -f docker-compose.backend.yml down
  docker compose -f docker-compose.backend.yml build
  docker compose -f docker-compose.backend.yml up -d
ENDSSH

# 4. 配置 OpenResty（首次部署需要）
echo -e "${YELLOW}[4/5] 检查 OpenResty 配置...${NC}"
read -p "是否需要配置 OpenResty？(y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  scp -P $SERVER_PORT openresty/conf.d/kpl-stats.conf $SERVER_USER@$SERVER_HOST:/path/to/openresty/conf.d/
  ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST "docker exec openresty nginx -s reload"
  echo -e "${GREEN}OpenResty 配置已更新${NC}"
fi

# 5. 检查服务状态
echo -e "${YELLOW}[5/5] 检查服务状态...${NC}"
ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST << 'ENDSSH'
  echo "--- 后端容器状态 ---"
  docker ps | grep kpl-stats-backend
  
  echo -e "\n--- 端口监听 ---"
  netstat -tlnp | grep 8001
  
  echo -e "\n--- 前端目录 ---"
  ls -la /var/www/kpl-stats/dist/
ENDSSH

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}   部署完成！${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "访问地址：http://data.kplwuyan.site"
echo ""
echo -e "${YELLOW}后续操作：${NC}"
echo "1. 配置 OpenResty（如果还没配置）"
echo "2. 申请 SSL 证书（推荐 Let's Encrypt）"
echo "3. 访问 https://blog.kplwuyan.site 测试"
