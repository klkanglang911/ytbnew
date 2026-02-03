import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta
from app.services.stream_resolver import StreamResolverService

@pytest.fixture
def resolver():
    """创建流解析服务实例"""
    return StreamResolverService()

@pytest.mark.asyncio
async def test_get_stream_url_success(resolver):
    """测试成功获取流地址"""
    with patch('app.services.stream_resolver.ytdlp_service.extract_stream_url') as mock_ytdlp:
        mock_ytdlp.return_value = {
            'url': 'https://example.com/stream.m3u8',
            'format': 'hls',
            'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }

        with patch('app.services.stream_resolver.cache_service.acquire_lock', return_value=True):
            with patch('app.services.stream_resolver.cache_service.release_lock', return_value=True):
                with patch('app.services.stream_resolver.cache_service.get_stream_url', return_value=None):
                    with patch('app.services.stream_resolver.cache_service.set_stream_url', return_value=True):
                        result = await resolver.get_stream_url(
                            'https://youtube.com/test',
                            'test_channel'
                        )

                        assert result == 'https://example.com/stream.m3u8'

@pytest.mark.asyncio
async def test_get_stream_url_cache_hit(resolver):
    """测试缓存命中"""
    cached_data = {
        'url': 'https://cached.com/stream.m3u8',
        'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat()
    }

    with patch('app.services.stream_resolver.cache_service.get_stream_url', return_value=cached_data):
        result = await resolver.get_stream_url(
            'https://youtube.com/test',
            'test_channel',
            use_cache=True
        )

        assert result == 'https://cached.com/stream.m3u8'

@pytest.mark.asyncio
async def test_is_expired(resolver):
    """测试过期检查"""
    future = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    assert resolver._is_expired({'expires_at': future}) is False

    past = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    assert resolver._is_expired({'expires_at': past}) is True
