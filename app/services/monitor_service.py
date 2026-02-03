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
