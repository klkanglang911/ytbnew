# YouTube 直播代理服务 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在美国 VPS 上部署 Docker 服务，为最多 10 个并发用户提供稳定的 YouTube 直播源代理，支持自动故障恢复和系统监控。

**Architecture:**
- **核心架构**：yt-dlp + FastAPI + Redis + Prometheus 监控
- **数据流**：VLC 客户端 → FastAPI 代理网关 → yt-dlp 流解析 → YouTube 直播流
- **缓存策略**：流地址缓存 6 小时（YouTube 限制），支持自动刷新和故障转移
- **监控体系**：Prometheus 指标采集 + Grafana 可视化 + 告警系统

**Tech Stack:**
- **后端**：Python 3.11 + FastAPI + Uvicorn
- **媒体解析**：yt-dlp（YouTube URL 解析）
- **缓存**：Redis（流地址缓存 + 并发控制）
- **监控**：Prometheus + Grafana + AlertManager
- **部署**：Docker Compose
- **协议**：HTTP/HLS（M3U8）

---

## 项目结构

```
youtube-proxy-service/
├── docker-compose.yml          # Docker 编排配置
├── .env.example                # 环境变量模板
├── .github/
│   └── workflows/
│       └── docker-build.yml    # CI/CD 流程
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── models.py               # 数据模型
│   ├── schemas.py              # 请求/响应 schema
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py           # API 路由（M3U、流地址）
│   │   └── health.py           # 健康检查端点
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ytdlp_service.py    # yt-dlp 集成
│   │   ├── cache_service.py    # Redis 缓存管理
│   │   ├── stream_resolver.py  # 流地址解析和故障转移
│   │   └── monitor_service.py  # 监控和告警
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py           # 日志配置
│   │   ├── retry.py            # 重试机制
│   │   └── validators.py       # 参数验证
│   └── templates/
│       └── channels.json        # 频道配置文件
├── monitoring/
│   ├── prometheus.yml          # Prometheus 配置
│   ├── alerting-rules.yml      # 告警规则
│   ├── grafana/
│   │   ├── dashboards.json     # Grafana 仪表板
│   │   └── datasources.json    # 数据源配置
│   └── health-check.sh         # 健康检查脚本
├── tests/
│   ├── test_ytdlp_service.py
│   ├── test_cache_service.py
│   ├── test_stream_resolver.py
│   └── test_api_routes.py
├── requirements.txt
├── Dockerfile
├── README.md
└── DEPLOYMENT.md
```

---

## Task 1: 项目初始化和环境配置

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `app/config.py`
- Create: `requirements.txt`
- Create: `Dockerfile`

**Step 1: 初始化项目目录和 Git**

```bash
cd D:\WORK\AI_WORK\ytb_new
git init
git config user.name "klkanglang911"
git config user.email "klkanglang@gmail.com"

mkdir -p app/{api,services,utils,templates} monitoring/{grafana} tests
touch README.md DEPLOYMENT.md
```

**Step 2: 创建 requirements.txt**

```txt
# 核心依赖
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# YouTube 流解析
yt-dlp==2024.1.1

# 缓存和并发
redis==5.0.1
hiredis==2.2.3

# 监控
prometheus-client==0.19.0

# 工具库
python-dotenv==1.0.0
requests==2.31.0
aiohttp==3.9.1

# 日志和调试
python-json-logger==2.0.7

# 测试
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2
```

**Step 3: 创建 Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ ./app/
COPY monitoring/ ./monitoring/

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动应用
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 4: 创建 app/config.py**

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    APP_NAME: str = "YouTube Proxy Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Redis 配置
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    CACHE_TTL: int = 21600  # 6 小时

    # yt-dlp 配置
    YTDLP_COOKIES_FILE: Optional[str] = None
    YTDLP_PROXY: Optional[str] = None
    YTDLP_TIMEOUT: int = 30
    YTDLP_MAX_RETRIES: int = 3

    # 并发控制
    MAX_CONCURRENT_STREAMS: int = 10
    MAX_CONCURRENT_YTDLP_REQUESTS: int = 3
    REQUEST_TIMEOUT: int = 30

    # 监控配置
    ENABLE_METRICS: bool = True
    PROMETHEUS_PORT: int = 9000

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json 或 text

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

**Step 5: 创建 .env.example**

```bash
# 应用配置
DEBUG=false
LOG_LEVEL=INFO

# Redis 配置（使用 Docker 服务名）
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_redis_password

# 缓存配置
CACHE_TTL=21600

# yt-dlp 配置
YTDLP_TIMEOUT=30
YTDLP_MAX_RETRIES=3
YTDLP_PROXY=  # 可选：如果需要代理

# 并发控制
MAX_CONCURRENT_STREAMS=10
MAX_CONCURRENT_YTDLP_REQUESTS=3
REQUEST_TIMEOUT=30

# 监控配置
ENABLE_METRICS=true
PROMETHEUS_PORT=9000
```

**Step 6: 创建 docker-compose.yml**

```yaml
version: '3.8'

services:
  # Redis 缓存
  redis:
    image: redis:7-alpine
    container_name: ytb_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - ytb_network

  # FastAPI 应用
  app:
    build: .
    container_name: ytb_app
    ports:
      - "8000:8000"
      - "9000:9000"  # Prometheus 指标端口
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - LOG_LEVEL=INFO
      - DEBUG=false
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - ./app:/app/app
      - ./logs:/app/logs
    restart: unless-stopped
    networks:
      - ytb_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

  # Prometheus 监控
  prometheus:
    image: prom/prometheus:latest
    container_name: ytb_prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./monitoring/alerting-rules.yml:/etc/prometheus/alerting-rules.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    depends_on:
      - app
    restart: unless-stopped
    networks:
      - ytb_network

  # Grafana 仪表板
  grafana:
    image: grafana/grafana:latest
    container_name: ytb_grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/datasources.json:/etc/grafana/provisioning/datasources/datasources.json
      - ./monitoring/grafana/dashboards.json:/etc/grafana/provisioning/dashboards/dashboards.json
    depends_on:
      - prometheus
    restart: unless-stopped
    networks:
      - ytb_network

volumes:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  ytb_network:
    driver: bridge
```

**Step 7: Commit**

```bash
git add docker-compose.yml .env.example app/config.py requirements.txt Dockerfile
git commit -m "初始化：项目结构和 Docker 配置"
```

---

## Task 2: 日志和监控基础设施

**Files:**
- Create: `app/utils/logger.py`
- Create: `monitoring/prometheus.yml`
- Create: `monitoring/alerting-rules.yml`
- Create: `app/services/monitor_service.py`

**Step 1: 创建日志配置 (app/utils/logger.py)**

```python
import logging
import json
import sys
from datetime import datetime
from app.config import settings

class JsonFormatter(logging.Formatter):
    """JSON 格式日志格式化器"""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)

def setup_logger(name: str) -> logging.Logger:
    """设置应用日志"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # 清除现有处理器
    logger.handlers.clear()

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)

    if settings.LOG_FORMAT == "json":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# 创建应用日志
app_logger = setup_logger("youtube_proxy")
```

**Step 2: 创建 monitoring/prometheus.yml**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'youtube-proxy-monitor'

alerting:
  alertmanagers:
    - static_configs:
        - targets: []

rule_files:
  - /etc/prometheus/alerting-rules.yml

scrape_configs:
  # FastAPI 应用指标
  - job_name: 'youtube_proxy'
    static_configs:
      - targets: ['app:9000']
    scrape_interval: 10s
    scrape_timeout: 5s

  # Redis 监控（可选）
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    metrics_path: /metrics
```

**Step 3: 创建 monitoring/alerting-rules.yml**

```yaml
groups:
  - name: youtube_proxy_alerts
    interval: 30s
    rules:
      # 应用不可用告警
      - alert: YouTubeProxyDown
        expr: up{job="youtube_proxy"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "YouTube Proxy 服务不可用"
          description: "YouTube Proxy 应用已离线超过 2 分钟"

      # 高错误率告警
      - alert: HighErrorRate
        expr: |
          (
            rate(ytdlp_request_errors_total[5m])
            /
            (rate(ytdlp_requests_total[5m]) + 1)
          ) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "YouTube 流解析错误率过高"
          description: "过去 5 分钟内错误率超过 10%"

      # Redis 连接失败
      - alert: RedisConnectionFailed
        expr: redis_connected_clients == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis 连接失败"
          description: "无法连接到 Redis 缓存服务"

      # 并发流过多
      - alert: HighConcurrentStreams
        expr: active_streams > 8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "并发流接近限制"
          description: "当前并发流数: {{ $value }} / 10"

      # 缓存命中率低
      - alert: LowCacheHitRate
        expr: cache_hit_rate < 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "缓存命中率过低"
          description: "过去 10 分钟缓存命中率: {{ $value }}"
```

**Step 4: 创建 app/services/monitor_service.py**

```python
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from app.utils.logger import setup_logger
import time

logger = setup_logger(__name__)

# Prometheus 指标定义
ytdlp_requests_total = Counter(
    'ytdlp_requests_total',
    '总 yt-dlp 请求数',
    ['channel', 'status']
)

ytdlp_request_errors_total = Counter(
    'ytdlp_request_errors_total',
    'yt-dlp 请求错误总数',
    ['channel', 'error_type']
)

ytdlp_request_duration_seconds = Histogram(
    'ytdlp_request_duration_seconds',
    'yt-dlp 请求耗时（秒）',
    ['channel'],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
)

active_streams = Gauge(
    'active_streams',
    '当前活跃流数'
)

cache_hits_total = Counter(
    'cache_hits_total',
    '缓存命中总数',
    ['channel']
)

cache_misses_total = Counter(
    'cache_misses_total',
    '缓存未命中总数',
    ['channel']
)

cache_hit_rate = Gauge(
    'cache_hit_rate',
    '缓存命中率'
)

stream_uptime_seconds = Gauge(
    'stream_uptime_seconds',
    '流正常运行时长',
    ['channel']
)

class MonitorService:
    """监控和指标收集服务"""

    def __init__(self):
        self.stream_start_times = {}

    def record_ytdlp_request(self, channel: str, status: str, duration: float, error_type: str = None):
        """记录 yt-dlp 请求"""
        ytdlp_requests_total.labels(channel=channel, status=status).inc()
        ytdlp_request_duration_seconds.labels(channel=channel).observe(duration)

        if error_type:
            ytdlp_request_errors_total.labels(channel=channel, error_type=error_type).inc()

    def record_stream_start(self, channel: str):
        """记录流启动"""
        active_streams.inc()
        self.stream_start_times[channel] = time.time()

    def record_stream_end(self, channel: str):
        """记录流停止"""
        active_streams.dec()
        if channel in self.stream_start_times:
            del self.stream_start_times[channel]

    def record_cache_hit(self, channel: str):
        """记录缓存命中"""
        cache_hits_total.labels(channel=channel).inc()
        self._update_cache_hit_rate()

    def record_cache_miss(self, channel: str):
        """记录缓存未命中"""
        cache_misses_total.labels(channel=channel).inc()
        self._update_cache_hit_rate()

    def _update_cache_hit_rate(self):
        """更新缓存命中率"""
        try:
            hits = sum([metric._value.get() for metric in [cache_hits_total]])
            misses = sum([metric._value.get() for metric in [cache_misses_total]])
            if hits + misses > 0:
                cache_hit_rate.set(hits / (hits + misses))
        except:
            pass

    def get_metrics(self):
        """获取所有指标"""
        return generate_latest()

# 全局监控服务实例
monitor_service = MonitorService()
```

**Step 5: Commit**

```bash
git add app/utils/logger.py monitoring/prometheus.yml monitoring/alerting-rules.yml app/services/monitor_service.py
git commit -m "添加：日志和监控基础设施"
```

---

## Task 3: Redis 缓存服务

**Files:**
- Create: `app/services/cache_service.py`
- Create: `tests/test_cache_service.py`

**Step 1: 创建缓存服务 (app/services/cache_service.py)**

```python
import redis
import json
import asyncio
from typing import Optional, Any
from datetime import datetime, timedelta
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class CacheService:
    """Redis 缓存服务"""

    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
            health_check_interval=30
        )
        self._test_connection()

    def _test_connection(self):
        """测试 Redis 连接"""
        try:
            self.redis_client.ping()
            logger.info("✓ Redis 连接成功")
        except Exception as e:
            logger.error(f"✗ Redis 连接失败: {e}")
            raise

    async def get_stream_url(self, channel: str) -> Optional[dict]:
        """
        获取缓存的流地址

        Args:
            channel: 频道名称或 URL

        Returns:
            缓存的流信息或 None
        """
        try:
            key = f"stream:{channel}"
            cached_data = self.redis_client.get(key)

            if cached_data:
                logger.debug(f"缓存命中: {channel}")
                return json.loads(cached_data)

            logger.debug(f"缓存未命中: {channel}")
            return None
        except Exception as e:
            logger.warning(f"缓存读取错误 ({channel}): {e}")
            return None

    async def set_stream_url(
        self,
        channel: str,
        stream_data: dict,
        ttl_seconds: int = None
    ) -> bool:
        """
        缓存流地址

        Args:
            channel: 频道名称
            stream_data: 流数据 {url, quality, expires_at, ...}
            ttl_seconds: 缓存时间（秒），默认使用配置的 CACHE_TTL

        Returns:
            是否成功
        """
        try:
            key = f"stream:{channel}"
            ttl = ttl_seconds or settings.CACHE_TTL

            cached_json = json.dumps(stream_data)
            self.redis_client.setex(key, ttl, cached_json)

            logger.info(f"✓ 缓存设置: {channel} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.warning(f"缓存设置错误 ({channel}): {e}")
            return False

    async def get_or_set(
        self,
        channel: str,
        fetch_func,
        ttl_seconds: int = None
    ) -> dict:
        """
        缓存模式：先读缓存，未命中时调用函数获取并缓存

        Args:
            channel: 频道名称
            fetch_func: 异步函数，返回流数据
            ttl_seconds: 缓存时间

        Returns:
            流数据
        """
        # 尝试读缓存
        cached = await self.get_stream_url(channel)
        if cached:
            return cached

        # 缓存未命中，调用 fetch 函数
        stream_data = await fetch_func(channel)

        # 缓存结果
        if stream_data:
            await self.set_stream_url(channel, stream_data, ttl_seconds)

        return stream_data

    async def invalidate(self, channel: str) -> bool:
        """使缓存失效"""
        try:
            key = f"stream:{channel}"
            self.redis_client.delete(key)
            logger.info(f"✓ 缓存已清除: {channel}")
            return True
        except Exception as e:
            logger.warning(f"缓存清除错误 ({channel}): {e}")
            return False

    async def get_all_cached_channels(self) -> list:
        """获取所有缓存的频道"""
        try:
            keys = self.redis_client.keys("stream:*")
            channels = [key.replace("stream:", "") for key in keys]
            return channels
        except Exception as e:
            logger.warning(f"获取缓存频道列表错误: {e}")
            return []

    async def acquire_lock(self, channel: str, timeout: int = 30) -> bool:
        """
        获取分布式锁（防止并发重复解析）

        Args:
            channel: 频道名称
            timeout: 锁过期时间（秒）

        Returns:
            是否成功获得锁
        """
        try:
            lock_key = f"lock:{channel}"
            result = self.redis_client.set(
                lock_key,
                "1",
                nx=True,  # 仅在键不存在时设置
                ex=timeout
            )
            return result is not None
        except Exception as e:
            logger.warning(f"获取锁失败 ({channel}): {e}")
            return False

    async def release_lock(self, channel: str) -> bool:
        """释放分布式锁"""
        try:
            lock_key = f"lock:{channel}"
            self.redis_client.delete(lock_key)
            return True
        except Exception as e:
            logger.warning(f"释放锁失败 ({channel}): {e}")
            return False

    async def close(self):
        """关闭 Redis 连接"""
        try:
            self.redis_client.close()
            logger.info("✓ Redis 连接已关闭")
        except Exception as e:
            logger.warning(f"Redis 关闭错误: {e}")

# 全局缓存服务实例
cache_service = CacheService()
```

**Step 2: 创建单元测试 (tests/test_cache_service.py)**

```python
import pytest
import asyncio
from app.services.cache_service import CacheService

@pytest.fixture
async def cache():
    """创建缓存服务实例"""
    service = CacheService()
    yield service
    # 清理
    await service.close()

@pytest.mark.asyncio
async def test_set_and_get_stream_url(cache):
    """测试缓存设置和读取"""
    channel = "test_channel"
    stream_data = {
        "url": "http://example.com/stream.m3u8",
        "quality": "720p",
        "expires_at": "2026-02-04T00:00:00Z"
    }

    # 设置缓存
    result = await cache.set_stream_url(channel, stream_data, ttl_seconds=60)
    assert result is True

    # 读取缓存
    cached = await cache.get_stream_url(channel)
    assert cached is not None
    assert cached["url"] == stream_data["url"]

@pytest.mark.asyncio
async def test_cache_miss(cache):
    """测试缓存未命中"""
    result = await cache.get_stream_url("non_existent_channel")
    assert result is None

@pytest.mark.asyncio
async def test_invalidate(cache):
    """测试缓存清除"""
    channel = "test_channel"
    stream_data = {"url": "http://example.com"}

    await cache.set_stream_url(channel, stream_data)
    assert await cache.get_stream_url(channel) is not None

    await cache.invalidate(channel)
    assert await cache.get_stream_url(channel) is None

@pytest.mark.asyncio
async def test_distributed_lock(cache):
    """测试分布式锁"""
    channel = "test_lock"

    # 获得锁
    result1 = await cache.acquire_lock(channel)
    assert result1 is True

    # 再次尝试获得同一个锁应该失败
    result2 = await cache.acquire_lock(channel)
    assert result2 is False

    # 释放锁
    await cache.release_lock(channel)

    # 再次应该能获得锁
    result3 = await cache.acquire_lock(channel)
    assert result3 is True

    await cache.release_lock(channel)

@pytest.mark.asyncio
async def test_get_or_set(cache):
    """测试缓存读写模式"""
    channel = "test_fetch"
    call_count = 0

    async def mock_fetch(ch):
        nonlocal call_count
        call_count += 1
        return {"url": f"http://example.com/{ch}", "quality": "1080p"}

    # 第一次调用应该调用 fetch_func
    result1 = await cache.get_or_set(channel, mock_fetch)
    assert call_count == 1
    assert result1["url"] == "http://example.com/test_fetch"

    # 第二次调用应该从缓存读取
    result2 = await cache.get_or_set(channel, mock_fetch)
    assert call_count == 1  # 没有再次调用
    assert result2 == result1
```

**Step 3: Commit**

```bash
git add app/services/cache_service.py tests/test_cache_service.py
git commit -m "实现：Redis 缓存服务"
```

---

## Task 4: yt-dlp 流解析服务

**Files:**
- Create: `app/services/ytdlp_service.py`
- Create: `app/utils/retry.py`
- Create: `tests/test_ytdlp_service.py`

**Step 1: 创建重试机制工具 (app/utils/retry.py)**

```python
import asyncio
import random
from typing import Callable, Any, TypeVar
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

T = TypeVar('T')

async def retry_with_backoff(
    func: Callable,
    *args,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    **kwargs
) -> Any:
    """
    带指数退避的重试机制

    Args:
        func: 异步函数
        max_retries: 最大重试次数
        initial_delay: 初始延迟（秒）
        max_delay: 最大延迟（秒）
        exponential_base: 指数退避基数
        jitter: 是否添加随机抖动

    Returns:
        函数执行结果

    Raises:
        最后一次尝试的异常
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e

            if attempt == max_retries:
                logger.error(f"重试失败 (已尝试 {max_retries + 1} 次): {e}")
                raise

            # 计算延迟时间
            delay = min(
                initial_delay * (exponential_base ** attempt),
                max_delay
            )

            if jitter:
                delay *= (0.5 + random.random())

            logger.warning(
                f"重试 {attempt + 1}/{max_retries} "
                f"(延迟 {delay:.1f}s): {type(e).__name__}: {e}"
            )

            await asyncio.sleep(delay)

    raise last_exception
```

**Step 2: 创建 yt-dlp 服务 (app/services/ytdlp_service.py)**

```python
import subprocess
import json
import asyncio
import re
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from app.config import settings
from app.utils.logger import setup_logger
from app.utils.retry import retry_with_backoff

logger = setup_logger(__name__)

class YtdlpService:
    """yt-dlp 流解析服务"""

    def __init__(self):
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_YTDLP_REQUESTS)
        self._validate_ytdlp()

    def _validate_ytdlp(self):
        """验证 yt-dlp 是否已安装"""
        try:
            result = subprocess.run(
                ["yt-dlp", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            version = result.stdout.strip()
            logger.info(f"✓ yt-dlp 可用: {version}")
        except Exception as e:
            logger.error(f"✗ yt-dlp 不可用: {e}")
            raise

    async def extract_stream_url(
        self,
        channel_url: str,
        channel_name: str = None
    ) -> Optional[Dict]:
        """
        从 YouTube URL 提取流地址

        Args:
            channel_url: YouTube 频道/直播 URL
            channel_name: 频道名称（用于日志）

        Returns:
            {
                'url': '直播流 URL',
                'quality': '清晰度',
                'format': 'hls 或 dash',
                'expires_at': '过期时间',
                'protocol': 'http/https'
            }
        """
        async with self.semaphore:
            try:
                logger.info(f"解析流地址: {channel_url} ({channel_name})")

                stream_data = await retry_with_backoff(
                    self._fetch_stream_url,
                    channel_url,
                    max_retries=settings.YTDLP_MAX_RETRIES
                )

                if stream_data:
                    logger.info(f"✓ 流解析成功: {channel_name}")
                    return stream_data
                else:
                    logger.warning(f"✗ 无可用流: {channel_name}")
                    return None

            except Exception as e:
                logger.error(f"✗ 流解析失败: {channel_name} - {e}")
                return None

    async def _fetch_stream_url(self, channel_url: str) -> Optional[Dict]:
        """
        实际的流地址提取逻辑

        这是一个同步函数，在线程池中运行以避免阻塞
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._sync_fetch_stream_url,
            channel_url
        )

    def _sync_fetch_stream_url(self, channel_url: str) -> Optional[Dict]:
        """同步流提取（在线程池中运行）"""
        try:
            # 构建 yt-dlp 命令
            cmd = [
                "yt-dlp",
                "-f", "best",  # 最佳质量
                "-j",  # JSON 输出
                "--socket-timeout", str(settings.YTDLP_TIMEOUT),
                "--no-warnings",
                "-q",
            ]

            # 添加代理（如果配置）
            if settings.YTDLP_PROXY:
                cmd.extend(["--proxy", settings.YTDLP_PROXY])

            cmd.append(channel_url)

            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=settings.YTDLP_TIMEOUT + 5
            )

            if result.returncode != 0:
                raise Exception(f"yt-dlp 错误: {result.stderr}")

            # 解析 JSON 输出
            info = json.loads(result.stdout)

            # 提取流 URL
            stream_url = info.get('url') or info.get('formats', [{}])[0].get('url')

            if not stream_url:
                raise Exception("无法提取流 URL")

            # YouTube 流 URL 通常有 1 小时有效期
            expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()

            return {
                'url': stream_url,
                'quality': info.get('format', 'unknown'),
                'format': 'hls' if '.m3u8' in stream_url else 'dash',
                'expires_at': expires_at,
                'protocol': 'https' if stream_url.startswith('https') else 'http',
                'channel_url': channel_url,
                'fetched_at': datetime.utcnow().isoformat()
            }

        except subprocess.TimeoutExpired:
            raise Exception(f"yt-dlp 超时 ({settings.YTDLP_TIMEOUT}s)")
        except json.JSONDecodeError:
            raise Exception("yt-dlp 输出解析失败")
        except Exception as e:
            raise e

    async def validate_stream_url(self, stream_url: str) -> bool:
        """
        验证流 URL 是否仍然有效

        通过尝试连接来检查 URL 有效性
        """
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.head(stream_url)
                is_valid = response.status_code < 400

                if is_valid:
                    logger.debug(f"✓ 流 URL 有效")
                else:
                    logger.warning(f"✗ 流 URL 返回 {response.status_code}")

                return is_valid
        except Exception as e:
            logger.warning(f"流 URL 验证失败: {e}")
            return False

# 全局 yt-dlp 服务实例
ytdlp_service = YtdlpService()
```

**Step 3: 创建 yt-dlp 服务测试 (tests/test_ytdlp_service.py)**

```python
import pytest
from unittest.mock import patch, MagicMock
from app.services.ytdlp_service import YtdlpService

@pytest.fixture
def ytdlp():
    """创建 yt-dlp 服务实例"""
    with patch('app.services.ytdlp_service.YtdlpService._validate_ytdlp'):
        service = YtdlpService()
        yield service

@pytest.mark.asyncio
async def test_extract_stream_url_success(ytdlp):
    """测试成功提取流地址"""
    mock_response = '''{
        "url": "https://example.com/stream.m3u8",
        "format": "hls",
        "formats": []
    }'''

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_response,
            stderr=""
        )

        result = await ytdlp.extract_stream_url(
            "https://www.youtube.com/channel/test",
            "test_channel"
        )

        assert result is not None
        assert result['url'] == "https://example.com/stream.m3u8"
        assert result['format'] == "hls"

@pytest.mark.asyncio
async def test_extract_stream_url_failure(ytdlp):
    """测试流地址提取失败"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: Video not found"
        )

        result = await ytdlp.extract_stream_url(
            "https://www.youtube.com/invalid",
            "invalid_channel"
        )

        assert result is None

@pytest.mark.asyncio
async def test_extract_stream_url_timeout(ytdlp):
    """测试超时处理"""
    with patch('subprocess.run') as mock_run:
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 30)

        result = await ytdlp.extract_stream_url(
            "https://www.youtube.com/test",
            "timeout_channel"
        )

        assert result is None
```

**Step 4: Commit**

```bash
git add app/utils/retry.py app/services/ytdlp_service.py tests/test_ytdlp_service.py
git commit -m "实现：yt-dlp 流解析服务和重试机制"
```

---

## Task 5: 流解析和故障转移服务

**Files:**
- Create: `app/services/stream_resolver.py`
- Create: `tests/test_stream_resolver.py`

**Step 1: 创建流解析服务 (app/services/stream_resolver.py)**

```python
import asyncio
from typing import Optional, List, Dict
from datetime import datetime
from app.services.ytdlp_service import ytdlp_service
from app.services.cache_service import cache_service
from app.services.monitor_service import monitor_service
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class StreamResolverService:
    """
    流解析和故障转移服务

    负责：
    1. 获取频道直播流地址
    2. 缓存管理和 TTL 刷新
    3. 故障转移和自动降级
    4. 监控指标收集
    """

    def __init__(self):
        self.fallback_timeout = 30  # 故障转移超时

    async def get_stream_url(
        self,
        channel_url: str,
        channel_name: str,
        use_cache: bool = True
    ) -> Optional[str]:
        """
        获取流地址，支持缓存和故障转移

        Args:
            channel_url: YouTube URL
            channel_name: 频道名称
            use_cache: 是否使用缓存

        Returns:
            流 URL 或 None
        """
        try:
            import time
            start_time = time.time()

            # 尝试从缓存获取
            if use_cache:
                cached = await cache_service.get_stream_url(channel_name)
                if cached:
                    # 检查缓存是否过期
                    if not self._is_expired(cached):
                        logger.info(f"从缓存返回流地址: {channel_name}")
                        monitor_service.record_cache_hit(channel_name)
                        return cached['url']
                    else:
                        logger.debug(f"缓存已过期: {channel_name}")
                        await cache_service.invalidate(channel_name)

                monitor_service.record_cache_miss(channel_name)

            # 缓存未命中或已过期，尝试重新解析
            # 使用分布式锁防止多个请求同时解析
            lock_acquired = await cache_service.acquire_lock(channel_name)

            if not lock_acquired:
                # 无法获得锁，其他请求正在解析
                # 等待一段时间后重试或返回缓存
                logger.info(f"等待其他请求完成解析: {channel_name}")
                await asyncio.sleep(2)

                cached = await cache_service.get_stream_url(channel_name)
                if cached:
                    return cached['url']

            try:
                # 解析流地址
                stream_data = await ytdlp_service.extract_stream_url(
                    channel_url,
                    channel_name
                )

                if stream_data:
                    # 缓存结果
                    await cache_service.set_stream_url(channel_name, stream_data)

                    duration = time.time() - start_time
                    monitor_service.record_ytdlp_request(
                        channel_name,
                        "success",
                        duration
                    )

                    return stream_data['url']
                else:
                    # 解析失败
                    duration = time.time() - start_time
                    monitor_service.record_ytdlp_request(
                        channel_name,
                        "error",
                        duration,
                        error_type="extraction_failed"
                    )

                    logger.error(f"无法解析流地址: {channel_name}")
                    return None

            finally:
                # 释放锁
                await cache_service.release_lock(channel_name)

        except Exception as e:
            logger.error(f"流解析异常: {channel_name} - {e}")
            monitor_service.record_ytdlp_request(
                channel_name,
                "error",
                0,
                error_type="exception"
            )
            return None

    def _is_expired(self, stream_data: Dict) -> bool:
        """检查缓存是否过期"""
        try:
            expires_at = datetime.fromisoformat(stream_data['expires_at'])
            return datetime.utcnow() >= expires_at
        except:
            return True

    async def verify_and_refresh_streams(self, channels: List[Dict]) -> List[Dict]:
        """
        验证和刷新多个频道的流地址

        Args:
            channels: 频道列表 [{"name": "...", "url": "..."}, ...]

        Returns:
            更新后的频道列表，包括流地址和状态
        """
        results = []

        for channel in channels:
            stream_url = await self.get_stream_url(
                channel['url'],
                channel['name'],
                use_cache=True
            )

            results.append({
                **channel,
                'stream_url': stream_url,
                'status': 'online' if stream_url else 'offline',
                'last_checked': datetime.utcnow().isoformat()
            })

        return results

    async def batch_get_streams(
        self,
        channels: List[Dict],
        timeout: int = None
    ) -> Dict[str, Optional[str]]:
        """
        批量获取流地址（支持超时）

        Args:
            channels: 频道列表
            timeout: 总超时时间（秒）

        Returns:
            {channel_name: stream_url, ...}
        """
        tasks = [
            self.get_stream_url(ch['url'], ch['name'])
            for ch in channels
        ]

        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout
            )

            return {
                ch['name']: result
                for ch, result in zip(channels, results)
                if not isinstance(result, Exception)
            }

        except asyncio.TimeoutError:
            logger.error(f"批量流解析超时")
            return {}

# 全局流解析服务实例
stream_resolver = StreamResolverService()
```

**Step 2: 创建测试 (tests/test_stream_resolver.py)**

```python
import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta
from app.services.stream_resolver import StreamResolverService

@pytest.fixture
def resolver():
    """创建流解析服务实例"""
    return StreamResolverService()

@pytest.mark.asyncio
async def test_get_stream_url_success(resolver):
    """测试成功获取流地址"""
    with patch('app.services.stream_resolver.ytdlp_service.extract_stream_url') as mock_ytdlp:
        mock_ytdlp.return_value = {
            'url': 'https://example.com/stream.m3u8',
            'format': 'hls',
            'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }

        with patch('app.services.stream_resolver.cache_service.acquire_lock', return_value=True):
            with patch('app.services.stream_resolver.cache_service.release_lock', return_value=True):
                with patch('app.services.stream_resolver.cache_service.get_stream_url', return_value=None):
                    with patch('app.services.stream_resolver.cache_service.set_stream_url', return_value=True):
                        result = await resolver.get_stream_url(
                            'https://youtube.com/test',
                            'test_channel'
                        )

                        assert result == 'https://example.com/stream.m3u8'

@pytest.mark.asyncio
async def test_get_stream_url_cache_hit(resolver):
    """测试缓存命中"""
    cached_data = {
        'url': 'https://cached.com/stream.m3u8',
        'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat()
    }

    with patch('app.services.stream_resolver.cache_service.get_stream_url', return_value=cached_data):
        result = await resolver.get_stream_url(
            'https://youtube.com/test',
            'test_channel',
            use_cache=True
        )

        assert result == 'https://cached.com/stream.m3u8'

@pytest.mark.asyncio
async def test_is_expired(resolver):
    """测试过期检查"""
    # 未来的过期时间
    future = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    assert resolver._is_expired({'expires_at': future}) is False

    # 过去的过期时间
    past = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    assert resolver._is_expired({'expires_at': past}) is True
```

**Step 3: Commit**

```bash
git add app/services/stream_resolver.py tests/test_stream_resolver.py
git commit -m "实现：流解析和故障转移服务"
```

---

## Task 6: API 路由和数据模型

**Files:**
- Create: `app/models.py`
- Create: `app/schemas.py`
- Create: `app/api/routes.py`
- Create: `app/api/health.py`

**Step 1: 创建数据模型 (app/models.py)**

```python
from typing import List, Optional
from datetime import datetime

class Channel:
    """频道模型"""

    def __init__(
        self,
        name: str,
        url: str,
        description: str = "",
        logo_url: Optional[str] = None
    ):
        self.name = name
        self.url = url
        self.description = description
        self.logo_url = logo_url

class StreamInfo:
    """流信息模型"""

    def __init__(
        self,
        channel_name: str,
        stream_url: str,
        quality: str,
        format: str,
        expires_at: str,
        status: str = "online"
    ):
        self.channel_name = channel_name
        self.stream_url = stream_url
        self.quality = quality
        self.format = format
        self.expires_at = expires_at
        self.status = status
        self.fetched_at = datetime.utcnow().isoformat()
```

**Step 2: 创建请求/响应 schema (app/schemas.py)**

```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ChannelResponse(BaseModel):
    """频道响应"""
    name: str
    url: str
    description: str = ""
    logo_url: Optional[str] = None

class StreamUrlResponse(BaseModel):
    """流地址响应"""
    channel_name: str
    stream_url: str
    quality: str
    format: str
    status: str  # "online" 或 "offline"
    expires_at: str
    fetched_at: str

class M3UPlaylistItem(BaseModel):
    """M3U 播放列表项"""
    name: str
    logo: str
    group_title: str
    tvg_id: str
    url: str

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: str
    version: str
    redis_connected: bool
    ytdlp_available: bool
    active_streams: int

class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    message: str
    timestamp: str
```

**Step 3: 创建 API 路由 (app/api/routes.py)**

```python
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.schemas import (
    ChannelResponse,
    StreamUrlResponse,
    M3UPlaylistItem,
    ErrorResponse
)
from app.services.stream_resolver import stream_resolver
from app.services.cache_service import cache_service
from app.templates.channels_config import CHANNELS
from app.utils.logger import setup_logger
from datetime import datetime

logger = setup_logger(__name__)
router = APIRouter()

@router.get("/", tags=["Info"])
async def root():
    """获取 API 信息"""
    return {
        "name": "YouTube 直播代理服务",
        "version": "1.0.0",
        "endpoints": {
            "channels": "/api/channels",
            "stream": "/api/stream/{channel_name}",
            "m3u": "/api/m3u",
            "health": "/health"
        }
    }

@router.get("/channels", response_model=List[ChannelResponse], tags=["Channels"])
async def list_channels():
    """获取所有频道列表"""
    try:
        return [
            ChannelResponse(
                name=ch['name'],
                url=ch['url'],
                description=ch.get('description', ''),
                logo_url=ch.get('logo')
            )
            for ch in CHANNELS
        ]
    except Exception as e:
        logger.error(f"获取频道列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取频道列表失败")

@router.get("/stream/{channel_name}", response_model=StreamUrlResponse, tags=["Streams"])
async def get_stream(
    channel_name: str,
    use_cache: bool = Query(True, description="是否使用缓存")
):
    """
    获取指定频道的流地址

    Args:
        channel_name: 频道名称
        use_cache: 是否使用缓存

    Returns:
        流地址和元数据
    """
    try:
        # 查找频道配置
        channel = next(
            (ch for ch in CHANNELS if ch['name'] == channel_name),
            None
        )

        if not channel:
            raise HTTPException(
                status_code=404,
                detail=f"频道未找到: {channel_name}"
            )

        # 获取流地址
        stream_url = await stream_resolver.get_stream_url(
            channel['url'],
            channel_name,
            use_cache=use_cache
        )

        # 获取缓存的流信息
        cached_data = await cache_service.get_stream_url(channel_name)

        if stream_url and cached_data:
            return StreamUrlResponse(
                channel_name=channel_name,
                stream_url=stream_url,
                quality=cached_data.get('quality', 'unknown'),
                format=cached_data.get('format', 'hls'),
                status="online",
                expires_at=cached_data.get('expires_at', ''),
                fetched_at=cached_data.get('fetched_at', datetime.utcnow().isoformat())
            )
        elif stream_url:
            return StreamUrlResponse(
                channel_name=channel_name,
                stream_url=stream_url,
                quality="unknown",
                format="hls",
                status="online",
                expires_at=(datetime.utcnow().isoformat() + " (预估)"),
                fetched_at=datetime.utcnow().isoformat()
            )
        else:
            # 频道离线或解析失败
            raise HTTPException(
                status_code=503,
                detail=f"频道离线或无法获取直播流: {channel_name}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取流地址失败 ({channel_name}): {e}")
        raise HTTPException(status_code=500, detail="获取流地址失败")

@router.get("/m3u", tags=["Playlists"])
async def get_m3u_playlist(use_cache: bool = Query(True)):
    """
    获取 M3U 播放列表

    格式：可直接导入 VLC
    """
    try:
        m3u_content = "#EXTM3U\n"

        for channel in CHANNELS:
            channel_name = channel['name']

            # 获取流地址
            stream_url = await stream_resolver.get_stream_url(
                channel['url'],
                channel_name,
                use_cache=use_cache
            )

            if stream_url:
                # M3U 格式
                m3u_content += (
                    f"#EXTINF:-1 "
                    f"tvg-id=\"{channel_name}\" "
                    f"tvg-name=\"{channel_name}\" "
                    f"logo=\"{channel.get('logo', '')}\" "
                    f"group-title=\"YouTube\"\n"
                    f"{stream_url}\n"
                )
            else:
                logger.warning(f"频道离线，跳过: {channel_name}")

        return m3u_content

    except Exception as e:
        logger.error(f"生成 M3U 播放列表失败: {e}")
        raise HTTPException(status_code=500, detail="生成播放列表失败")

@router.post("/cache/invalidate/{channel_name}", tags=["Cache"])
async def invalidate_cache(channel_name: str):
    """手动清除频道缓存"""
    try:
        result = await cache_service.invalidate(channel_name)

        if result:
            return {"message": f"缓存已清除: {channel_name}"}
        else:
            raise HTTPException(status_code=404, detail="缓存不存在或清除失败")

    except Exception as e:
        logger.error(f"缓存清除失败 ({channel_name}): {e}")
        raise HTTPException(status_code=500, detail="缓存清除失败")

@router.get("/metrics", tags=["Monitoring"])
async def get_prometheus_metrics():
    """获取 Prometheus 指标"""
    from app.services.monitor_service import monitor_service

    try:
        metrics = monitor_service.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"获取指标失败: {e}")
        raise HTTPException(status_code=500, detail="获取指标失败")
```

**Step 4: 创建健康检查端点 (app/api/health.py)**

```python
from fastapi import APIRouter, HTTPException
from app.config import settings
from app.services.cache_service import cache_service
from app.services.ytdlp_service import ytdlp_service
from app.services.monitor_service import monitor_service
from app.utils.logger import setup_logger
from datetime import datetime

logger = setup_logger(__name__)
router = APIRouter()

@router.get("/health", tags=["Health"])
async def health_check():
    """
    系统健康检查

    检查项：
    - Redis 连接
    - yt-dlp 可用性
    - 应用状态
    """
    try:
        # 检查 Redis
        redis_ok = False
        try:
            cache_service.redis_client.ping()
            redis_ok = True
        except Exception as e:
            logger.warning(f"Redis 健康检查失败: {e}")

        # 检查 yt-dlp
        ytdlp_ok = False
        try:
            import subprocess
            result = subprocess.run(
                ["yt-dlp", "--version"],
                capture_output=True,
                timeout=5
            )
            ytdlp_ok = result.returncode == 0
        except Exception as e:
            logger.warning(f"yt-dlp 健康检查失败: {e}")

        # 获取活跃流数
        active_streams = getattr(monitor_service, 'active_streams', 0)

        # 健康状态判定
        status = "healthy" if (redis_ok and ytdlp_ok) else "degraded"

        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.APP_VERSION,
            "redis_connected": redis_ok,
            "ytdlp_available": ytdlp_ok,
            "active_streams": active_streams
        }

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=503, detail="健康检查失败")

@router.get("/ready", tags=["Health"])
async def readiness_check():
    """就绪检查（用于 Docker 容器编排）"""
    try:
        cache_service.redis_client.ping()
        return {"status": "ready"}
    except:
        raise HTTPException(status_code=503, detail="系统未就绪")
```

**Step 5: 创建频道配置 (app/templates/channels.json)**

```json
[
  {
    "name": "三立新闻",
    "url": "https://www.youtube.com/@setn/live",
    "description": "三立新闻 YouTube 直播",
    "logo": "https://yt3.googleusercontent.com/xxx"
  },
  {
    "name": "民视新闻",
    "url": "https://www.youtube.com/@ftv/live",
    "description": "民视新闻 YouTube 直播",
    "logo": "https://yt3.googleusercontent.com/yyy"
  }
]
```

**Step 6: 创建 app/templates/channels_config.py**

```python
# 频道配置（从 JSON 加载或硬编码）
CHANNELS = [
    {
        "name": "三立新闻",
        "url": "https://www.youtube.com/@setn/live",
        "description": "台湾新闻频道",
        "logo": "https://yt3.googleusercontent.com/xxx"
    },
    {
        "name": "民视新闻",
        "url": "https://www.youtube.com/@ftv/live",
        "description": "台湾新闻频道",
        "logo": "https://yt3.googleusercontent.com/yyy"
    },
    {
        "name": "BBC News",
        "url": "https://www.youtube.com/@BBCNews/live",
        "description": "英国新闻频道",
        "logo": "https://yt3.googleusercontent.com/zzz"
    }
]

def load_channels_from_json(path: str):
    """从 JSON 文件加载频道配置"""
    import json
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
```

**Step 7: Commit**

```bash
git add app/models.py app/schemas.py app/api/routes.py app/api/health.py app/templates/channels_config.py app/templates/channels.json
git commit -m "实现：API 路由和数据模型"
```

---

## Task 7: FastAPI 应用主入口

**Files:**
- Create: `app/__init__.py`
- Create: `app/api/__init__.py`
- Create: `app/services/__init__.py`
- Create: `app/utils/__init__.py`
- Modify: `app/main.py`

**Step 1: 创建应用主入口 (app/main.py)**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import asyncio
from app.config import settings
from app.api.routes import router as api_router
from app.api.health import router as health_router
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="YouTube 直播代理服务 - 为 VLC 提供代理直播源",
    debug=settings.DEBUG
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api")
app.include_router(health_router)

# M3U 播放列表特殊处理
@app.get("/playlist.m3u", response_class=PlainTextResponse)
async def get_m3u_file():
    """获取 M3U 播放列表（用于 VLC 直接导入）"""
    from app.api.routes import get_m3u_playlist
    return await get_m3u_playlist(use_cache=True)

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")

    # 初始化服务
    try:
        # 测试 Redis 连接
        from app.services.cache_service import cache_service
        await asyncio.sleep(0.5)  # 等待 Redis 启动
        logger.info("✓ 缓存服务初始化完成")

        # 测试 yt-dlp
        from app.services.ytdlp_service import ytdlp_service
        logger.info("✓ yt-dlp 服务初始化完成")

        logger.info("✓ 所有服务初始化完成")

    except Exception as e:
        logger.error(f"✗ 启动失败: {e}")
        raise

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("🛑 应用关闭中...")

    try:
        from app.services.cache_service import cache_service
        await cache_service.close()
        logger.info("✓ 缓存服务已关闭")
    except Exception as e:
        logger.warning(f"关闭缓存服务异常: {e}")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level=settings.LOG_LEVEL.lower()
    )
```

**Step 2: 创建包初始化文件**

```bash
# app/__init__.py (空文件)
echo "" > app/__init__.py

# app/api/__init__.py (空文件)
echo "" > app/api/__init__.py

# app/services/__init__.py (空文件)
echo "" > app/services/__init__.py

# app/utils/__init__.py (空文件)
echo "" > app/utils/__init__.py
```

**Step 3: Commit**

```bash
git add app/__init__.py app/api/__init__.py app/services/__init__.py app/utils/__init__.py app/main.py
git commit -m "实现：FastAPI 应用主入口"
```

---

## Task 8: Grafana 监控仪表板配置

**Files:**
- Create: `monitoring/grafana/datasources.json`
- Create: `monitoring/grafana/dashboards.json`

**Step 1: 创建 Prometheus 数据源配置 (monitoring/grafana/datasources.json)**

```json
{
  "apiVersion": 1,
  "providers": [
    {
      "name": "Prometheus",
      "orgId": 1,
      "folder": "",
      "type": "file",
      "disableDeletion": false,
      "updateIntervalSeconds": 10,
      "allowUiUpdates": true,
      "options": {
        "path": "/etc/grafana/provisioning/datasources"
      }
    }
  ],
  "datasources": [
    {
      "name": "Prometheus",
      "type": "prometheus",
      "access": "proxy",
      "url": "http://prometheus:9090",
      "isDefault": true,
      "editable": true
    }
  ]
}
```

**Step 2: 创建仪表板配置 (monitoring/grafana/dashboards.json)**

这个文件会很大，包含完整的 Grafana JSON 模型。简化版本：

```json
{
  "dashboard": {
    "title": "YouTube Proxy Service",
    "panels": [
      {
        "title": "活跃流数",
        "targets": [
          {
            "expr": "active_streams"
          }
        ]
      },
      {
        "title": "yt-dlp 请求速率",
        "targets": [
          {
            "expr": "rate(ytdlp_requests_total[5m])"
          }
        ]
      },
      {
        "title": "错误率",
        "targets": [
          {
            "expr": "rate(ytdlp_request_errors_total[5m])"
          }
        ]
      },
      {
        "title": "缓存命中率",
        "targets": [
          {
            "expr": "cache_hit_rate"
          }
        ]
      }
    ]
  }
}
```

**Step 3: Commit**

```bash
git add monitoring/grafana/datasources.json monitoring/grafana/dashboards.json
git commit -m "添加：Grafana 监控仪表板配置"
```

---

## Task 9: 测试和 CI/CD

**Files:**
- Create: `.github/workflows/docker-build.yml`
- Create: `tests/test_api_routes.py`

**Step 1: 创建 API 路由测试 (tests/test_api_routes.py)**

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """测试健康检查"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in ["healthy", "degraded"]

def test_list_channels():
    """测试频道列表"""
    response = client.get("/api/channels")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_m3u_playlist():
    """测试 M3U 播放列表"""
    response = client.get("/api/m3u")
    assert response.status_code == 200 or response.status_code == 503
    if response.status_code == 200:
        assert "#EXTM3U" in response.text

def test_root_endpoint():
    """测试根端点"""
    response = client.get("/api/")
    assert response.status_code == 200
    assert "endpoints" in response.json()
```

**Step 2: 创建 CI/CD 流程 (.github/workflows/docker-build.yml)**

```yaml
name: Docker Build & Push

on:
  push:
    branches:
      - main
      - develop
  pull_request:
    branches:
      - main

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: |
          pytest tests/ -v --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

      - name: Build Docker image
        run: |
          docker build -t youtube-proxy:latest .

      - name: Run Docker container tests
        run: |
          docker-compose up -d
          sleep 5
          docker-compose exec -T app curl http://localhost:8000/health
          docker-compose down
```

**Step 3: Commit**

```bash
git add tests/test_api_routes.py .github/workflows/docker-build.yml
git commit -m "实现：测试和 CI/CD 流程"
```

---

## Task 10: 部署文档和最终配置

**Files:**
- Create: `README.md`
- Create: `DEPLOYMENT.md`
- Modify: `.gitignore`

**Step 1: 创建 README (README.md)**

```markdown
# YouTube 直播代理服务

为中国大陆 VLC 播放器提供 YouTube 直播源代理，支持最多 10 个并发直播流。

## 核心特性

✨ **功能**
- YouTube 直播流解析和代理
- 6 小时流地址缓存机制
- 自动故障恢复和降级
- 支持 M3U 播放列表格式
- 分布式锁防止并发重复解析

📊 **监控**
- Prometheus 指标收集
- Grafana 实时仪表板
- AlertManager 告警系统
- 健康检查端点

🚀 **部署**
- Docker Compose 一键启动
- 自动故障重启
- 热更新支持

## 快速开始

### 前置要求
- Docker & Docker Compose
- 美国 VPS (2 CPU, 2.5GB RAM, 1Gbps)

### 部署步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/klkanglang911/youtube-proxy.git
   cd youtube-proxy
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 配置
   ```

3. **启动服务**
   ```bash
   docker-compose up -d
   ```

4. **验证运行**
   ```bash
   curl http://localhost:8000/health
   ```

## VLC 使用方法

### 方法 1：导入 M3U 播放列表
1. 获取 M3U 文件：`http://your-vps-ip:8000/api/m3u`
2. 在 VLC 中：媒体 → 打开网络流
3. 粘贴 URL: `http://your-vps-ip:8000/api/m3u`

### 方法 2：手动添加直播源
1. VLC → 媒体 → 打开网络流
2. 输入：`http://your-vps-ip:8000/api/stream/三立新闻`

## API 端点

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/api/channels` | 频道列表 |
| GET | `/api/stream/{channel_name}` | 获取直播流 |
| GET | `/api/m3u` | M3U 播放列表 |
| POST | `/api/cache/invalidate/{channel_name}` | 清除缓存 |

## 监控和告警

### Grafana 仪表板
访问：`http://your-vps-ip:3000`
默认账号：admin / admin

### Prometheus 指标
访问：`http://your-vps-ip:9090`

## 故障排查

### Redis 连接失败
```bash
docker-compose logs redis
docker-compose restart redis
```

### yt-dlp 解析失败
```bash
# 更新 yt-dlp
docker exec ytb_app pip install --upgrade yt-dlp
docker-compose restart app
```

### 缓存问题
```bash
# 清除所有缓存
docker exec ytb_redis redis-cli FLUSHDB
```

## 配置说明

参考 `DEPLOYMENT.md` 获取详细配置指南。

## 许可证

MIT License

## 贡献

欢迎 PR 和 Issue！
```

**Step 2: 创建部署文档 (DEPLOYMENT.md)**

```markdown
# 部署指南

## VPS 环境要求

- **系统**：Ubuntu 20.04+
- **CPU**：2 核心
- **内存**：2.5GB
- **存储**：10GB+ (用于日志和缓存)
- **带宽**：1Gbps+
- **地区**：美国或其他能访问 YouTube 的地区

## 前置安装

### 1. 安装 Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### 2. 安装 Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 3. 安装 Git

```bash
sudo apt update && sudo apt install -y git
```

## 部署步骤

### 1. 克隆仓库

```bash
cd /opt
sudo git clone https://github.com/klkanglang911/youtube-proxy.git
sudo chown -R $USER:$USER youtube-proxy
cd youtube-proxy
```

### 2. 配置环境

```bash
cp .env.example .env

# 编辑 .env 文件
nano .env

# 关键配置：
# REDIS_PASSWORD=your_strong_password
# MAX_CONCURRENT_STREAMS=10
# YTDLP_TIMEOUT=30
```

### 3. 启动服务

```bash
docker-compose up -d

# 等待 30 秒让服务完全启动
sleep 30

# 验证
docker-compose ps
docker-compose logs app
```

### 4. 验证部署

```bash
# 测试健康检查
curl http://localhost:8000/health

# 预期响应：
# {"status":"healthy","version":"1.0.0",...}

# 测试频道列表
curl http://localhost:8000/api/channels

# 获取 M3U 播放列表
curl http://localhost:8000/api/m3u > playlist.m3u
```

## 配置详解

### Redis

```ini
REDIS_HOST=redis              # Redis 容器名
REDIS_PORT=6379              # 默认端口
REDIS_PASSWORD=your_password  # 必须设置强密码！
CACHE_TTL=21600              # 6 小时缓存有效期
```

### yt-dlp

```ini
YTDLP_TIMEOUT=30                    # 单个请求超时（秒）
YTDLP_MAX_RETRIES=3                 # 最大重试次数
YTDLP_PROXY=                        # 可选代理（格式：http://proxy:port）
```

### 并发控制

```ini
MAX_CONCURRENT_STREAMS=10           # 最大并发流数
MAX_CONCURRENT_YTDLP_REQUESTS=3    # 最大并发解析任务
REQUEST_TIMEOUT=30                  # API 请求超时
```

## 监控和日志

### 查看日志

```bash
# 应用日志
docker-compose logs -f app

# Redis 日志
docker-compose logs -f redis

# Prometheus 日志
docker-compose logs -f prometheus
```

### 监控仪表板

- **Grafana**：http://your-vps-ip:3000
  - 用户名：admin
  - 密码：admin

- **Prometheus**：http://your-vps-ip:9090

### 健康检查

```bash
# 系统健康检查
curl http://your-vps-ip:8000/health

# Redis 状态
docker-compose exec redis redis-cli INFO

# 活跃流数
curl http://your-vps-ip:8000/metrics | grep active_streams
```

## 日常维护

### 更新 yt-dlp

YouTube 经常更新，需要定期更新 yt-dlp：

```bash
cd /opt/youtube-proxy

# 方法 1：更新 Docker 镜像
docker-compose build --no-cache
docker-compose up -d

# 方法 2：容器内更新
docker exec ytb_app pip install --upgrade yt-dlp
docker-compose restart app
```

### 清理缓存

```bash
# 清除所有缓存
docker exec ytb_redis redis-cli FLUSHDB

# 清除特定频道缓存
curl -X POST http://localhost:8000/api/cache/invalidate/三立新闻
```

### 备份配置

```bash
# 备份 Redis 数据
docker exec ytb_redis redis-cli BGSAVE
docker cp ytb_redis:/data/dump.rdb ./backup/redis-dump-$(date +%Y%m%d).rdb

# 备份 .env
cp .env ./backup/.env-$(date +%Y%m%d)
```

## 故障排查

### 服务无法启动

```bash
# 检查日志
docker-compose logs app

# 常见问题：
# 1. Redis 连接失败 → 检查 REDIS_PASSWORD
# 2. yt-dlp 不可用 → docker-compose rebuild
# 3. 端口冲突 → 修改 docker-compose.yml 中的端口
```

### 流解析失败

```bash
# 检查 yt-dlp 是否最新
docker exec ytb_app yt-dlp --version

# 手动测试解析
docker exec ytb_app yt-dlp -j "https://www.youtube.com/@setn/live"

# 如果失败，可能是：
# 1. YouTube 更新了 API
# 2. IP 被限制
# 3. 网络连接问题
```

### 缓存命中率低

如果缓存命中率 < 50%：

```bash
# 检查 Redis 连接
docker-compose logs redis

# 增加缓存时间
# 编辑 .env：CACHE_TTL=86400  # 24 小时
docker-compose restart app
```

### 并发流过多

```bash
# 监控当前活跃流
curl http://localhost:8000/metrics | grep active_streams

# 如果经常超过 8：
# 1. 检查是否有僵尸流
# 2. 增加 MAX_CONCURRENT_STREAMS
# 3. 考虑升级 VPS
```

## 性能调优

### 1. Redis 优化

```bash
# 修改 docker-compose.yml
# 增加 Redis 内存上限：
redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### 2. yt-dlp 并发优化

```bash
# 编辑 .env
MAX_CONCURRENT_YTDLP_REQUESTS=5  # 从 3 增加到 5
```

### 3. 缓存策略优化

```bash
# 增加缓存时间（但要注意 URL 过期）
CACHE_TTL=43200  # 12 小时

# 定期刷新即将过期的缓存
```

## 安全建议

1. **修改 Grafana 密码**
   - 登录 Grafana → 设置 → 用户 → 修改密码

2. **使用防火墙**
   ```bash
   sudo ufw allow 8000/tcp  # API
   sudo ufw allow 3000/tcp  # Grafana (限制 IP)
   sudo ufw allow 9090/tcp  # Prometheus (限制 IP)
   sudo ufw enable
   ```

3. **定期备份**
   - 每周备份 Redis 数据
   - 备份 .env 文件（保存到安全位置）

4. **监控异常**
   - 设置告警阈值
   - 定期检查日志

## 联系和支持

- GitHub Issues: https://github.com/klkanglang911/youtube-proxy/issues
- Email: klkanglang@gmail.com
```

**Step 3: 创建 .gitignore**

```
# 环境文件
.env
.env.local

# 日志
logs/
*.log

# 缓存和临时文件
__pycache__/
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Docker
.docker/

# 监控数据
prometheus/data/
grafana/data/
redis/data/
```

**Step 4: Commit**

```bash
git add README.md DEPLOYMENT.md .gitignore
git commit -m "添加：部署文档和项目配置"
```

---

## 最终检查清单

在执行计划前，请确认：

- [ ] VPS 环境满足要求（2 CPU, 2.5GB RAM, 1Gbps）
- [ ] Git 已配置用户信息
- [ ] Docker 和 Docker Compose 已安装
- [ ] 理解 yt-dlp、Redis、FastAPI 的基本概念
- [ ] 有 Grafana 和 Prometheus 监控经验（可选但推荐）

---

## 执行路线图

**第 1 天**：环境初始化和基础设施（Task 1-3）
**第 2 天**：核心服务实现（Task 4-5）
**第 3 天**：API 和应用层（Task 6-7）
**第 4 天**：监控和部署（Task 8-10）
**第 5 天**：测试、优化和生产部署

---

Plan complete and saved to `docs/plans/2026-02-03-youtube-proxy-service.md`.

现在有两个执行选项：

**1. Subagent-Driven（当前会话）**
- 我在当前会话中分派独立任务
- 每个任务有新的 subagent 执行
- 任务间进行代码审查
- 适合快速迭代和实时反馈

**2. Parallel Session（独立会话）**
- 在新的 Git Worktree 中开启独立会话
- 使用 executing-plans 批量执行任务
- 有明确的检查点和里程碑
- 适合系统化、集中式执行

**你倾向哪种方式？**