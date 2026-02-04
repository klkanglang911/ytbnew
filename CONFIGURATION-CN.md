# YouTube 直播代理服务 - 完整配置指南

## 🎯 当前状态

✅ **已完成**：
- Docker 容器全部启动（FastAPI、Redis、Prometheus、Grafana、AlertManager）
- 应用健康检查通过
- 基础频道配置已存在

## 📋 还需配置的步骤

### 1️⃣ HTTPS/SSL 配置（10分钟）

在 VPS 上执行：
```bash
cd /opt/ytbnew
chmod +x deploy-https.sh
sudo ./deploy-https.sh
```

这会：
- 安装 Certbot 和 Nginx
- 自动申请 Let's Encrypt 证书
- 配置 HTTPS 反向代理

### 2️⃣ 配置 Nginx 容器

编辑 docker-compose.yml，添加 Nginx 服务（我会为你准备）

### 3️⃣ 配置 WeChat 企业告警

已配置 Webhook URL：
```
https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=444ce8c7-2978-4ed6-89d3-4dfc2032eea9
```

告警级别：
- 🔴 **Critical**（关键）：立即发送，1小时重复
- 🟠 **Warning**（警告）：30秒后发送，4小时重复
- 🟡 **Info**（信息）：5分钟后发送，12小时重复

### 4️⃣ 监控仪表板

**Prometheus** (http://你的IP:9090)：
- 查看原始指标

**Grafana** (http://你的IP:3000)：
- 用户名: admin
- 密码: admin
- 需要导入 Prometheus 数据源和仪表板

### 5️⃣ YouTube 频道

当前配置的频道：
- ✅ 三立新闻 (https://www.youtube.com/@setn/live)
- ✅ 民视新闻 (https://www.youtube.com/@ftv/live)
- ✅ BBC News (https://www.youtube.com/@BBCNews/live)

或从 M3U 导入：
```
https://raw.githubusercontent.com/zzq1234567890/epg/refs/heads/main/youtube.m3u
```

## 🔗 访问地址（配置完成后）

| 服务 | 地址 | 说明 |
|------|------|------|
| **M3U 播放列表** | https://ytb.982788.xyz/playlist.m3u | VLC 直接导入 |
| **API 文档** | https://ytb.982788.xyz/docs | 查看 API 端点 |
| **Prometheus** | http://IP:9090 | 监控指标 |
| **Grafana** | http://IP:3000 | 仪表板可视化 |
| **AlertManager** | http://IP:9093 | 告警管理 |

## 🚀 快速开始

### 在 VLC 中导入 M3U：
1. 打开 VLC
2. 菜单 → 媒体 → 打开网络串流
3. 输入：`https://ytb.982788.xyz/playlist.m3u`
4. 选择要看的频道

### 监控告警：
1. 访问 https://ytb.982788.xyz/docs 测试 API
2. 查看 Prometheus 指标
3. WeChat 企业号会自动接收告警

## ⚙️ 环境变量

所有配置都在 `.env` 文件中：

```env
# Redis
REDIS_HOST=redis
REDIS_PASSWORD=password

# 应用
LOG_LEVEL=INFO
LOG_FORMAT=text
CACHE_TTL=21600      # 缓存6小时

# 并发
MAX_CONCURRENT_STREAMS=10
MAX_CONCURRENT_YTDLP_REQUESTS=3

# WeChat 告警
WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=...
```

## 🔧 故障排查

### 检查应用状态：
```bash
docker-compose ps
docker-compose logs app
```

### 检查 Nginx 状态：
```bash
sudo systemctl status nginx
sudo nginx -t  # 测试配置
```

### 检查 SSL 证书：
```bash
certbot certificates
```

### 重启服务：
```bash
docker-compose restart app
sudo systemctl restart nginx
```

## 📞 技术支持

- API 文档：https://ytb.982788.xyz/docs
- 健康检查：https://ytb.982788.xyz/health
- 错误日志：`docker-compose logs`

