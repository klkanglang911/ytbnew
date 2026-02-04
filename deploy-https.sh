#!/bin/bash

# HTTPS 部署脚本 for YouTube 代理服务
# 使用 Let's Encrypt 和 Certbot

set -e

DOMAIN="ytb.982788.xyz"
EMAIL="klkanglang@gmail.com"
DOCKER_DIR="/opt/ytbnew"

echo "=========================================="
echo "YouTube 代理服务 HTTPS 部署脚本"
echo "=========================================="
echo "域名: $DOMAIN"
echo ""

# 1. 检查 Certbot 和 Nginx
echo "[1/4] 检查依赖..."
if ! command -v certbot &> /dev/null; then
    echo "❌ Certbot 未安装，正在安装..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
fi

if ! command -v nginx &> /dev/null; then
    echo "❌ Nginx 未安装，正在安装..."
    apt-get install -y nginx
fi
echo "✅ 依赖检查完毕"

# 2. 创建必要的目录
echo "[2/4] 创建证书目录..."
mkdir -p $DOCKER_DIR/certbot/conf
mkdir -p $DOCKER_DIR/certbot/www
mkdir -p $DOCKER_DIR/nginx/logs
echo "✅ 目录创建完毕"

# 3. 获取 SSL 证书
echo "[3/4] 申请 SSL 证书..."
if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    certbot certonly --standalone \
        -d $DOMAIN \
        --email $EMAIL \
        --agree-tos \
        --non-interactive
    echo "✅ SSL 证书申请成功"
else
    echo "ℹ️  SSL 证书已存在"
    certbot renew --quiet
    echo "✅ SSL 证书已更新"
fi

# 4. 复制证书到 Docker 目录
echo "[4/4] 配置 Docker 环境..."
sudo cp -r /etc/letsencrypt/live/$DOMAIN $DOCKER_DIR/certbot/conf/ 2>/dev/null || true
sudo cp -r /etc/letsencrypt/archive $DOCKER_DIR/certbot/conf/ 2>/dev/null || true
sudo chown -R $(whoami):$(whoami) $DOCKER_DIR/certbot/conf/ 2>/dev/null || true

echo ""
echo "=========================================="
echo "✅ HTTPS 部署完成！"
echo "=========================================="
echo ""
echo "证书位置: /etc/letsencrypt/live/$DOMAIN"
echo "证书更新: certbot renew"
echo ""
echo "访问地址:"
echo "  - HTTPS: https://$DOMAIN"
echo "  - API 文档: https://$DOMAIN/docs"
echo "  - M3U 列表: https://$DOMAIN/playlist.m3u"
echo ""
echo "💡 提示："
echo "  1. 确保端口 80 和 443 对外开放"
echo "  2. 确保 DNS A 记录指向此服务器"
echo "  3. 运行 docker-compose up -d 启动服务"
echo ""
