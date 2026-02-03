from typing import List, Optional
from datetime import datetime

class Channel:
    """频道模型"""

    def __init__(
        self,
        name: str,
        url: str,
        description: str = "",
        logo_url: Optional[str] = None
    ):
        self.name = name
        self.url = url
        self.description = description
        self.logo_url = logo_url

class StreamInfo:
    """流信息模型"""

    def __init__(
        self,
        channel_name: str,
        stream_url: str,
        quality: str,
        format: str,
        expires_at: str,
        status: str = "online"
    ):
        self.channel_name = channel_name
        self.stream_url = stream_url
        self.quality = quality
        self.format = format
        self.expires_at = expires_at
        self.status = status
        self.fetched_at = datetime.utcnow().isoformat()
