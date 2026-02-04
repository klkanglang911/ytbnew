# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

YouTube 直播代理服务：为中国大陆用户通过 VLC 播放器观看 YouTube 直播提供代理服务。支持最多 10 个并发直播流，缓存机制 + Prometheus 监控 + AlertManager 告警 + Grafana 仪表板。

**核心特性**：
- yt-dlp 直播流提取与代理
- Redis 分布式缓存（6 小时 TTL）
- M3U 播放列表生成（VLC 兼容）
- Prometheus/Grafana 实时监控
- 企业微信 Webhook 告警
- Docker Compose 编排部署
- 健康检查与自动故障恢复

## 核心架构

### 技术栈

| 组件 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.104.1 | Web 框架，RESTful API |
| Python | 3.11 | 运行时 |
| Redis | 7-alpine | 分布式缓存 + 分布式锁 |
| yt-dlp | >=2024.12.0 | YouTube 流提取 |
| Prometheus | latest | 指标收集 |
| Grafana | latest | 可视化仪表板 |
| AlertManager | latest | 告警管理与路由 |
| Nginx | alpine | 反向代理 + HTTPS 终止 |

### 应用层结构

```
app/
├── main.py                    # FastAPI 应用入口，启动/关闭事件
├── config.py                  # Pydantic Settings 配置管理
├── schemas.py                 # Pydantic 数据模型（请求/响应）
├── models.py                  # 数据库或内部数据模型
├── api/
│   ├── routes.py             # 主要 API 路由（/channels, /stream, /m3u）
│   └── health.py             # 健康检查路由 (/health)
├── services/
│   ├── ytdlp_service.py      # yt-dlp 流提取服务（并发控制、超时管理）
│   ├── cache_service.py      # Redis 缓存服务（Get/Set/Lock/Invalidate）
│   ├── stream_resolver.py    # 流解析编排（调度缓存 + yt-dlp）
│   └── monitor_service.py    # Prometheus 指标上报
├── utils/
│   ├── logger.py             # 日志配置（JSON + 结构化日志）
│   └── retry.py              # 指数退避重试装饰器
└── templates/
    └── channels_config.py    # 静态频道列表配置
```

### 请求流程

```
VLC 用户请求
    ↓
Nginx 反向代理 (HTTPS 终止)
    ↓
FastAPI 应用
    ↓
routes.py → get_stream() 路由
    ↓
stream_resolver.get_stream_url()
    ├─ cache_service.get_stream_url() → 检查缓存
    ├─ (缓存未命中) ytdlp_service.extract_stream_url() → 提取流
    │   └─ retry_with_backoff() + subprocess yt-dlp 命令
    └─ cache_service.set_stream_url() → 存入缓存
    ↓
Response: StreamUrlResponse (流 URL + 元数据)
    ↓
VLC 获得流地址，开始播放直播
```

### 并发控制机制

1. **yt-dlp 并发限制**：`asyncio.Semaphore(MAX_CONCURRENT_YTDLP_REQUESTS=3)`
   - 防止 yt-dlp 进程爆炸
   - 单位时间最多 3 个流提取请求

2. **分布式锁**：Redis `lock:{channel}` 键
   - 防止并发重复解析同一频道
   - 获取锁后才能调用 yt-dlp（30秒过期）

3. **流级并发**：`MAX_CONCURRENT_STREAMS=10`
   - VLC 播放器能同时打开的流数量上限
   - 应用级别限流

### 配置管理

所有配置都在 `app/config.py` 的 `Settings` 类中，通过环境变量注入（`.env` 文件）：

| 环境变量 | 默认值 | 说明 |
|---------|-------|------|
| DEBUG | false | 调试模式 |
| LOG_LEVEL | INFO | 日志级别 (DEBUG/INFO/WARNING) |
| LOG_FORMAT | text | 日志格式 (text/json) |
| REDIS_HOST | redis | Redis 主机 |
| REDIS_PORT | 6379 | Redis 端口 |
| REDIS_PASSWORD | password | Redis 密码 |
| CACHE_TTL | 21600 | 缓存 TTL（秒）= 6 小时 |
| YTDLP_TIMEOUT | 30 | yt-dlp 超时（秒） |
| YTDLP_MAX_RETRIES | 3 | yt-dlp 重试次数 |
| MAX_CONCURRENT_YTDLP_REQUESTS | 3 | yt-dlp 并发限制 |
| MAX_CONCURRENT_STREAMS | 10 | 最大流数量 |
| REQUEST_TIMEOUT | 30 | API 请求超时 |

## 本地开发命令

### 本地环境准备

```powershell
# 需要：Docker Desktop for Windows + Python 3.11+
# 验证 Docker
docker --version
docker-compose --version

# 进入项目目录
cd D:\WORK\AI_WORK\ytb_new

# 拉取最新代码
git pull origin main
```

### 启动本地开发环境

```powershell
# 1. 创建 .env 文件（本地测试）
@"
REDIS_HOST=redis
REDIS_PASSWORD=password
DEBUG=true
LOG_LEVEL=DEBUG
CACHE_TTL=21600
YTDLP_TIMEOUT=30
YTDLP_MAX_RETRIES=3
MAX_CONCURRENT_STREAMS=10
MAX_CONCURRENT_YTDLP_REQUESTS=3
REQUEST_TIMEOUT=30
GRAFANA_PASSWORD=admin
WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR-KEY
"@ | Out-File -Encoding UTF8 .env

# 2. 启动所有容器
docker-compose up -d

# 3. 等待容器初始化并查看状态
Start-Sleep -Seconds 5
docker-compose ps

# 4. 实时查看日志（在新窗口）
docker-compose logs -f app
```

### 验证各服务

```powershell
# 应用健康检查
curl http://localhost:8000/health

# API 文档（Swagger UI）
curl http://localhost:8000/docs

# Redis 连接测试
docker-compose exec redis redis-cli -a password ping

# Prometheus 指标
curl http://localhost:9090/api/v1/status/config

# Grafana 仪表板
Start-Process http://localhost:3000
# 用户名: admin, 密码: admin

# AlertManager UI
Start-Process http://localhost:9093
```

### 测试 API

```powershell
# 获取频道列表
curl http://localhost:8000/api/channels

# 获取特定频道的流 URL
curl "http://localhost:8000/api/stream/%E4%B8%89%E7%AB%8B%E6%96%B0%E9%97%BB"

# 获取 M3U 播放列表
curl http://localhost:8000/playlist.m3u

# 查看 Prometheus 暴露的指标
curl http://localhost:9000/metrics
```

### 常见开发命令

```powershell
# 查看容器日志
docker-compose logs app --tail=50
docker-compose logs -f app  # 跟踪日志

# 进入应用容器执行命令
docker-compose exec app bash
docker-compose exec app python -m pytest

# 重启特定服务
docker-compose restart app
docker-compose restart redis

# 停止所有容器
docker-compose down

# 完全清理（含卷）
docker-compose down -v

# 重新构建镜像
docker-compose build --no-cache app

# 查看容器详细信息
docker-compose ps --format "table {{.Names}}\t{{.Status}}"
```

## API 端点详解

### 健康检查 `/health`
- **方法**：GET
- **响应**：JSON 对象，包含应用状态、Redis 连接、yt-dlp 可用性
- **用途**：Nginx 反向代理健康检查

### 频道列表 `/api/channels`
- **方法**：GET
- **响应**：`List[ChannelResponse]`
- **参数**：无
- **缓存**：不缓存

### 获取流 `/api/stream/{channel_name}`
- **方法**：GET
- **参数**：
  - `channel_name`：URL 路径参数，频道名称
  - `use_cache`：查询参数，bool，默认 true
- **响应**：`StreamUrlResponse`
- **逻辑**：
  1. 查找频道配置
  2. 调用 `stream_resolver.get_stream_url()`
  3. 返回流 URL + 元数据

### M3U 播放列表 `/playlist.m3u`
- **方法**：GET
- **响应**：纯文本，M3U 格式
- **内容**：所有频道的流 URL（前缀 `http://localhost:8000/api/stream/`）
- **用途**：VLC 直接导入播放列表

## 核心服务深入理解

### YtdlpService（yt-dlp 流提取）

**关键设计**：
- 使用 `asyncio.Semaphore` 限制并发数（最多 3）
- 同步操作（subprocess 调用）运行在线程池避免阻塞
- 指数退避重试（最多 3 次）
- YouTube 流 URL 有效期约 1 小时

**yt-dlp 命令行**：
```bash
yt-dlp -f best -j --socket-timeout 30 --no-warnings -q [URL]
```
输出 JSON，提取其中的 `url` 或 `formats[0].url` 字段。

**错误处理**：
- `TimeoutExpired`：超过 `YTDLP_TIMEOUT + 5` 秒
- `JSONDecodeError`：yt-dlp 输出格式错误
- 其他异常：频道不直播、网络错误等

### CacheService（Redis 缓存）

**关键方法**：
- `get_stream_url(channel)`：获取缓存，未命中返回 None
- `set_stream_url(channel, data, ttl)`：存入缓存，TTL 默认 6 小时
- `get_or_set(channel, fetch_func)`：缓存模式（Miss On Fill）
- `acquire_lock(channel)`：分布式锁，防止并发重复解析
- `release_lock(channel)`：释放锁
- `invalidate(channel)`：清除特定频道缓存

**Redis 键设计**：
- `stream:{channel_name}`：存储流数据（JSON）
- `lock:{channel_name}`：分布式锁标记

### StreamResolver（流解析编排）

调度流程：
1. 尝试 Redis `acquire_lock()`
2. 如果获得锁，调用 `ytdlp_service.extract_stream_url()`
3. 缓存结果到 Redis
4. 释放锁
5. 如果未获得锁，等待并轮询缓存

### Logger（日志系统）

日志级别从低到高：
- `DEBUG`：详细调试信息（缓存命中/未命中等）
- `INFO`：关键操作（服务启动、流提取成功）
- `WARNING`：非致命错误（缓存读写失败）
- `ERROR`：致命错误（Redis 连接失败、yt-dlp 不可用）

## Docker Compose 编排

### 关键配置

**资源限制**（防止内存溢出）：
```yaml
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

**健康检查**：
```yaml
healthcheck:
  test: [CMD, curl, -f, "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

**依赖关系**：
```yaml
depends_on:
  redis:
    condition: service_healthy  # 等待 Redis 健康
```

**日志配置**（防止日志爆炸）：
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "20m"
    max-file: "5"
```

### 容器说明

| 容器 | 镜像 | 端口 | 用途 |
|------|------|------|------|
| ytb_redis | redis:7-alpine | 6379 | 缓存 + 分布式锁 |
| ytb_app | 本地构建 | 8000/9000 | FastAPI + Prometheus |
| ytb_prometheus | prom/prometheus | 9090 | 指标收集 |
| ytb_grafana | grafana/grafana | 3000 | 仪表板 |
| ytb_alertmanager | prom/alertmanager | 9093 | 告警管理 |
| ytb_nginx | nginx:alpine | 80/443 | 反向代理 + HTTPS |

## 部署到生产（VPS）

### 前置条件

- VPS：2 CPU, 2.5GB RAM, 1Gbps
- 系统：Ubuntu 20.04+
- 已安装：Docker & Docker Compose
- 已配置：DNS A 记录指向 VPS IP
- 已配置：SSL 证书（Cloudflare 或 Let's Encrypt）

### 部署步骤

1. **拉取最新代码**
   ```bash
   cd /opt/ytbnew
   git pull origin main
   ```

2. **配置环境**
   ```bash
   # 编辑 .env 文件，设置 Webhook URL 等
   nano .env
   ```

3. **启动服务**
   ```bash
   docker-compose down
   docker-compose up -d
   docker-compose ps
   ```

4. **验证**
   ```bash
   curl -s http://localhost/health | jq .
   curl -s https://ytb.example.com/health
   ```

### Nginx 配置关键点

- **HTTPS 重定向**：HTTP → HTTPS
- **代理目标**：`http://ytb_app:8000`
- **证书路径**：`/etc/letsencrypt/live/ytb.example.com/`
- **日志轮转**：`max-size: 10m, max-file: 3`

### 监控告警配置

- **Prometheus 告警规则**：`monitoring/alerting-rules.yml`
- **AlertManager 路由**：`alertmanager.yml`
- **企业微信 Webhook**：直接配置在 AlertManager

## 常见问题排查

### 1. Redis 连接失败
```powershell
# 检查 Redis 容器
docker-compose ps redis

# 进入容器测试
docker-compose exec redis redis-cli -a password ping

# 检查日志
docker-compose logs redis
```

### 2. yt-dlp 版本过旧
```bash
# 在容器中更新
docker-compose exec app pip install --upgrade yt-dlp

# 验证版本
docker-compose exec app yt-dlp --version
```

### 3. 频道直播流提取失败
```powershell
# 查看详细错误日志
docker-compose logs -f app | Select-String "extract_stream_url"

# 手动测试 yt-dlp 命令
docker-compose exec app yt-dlp -f best -j "https://www.youtube.com/@setn/live"
```

### 4. Prometheus 无法连接到应用
```bash
# 检查应用是否暴露 /metrics 端点
curl http://localhost:9000/metrics

# 检查 Prometheus 配置
cat monitoring/prometheus.yml
```

### 5. AlertManager Webhook 失败
```bash
# 检查配置
cat alertmanager.yml

# 手动测试 Webhook URL
curl -X POST "WEBHOOK_URL" -H "Content-Type: application/json" -d '{}'
```

## Git 工作流

### 分支策略

- `main`：生产分支，部署到 VPS
- `develop`：开发分支
- `feature/*`：功能分支

### 提交规范

```
feat: 新增功能
fix: 修复 bug
docs: 文档更新
refactor: 代码重构
test: 测试相关
perf: 性能优化
chore: 构建/依赖更新
```

### 推送到 GitHub

```powershell
# 确保代码已提交
git status

# 推送到远程
git push origin main

# 如果本地领先远程
git push -u origin main
```

## 关键代码片段速查

### 添加新频道

编辑 `app/templates/channels_config.py`：
```python
CHANNELS = [
    {
        'name': '频道名称',
        'url': 'https://www.youtube.com/@channel/live',
        'description': '频道描述',
        'logo': 'https://...'
    },
    # ...
]
```

### 调整缓存时间

修改 `.env`：
```
CACHE_TTL=43200  # 12 小时
```

### 修改并发限制

修改 `.env`：
```
MAX_CONCURRENT_YTDLP_REQUESTS=5  # 最多 5 个并发
MAX_CONCURRENT_STREAMS=20        # 最多 20 个直播流
```

### 启用 DEBUG 模式

修改 `.env`：
```
DEBUG=true
LOG_LEVEL=DEBUG
```

查看详细日志（包括缓存命中/未命中、锁竞争等）。

## 性能优化建议

1. **缓存策略**：增加 CACHE_TTL 至 43200（12 小时）
2. **并发控制**：根据 VPS 资源调整 MAX_CONCURRENT_YTDLP_REQUESTS
3. **yt-dlp 超时**：生产环境可降低 YTDLP_TIMEOUT 至 15 秒
4. **连接池**：Redis 已配置健康检查和连接保活
5. **日志级别**：生产环境使用 INFO 级别，避免大量 DEBUG 日志

## 快速参考

| 需求 | 操作 |
|------|------|
| 启动本地测试 | `docker-compose up -d` |
| 查看应用日志 | `docker-compose logs -f app` |
| 清除频道缓存 | `curl -X POST http://localhost:8000/api/cache/invalidate/频道名` |
| 更新 yt-dlp | `docker-compose exec app pip install --upgrade yt-dlp` |
| 重启应用 | `docker-compose restart app` |
| 部署到 VPS | `git push origin main` + VPS 上 `git pull && docker-compose restart` |
| 查看 Prometheus 指标 | 访问 http://localhost:9090 |
| 配置 Grafana 仪表板 | 访问 http://localhost:3000，导入 Prometheus 数据源 |
