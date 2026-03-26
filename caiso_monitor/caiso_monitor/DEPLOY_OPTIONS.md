# CAISO Monitor 部署方式总览

本项目支持多种部署方式，选择最适合你的：

---

## 🚀 推荐方式：Git Clone

适用于：有 Git 仓库，需要版本控制和后续更新

```bash
# 服务器上执行
git clone https://github.com/your-username/caiso-monitor.git
cd caiso-monitor
cp .env.example .env
nano .env
./deploy.sh
```

**文档**: [CLONE.md](CLONE.md) | [GIT_DEPLOY.md](GIT_DEPLOY.md)

---

## 📦 替代方式：文件上传

### 方式 A：打包上传

适用于：没有 Git 或内网环境

```bash
# 本地打包
./package.sh

# 上传并部署
scp caiso-monitor_20250122.tar.gz user@server:/home/user/
ssh user@server
tar -xzf caiso-monitor_20250122.tar.gz
cd caiso-monitor
./deploy.sh
```

**文档**: [UPLOAD.md](UPLOAD.md)

---

### 方式 B：SFTP 工具上传

适用于：Windows 用户，习惯图形界面

使用 FileZilla、WinSCP 等工具上传项目文件夹，然后：

```bash
ssh user@server
cd ~/caiso-monitor
./deploy.sh
```

---

## 🧪 测试方式：本地运行

适用于：想先测试数据能否获取，再决定是否部署

```bash
# 不需要 Docker，不需要数据库
pip install pandas requests
python test_caiso_live.py
```

**文档**: [QUICKSTART.md](QUICKSTART.md)

---

## 📊 部署方式对比

| 方式 | 难度 | 更新 | 适用场景 |
|------|------|------|----------|
| **Git Clone** | ⭐⭐ | `git pull` | 有 Git 仓库，需要频繁更新 |
| **打包上传** | ⭐⭐⭐ | 重新上传 | 无 Git，一次性部署 |
| **SFTP 上传** | ⭐⭐ | 重新上传 | Windows 用户，图形界面 |
| **本地测试** | ⭐ | - | 验证可行性 |

---

## 📝 部署步骤总结

无论哪种方式，部署核心步骤都是：

1. **准备环境**: 服务器 + Docker
2. **获取代码**: Git clone 或上传文件
3. **配置环境**: `cp .env.example .env` 并编辑
4. **执行部署**: `./deploy.sh`
5. **验证访问**: 浏览器打开 `http://服务器IP:8501`

---

## 🔗 文档索引

| 文档 | 内容 |
|------|------|
| [README.md](README.md) | 完整部署教程（主文档） |
| [CLONE.md](CLONE.md) | Git 克隆部署（快速版） |
| [GIT_DEPLOY.md](GIT_DEPLOY.md) | Git 部署详解（含分支管理） |
| [DEPLOY.md](DEPLOY.md) | Docker 部署详细说明 |
| [QUICKSTART.md](QUICKSTART.md) | 5 分钟快速开始 |
| [UPLOAD.md](UPLOAD.md) | 文件上传清单 |

---

## 💡 推荐路径

```
有 Git 仓库 ────────────────────────────────▶ Git Clone
                                          [CLONE.md]

无 Git ─────┬── 有命令行 ──▶ 打包上传
            │              [UPLOAD.md]
            │
            └── Windows ──▶ SFTP 工具上传
                           [UPLOAD.md]

想先测试 ─────────────────────────────────▶ 本地测试
                                          [QUICKSTART.md]
```

---

## ❓ 遇到问题？

1. 查看详细文档 [README.md](README.md)
2. 查看日志 `docker-compose logs -f`
3. 检查服务 `docker-compose ps`
4. 重启服务 `docker-compose restart`

---

**选择你的部署方式，开始监控 CAISO 电力市场！** ⚡