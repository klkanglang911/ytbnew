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
