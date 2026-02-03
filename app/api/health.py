from fastapi import APIRouter, HTTPException
from app.config import settings
from app.services.cache_service import cache_service
from app.services.ytdlp_service import ytdlp_service
from app.services.monitor_service import monitor_service
from app.utils.logger import setup_logger
from datetime import datetime

logger = setup_logger(__name__)
router = APIRouter()

@router.get("/health", tags=["Health"])
async def health_check():
    """
    系统健康检查

    检查项：
    - Redis 连接
    - yt-dlp 可用性
    - 应用状态
    """
    try:
        # 检查 Redis
        redis_ok = False
        try:
            cache_service.redis_client.ping()
            redis_ok = True
        except Exception as e:
            logger.warning(f"Redis 健康检查失败: {e}")

        # 检查 yt-dlp
        ytdlp_ok = False
        try:
            import subprocess
            result = subprocess.run(
                ["yt-dlp", "--version"],
                capture_output=True,
                timeout=5
            )
            ytdlp_ok = result.returncode == 0
        except Exception as e:
            logger.warning(f"yt-dlp 健康检查失败: {e}")

        # 获取活跃流数
        active_streams = getattr(monitor_service, 'active_streams', 0)

        # 健康状态判定
        status = "healthy" if (redis_ok and ytdlp_ok) else "degraded"

        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.APP_VERSION,
            "redis_connected": redis_ok,
            "ytdlp_available": ytdlp_ok,
            "active_streams": active_streams
        }

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=503, detail="健康检查失败")

@router.get("/ready", tags=["Health"])
async def readiness_check():
    """就绪检查（用于 Docker 容器编排）"""
    try:
        cache_service.redis_client.ping()
        return {"status": "ready"}
    except:
        raise HTTPException(status_code=503, detail="系统未就绪")
