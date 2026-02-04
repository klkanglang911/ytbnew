"""
YouTube 频道验证器

异步验证频道是否可用，通过调用 yt-dlp 测试直播流。
支持批量验证和进度回调。
"""

import asyncio
from typing import List, Optional, Callable, Dict
from datetime import datetime
from pydantic import BaseModel
from app.services.ytdlp_service import YtdlpService
from app.utils.logger import logger


class ChannelValidationResult(BaseModel):
    """频道验证结果"""
    url: str
    status: str  # "valid" | "invalid" | "error"
    error_message: Optional[str] = None
    validated_at: str


class ChannelValidator:
    """频道验证器 - 异步验证频道是否可用"""

    def __init__(self, ytdlp_service: Optional[YtdlpService] = None):
        """
        初始化验证器。

        Args:
            ytdlp_service: yt-dlp 服务实例。如果为 None，会创建新实例。
        """
        self.ytdlp_service = ytdlp_service or YtdlpService()
        # 并发限制：最多 3 个并发验证任务
        self.semaphore = asyncio.Semaphore(3)

    async def validate_channel(self, channel_url: str) -> ChannelValidationResult:
        """
        验证单个频道是否可用。

        通过调用 yt-dlp 尝试提取流 URL 来测试频道可用性。
        如果能成功提取流 URL，说明频道可用。

        Args:
            channel_url: YouTube 频道或直播 URL

        Returns:
            验证结果
        """
        async with self.semaphore:
            try:
                # 尝试提取流 URL（这会触发 yt-dlp 验证）
                logger.debug(f"验证频道：{channel_url}")

                # 使用 yt-dlp 服务提取流 URL
                stream_data = await self.ytdlp_service.extract_stream_url(channel_url)

                if stream_data and stream_data.get('url'):
                    logger.info(f"频道验证成功：{channel_url}")
                    return ChannelValidationResult(
                        url=channel_url,
                        status="valid",
                        validated_at=datetime.now().isoformat()
                    )
                else:
                    logger.warning(f"频道验证失败（无流 URL）：{channel_url}")
                    return ChannelValidationResult(
                        url=channel_url,
                        status="invalid",
                        error_message="无法获取直播流",
                        validated_at=datetime.now().isoformat()
                    )

            except asyncio.TimeoutError:
                logger.warning(f"频道验证超时：{channel_url}")
                return ChannelValidationResult(
                    url=channel_url,
                    status="error",
                    error_message="验证超时",
                    validated_at=datetime.now().isoformat()
                )

            except Exception as e:
                error_msg = str(e)
                logger.error(f"频道验证异常：{channel_url}，错误：{error_msg}")

                # 根据错误类型判断是否为真的无效频道
                if any(keyword in error_msg.lower() for keyword in [
                    'not found', 'unavailable', 'not available', 'no such file',
                    'does not exist', '404', 'channel not found'
                ]):
                    status = "invalid"
                else:
                    status = "error"

                return ChannelValidationResult(
                    url=channel_url,
                    status=status,
                    error_message=error_msg[:100],  # 限制错误信息长度
                    validated_at=datetime.now().isoformat()
                )

    async def validate_channels_async(
        self,
        channels: List[Dict[str, str]],
        progress_callback: Optional[Callable[[Dict], None]] = None
    ) -> List[ChannelValidationResult]:
        """
        异步验证多个频道，支持进度回调。

        Args:
            channels: 频道列表，每个频道是一个字典，至少包含 'url' 字段
            progress_callback: 进度回调函数，会被调用多次
                              回调参数：{"total": int, "validated": int, "current": str}

        Returns:
            验证结果列表
        """
        if not channels:
            return []

        total = len(channels)
        validated = 0
        results = []

        # 创建验证任务
        tasks = []
        for channel in channels:
            url = channel.get('url', '')
            if url:
                tasks.append(self.validate_channel(url))

        # 异步执行所有验证任务，同时跟踪进度
        logger.info(f"开始验证 {total} 个频道，并发数：3")

        for i, task in enumerate(asyncio.as_completed(tasks)):
            try:
                result = await task
                results.append(result)
                validated += 1

                # 调用进度回调
                if progress_callback:
                    progress_callback({
                        'total': total,
                        'validated': validated,
                        'current': result.url,
                        'status': result.status
                    })

                logger.debug(f"验证进度：{validated}/{total} - {result.url} ({result.status})")

            except Exception as e:
                logger.error(f"验证任务异常：{e}")
                validated += 1

        logger.info(f"频道验证完成：{validated}/{total}")
        return results

    @staticmethod
    async def validate_channels_batch(
        urls: List[str],
        ytdlp_service: Optional[YtdlpService] = None,
        progress_callback: Optional[Callable[[Dict], None]] = None
    ) -> List[ChannelValidationResult]:
        """
        静态方法：验证 URL 列表。

        这是一个便利方法，直接接收 URL 列表而不需要格式化。

        Args:
            urls: URL 列表
            ytdlp_service: yt-dlp 服务实例
            progress_callback: 进度回调函数

        Returns:
            验证结果列表
        """
        validator = ChannelValidator(ytdlp_service)
        channels = [{'url': url} for url in urls]
        return await validator.validate_channels_async(channels, progress_callback)

    async def validate_and_filter(
        self,
        channels: List[Dict[str, str]],
        include_invalid: bool = False
    ) -> tuple[List[Dict[str, str]], List[ChannelValidationResult]]:
        """
        验证频道并返回有效频道列表。

        Args:
            channels: 频道列表
            include_invalid: 是否包含无效频道（默认只返回有效的）

        Returns:
            (有效频道列表, 全部验证结果)
        """
        results = await self.validate_channels_async(channels)

        # 构建有效频道列表
        valid_channels = []
        for channel, result in zip(channels, results):
            if include_invalid or result.status == "valid":
                # 添加验证信息到频道数据
                channel_with_status = {
                    **channel,
                    'validation_status': result.status,
                    'validation_error': result.error_message,
                    'validated_at': result.validated_at
                }
                valid_channels.append(channel_with_status)

        return valid_channels, results
