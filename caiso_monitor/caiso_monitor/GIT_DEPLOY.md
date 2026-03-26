# CAISO Monitor - Git 部署指南

本文档介绍如何使用 Git 管理并部署 CAISO 实时监控系统。

---

## 📋 前置要求

- 服务器已安装 Git
- 服务器已安装 Docker 和 Docker Compose
- 你有一个 Git 仓库（GitHub/GitLab/自建等）

---

## 🚀 快速部署流程

### 第一步：在服务器上 Clone 仓库

```bash
# 进入应用目录
mkdir -p ~/apps
cd ~/apps

# Clone 仓库（替换为你的仓库地址）
git clone https://github.com/your-username/caiso-monitor.git

# 进入项目目录
cd caiso-monitor
```

### 第二步：配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置
nano .env
```

**`.env` 文件修改要点：**
```bash
# 1. 修改数据库密码（必须！）
POSTGRES_PASSWORD=YourStrongPassword123!

# 2. 选择监控节点（可选）
CAISO_NODE=SP15  # SP15/NP15/ZP26

# 3. 选择市场类型（可选）
CAISO_MARKET=RTM  # RTM/DAM/RTPD
```

### 第三步：启动服务

```bash
# 一键部署
chmod +x deploy.sh
./deploy.sh
```

或手动启动：
```bash
docker-compose up -d
```

### 第四步：验证部署

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f data_fetcher
```

访问：`http://服务器IP:8501`

---

## 🔄 更新代码

### 本地修改后推送到服务器

```bash
# 本地：修改代码后提交
git add .
git commit -m "修改描述"
git push origin main

# 服务器：拉取更新
cd ~/apps/caiso-monitor
git pull origin main

# 重启服务
docker-compose down
docker-compose up -d --build
```

### 直接编辑服务器上的代码

```bash
# 服务器上修改文件后
nano backend/main.py  # 编辑文件

docker-compose restart backend  # 重启生效

# 提交更改（可选）
git add .
git commit -m "服务器端修改"
git push origin main
```

---

## 📁 仓库结构

```
caiso-monitor/
├── .git/                      # Git 版本控制
├── .gitignore                 # Git 忽略文件
├── .env.example              # 环境变量模板（提交到仓库）
├── .env                      # 环境变量（不提交到仓库！）
├── docker-compose.yml        # Docker 编排
├── deploy.sh                 # 部署脚本
├── backend/                  # 后端代码
├── frontend/                 # 前端代码
├── database/                 # 数据库脚本
└── nginx/                    # Nginx 配置
```

---

## 🔐 安全注意事项

### 1. 永远不要提交 .env 文件

`.env` 文件包含数据库密码等敏感信息，已被加入 `.gitignore`。

如果意外提交：
```bash
# 从 Git 历史中删除
git rm --cached .env
git commit -m "Remove .env from repo"
git push origin main
```

### 2. 保护数据库端口

生产环境建议修改 `docker-compose.yml`，删除数据库端口映射：

```yaml
db:
  # 删除或注释掉这行
  # ports:
  #   - "5432:5432"
```

### 3. 使用 Deploy Key（推荐）

如果是 GitHub 仓库，建议使用 Deploy Key 而非个人账户：

```bash
# 在服务器生成 SSH 密钥
ssh-keygen -t ed25519 -C "caiso-monitor-deploy" -f ~/.ssh/caiso_deploy

# 复制公钥到 GitHub
# Settings -> Deploy keys -> Add deploy key
cat ~/.ssh/caiso_deploy.pub

# 配置 SSH 使用特定密钥
nano ~/.ssh/config
```

添加：
```
Host github-caiso
    HostName github.com
    User git
    IdentityFile ~/.ssh/caiso_deploy
```

然后使用：
```bash
git clone git@github-caiso:your-username/caiso-monitor.git
```

---

## 🌿 分支管理建议

```bash
# 开发分支
git checkout -b develop
# 开发、测试...
git push origin develop

# 生产部署
git checkout main
git merge develop
git push origin main

# 服务器拉取
git pull origin main
docker-compose up -d --build
```

---

## 📊 Git 工作流程图

```
┌─────────────┐     git push      ┌─────────────┐
│  本地开发    │ ─────────────────▶ │  Git 仓库   │
│  (修改代码)  │                    │ (GitHub)    │
└─────────────┘                    └──────┬──────┘
                                          │
                     git pull             │
                     docker-compose up    │
                                          ▼
                                    ┌─────────────┐
                                    │   服务器    │
                                    │  (生产环境) │
                                    └─────────────┘
```

---

## 🆘 常见问题

### Q1: Clone 后部署失败

```bash
# 检查文件是否完整
ls -la

# 检查 .env 是否存在
ls .env  # 如果不存在：cp .env.example .env

# 检查 Docker
docker --version
docker-compose --version
```

### Q2: 拉取更新后服务出错

```bash
# 完整重建
docker-compose down -v  # 删除卷（会清空数据！谨慎使用）
docker-compose up -d --build

# 或仅重建代码
docker-compose up -d --build --no-deps backend frontend
```

### Q3: 权限不足

```bash
# 添加用户到 docker 组
sudo usermod -aG docker $USER
newgrp docker

# 或每次都使用 sudo
sudo docker-compose up -d
```

---

## 📝 完整命令速查表

| 操作 | 命令 |
|------|------|
| 首次克隆 | `git clone <repo-url>` |
| 拉取更新 | `git pull origin main` |
| 查看状态 | `git status` |
| 查看日志 | `docker-compose logs -f` |
| 重启服务 | `docker-compose restart` |
| 停止服务 | `docker-compose down` |
| 重建服务 | `docker-compose up -d --build` |

---

## 🎯 示例：从零到部署

```bash
# 1. 连接服务器
ssh username@your-server

# 2. 安装 Docker（如果未安装）
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# 3. Clone 项目
cd ~
git clone https://github.com/your-username/caiso-monitor.git
cd caiso-monitor

# 4. 配置环境
cp .env.example .env
nano .env  # 修改密码等配置

# 5. 部署
chmod +x deploy.sh
./deploy.sh

# 6. 访问 Dashboard
# 浏览器打开 http://your-server-ip:8501

# 7. 查看日志
docker-compose logs -f
```

---

## 🔗 相关文档

- [README.md](README.md) - 完整部署教程
- [DEPLOY.md](DEPLOY.md) - 详细配置说明
- [QUICKSTART.md](QUICKSTART.md) - 快速开始

---

**Git 仓库地址：** `https://github.com/your-username/caiso-monitor.git`

**部署完成后访问：** `http://服务器IP:8501`