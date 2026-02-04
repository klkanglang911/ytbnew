"""
频道管理 API 路由

提供频道的 CRUD 操作和导入管理接口。
"""

import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from app.services.url_parser import URLParser
from app.services.channel_manager import ChannelManager
from app.services.channel_validator import ChannelValidator
from app.schemas import (
    ChannelInfo,
    ImportPreviewResponse,
    ConfirmImportRequest,
    ImportResultResponse,
    ChannelListResponse,
    ChannelWithStatusResponse,
    ChannelUpdateRequest,
    DeleteChannelResponse,
    ValidationStatusResponse,
)
from app.utils.logger import logger
from app.config import settings

# 初始化路由
router = APIRouter(prefix="/api/admin/channels", tags=["频道管理"])

# 全局实例
channel_manager: Optional[ChannelManager] = None
channel_validator: Optional[ChannelValidator] = None

# 存储正在进行的验证任务
validation_tasks = {}


def set_manager(manager: ChannelManager) -> None:
    """设置频道管理器实例"""
    global channel_manager
    channel_manager = manager


def set_validator(validator: ChannelValidator) -> None:
    """设置频道验证器实例"""
    global channel_validator
    channel_validator = validator


@router.post("/import", response_model=ImportPreviewResponse)
async def preview_import(raw_input: str) -> ImportPreviewResponse:
    """
    预览导入结果。

    解析输入的 URL 或 M3U 内容，返回待导入的频道列表。

    Args:
        raw_input: 原始输入字符串（URL 或 M3U 内容）

    Returns:
        导入预览结果，包含新频道列表和统计信息
    """
    if not raw_input or not raw_input.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="输入内容不能为空"
        )

    try:
        # 解析 URL
        urls = URLParser.parse_urls(raw_input)

        if not urls:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未找到有效的 YouTube URL"
            )

        logger.info(f"解析了 {len(urls)} 个 URL")

        # 检查重复
        new_channels = []
        duplicate_count = 0

        for url in urls:
            # 检查 URL 是否已存在
            if channel_manager and channel_manager.is_duplicate_url(url):
                duplicate_count += 1
                logger.debug(f"URL 已存在，跳过：{url}")
            else:
                # 生成频道信息
                channel = ChannelInfo(
                    name=f"新频道 {len(new_channels) + 1}",
                    url=url,
                    description="",
                    logo=None
                )
                new_channels.append(channel)

        return ImportPreviewResponse(
            total_count=len(urls),
            new_count=len(new_channels),
            duplicate_count=duplicate_count,
            channels=new_channels
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入预览失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理失败：{str(e)}"
        )


@router.post("/confirm-import", response_model=ImportResultResponse)
async def confirm_import(
    request: ConfirmImportRequest,
    background_tasks: BackgroundTasks
) -> ImportResultResponse:
    """
    确认导入，异步验证频道。

    Args:
        request: 确认导入请求，包含要导入的频道列表和是否验证的标志
        background_tasks: FastAPI 后台任务

    Returns:
        导入结果，包含任务 ID（如果进行了验证）
    """
    if not request.channels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="频道列表不能为空"
        )

    try:
        # 转换为字典列表
        channels_data = [ch.dict(exclude_none=True) for ch in request.channels]

        # 添加频道（不验证）
        result = channel_manager.add_channels(channels_data)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )

        added_count = result.data.get('added', 0) if result.data else 0
        duplicate_count = result.data.get('duplicate', 0) if result.data else 0

        # 如果需要验证，在后台进行
        task_id = None
        invalid_count = 0

        if request.validate and channel_validator and added_count > 0:
            task_id = f"import_{int(__import__('time').time() * 1000)}"

            # 获取新添加的频道进行验证
            added_channels = channels_data[-added_count:] if added_count > 0 else []

            # 在后台任务中验证
            background_tasks.add_task(
                _validate_channels_task,
                task_id,
                added_channels
            )

            logger.info(f"启动异步验证任务：{task_id}，频道数：{len(added_channels)}")

        return ImportResultResponse(
            success=True,
            message=f"成功导入 {added_count} 个频道" + (f"，任务 ID：{task_id}" if task_id else ""),
            added_count=added_count,
            duplicate_count=duplicate_count,
            invalid_count=invalid_count,
            task_id=task_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"确认导入失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败：{str(e)}"
        )


async def _validate_channels_task(task_id: str, channels: list) -> None:
    """
    后台验证频道任务。

    Args:
        task_id: 任务 ID
        channels: 要验证的频道列表
    """
    try:
        validation_tasks[task_id] = {
            'status': 'running',
            'progress': {'total': len(channels), 'validated': 0, 'succeeded': 0, 'failed': 0},
            'results': []
        }

        # 验证频道
        results = await channel_validator.validate_channels_async(
            channels,
            progress_callback=lambda info: _update_progress(task_id, info)
        )

        # 更新验证结果到频道
        for channel, result in zip(channels, results):
            if result.status == 'valid':
                channel_manager.update_channel(
                    channel['name'],
                    {'validation_status': 'valid'}
                )
                validation_tasks[task_id]['progress']['succeeded'] += 1
            else:
                channel_manager.update_channel(
                    channel['name'],
                    {'validation_status': result.status}
                )
                validation_tasks[task_id]['progress']['failed'] += 1

        # 标记任务完成
        validation_tasks[task_id]['status'] = 'completed'
        validation_tasks[task_id]['results'] = [r.dict() for r in results]

        logger.info(f"验证任务完成：{task_id}")

    except Exception as e:
        logger.error(f"验证任务失败：{task_id}，错误：{e}")
        validation_tasks[task_id]['status'] = 'failed'
        validation_tasks[task_id]['error_message'] = str(e)


def _update_progress(task_id: str, info: dict) -> None:
    """更新任务进度"""
    if task_id in validation_tasks:
        validation_tasks[task_id]['progress']['validated'] = info.get('validated', 0)
        logger.debug(f"任务进度 {task_id}：{info}")


@router.get("/list", response_model=ChannelListResponse)
async def list_channels() -> ChannelListResponse:
    """
    获取所有频道及其验证状态。

    Returns:
        频道列表响应
    """
    try:
        channels = channel_manager.get_all_channels()

        # 转换为响应格式
        channels_with_status = [
            ChannelWithStatusResponse(
                name=ch.name,
                url=ch.url,
                description=ch.description,
                logo=ch.logo,
                created_at=ch.created_at,
                updated_at=ch.updated_at,
                validation_status=ch.validation_status
            )
            for ch in channels
        ]

        stats = channel_manager.get_statistics()

        return ChannelListResponse(
            channels=channels_with_status,
            total=len(channels),
            statistics=stats
        )

    except Exception as e:
        logger.error(f"获取频道列表失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败：{str(e)}"
        )


@router.put("/{channel_name}", response_model=ChannelInfo)
async def update_channel(
    channel_name: str,
    data: ChannelUpdateRequest
) -> ChannelInfo:
    """
    更新频道信息。

    Args:
        channel_name: 频道名称
        data: 更新数据

    Returns:
        更新后的频道信息
    """
    try:
        update_dict = data.dict(exclude_none=True)

        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有更新数据"
            )

        result = channel_manager.update_channel(channel_name, update_dict)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.message
            )

        updated_channel = channel_manager.get_channel(channel_name)
        return updated_channel

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新频道失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新失败：{str(e)}"
        )


@router.delete("/{channel_name}", response_model=DeleteChannelResponse)
async def delete_channel(channel_name: str) -> DeleteChannelResponse:
    """
    删除频道。

    Args:
        channel_name: 频道名称

    Returns:
        删除结果
    """
    try:
        result = channel_manager.delete_channel(channel_name)

        return DeleteChannelResponse(
            success=result.success,
            message=result.message,
            deleted_channel=ChannelInfo(**result.data) if result.data else None
        )

    except Exception as e:
        logger.error(f"删除频道失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败：{str(e)}"
        )


@router.get("/validation-status/{task_id}", response_model=ValidationStatusResponse)
async def get_validation_status(task_id: str) -> ValidationStatusResponse:
    """
    获取异步验证任务的状态。

    Args:
        task_id: 任务 ID

    Returns:
        验证状态响应
    """
    if task_id not in validation_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务不存在：{task_id}"
        )

    task_info = validation_tasks[task_id]

    return ValidationStatusResponse(
        task_id=task_id,
        status=task_info.get('status', 'unknown'),
        progress=task_info.get('progress'),
        results=[item for item in task_info.get('results', [])],
        error_message=task_info.get('error_message')
    )
