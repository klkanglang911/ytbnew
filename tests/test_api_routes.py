import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """测试健康检查"""
    response = client.get("/health")
    assert response.status_code in [200, 503]

def test_list_channels():
    """测试频道列表"""
    response = client.get("/api/channels")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_m3u_playlist():
    """测试 M3U 播放列表"""
    response = client.get("/api/m3u")
    assert response.status_code in [200, 503]

def test_root_endpoint():
    """测试根端点"""
    response = client.get("/api/")
    assert response.status_code == 200
    assert "endpoints" in response.json()
