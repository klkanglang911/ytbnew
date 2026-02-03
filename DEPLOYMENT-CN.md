# YouTube 直播代理服务 - VPS 部署指南（企业微信告警）

## 📋 前置要求

- **VPS 环境**：Ubuntu 20.04+ / CentOS 7+
- **硬件配置**：2 CPU、2.5GB RAM、10GB+ 存储、1Gbps 带宽
- **域名**：已购买并解析到 VPS IP
- **企业微信**：已创建群组和自定义机器人（用于告警推送）

## 🚀 快速开始

### 1. 连接到 VPS

```bash
ssh user@your-vps-ip
# 或使用密钥
ssh -i /path/to/key.pem user@your-vps-ip
```

### 2. 克隆项目

```bash
git clone https://github.com/klkanglang911/ytbnew.git
cd ytbnew
```

### 3. 执行一键部署脚本

```bash
bash deploy.sh \
  --domain ytb.example.com \
  --email admin@example.com \
  --webhook https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-webhook-key
```

**参数说明：**

| 参数 | 说明 | 示例 |
|------|------|------|
| `--domain` | 你的域名（必需） | `ytb.example.com` |
| `--email` | SSL 证书邮箱（必需） | `admin@example.com` |
| `--webhook` | 企业微信 Webhook URL（可选） | `https://qyapi.weixin.qq.com/...` |
| `--port` | Nginx 监听端口（默认 443） | `443` |
| `--skip-ssl` | 跳过 SSL 配置 | 仅 HTTP 测试 |
| `--skip-nginx` | 跳过 Nginx 配置 | 直接访问 `localhost:8000` |

### 4. 验证部署

```bash
# 检查服务状态
docker-compose ps

# 查看应用日志
docker-compose logs -f app

# 测试 API
curl https://ytb.example.com/health
```

---

## 🤖 企业微信告警配置

### A. 创建企业微信群机器人

1. **打开企业微信**
   - 群聊 → 选择目标群 → 群设置 → 群机器人 → 添加

2. **创建自定义机器人**
   - 名称：YouTube Proxy Alert
   - 复制 Webhook URL

### B. 获取 Webhook URL

企业微信机器人 Webhook URL 格式：

```
https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### C. 部署时配置

在 `deploy.sh` 中使用 `--webhook` 参数：

```bash
bash deploy.sh \
  --domain ytb.example.com \
  --email admin@example.com \
  --webhook "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-key"
```

### D. 测试告警

脚本部署完成后，可以手动触发告警测试：

```bash
# 停止应用容器（触发 "服务不可用" 告警）
docker-compose stop app

# 等待 2 分钟左右，应该收到企业微信告警消息

# 恢复服务
docker-compose start app
```

---

## 📊 访问各个服务

### API 服务

```
https://ytb.example.com/api/
```

**常用端点：**

| 端点 | 说明 |
|------|------|
| `GET /health` | 健康检查 |
| `GET /api/channels` | 频道列表 |
| `GET /api/stream/{name}` | 获取流地址 |
| `GET /api/m3u` | M3U 播放列表 |

### Grafana 仪表板

```
https://ytb.example.com:3001/
```

- **默认用户名**：admin
- **默认密码**：admin

**⚠️ 重要：首次登录后立即修改密码！**

### Prometheus

```
https://ytb.example.com:9091/
```

可视化查看所有监控指标和告警状态。

---

## 🔧 日常维护

### 查看日志

```bash
# 应用日志
docker-compose logs -f app

# Redis 日志
docker-compose logs -f redis

# Prometheus 日志
docker-compose logs -f prometheus

# Grafana 日志
docker-compose logs -f grafana

# Nginx 日志（如已配置）
sudo tail -f /var/log/nginx/ytb.example.com.access.log
sudo tail -f /var/log/nginx/ytb.example.com.error.log
```

### 更新 yt-dlp

当 YouTube 更新导致流解析失败时，需要更新 yt-dlp：

```bash
# 方法 1：更新容器镜像
cd ~/ytbnew
docker-compose build --no-cache app
docker-compose up -d app

# 方法 2：容器内直接更新
docker-compose exec app pip install --upgrade yt-dlp

# 验证更新
docker-compose exec app yt-dlp --version
```

### 清理缓存

```bash
# 清除所有缓存
docker-compose exec redis redis-cli FLUSHDB

# 清除特定频道缓存
curl -X POST https://ytb.example.com/api/cache/invalidate/三立新闻
```

### 备份数据

```bash
# 备份 Redis 数据库
mkdir -p ~/backups
docker-compose exec redis redis-cli BGSAVE
docker cp ytb_redis:/data/dump.rdb ~/backups/redis-$(date +%Y%m%d-%H%M%S).rdb

# 备份配置文件
cp ~/.env ~/backups/.env-$(date +%Y%m%d-%H%M%S)
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart app
docker-compose restart redis
docker-compose restart prometheus

# 完全关闭并重新启动
docker-compose down
docker-compose up -d
```

---

## ⚠️ 故障排查

### API 服务无法访问

**症状**：访问 `https://ytb.example.com/` 返回 502 Bad Gateway

**排查步骤**：

```bash
# 1. 检查容器是否运行
docker-compose ps

# 2. 查看应用日志
docker-compose logs app | tail -50

# 3. 检查健康状态
curl http://localhost:8000/health

# 4. 检查 Nginx 配置
sudo nginx -t

# 5. 查看 Nginx 错误日志
sudo tail -f /var/log/nginx/ytb.example.com.error.log
```

**解决方案**：

```bash
# 重启应用
docker-compose restart app

# 如果问题持续，查看完整日志
docker-compose logs app --tail=100

# 最后的手段：重新部署
docker-compose down
docker-compose up -d
```

### 流解析失败

**症状**：获取频道直播流时返回 503 错误

**排查步骤**：

```bash
# 1. 检查 yt-dlp 是否可用
docker-compose exec app yt-dlp --version

# 2. 手动测试解析
docker-compose exec app yt-dlp -j "https://www.youtube.com/@setn/live"

# 3. 查看应用日志中的错误
docker-compose logs app | grep -i "error\|fail"
```

**解决方案**：

```bash
# YouTube 经常更新，需要更新 yt-dlp
docker-compose exec app pip install --upgrade yt-dlp

# 或重新构建镜像
docker-compose build --no-cache app
docker-compose up -d app
```

### Redis 连接失败

**症状**：应用启动时显示 Redis 连接错误

**排查步骤**：

```bash
# 1. 检查 Redis 容器状态
docker-compose ps redis

# 2. 测试 Redis 连接
docker-compose exec redis redis-cli ping

# 3. 查看 Redis 日志
docker-compose logs redis
```

**解决方案**：

```bash
# 重启 Redis
docker-compose restart redis

# 如果问题持续，删除数据并重新初始化
docker-compose down
rm -rf /var/lib/youtube-proxy/redis/*
docker-compose up -d
```

### 证书相关问题

**症状**：HTTPS 访问返回证书错误

**排查步骤**：

```bash
# 检查证书状态
sudo certbot certificates

# 查看证书详情
sudo openssl x509 -in /etc/letsencrypt/live/ytb.example.com/fullchain.pem -text -noout

# 查看证书过期时间
sudo openssl x509 -in /etc/letsencrypt/live/ytb.example.com/fullchain.pem -enddate -noout
```

**解决方案**：

```bash
# 手动续期证书
sudo certbot renew --force-renewal

# 自动续期（应该已启用）
sudo systemctl status certbot.timer

# 如果自动续期失败，查看日志
sudo journalctl -u certbot.service --no-pager
```

### 企业微信告警未收到

**排查步骤**：

```bash
# 1. 检查 AlertManager 容器是否运行
docker-compose ps | grep alertmanager

# 2. 查看 AlertManager 日志
docker-compose logs alertmanager

# 3. 测试 Webhook URL 连接
curl -X POST "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-key" \
  -H 'Content-Type: application/json' \
  -d '{
    "msgtype": "text",
    "text": {
      "content": "Test message from YouTube Proxy Service"
    }
  }'
```

**解决方案**：

```bash
# 1. 重新检查 Webhook URL 是否正确
# 企业微信群聊 → 群设置 → 群机器人 → 复制 Webhook URL

# 2. 重启 AlertManager
docker-compose restart alertmanager

# 3. 验证告警规则是否正确
curl http://localhost:9090/api/v1/rules

# 4. 查看告警状态
curl http://localhost:9090/api/v1/alerts
```

---

## 🛡️ 安全建议

### 1. 修改 Grafana 密码

```bash
# 首次登录后立即修改
# Grafana UI → 设置 → 用户 → 修改密码

# 或通过 API 修改
curl -X PUT "http://admin:admin@localhost:3000/api/user/password" \
  -H "Content-Type: application/json" \
  -d '{
    "oldPassword": "admin",
    "newPassword": "your-new-password"
  }'
```

### 2. 配置防火墙

```bash
# 允许必需的端口
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS

# 限制 Prometheus 访问（仅内网）
sudo ufw allow from 10.0.0.0/8 to any port 9091

# 启用防火墙
sudo ufw enable
```

### 3. 定期备份

```bash
# 每日自动备份脚本
cat > /usr/local/bin/backup-youtube-proxy.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/user/backups/youtube-proxy"
mkdir -p "$BACKUP_DIR"

# 备份 Redis
docker-compose -f /home/user/ytbnew/docker-compose.yml exec -T redis redis-cli BGSAVE
docker cp ytb_redis:/data/dump.rdb "$BACKUP_DIR/redis-$(date +%Y%m%d).rdb"

# 备份配置
cp /home/user/ytbnew/.env "$BACKUP_DIR/.env-$(date +%Y%m%d)"

# 保留最近 30 天的备份
find "$BACKUP_DIR" -type f -mtime +30 -delete
EOF

chmod +x /usr/local/bin/backup-youtube-proxy.sh

# 添加到 crontab
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup-youtube-proxy.sh") | crontab -
```

### 4. 监控服务器资源

```bash
# 查看实时资源使用
docker stats

# 设置资源限制（在 docker-compose.yml 中）
# 示例已在文件中包含
```

---

## 📞 故障回滚

如果部署出现问题，可以快速回滚到上一个正常版本：

```bash
# 列出可用的备份
bash rollback.sh --list

# 回滚到最新备份
bash rollback.sh --latest

# 回滚到指定备份
bash rollback.sh --backup-file /var/lib/youtube-proxy/backups/app-backup-20260203-120000.tar.gz
```

---

## 📈 性能优化

### 1. Redis 内存优化

```bash
# 查看 Redis 内存使用
docker-compose exec redis redis-cli INFO memory

# 设置最大内存
docker-compose exec redis redis-cli CONFIG SET maxmemory 512mb
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### 2. 缓存策略优化

编辑 `.env`：

```bash
# 增加缓存时间（但要注意 URL 过期）
CACHE_TTL=86400  # 24 小时

# 或减少，如果命中率低
CACHE_TTL=3600   # 1 小时
```

### 3. 并发控制优化

```bash
# 编辑 .env
MAX_CONCURRENT_YTDLP_REQUESTS=5  # 增加并发数

# 重启应用
docker-compose restart app
```

---

## 📚 常用命令速查

| 命令 | 说明 |
|------|------|
| `docker-compose ps` | 查看容器状态 |
| `docker-compose logs -f app` | 实时查看应用日志 |
| `docker-compose restart` | 重启所有服务 |
| `docker-compose down` | 停止所有服务 |
| `docker-compose up -d` | 启动所有服务 |
| `docker-compose exec app bash` | 进入应用容器 |
| `curl https://ytb.example.com/health` | 检查健康状态 |
| `bash rollback.sh` | 故障回滚 |

---

## 🆘 获取帮助

- **GitHub Issues**：https://github.com/klkanglang911/ytbnew/issues
- **邮件**：klkanglang@gmail.com
- **文档**：本目录的 `README.md` 和 `DEPLOYMENT-CN.md`

---

## 📝 更新日志

**v1.0.0** (2026-02-03)
- ✨ 初始版本
- ✅ 支持 Docker Compose 部署
- ✅ 集成 Nginx + Let's Encrypt
- ✅ 企业微信告警推送
- ✅ Prometheus + Grafana 监控
- ✅ 一键部署和回滚脚本
