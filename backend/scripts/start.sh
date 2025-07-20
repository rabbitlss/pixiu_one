#!/bin/bash

# 股票信息采集系统启动脚本

set -e

echo "🚀 Starting Stock Info Collection System..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# 安装依赖
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# 检查环境配置
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found, copying from .env.example"
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration"
fi

# 初始化数据库
echo "🗄️  Initializing database..."
python -c "import asyncio; from app.core.init_db import init_db; asyncio.run(init_db())"

# 启动应用
echo "🌟 Starting application..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload