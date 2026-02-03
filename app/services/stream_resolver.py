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
