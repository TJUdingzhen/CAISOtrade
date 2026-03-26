# CAISO 实时数据监控 - 快速启动指南

## 🚀 方式一：本地快速测试（推荐先跑这个）

不需要 Docker、不需要数据库，直接用 Python 拉真实数据。

### 1. 安装依赖

```bash
cd caiso_monitor

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install pandas requests
```

### 2. 运行测试脚本

```bash
python test_caiso_live.py
```

你会看到类似这样的输出：

```
🚀 CAISO 实时数据监控
节点: SP15, 市场: RTM
--------------------------------------------------
📡 正在获取 TH_SP15_GEN-APND (RTM) 的数据...
   时间范围: 2025-01-21 12:00:00 ~ 2025-01-22 12:00:00
✅ 成功获取 288 条数据

==================================================
⚡ CAISO 实时电价 - SP15
==================================================
📍 节点: SP15
📊 市场: RTM
⏰ 时间: 2025-01-22 11:55:00+00:00
💰 电价: $45.23/MWh
📈 24h 最高: $127.50
📉 24h 最低: $18.75
📊 24h 平均: $52.34
==================================================

📈 价格趋势 (最近24小时):
--------------------------------------------------------------------------------
$18.75 | 
$23.45 | ███
$31.20 | ███████
$45.23 | ████████████
$67.80 | ██████████████████
$127.50| ████████████████████████████████████████
--------------------------------------------------------------------------------

💾 数据已保存: caiso_SP15_20250122_120000.csv
```

如果这步成功了，说明能接到真实 CAISO 数据。

---

## 🐳 方式二：完整 Docker 部署（带 Dashboard）

### 1. 快速启动

```bash
cd caiso_monitor

# 运行一键部署脚本
./deploy.sh
```

或手动启动：

```bash
# 1. 配置环境变量
cp .env.example .env

# 2. 启动所有服务
docker-compose up -d

# 3. 等待数据库初始化（约30秒）
sleep 30

# 4. 查看状态
docker-compose ps
```

### 2. 访问 Dashboard

```
📊 Dashboard: http://localhost:8501
🔌 API:       http://localhost:8000
📚 API 文档:  http://localhost:8000/docs
```

### 3. 查看数据获取日志

```bash
# 实时查看数据获取 worker 的日志
docker-compose logs -f data_fetcher
```

你会看到类似这样的日志：

```
data_fetcher_1  | 2025-01-22 12:00:00 | INFO | Fetching CAISO data: TH_SP15_GEN-APND (RTM)...
data_fetcher_1  | 2025-01-22 12:00:05 | INFO | Fetched 12 records from CAISO
data_fetcher_1  | 2025-01-22 12:00:05 | INFO | Inserted 12 records for SP15
data_fetcher_1  | 2025-01-22 12:00:05 | INFO | Fetch cycle complete. Next fetch in 300s
```

---

## 📊 可视化 Dashboard 功能

打开 http://localhost:8501 后你会看到：

### 1. 实时指标卡片
- 当前电价（带 24h 涨跌幅）
- 24h 均价
- 24h 最高价
- 24h 最低价

### 2. 价格趋势图
- 可缩放的时间序列图
- 支持选择 1-168 小时历史数据
- 显示均价/最高/最低三条线

### 3. 交易信号面板
- 显示策略生成的交易信号
- CHARGE(充电)/DISCHARGE(放电)/HOLD(持有)

### 4. 节点切换
- 侧边栏可选择 SP15/NP15/ZP26 等节点
- 可切换 RTM/DAM/RTPD 市场

---

## ⚙️ 配置说明

编辑 `.env` 文件修改配置：

```bash
# 监控节点
CAISO_NODE=SP15          # 可选: SP15, NP15, ZP26

# 市场类型
CAISO_MARKET=RTM         # 可选: RTM(实时), DAM(日前), RTPD(15分钟)

# 数据获取间隔（秒）
FETCH_INTERVAL=300       # 默认 5 分钟
```

---

## 🔧 常见问题

### Q1: 测试脚本跑不通？

检查网络连接：
```bash
# 测试能否访问 CAISO
curl -I http://oasis.caiso.com/oasisapi
```

如果在国内，可能需要代理。

### Q2: Docker 启动失败？

```bash
# 查看具体错误
docker-compose logs

# 常见：端口被占用
# 修改 docker-compose.yml 里的端口映射
```

### Q3: Dashboard 显示"暂无数据"？

```bash
# 手动触发一次数据获取
curl "http://localhost:8000/api/fetch?node=SP15&market=RTM&hours=2"

# 或检查 data_fetcher 日志
docker-compose logs data_fetcher
```

### Q4: 数据更新太慢？

CAISO RTM 数据本身有 5-15 分钟延迟，这是正常的。

---

## 🎯 下一步

1. **换节点测试** - 试试 NP15（北加州）的数据
2. **加告警** - 在 `data_fetcher_worker.py` 里加价格阈值判断
3. **写策略** - 在 backend 里加交易信号生成逻辑
4. **上云部署** - 把这套丢到 AWS/阿里云上 24h 跑

---

## 📁 文件说明

| 文件 | 作用 |
|------|------|
| `test_caiso_live.py` | 本地快速测试，不依赖 Docker |
| `backend/data_fetcher_worker.py` | 真实数据获取 worker |
| `backend/main.py` | FastAPI 后端 |
| `frontend/app.py` | Streamlit Dashboard |
| `docker-compose.yml` | 容器编排 |
| `deploy.sh` | 一键部署脚本 |