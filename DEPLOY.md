# CAISO 电力市场实时监控系统

## 📋 项目简介

这是一个完整的 **CAISO 电力市场实时监控平台**，包含：
- 🗄️ **时序数据库**（TimescaleDB）存储电价数据
- 🔌 **后端 API**（FastAPI）提供数据接口
- 📊 **实时监控 Dashboard**（Streamlit）可视化展示
- 🐳 **全容器化部署**，支持一键启动

## 🏗️ 系统架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Nginx     │────▶│   前端      │────▶│   后端 API  │
│  (反向代理)  │     │ (Streamlit)│     │  (FastAPI)  │
└─────────────┘     └─────────────┘     └──────┬──────┘
       │                                       │
       │          ┌─────────────┐              │
       └─────────▶│  数据获取   │◀─────────────┘
                  │   Worker    │
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │  TimescaleDB│
                  │ (PostgreSQL)│
                  └─────────────┘
```

## 📦 服务说明

| 服务 | 端口 | 说明 |
|------|------|------|
| `db` | 5432 | TimescaleDB 时序数据库 |
| `backend` | 8000 | FastAPI 后端服务 |
| `data_fetcher` | - | 后台数据获取 Worker |
| `frontend` | 8501 | Streamlit 监控面板 |
| `nginx` | 80/443 | 反向代理（生产环境） |

## 🚀 快速开始

### 1. 环境要求

- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB+ 可用内存
- 20GB+ 磁盘空间

### 2. 部署步骤

```bash
# 1. 克隆/复制项目到服务器
cd /opt  # 或其他你喜欢的目录
git clone <your-repo> caiso_monitor
cd caiso_monitor

# 2. 配置环境变量（可选）
cp .env.example .env
# 编辑 .env 文件修改配置

# 3. 启动服务
docker-compose up -d

# 4. 等待数据库初始化（约30秒）
docker-compose logs -f db

# 5. 查看所有服务状态
docker-compose ps
```

### 3. 访问系统

- **监控面板**: http://localhost:8501 （或服务器IP）
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

### 4. 默认配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| CAISO_NODE | SP15 | 监控节点 |
| CAISO_MARKET | RTM | 市场类型 |
| FETCH_INTERVAL | 300 | 数据获取间隔（秒） |
| 数据库 | caiso/caiso_password | 用户名/密码 |

## 📁 项目结构

```
caiso_monitor/
├── docker-compose.yml          # Docker 编排配置
├── .env                        # 环境变量（需自行创建）
├── backend/                    # 后端服务
│   ├── Dockerfile
│   ├── Dockerfile.fetcher
│   ├── requirements.txt
│   ├── main.py                 # FastAPI 主应用
│   └── data_fetcher_worker.py  # 数据获取 Worker
├── frontend/                   # 前端 Dashboard
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py                  # Streamlit 应用
├── database/                   # 数据库初始化
│   └── init.sql                # 表结构 + 时序扩展
├── nginx/                      # 反向代理配置
│   └── nginx.conf
└── docs/                       # 文档
    └── DEPLOY.md               # 本文件
```

## ⚙️ 环境变量配置

创建 `.env` 文件自定义配置：

```bash
# CAISO 配置
CAISO_NODE=SP15
CAISO_MARKET=RTM
FETCH_INTERVAL=300

# 数据库配置
POSTGRES_USER=caiso
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=caiso_market

# 可选：外部数据库
# DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

## 🛠️ 运维管理

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务
docker-compose logs -f backend
docker-compose logs -f data_fetcher
docker-compose logs -f db
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启单个服务
docker-compose restart backend
```

### 更新部署

```bash
# 拉取最新代码后
docker-compose pull
docker-compose up -d --build
```

### 备份数据

```bash
# 备份数据库
docker exec caiso_db pg_dump -U caiso caiso_market > backup_$(date +%Y%m%d).sql

# 恢复数据库
cat backup_20240101.sql | docker exec -i caiso_db psql -U caiso caiso_market
```

### 进入数据库

```bash
docker exec -it caiso_db psql -U caiso -d caiso_market
```

## 🔌 API 接口说明

### 健康检查
```
GET /health
```

### 获取最新价格
```
GET /api/lmp/latest?node=SP15&market=RTM
```

### 获取历史数据
```
GET /api/lmp/history?node=SP15&market=RTM&hours=24&aggregation=raw

# aggregation 可选: raw, hour, day
```

### 获取价格统计
```
GET /api/lmp/stats?node=SP15&market=RTM
```

### 获取节点列表
```
GET /api/nodes
```

### 手动触发数据获取
```
POST /api/fetch?node=SP15&market=RTM&hours=1
```

## 🌐 生产环境部署

### 使用 Nginx 反向代理

```bash
# 使用 production profile 启动（包含 nginx）
docker-compose --profile production up -d
```

### 配置 HTTPS

1. 将 SSL 证书放入 `nginx/ssl/` 目录：
   - `cert.pem` - 证书
   - `key.pem` - 私钥

2. 编辑 `nginx/nginx.conf` 取消 HTTPS server 配置的注释

3. 重启 nginx：
   ```bash
   docker-compose restart nginx
   ```

### 使用外部数据库

在 `.env` 中配置外部数据库 URL：
```bash
DATABASE_URL=postgresql://user:password@your-db-host:5432/caiso_market
```

然后注释掉 `docker-compose.yml` 中的 `db` 服务。

## 📊 监控节点说明

CAISO 主要节点：

| 节点 | 说明 |
|------|------|
| SP15 | 南加州主要枢纽 |
| NP15 | 北加州主要枢纽 |
| ZP26 | 26区 |
| PGEB-APND | PG&E 区域 |
| SDGE-APND | SDG&E 区域 |
| SCE-APND | SCE 区域 |

## 🐛 故障排查

### 数据库连接失败

```bash
# 检查数据库状态
docker-compose ps db
docker-compose logs db

# 检查网络连接
docker network inspect caiso_monitor_caiso_network
```

### 数据未更新

```bash
# 检查数据获取 Worker
docker-compose logs -f data_fetcher

# 手动触发数据获取
curl "http://localhost:8000/api/fetch?node=SP15&market=RTM&hours=2"
```

### 前端无法访问

```bash
# 检查前端日志
docker-compose logs frontend

# 检查后端 API
curl http://localhost:8000/health
```

## 📝 开发说明

### 本地开发（不使用 Docker）

```bash
# 1. 安装 PostgreSQL 并启用 TimescaleDB
# 2. 创建数据库并运行 database/init.sql

# 3. 启动后端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# 4. 启动前端（新终端）
cd frontend
pip install -r requirements.txt
streamlit run app.py

# 5. 启动数据获取（新终端）
python backend/data_fetcher_worker.py
```

## 📜 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 PR！

---

**注意**: 本项目仅供学习和研究使用。CAISO 数据使用需遵守其服务条款。