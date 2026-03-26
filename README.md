# CAISO 电力市场实时监控系统 - 完整部署教程

本文档指导你在服务器上完整部署 CAISO 实时数据监控系统，包含真实 CAISO 数据接入、时序数据库存储、Web Dashboard 可视化。

---

## 📋 前置要求

### 硬件要求
- **CPU**: 2 核+
- **内存**: 4GB+
- **磁盘**: 20GB 可用空间
- **网络**: 能访问外网（特别是 http://oasis.caiso.com）

### 软件要求
- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 任意版本

### 检查环境
```bash
# 检查 Docker
docker --version
docker-compose --version

# 如果没有安装，Ubuntu/Debian 安装命令：
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

---

## 🌏 中国大陆用户特别说明

**重要**: CAISO OASIS API 服务器位于美国加州，中国大陆直接访问可能超时或失败。

### 解决方案

#### 方案 1：使用模拟数据（推荐先测试系统）

编辑 `.env` 文件：
```bash
USE_MOCK_DATA=true
```

系统会自动生成模拟的 CAISO 电价数据（符合日内波动特征：早晚高峰、偶发负电价），让你在国内也能完整测试 Dashboard、数据库和 API。

#### 方案 2：配置代理

如果你有可用的 HTTP 代理：
```bash
USE_PROXY=true
HTTP_PROXY=http://your-proxy:port
HTTPS_PROXY=http://your-proxy:port
```

#### 方案 3：使用海外服务器

将系统部署在 AWS (us-west)、阿里云香港/新加坡等海外节点，无需额外配置即可访问真实 CAISO 数据。

### 网络检查

```bash
# 测试能否访问 CAISO
curl -I http://oasis.caiso.com/oasisapi
# 国内大概率返回超时或连接失败
```

---

## 🚀 快速部署（5 分钟）

### 方式一：Git Clone（推荐）

```bash
# 1. 连接服务器并安装 Docker
ssh username@your-server-ip
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# 2. Clone 仓库并部署
git clone https://github.com/your-username/caiso-monitor.git ~/apps/caiso-monitor
cd ~/apps/caiso-monitor
cp .env.example .env
nano .env  # 修改数据库密码
./deploy.sh

# 3. 访问系统
# Dashboard: http://服务器IP:8501
```

**详细 Git 部署说明**: [CLONE.md](CLONE.md)

---

### 方式二：手动上传文件

如果没有 Git，可以将项目文件打包上传到服务器：

```bash
# 本地打包
tar -czf caiso-monitor.tar.gz caiso-monitor/

# 上传到服务器
scp caiso-monitor.tar.gz user@server:/home/user/

# 服务器解压部署
ssh user@server
tar -xzf caiso-monitor.tar.gz
cd caiso-monitor
./deploy.sh
```

---

### 步骤 2：进入项目目录

```bash
cd ~/apps/caiso_monitor

# 查看目录结构
ls -la
```

你应该看到：
```
docker-compose.yml
.env.example
backend/
frontend/
database/
nginx/
deploy.sh
```

### 步骤 3：配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置
nano .env  # 或 vim .env
```

**`.env` 文件内容示例：**
```bash
# ===========================================
# CAISO 配置（按需修改）
# ===========================================

# 监控节点 - 可选值：
# SP15  = 南加州主要枢纽（推荐）
# NP15  = 北加州主要枢纽
# ZP26  = 26区
# PGEB-APND = PG&E 区域
# SDGE-APND = SDG&E 区域
# SCE-APND  = SCE 区域
CAISO_NODE=SP15

# 市场类型 - 可选值：
# RTM  = 实时市场（Real-Time，推荐）
# DAM  = 日前市场（Day-Ahead）
# RTPD = 实时15分钟（Real-Time 15-Minute）
CAISO_MARKET=RTM

# 数据获取间隔（秒）- 默认 5 分钟
# CAISO RTM 数据本身有约 5-15 分钟延迟，不建议设太小
FETCH_INTERVAL=300

# ===========================================
# 数据库配置（生产环境请修改密码）
# ===========================================
POSTGRES_USER=caiso
POSTGRES_PASSWORD=YourSecurePassword123!  # 修改此处！
POSTGRES_DB=caiso_market

# 完整数据库 URL（一般不用改）
DATABASE_URL=postgresql://caiso:YourSecurePassword123!@db:5432/caiso_market

# ===========================================
# 高级配置（一般保持默认）
# ===========================================
BACKFILL_DAYS=7
LOG_LEVEL=INFO
TZ=America/Los_Angeles
```

**保存退出**：按 `Ctrl+O`，然后 `Enter`，再按 `Ctrl+X`。

### 步骤 4：一键部署

```bash
# 赋予脚本执行权限
chmod +x deploy.sh

# 执行部署
./deploy.sh
```

脚本会自动：
1. 检查 Docker 环境
2. 创建必要目录
3. 拉取 Docker 镜像
4. 启动所有服务
5. 等待数据库初始化

部署过程约 3-5 分钟（取决于网络速度）。

### 步骤 5：验证部署

```bash
# 查看所有服务状态
docker-compose ps
```

预期输出：
```
    Name                   Command               State           Ports
--------------------------------------------------------------------------------
caiso_backend     uvicorn main:app --host ...   Up      0.0.0.0:8000->8000/tcp
caiso_db          docker-entrypoint.sh postgres Up      0.0.0.0:5432->5432/tcp
caiso_fetcher     python data_fetcher_worke...  Up
caiso_frontend    streamlit run app.py --s...   Up      0.0.0.0:8501->8501/tcp
```

所有服务都应该是 `Up` 状态。

### 步骤 6：访问系统

打开浏览器，访问以下地址：

| 服务 | 地址 | 说明 |
|------|------|------|
| **Dashboard** | http://服务器IP:8501 | 实时数据可视化 |
| **API 文档** | http://服务器IP:8000/docs | Swagger UI |
| **API** | http://服务器IP:8000 | REST API |

**示例：**
```
http://192.168.1.100:8501
http://your-server-domain.com:8501
```

---

## 📊 功能介绍

### Dashboard 界面

打开 Dashboard 后，你会看到：

#### 1. 实时指标卡片
- **当前电价**: 最新实时价格，带 24 小时涨跌幅
- **24h 均价**: 过去24小时平均价格
- **24h 最高价**: 过去24小时峰值
- **24h 最低价**: 过去24小时谷值

#### 2. 价格趋势图
- 可交互的 Plotly 图表
- 支持缩放、平移
- 显示均价/最高/最低三条线
- 可调整时间范围（1-168 小时）

#### 3. 侧边栏控制
- **节点选择**: SP15/NP15/ZP26 等
- **市场选择**: RTM/DAM/RTPD
- **历史范围**: 1-168 小时滑块
- **自动刷新**: 开关控制

#### 4. 系统状态
- API 服务健康状态
- 数据覆盖节点统计

---

## 🔧 常用操作

### 查看日志

```bash
cd ~/apps/caiso_monitor

# 查看所有服务日志
docker-compose logs -f

# 只看数据获取 worker（最重要）
docker-compose logs -f data_fetcher

# 只看后端 API
docker-compose logs -f backend

# 只看前端
docker-compose logs -f frontend

# 只看数据库
docker-compose logs -f db
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启单个服务
docker-compose restart backend
docker-compose restart data_fetcher
```

### 停止/启动

```bash
# 停止所有服务（数据会保留）
docker-compose down

# 彻底删除（包括数据库数据！）
docker-compose down -v

# 启动
docker-compose up -d
```

### 更新部署

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

### 进入数据库

```bash
# 进入 PostgreSQL 命令行
docker exec -it caiso_db psql -U caiso -d caiso_market

# 常用 SQL 查询
\dt                    # 列出所有表
SELECT * FROM lmp_data ORDER BY interval_start DESC LIMIT 10;  # 查看最新数据
SELECT COUNT(*) FROM lmp_data;  # 统计总数据量
\q                     # 退出
```

### 手动触发数据获取

```bash
# 手动触发一次数据拉取
curl "http://localhost:8000/api/fetch?node=SP15&market=RTM&hours=2"
```

---

## 🌐 配置域名和 HTTPS（生产环境）

### 使用 Nginx 反向代理

1. **编辑 `nginx/nginx.conf`**

将域名 `your-domain.com` 替换为你的实际域名：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 修改此处
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;  # 修改此处

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # ... 其余配置保持不变
}
```

2. **准备 SSL 证书**

```bash
# 创建证书目录
mkdir -p nginx/ssl

# 方式一：使用 Let's Encrypt（推荐）
sudo apt install certbot
certbot certonly --standalone -d your-domain.com
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem

# 方式二：自签名证书（测试用）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem \
  -subj "/CN=your-domain.com"
```

3. **启动带 Nginx 的服务**

```bash
# 使用 production profile 启动
docker-compose --profile production up -d
```

4. **防火墙开放端口**

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# CentOS (Firewalld)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

---

## 📦 备份与恢复

### 备份数据库

```bash
# 创建备份目录
mkdir -p ~/backups

# 备份数据库
docker exec caiso_db pg_dump -U caiso caiso_market \
  > ~/backups/caiso_backup_$(date +%Y%m%d_%H%M%S).sql

# 查看备份
ls -lh ~/backups/
```

### 恢复数据库

```bash
# 停止服务
docker-compose down

# 删除旧数据（谨慎！）
docker volume rm caiso_monitor_postgres_data

# 重新启动（会自动初始化）
docker-compose up -d

# 等待数据库初始化完成（约30秒）
sleep 30

# 恢复数据
cat ~/backups/caiso_backup_20240122_120000.sql | \
  docker exec -i caiso_db psql -U caiso caiso_market
```

---

## 🐛 故障排除

### 问题 1：部署后无法访问 Dashboard

**症状**：浏览器访问 http://服务器IP:8501 无响应

**排查步骤**：
```bash
# 1. 检查服务状态
docker-compose ps

# 2. 检查端口监听
netstat -tlnp | grep 8501
# 或
ss -tlnp | grep 8501

# 3. 检查防火墙
sudo ufw status
# 如果 8501 未开放：
sudo ufw allow 8501/tcp

# 4. 检查前端日志
docker-compose logs frontend
```

### 问题 2：数据获取失败

**症状**：Dashboard 显示"暂无数据"，data_fetcher 日志报错

**排查步骤**：
```bash
# 1. 查看详细日志
docker-compose logs data_fetcher

# 2. 检查能否访问 CAISO
curl -I http://oasis.caiso.com/oasisapi

# 3. 手动测试 API
curl "http://localhost:8000/api/fetch?node=SP15&market=RTM&hours=1"

# 4. 检查数据库连接
docker-compose exec backend python -c "
from sqlalchemy import create_engine
import os
url = os.getenv('DATABASE_URL')
engine = create_engine(url)
print('Database connected!' if engine.connect() else 'Failed')
"
```

**常见原因**：
- 服务器无法访问外网（CAISO API）
- 数据库未初始化完成
- 节点名称错误

### 问题 3：数据库连接失败

**症状**：backend/data_fetcher 反复重启，日志显示连接被拒绝

**解决**：
```bash
# 等待数据库完全启动
docker-compose logs -f db

# 直到看到 "database system is ready to accept connections"
# 然后重启其他服务
docker-compose restart backend data_fetcher
```

### 问题 4：内存不足

**症状**：服务启动后被杀死，日志显示 `OOM`

**解决**：
```bash
# 增加交换空间
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 验证
free -h
```

---

## 🔐 安全配置建议

### 1. 修改默认密码

编辑 `.env` 文件：
```bash
POSTGRES_PASSWORD=YourStrongPassword123!
```

然后重启：
```bash
docker-compose down
docker-compose up -d
```

### 2. 限制数据库端口暴露

如果不需要外网访问数据库，编辑 `docker-compose.yml`：

```yaml
db:
  # 去掉端口映射，只允许内部访问
  # ports:
  #   - "5432:5432"
```

### 3. 使用防火墙

```bash
# 只允许必要端口
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 8501/tcp    # Dashboard
# sudo ufw allow 8000/tcp  # API（如不需要外网访问，注释掉）
sudo ufw enable
```

### 4. 配置 Nginx Basic Auth（可选）

```bash
# 创建密码文件
sudo apt install apache2-utils
htpasswd -c nginx/.htpasswd admin

# 修改 nginx.conf
location / {
    auth_basic "CAISO Monitor";
    auth_basic_user_file /etc/nginx/.htpasswd;
    # ...
}
```

---

## 📝 API 使用示例

### 获取最新价格
```bash
curl "http://localhost:8000/api/lmp/latest?node=SP15&market=RTM"
```

### 获取历史数据
```bash
curl "http://localhost:8000/api/lmp/history?node=SP15&market=RTM&hours=24"
```

### 获取统计信息
```bash
curl "http://localhost:8000/api/lmp/stats?node=SP15&market=RTM"
```

### Python 调用示例
```python
import requests

API_URL = "http://your-server:8000"

# 获取最新价格
resp = requests.get(f"{API_URL}/api/lmp/latest", params={
    "node": "SP15",
    "market": "RTM"
})
data = resp.json()
print(f"当前电价: ${data['price']}/MWh")
```

---

## 🎯 进阶配置

### 监控多个节点

编辑 `.env`：
```bash
# 启动多个 data_fetcher 实例（需要修改 docker-compose.yml）
```

或手动运行额外 worker：
```bash
docker run -d --name caiso_np15 \
  -e CAISO_NODE=NP15 \
  -e CAISO_MARKET=RTM \
  -e DATABASE_URL=postgresql://caiso:pass@db:5432/caiso_market \
  --network caiso_monitor_caiso_network \
  caiso_monitor_backend python data_fetcher_worker.py
```

### 配置告警

编辑 `backend/data_fetcher_worker.py`，在 `fetch_and_store_data` 函数后添加：

```python
# 价格告警
if price > 200:  # $200/MWh
    send_alert(f"高价告警: {node_name} 电价达到 ${price}/MWh")

if price < 0:  # 负电价
    send_alert(f"负电价提醒: {node_name} 电价为 ${price}/MWh")
```

实现 `send_alert` 函数（钉钉/邮件/Slack）。

---

## 📞 获取帮助

如果遇到问题：

1. 查看日志：`docker-compose logs -f`
2. 检查服务状态：`docker-compose ps`
3. 重启服务：`docker-compose restart`

---

## 📄 文件清单

部署完成后，项目目录包含：

```
caiso_monitor/
├── docker-compose.yml      # Docker 编排配置
├── .env                    # 环境变量（你创建的）
├── .env.example            # 环境变量模板
├── deploy.sh               # 一键部署脚本
├── README.md               # 项目说明
├── DEPLOY.md               # 本文件（部署教程）
├── QUICKSTART.md           # 快速开始指南
├── test_caiso_live.py      # 本地测试脚本
├── backend/                # 后端代码
│   ├── Dockerfile
│   ├── Dockerfile.fetcher
│   ├── requirements.txt
│   ├── main.py            # FastAPI 主程序
│   └── data_fetcher_worker.py
├── frontend/               # 前端代码
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py             # Streamlit Dashboard
├── database/               # 数据库初始化
│   └── init.sql
└── nginx/                  # Nginx 配置
    └── nginx.conf
```

---

## ✅ 部署检查清单

部署完成后，确认以下事项：

- [ ] `docker-compose ps` 显示所有服务 Up
- [ ] http://服务器IP:8501 能打开 Dashboard
- [ ] Dashboard 显示"当前电价"数值
- [ ] `docker-compose logs data_fetcher` 显示数据获取成功
- [ ] （可选）配置了域名和 HTTPS
- [ ] （可选）修改了默认数据库密码
- [ ] （可选）配置了防火墙规则

---

**部署完成！开始监控 CAISO 电力市场吧！⚡**