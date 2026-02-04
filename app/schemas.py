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


# ============ 频道管理相关数据模型 ============

class ChannelInfo(BaseModel):
    """频道基本信息"""
    name: str
    url: str
    description: Optional[str] = ""
    logo: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    validation_status: Optional[str] = None  # "valid" | "invalid" | "pending"


class ChannelValidationResult(BaseModel):
    """频道验证结果"""
    url: str
    status: str  # "valid" | "invalid" | "error"
    error_message: Optional[str] = None
    validated_at: str


class ImportPreviewResponse(BaseModel):
    """导入预览响应"""
    total_count: int
    new_count: int  # 不重复的新频道数
    duplicate_count: int
    channels: List[ChannelInfo]


class ConfirmImportRequest(BaseModel):
    """确认导入请求"""
    channels: List[ChannelInfo]
    validate: bool = True  # 是否验证


class ImportResultResponse(BaseModel):
    """导入结果响应"""
    success: bool
    message: str
    added_count: int
    duplicate_count: int
    invalid_count: int
    task_id: Optional[str] = None  # 验证任务 ID


class ChannelWithStatusResponse(ChannelInfo):
    """带验证状态的频道信息"""
    validation_result: Optional[ChannelValidationResult] = None


class ChannelListResponse(BaseModel):
    """频道列表响应"""
    channels: List[ChannelWithStatusResponse]
    total: int
    statistics: Optional[dict] = None


class ChannelUpdateRequest(BaseModel):
    """频道更新请求"""
    name: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    logo: Optional[str] = None


class DeleteChannelResponse(BaseModel):
    """删除频道响应"""
    success: bool
    message: str
    deleted_channel: Optional[ChannelInfo] = None


class ValidationStatusResponse(BaseModel):
    """验证状态响应"""
    task_id: str
    status: str  # "running" | "completed" | "failed"
    progress: Optional[dict] = None
    results: Optional[List[ChannelValidationResult]] = None
    error_message: Optional[str] = None
