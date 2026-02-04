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

    注：此端点返回已缓存的频道流地址。
    对于未缓存的频道，先调用 /api/stream/{channel} 来获取并缓存流地址。
    """
    try:
        import asyncio

        m3u_content = "#EXTM3U\n"

        for channel in CHANNELS:
            channel_name = channel['name']

            try:
                # 直接从缓存读取，不主动调用 yt-dlp
                # 这样避免单个频道卡住导致整个 M3U 无响应
                cached_data = await cache_service.get_stream_url(channel_name)

                if cached_data and 'url' in cached_data:
                    stream_url = cached_data.get('url')
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
                        logger.debug(f"频道缓存为空，跳过: {channel_name}")
                else:
                    logger.debug(f"频道未缓存，跳过: {channel_name}")

            except Exception as e:
                logger.warning(f"处理频道时出错，跳过: {channel_name} - {e}")

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
