import pytest
import asyncio
from app.services.cache_service import CacheService

@pytest.fixture
async def cache():
    """创建缓存服务实例"""
    service = CacheService()
    yield service
    await service.close()

@pytest.mark.asyncio
async def test_set_and_get_stream_url(cache):
    """测试缓存设置和读取"""
    channel = "test_channel"
    stream_data = {
        "url": "http://example.com/stream.m3u8",
        "quality": "720p",
        "expires_at": "2026-02-04T00:00:00Z"
    }

    result = await cache.set_stream_url(channel, stream_data, ttl_seconds=60)
    assert result is True

    cached = await cache.get_stream_url(channel)
    assert cached is not None
    assert cached["url"] == stream_data["url"]

@pytest.mark.asyncio
async def test_cache_miss(cache):
    """测试缓存未命中"""
    result = await cache.get_stream_url("non_existent_channel")
    assert result is None

@pytest.mark.asyncio
async def test_invalidate(cache):
    """测试缓存清除"""
    channel = "test_channel"
    stream_data = {"url": "http://example.com"}

    await cache.set_stream_url(channel, stream_data)
    assert await cache.get_stream_url(channel) is not None

    await cache.invalidate(channel)
    assert await cache.get_stream_url(channel) is None

@pytest.mark.asyncio
async def test_distributed_lock(cache):
    """测试分布式锁"""
    channel = "test_lock"

    result1 = await cache.acquire_lock(channel)
    assert result1 is True

    result2 = await cache.acquire_lock(channel)
    assert result2 is False

    await cache.release_lock(channel)

    result3 = await cache.acquire_lock(channel)
    assert result3 is True

    await cache.release_lock(channel)

@pytest.mark.asyncio
async def test_get_or_set(cache):
    """测试缓存读写模式"""
    channel = "test_fetch"
    call_count = 0

    async def mock_fetch(ch):
        nonlocal call_count
        call_count += 1
        return {"url": f"http://example.com/{ch}", "quality": "1080p"}

    result1 = await cache.get_or_set(channel, mock_fetch)
    assert call_count == 1
    assert result1["url"] == "http://example.com/test_fetch"

    result2 = await cache.get_or_set(channel, mock_fetch)
    assert call_count == 1
    assert result2 == result1
