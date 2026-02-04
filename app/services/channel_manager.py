"""
频道管理器

管理频道配置的加载、保存、添加、删除等操作。
支持从 JSON 文件持久化存储。
"""

import json
import os
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
from app.utils.logger import logger


class ChannelInfo(BaseModel):
    """频道基本信息"""
    name: str
    url: str
    description: Optional[str] = ""
    logo: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    validation_status: Optional[str] = None  # "valid" | "invalid" | "pending"


class ChannelOperationResult(BaseModel):
    """操作结果"""
    success: bool
    message: str
    data: Optional[Dict] = None


class ChannelManager:
    """频道管理器 - 管理频道的 CRUD 操作和持久化"""

    def __init__(self, config_path: str = "app/templates/channels.json"):
        """
        初始化频道管理器。

        Args:
            config_path: JSON 配置文件路径
        """
        self.config_path = config_path
        self.channels: List[ChannelInfo] = []
        self.metadata: Dict = {
            'version': '1.0',
            'last_updated': None,
            'total_channels': 0
        }

        # 初始加载配置
        self._ensure_config_exists()
        self.load_channels()

    def _ensure_config_exists(self) -> None:
        """确保配置文件存在，如果不存在则创建空配置。"""
        if not os.path.exists(self.config_path):
            # 如果目录不存在，创建目录
            directory = os.path.dirname(self.config_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            # 创建空配置文件
            initial_config = {
                'channels': [],
                'metadata': {
                    'version': '1.0',
                    'last_updated': datetime.now().isoformat(),
                    'total_channels': 0
                }
            }

            self.save_config(initial_config)
            logger.info(f"创建新配置文件：{self.config_path}")

    def load_channels(self) -> List[ChannelInfo]:
        """
        从 JSON 文件加载频道配置。

        Returns:
            频道列表
        """
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"配置文件不存在：{self.config_path}")
                self.channels = []
                return []

            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 加载频道列表
            channels_data = config.get('channels', [])
            self.channels = [ChannelInfo(**ch) for ch in channels_data]

            # 加载元数据
            self.metadata = config.get('metadata', {
                'version': '1.0',
                'last_updated': None,
                'total_channels': len(self.channels)
            })

            logger.info(f"加载了 {len(self.channels)} 个频道")
            return self.channels

        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析错误：{e}")
            return []
        except Exception as e:
            logger.error(f"加载频道失败：{e}")
            return []

    def save_channels(self) -> bool:
        """
        保存频道配置到 JSON 文件。

        Returns:
            是否保存成功
        """
        try:
            config = {
                'channels': [ch.dict() for ch in self.channels],
                'metadata': {
                    **self.metadata,
                    'last_updated': datetime.now().isoformat(),
                    'total_channels': len(self.channels)
                }
            }

            self.save_config(config)
            logger.info(f"保存了 {len(self.channels)} 个频道到 {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"保存频道失败：{e}")
            return False

    def save_config(self, config: Dict) -> bool:
        """
        保存配置字典到 JSON 文件。

        Args:
            config: 配置字典

        Returns:
            是否保存成功
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败：{e}")
            return False

    def reload_channels(self) -> bool:
        """
        热加载频道配置（重新从文件加载到内存）。

        这允许在不重启应用的情况下更新频道配置。

        Returns:
            是否重加载成功
        """
        try:
            old_count = len(self.channels)
            self.load_channels()
            new_count = len(self.channels)
            logger.info(f"热加载频道配置：{old_count} → {new_count}")
            return True
        except Exception as e:
            logger.error(f"热加载频道失败：{e}")
            return False

    def add_channels(self, new_channels: List[Dict[str, str]]) -> ChannelOperationResult:
        """
        添加新频道（支持批量）。

        会自动去重（检查 URL 是否已存在）。

        Args:
            new_channels: 新频道列表，每个是字典

        Returns:
            操作结果
        """
        if not new_channels:
            return ChannelOperationResult(
                success=False,
                message="频道列表为空"
            )

        added_count = 0
        duplicate_count = 0
        errors = []

        for channel_data in new_channels:
            try:
                # 检查必要字段
                if 'name' not in channel_data or 'url' not in channel_data:
                    errors.append(f"缺少必要字段：{channel_data}")
                    continue

                # 检查 URL 重复
                if self.is_duplicate_url(channel_data['url']):
                    duplicate_count += 1
                    logger.debug(f"URL 已存在，跳过：{channel_data['url']}")
                    continue

                # 检查名称重复
                if self._is_duplicate_name(channel_data['name']):
                    # 如果名称重复，尝试生成唯一名称
                    original_name = channel_data['name']
                    counter = 1
                    while self._is_duplicate_name(channel_data['name']):
                        channel_data['name'] = f"{original_name} ({counter})"
                        counter += 1
                    logger.debug(f"名称重复，重命名为：{channel_data['name']}")

                # 添加时间戳
                now = datetime.now().isoformat()
                if 'created_at' not in channel_data:
                    channel_data['created_at'] = now
                channel_data['updated_at'] = now

                # 创建 ChannelInfo 对象
                channel = ChannelInfo(**channel_data)
                self.channels.append(channel)
                added_count += 1

                logger.info(f"添加频道：{channel.name} - {channel.url}")

            except Exception as e:
                error_msg = f"添加频道失败：{channel_data}，错误：{e}"
                logger.error(error_msg)
                errors.append(error_msg)

        # 保存到文件
        if added_count > 0:
            self.save_channels()

        message = f"添加成功 {added_count} 个，重复 {duplicate_count} 个"
        if errors:
            message += f"，错误 {len(errors)} 个"

        return ChannelOperationResult(
            success=added_count > 0,
            message=message,
            data={
                'added': added_count,
                'duplicate': duplicate_count,
                'errors': errors[:5]  # 只返回前 5 个错误
            }
        )

    def update_channel(self, name: str, update_data: Dict) -> ChannelOperationResult:
        """
        更新频道信息。

        Args:
            name: 频道名称（唯一标识）
            update_data: 更新数据

        Returns:
            操作结果
        """
        for i, channel in enumerate(self.channels):
            if channel.name == name:
                try:
                    # 如果更新 URL，检查是否重复
                    if 'url' in update_data and update_data['url'] != channel.url:
                        if self.is_duplicate_url(update_data['url']):
                            return ChannelOperationResult(
                                success=False,
                                message=f"URL 已存在：{update_data['url']}"
                            )

                    # 更新字段
                    for key, value in update_data.items():
                        if key in ['name', 'url', 'description', 'logo']:
                            setattr(channel, key, value)

                    # 更新时间戳
                    channel.updated_at = datetime.now().isoformat()

                    self.channels[i] = channel
                    self.save_channels()

                    logger.info(f"更新频道：{name}")
                    return ChannelOperationResult(
                        success=True,
                        message=f"频道已更新：{name}",
                        data=channel.dict()
                    )

                except Exception as e:
                    return ChannelOperationResult(
                        success=False,
                        message=f"更新失败：{e}"
                    )

        return ChannelOperationResult(
            success=False,
            message=f"未找到频道：{name}"
        )

    def delete_channel(self, name: str) -> ChannelOperationResult:
        """
        删除频道。

        Args:
            name: 频道名称

        Returns:
            操作结果
        """
        for i, channel in enumerate(self.channels):
            if channel.name == name:
                try:
                    deleted_channel = self.channels.pop(i)
                    self.save_channels()
                    logger.info(f"删除频道：{name}")
                    return ChannelOperationResult(
                        success=True,
                        message=f"频道已删除：{name}",
                        data=deleted_channel.dict()
                    )
                except Exception as e:
                    return ChannelOperationResult(
                        success=False,
                        message=f"删除失败：{e}"
                    )

        return ChannelOperationResult(
            success=False,
            message=f"未找到频道：{name}"
        )

    def get_channel(self, name: str) -> Optional[ChannelInfo]:
        """
        获取单个频道。

        Args:
            name: 频道名称

        Returns:
            频道对象，如果不存在返回 None
        """
        for channel in self.channels:
            if channel.name == name:
                return channel
        return None

    def get_all_channels(self) -> List[ChannelInfo]:
        """
        获取所有频道。

        Returns:
            频道列表
        """
        return self.channels

    def is_duplicate_url(self, url: str) -> bool:
        """
        检查 URL 是否已存在。

        Args:
            url: YouTube URL

        Returns:
            是否重复
        """
        for channel in self.channels:
            if channel.url == url:
                return True
        return False

    def _is_duplicate_name(self, name: str) -> bool:
        """
        检查频道名称是否已存在。

        Args:
            name: 频道名称

        Returns:
            是否重复
        """
        for channel in self.channels:
            if channel.name == name:
                return True
        return False

    def get_statistics(self) -> Dict:
        """
        获取频道统计信息。

        Returns:
            统计信息字典
        """
        valid_count = sum(1 for ch in self.channels if ch.validation_status == 'valid')
        invalid_count = sum(1 for ch in self.channels if ch.validation_status == 'invalid')
        pending_count = sum(1 for ch in self.channels if ch.validation_status is None or ch.validation_status == 'pending')

        return {
            'total': len(self.channels),
            'valid': valid_count,
            'invalid': invalid_count,
            'pending': pending_count,
            'last_updated': self.metadata.get('last_updated'),
        }
