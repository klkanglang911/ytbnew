import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用信息
    APP_NAME: str = "YouTube 直播代理服务"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Redis 配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "password")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # 缓存配置
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "21600"))  # 6小时

    # yt-dlp 配置
    YTDLP_TIMEOUT: int = int(os.getenv("YTDLP_TIMEOUT", "30"))
    YTDLP_MAX_RETRIES: int = int(os.getenv("YTDLP_MAX_RETRIES", "3"))

    # 并发控制
    MAX_CONCURRENT_STREAMS: int = int(os.getenv("MAX_CONCURRENT_STREAMS", "10"))
    MAX_CONCURRENT_YTDLP_REQUESTS: int = int(os.getenv("MAX_CONCURRENT_YTDLP_REQUESTS", "3"))

    # 请求超时
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
