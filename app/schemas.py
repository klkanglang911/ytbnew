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
    status: str
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
