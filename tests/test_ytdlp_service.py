import pytest
from unittest.mock import patch, MagicMock
from app.services.ytdlp_service import YtdlpService

@pytest.fixture
def ytdlp():
    """创建 yt-dlp 服务实例"""
    with patch('app.services.ytdlp_service.YtdlpService._validate_ytdlp'):
        service = YtdlpService()
        yield service

@pytest.mark.asyncio
async def test_extract_stream_url_success(ytdlp):
    """测试成功提取流地址"""
    mock_response = '''{
        "url": "https://example.com/stream.m3u8",
        "format": "hls",
        "formats": []
    }'''

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_response,
            stderr=""
        )

        result = await ytdlp.extract_stream_url(
            "https://www.youtube.com/channel/test",
            "test_channel"
        )

        assert result is not None
        assert result['url'] == "https://example.com/stream.m3u8"
        assert result['format'] == "hls"

@pytest.mark.asyncio
async def test_extract_stream_url_failure(ytdlp):
    """测试流地址提取失败"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: Video not found"
        )

        result = await ytdlp.extract_stream_url(
            "https://www.youtube.com/invalid",
            "invalid_channel"
        )

        assert result is None

@pytest.mark.asyncio
async def test_extract_stream_url_timeout(ytdlp):
    """测试超时处理"""
    with patch('subprocess.run') as mock_run:
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 30)

        result = await ytdlp.extract_stream_url(
            "https://www.youtube.com/test",
            "timeout_channel"
        )

        assert result is None
