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
