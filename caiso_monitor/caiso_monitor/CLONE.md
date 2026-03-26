# 🚀 Git Clone 一键部署指南

使用 Git 部署 CAISO 实时电力市场监控系统。

---

## 📥 部署命令（复制即用）

### 1. 连接服务器并安装 Docker

```bash
# 连接服务器
ssh username@your-server-ip

# 安装 Docker（Ubuntu/Debian）
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# 验证安装
docker --version && docker-compose --version
```

### 2. Clone 项目并部署

```bash
# 创建应用目录
mkdir -p ~/apps && cd ~/apps

# Clone 仓库（替换为你的仓库地址）
git clone https://github.com/your-username/caiso-monitor.git
cd caiso-monitor

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件修改数据库密码
nano .env

# 一键部署
chmod +x deploy.sh
./deploy.sh
```

### 3. 访问系统

```
Dashboard: http://your-server-ip:8501
API 文档:  http://your-server-ip:8000/docs
API:       http://your-server-ip:8000
```

---

## 📋 完整示例（复制粘贴执行）

```bash
#!/bin/bash
# CAISO Monitor 完整部署脚本 - 在服务器上执行

set -e

echo "🚀 开始部署 CAISO Monitor..."

# 安装 Docker
if ! command -v docker &> /dev/null; then
    echo "📦 安装 Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "✅ Docker 安装完成，请重新登录或执行: newgrp docker"
    exit 0
fi

# 创建目录
mkdir -p ~/apps
cd ~/apps

# Clone 项目（替换为你的仓库）
if [ ! -d "caiso-monitor" ]; then
    echo "📥 克隆仓库..."
    git clone https://github.com/your-username/caiso-monitor.git
fi

cd caiso-monitor

# 拉取最新代码
echo "🔄 拉取最新代码..."
git pull origin main

# 配置环境变量
if [ ! -f ".env" ]; then
    echo "⚙️  创建环境变量文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件修改数据库密码，然后重新运行此脚本"
    nano .env
    exit 0
fi

# 部署
echo "🐳 启动服务..."
chmod +x deploy.sh
./deploy.sh

echo ""
echo "✅ 部署完成！"
echo "📊 Dashboard: http://$(hostname -I | awk '{print $1}'):8501"
echo "📚 API 文档:  http://$(hostname -I | awk '{print $1}'):8000/docs"
echo ""
echo "查看日志: docker-compose logs -f"
```

将上述内容保存为 `install.sh`，在服务器上执行：
```bash
chmod +x install.sh
./install.sh
```

---

## 🔄 更新代码

```bash
cd ~/apps/caiso-monitor

# 拉取更新
git pull origin main

# 重启服务
docker-compose down
docker-compose up -d --build
```

---

## 📝 项目结构

```
caiso-monitor/
├── .git/                  # Git 版本控制
├── .gitignore            # 忽略文件（包含 .env）
├── .env.example          # 环境变量模板
├── docker-compose.yml    # Docker 编排
├── deploy.sh            # 部署脚本
├── backend/             # FastAPI 后端
├── frontend/            # Streamlit 前端
├── database/            # TimescaleDB 初始化
└── nginx/               # Nginx 配置
```

---

## 🔐 安全提示

1. **永远不要提交 `.env` 文件**（已在 .gitignore 中排除）
2. **修改默认数据库密码**
3. **生产环境配置防火墙**：
   ```bash
   sudo ufw allow 22/tcp     # SSH
   sudo ufw allow 80/tcp     # HTTP
   sudo ufw allow 443/tcp    # HTTPS
   sudo ufw allow 8501/tcp   # Dashboard
   sudo ufw enable
   ```

---

## 📚 相关文档

- [完整部署教程](README.md)
- [Git 部署详情](GIT_DEPLOY.md)
- [快速开始](QUICKSTART.md)

---

**Git 仓库**: `https://github.com/your-username/caiso-monitor.git`