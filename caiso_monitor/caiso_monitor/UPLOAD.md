# 📤 上传到服务器的文件清单

将以下文件上传到服务器的任意目录（例如 `/home/username/apps/`）：

## 必需文件

```
caiso_monitor/
├── docker-compose.yml          ✅ 主配置文件
├── .env.example               ✅ 环境变量模板
├── deploy.sh                  ✅ 一键部署脚本
├── backend/                   ✅ 后端代码目录
│   ├── Dockerfile
│   ├── Dockerfile.fetcher
│   ├── requirements.txt
│   ├── main.py
│   └── data_fetcher_worker.py
├── frontend/                  ✅ 前端代码目录
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── database/                  ✅ 数据库初始化
│   └── init.sql
└── nginx/                     ✅ Nginx配置
    └── nginx.conf
```

## 可选文件（推荐一起上传）

```
├── README.md                  📖 完整部署教程
├── DEPLOY.md                  📖 详细部署说明
├── QUICKSTART.md              📖 快速开始指南
├── test_caiso_live.py         🧪 本地测试脚本
└── package.sh                 📦 打包脚本
```

---

## 上传方式

### 方式一：SCP 命令行

在本地项目目录执行：

```bash
# 打包
tar -czf caiso_monitor.tar.gz caiso_monitor/

# 上传到服务器
scp caiso_monitor.tar.gz username@your-server-ip:/home/username/

# 登录服务器解压
ssh username@your-server-ip
tar -xzf caiso_monitor.tar.gz
cd caiso_monitor
./deploy.sh
```

### 方式二：SFTP 工具

使用 FileZilla、WinSCP 等工具：
1. 连接服务器
2. 创建目录 `/home/username/caiso_monitor`
3. 将上述文件拖拽上传到该目录

### 方式三：Git 克隆（如果服务器有 Git）

```bash
# 在服务器上
git clone https://github.com/your-repo/caiso-monitor.git
cd caiso-monitor
./deploy.sh
```

---

## 服务器部署命令

```bash
# 1. 进入项目目录
cd ~/caiso_monitor

# 2. 配置环境变量
cp .env.example .env
nano .env  # 编辑配置

# 3. 执行部署
chmod +x deploy.sh
./deploy.sh

# 4. 等待完成，访问 Dashboard
# http://your-server-ip:8501
```

---

## 目录结构检查

部署前确保服务器上的目录结构：

```
~/caiso_monitor/
├── docker-compose.yml
├── .env (你创建的)
├── .env.example
├── deploy.sh
├── backend/
├── frontend/
├── database/
├── nginx/
└── README.md
```

---

## 端口需求

确保服务器防火墙开放以下端口：

| 端口 | 用途 | 必需 |
|------|------|------|
| 8501 | Dashboard | ✅ 是 |
| 8000 | API 接口 | ⚪ 可选 |
| 5432 | 数据库 | ⚪ 可选（仅外部访问需要） |
| 80/443 | HTTP/HTTPS | ⚪ 使用 Nginx 时需要 |

---

## 最小化部署（仅必需文件）

如果只需要最基本功能，最少需要这些文件：

```bash
# 在服务器上创建目录
mkdir -p ~/caiso_monitor
cd ~/caiso_monitor

# 创建 docker-compose.yml
# 创建 backend/ 目录及其中文件
# 创建 frontend/ 目录及其中文件
# 创建 database/init.sql

# 然后执行
docker-compose up -d
```

---

**提示**：建议使用 `package.sh` 脚本打包后再上传，避免遗漏文件。