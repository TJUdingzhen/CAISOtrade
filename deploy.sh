#!/bin/bash
# CAISO Monitor 快速部署脚本

set -e

echo "========================================"
echo " CAISO 电力市场监控系统部署脚本"
echo "========================================"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

echo "✅ Docker 检查通过"

# 创建环境变量文件（如果不存在）
if [ ! -f .env ]; then
    echo "📝 创建环境变量文件 .env..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件修改默认配置（特别是数据库密码）"
fi

# 创建必要目录
echo "📁 创建数据目录..."
mkdir -p data/postgres
mkdir -p nginx/ssl

# 拉取镜像并启动
echo "🐳 启动服务..."
docker-compose pull
docker-compose up -d --build

# 等待数据库初始化
echo "⏳ 等待数据库初始化..."
sleep 15

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

echo ""
echo "========================================"
echo "✅ 部署完成！"
echo "========================================"
echo ""
echo "访问地址:"
echo "  📊 Dashboard: http://localhost:8501"
echo "  🔌 API 文档:  http://localhost:8000/docs"
echo "  🔌 API:       http://localhost:8000"
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo ""
echo "⚠️  首次启动需要等待几分钟加载历史数据"
echo "========================================"