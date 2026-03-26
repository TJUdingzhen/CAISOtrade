#!/bin/bash
# CAISO Monitor 打包脚本 - 用于上传到服务器部署

set -e

PROJECT_NAME="caiso_monitor"
PACKAGE_NAME="${PROJECT_NAME}_$(date +%Y%m%d).tar.gz"

echo "📦 打包 CAISO Monitor 项目..."

# 创建临时目录
TEMP_DIR=$(mktemp -d)
DEST_DIR="$TEMP_DIR/$PROJECT_NAME"
mkdir -p "$DEST_DIR"

# 复制必要文件
echo "📂 复制项目文件..."
cp -r backend "$DEST_DIR/"
cp -r frontend "$DEST_DIR/"
cp -r database "$DEST_DIR/"
cp -r nginx "$DEST_DIR/"
cp docker-compose.yml "$DEST_DIR/"
cp .env.example "$DEST_DIR/"
cp deploy.sh "$DEST_DIR/"
cp README.md "$DEST_DIR/"
cp DEPLOY.md "$DEST_DIR/"
cp QUICKSTART.md "$DEST_DIR/"
cp test_caiso_live.py "$DEST_DIR/"

# 清理不需要的文件
echo "🧹 清理临时文件..."
rm -rf "$DEST_DIR/backend/__pycache__"
rm -rf "$DEST_DIR/frontend/__pycache__"

# 打包
echo "📦 创建压缩包..."
tar -czf "$PACKAGE_NAME" -C "$TEMP_DIR" "$PROJECT_NAME"

# 清理临时目录
rm -rf "$TEMP_DIR"

echo ""
echo "✅ 打包完成: $PACKAGE_NAME"
echo ""
echo "📤 上传到服务器的命令:"
echo "   scp $PACKAGE_NAME user@your-server:/home/user/"
echo ""
echo "📥 在服务器上解压:"
echo "   tar -xzf $PACKAGE_NAME"
echo "   cd $PROJECT_NAME"
echo "   ./deploy.sh"
echo ""

# 显示文件大小
ls -lh "$PACKAGE_NAME"