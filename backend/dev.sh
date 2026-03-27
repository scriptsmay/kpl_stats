#!/bin/bash

# KPL Stats Backend Development Server
# 使用方法：./dev.sh

echo "🚀 启动 KPL Stats 后端开发服务器..."

# 检查 Python 虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 已激活虚拟环境"
fi

# 检查 .env 文件
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "⚠️  .env 文件不存在，从 .env.example 复制..."
    cp .env.example .env
fi

# 使用 python -m uvicorn 确保使用当前环境的 Python
echo "🌐 服务器地址：http://localhost:8001"
echo "📖 API 文档：http://localhost:8001/docs"
echo ""

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
