# YouTube 直播代理服务

为中国大陆 VLC 播放器提供 YouTube 直播源代理，支持最多 10 个并发直播流。

## 核心特性

✨ **功能**
- YouTube 直播流解析和代理
- 6 小时流地址缓存机制
- 自动故障恢复和降级
- 支持 M3U 播放列表格式
- 分布式锁防止并发重复解析

📊 **监控**
- Prometheus 指标收集
- Grafana 实时仪表板
- AlertManager 告警系统
- 健康检查端点

🚀 **部署**
- Docker Compose 一键启动
- 自动故障重启
- 热更新支持

## 快速开始

### 前置要求
- Docker & Docker Compose
- 美国 VPS (2 CPU, 2.5GB RAM, 1Gbps)

### 部署步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/klkanglang911/ytbnew.git
   cd ytbnew
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   ```

3. **执行一键部署**
   ```bash
   bash deploy.sh \
     --domain ytb.yourdomain.com \
     --email admin@yourdomain.com \
     --webhook "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR-KEY"
   ```

4. **验证运行**
   ```bash
   curl https://ytb.yourdomain.com/health
   ```

## VLC 使用方法

### 导入 M3U 播放列表
1. VLC 菜单：媒体 → 打开网络流
2. 粘贴 URL：`https://ytb.yourdomain.com/api/m3u`
3. 点击播放

### 手动添加直播源
```
https://ytb.yourdomain.com/api/stream/三立新闻
```

## API 端点

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/api/channels` | 频道列表 |
| GET | `/api/stream/{name}` | 获取直播流 |
| GET | `/api/m3u` | M3U 播放列表 |
| POST | `/api/cache/invalidate/{name}` | 清除缓存 |

## 监控和告警

### Grafana 仪表板
- 访问：`https://ytb.yourdomain.com:3001/`
- 默认：admin / admin

### Prometheus
- 访问：`https://ytb.yourdomain.com:9091/`

### 企业微信告警
- 自动推送关键告警至企业微信群组

## 故障排查

### 查看日志
```bash
docker-compose logs -f app
```

### 重启服务
```bash
docker-compose restart app
```

### 更新 yt-dlp
```bash
docker-compose exec app pip install --upgrade yt-dlp
docker-compose restart app
```

### 故障回滚
```bash
bash rollback.sh --latest
```

## 常用命令

```bash
# 查看容器状态
docker-compose ps

# 查看实时日志
docker-compose logs -f app

# 重启所有服务
docker-compose restart

# 停止服务
docker-compose down

# 启动服务
docker-compose up -d
```

## 配置说明

详见 `DEPLOYMENT-CN.md`

## 许可证

MIT License

## 联系方式

- GitHub: https://github.com/klkanglang911/ytbnew
- 邮件: klkanglang@gmail.com
