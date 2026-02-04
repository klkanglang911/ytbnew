from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio
from app.config import settings
from app.api.routes import router as api_router
from app.api.health import router as health_router
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# UTF-8 编码中间件：确保所有文本响应都明确指定字符集
class UTF8EncodingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # 获取当前的 content-type
        content_type = response.headers.get("content-type", "")

        # 仅在没有字符集信息时添加 charset=utf-8
        if content_type and "charset" not in content_type:
            if content_type.startswith("application/json"):
                response.headers["content-type"] = "application/json; charset=utf-8"
            elif content_type.startswith("text/"):
                response.headers["content-type"] = f"{content_type}; charset=utf-8"

        return response

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="YouTube 直播代理服务 - 为 VLC 提供代理直播源",
    debug=settings.DEBUG
)

# 注册中间件（顺序很重要：UTF-8 中间件最后添加）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(UTF8EncodingMiddleware)

# 注册路由
app.include_router(api_router, prefix="/api")
app.include_router(health_router)

# M3U 播放列表特殊处理
@app.get("/playlist.m3u", response_class=PlainTextResponse)
async def get_m3u_file():
    """获取 M3U 播放列表（用于 VLC 直接导入）"""
    from app.api.routes import get_m3u_playlist
    return await get_m3u_playlist(use_cache=True)

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")

    # 初始化服务
    try:
        # 测试 Redis 连接
        from app.services.cache_service import cache_service
        await asyncio.sleep(0.5)  # 等待 Redis 启动
        logger.info("✓ 缓存服务初始化完成")

        # 测试 yt-dlp
        from app.services.ytdlp_service import ytdlp_service
        logger.info("✓ yt-dlp 服务初始化完成")

        logger.info("✓ 所有服务初始化完成")

    except Exception as e:
        logger.error(f"✗ 启动失败: {e}")
        raise

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("🛑 应用关闭中...")

    try:
        from app.services.cache_service import cache_service
        await cache_service.close()
        logger.info("✓ 缓存服务已关闭")
    except Exception as e:
        logger.warning(f"关闭缓存服务异常: {e}")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level=settings.LOG_LEVEL.lower()
    )
