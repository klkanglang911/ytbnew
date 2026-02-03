#!/bin/bash

################################################################################
# YouTube 直播代理服务 - 一键部署脚本
# 支持：Docker Compose + Nginx + Let's Encrypt + 企业微信告警
# 用法：bash deploy.sh [options]
# 选项：
#   --domain <domain>       域名 (如: ytb.example.com)
#   --email <email>         SSL 证书邮箱
#   --webhook <webhook-url> 企业微信 Webhook URL
#   --port <port>          Nginx 端口 (默认: 443)
################################################################################

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="youtube-proxy"
CONTAINER_PREFIX="ytb"
NGINX_CONF_DIR="/etc/nginx/sites-available"
NGINX_SITES_ENABLED="/etc/nginx/sites-enabled"
LETSENCRYPT_DIR="/etc/letsencrypt"
DATA_DIR="/var/lib/${PROJECT_NAME}"
LOG_DIR="/var/log/${PROJECT_NAME}"
BACKUP_DIR="${DATA_DIR}/backups"

# 默认值
DOMAIN=""
EMAIL=""
WEBHOOK_URL=""
NGINX_PORT="443"
SKIP_SSL="false"
SKIP_NGINX="false"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# 显示使用帮助
show_help() {
    echo "使用: bash deploy.sh [options]"
    echo ""
    echo "选项:"
    echo "  --domain <domain>       域名 (必需, 如: ytb.example.com)"
    echo "  --email <email>         SSL 证书邮箱 (必需, 如: admin@example.com)"
    echo "  --webhook <url>         企业微信 Webhook URL (可选)"
    echo "  --port <port>           Nginx 监听端口 (默认: 443)"
    echo "  --skip-ssl              跳过 SSL 配置 (仅 HTTP)"
    echo "  --skip-nginx            跳过 Nginx 配置"
    echo "  --help                  显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  bash deploy.sh --domain ytb.example.com --email admin@example.com --webhook https://qyapi.weixin.qq.com/cgi-bin/..."
}

# 解析命令行参数
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --domain)
                DOMAIN="$2"
                shift 2
                ;;
            --email)
                EMAIL="$2"
                shift 2
                ;;
            --webhook)
                WEBHOOK_URL="$2"
                shift 2
                ;;
            --port)
                NGINX_PORT="$2"
                shift 2
                ;;
            --skip-ssl)
                SKIP_SSL="true"
                shift
                ;;
            --skip-nginx)
                SKIP_NGINX="true"
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 验证参数
validate_arguments() {
    if [[ -z "$DOMAIN" ]]; then
        log_error "必须指定 --domain 参数"
        show_help
        exit 1
    fi

    if [[ -z "$EMAIL" ]]; then
        log_error "必须指定 --email 参数"
        show_help
        exit 1
    fi

    # 验证域名格式
    if ! [[ "$DOMAIN" =~ ^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$ ]]; then
        log_error "无效的域名格式: $DOMAIN"
        exit 1
    fi

    # 验证邮箱格式
    if ! [[ "$EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        log_error "无效的邮箱格式: $EMAIL"
        exit 1
    fi
}

# 检查系统依赖
check_dependencies() {
    log_info "检查系统依赖..."

    local missing_deps=()

    # 检查必需的命令
    for cmd in docker docker-compose curl wget git; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done

    # 检查可选的命令
    if [[ "$SKIP_NGINX" != "true" ]]; then
        if ! command -v nginx &> /dev/null; then
            log_warning "Nginx 未安装，将自动安装"
        fi
        if ! command -v certbot &> /dev/null; then
            log_warning "Certbot 未安装，将自动安装"
        fi
    fi

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "缺少以下依赖: ${missing_deps[*]}"
        log_info "请先执行: sudo apt update && sudo apt install -y ${missing_deps[*]}"
        exit 1
    fi

    log_success "所有依赖已满足"
}

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0  # 端口被占用
    else
        return 1  # 端口未被占用
    fi
}

# 检查端口冲突
check_ports() {
    log_info "检查端口是否被占用..."

    local ports=("80" "443" "8000" "8001" "3000" "3001" "9090" "9091" "9000" "6379")
    local conflicts=()

    for port in "${ports[@]}"; do
        if check_port "$port"; then
            conflicts+=("$port")
        fi
    done

    if [[ ${#conflicts[@]} -gt 0 ]]; then
        log_warning "以下端口已被占用: ${conflicts[*]}"
        log_info "将尝试继续部署，如有问题请调整配置"
    else
        log_success "所有必需端口都未被占用"
    fi
}

# 创建数据目录
create_directories() {
    log_info "创建数据目录..."

    mkdir -p "$DATA_DIR"/{redis,prometheus,grafana}
    mkdir -p "$LOG_DIR"
    mkdir -p "$BACKUP_DIR"

    # 设置权限
    chmod 755 "$DATA_DIR"
    chmod 755 "$LOG_DIR"

    log_success "数据目录已创建: $DATA_DIR"
}

# 备份现有配置
backup_existing() {
    log_info "备份现有配置..."

    if [[ -d "$SCRIPT_DIR/app" ]]; then
        local backup_file="$BACKUP_DIR/app-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
        tar -czf "$backup_file" -C "$SCRIPT_DIR" . --exclude=.git --exclude=.env \
            2>/dev/null || true
        log_success "配置已备份到: $backup_file"
    fi

    if [[ -f "$SCRIPT_DIR/.env" ]]; then
        cp "$SCRIPT_DIR/.env" "$BACKUP_DIR/.env-backup-$(date +%Y%m%d-%H%M%S)"
    fi
}

# 生成 .env 文件
generate_env_file() {
    log_info "生成环境配置文件..."

    local env_file="$SCRIPT_DIR/.env"

    if [[ -f "$env_file" ]]; then
        log_warning ".env 文件已存在，跳过生成"
        return
    fi

    cat > "$env_file" << 'EOF'
# YouTube 代理服务配置

# 应用配置
DEBUG=false
LOG_LEVEL=INFO

# Redis 配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=ytb_secure_password_$(date +%s)
CACHE_TTL=21600

# yt-dlp 配置
YTDLP_TIMEOUT=30
YTDLP_MAX_RETRIES=3
YTDLP_PROXY=

# 并发控制
MAX_CONCURRENT_STREAMS=10
MAX_CONCURRENT_YTDLP_REQUESTS=3
REQUEST_TIMEOUT=30

# 监控配置
ENABLE_METRICS=true
PROMETHEUS_PORT=9000

# Webhook 企业微信告警（可选）
WEBHOOK_URL=
EOF

    # 生成强密码
    local strong_password=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    sed -i "s/ytb_secure_password_\$(date +%s)/$strong_password/" "$env_file"

    # 如果提供了 Webhook URL，则设置
    if [[ -n "$WEBHOOK_URL" ]]; then
        sed -i "s|WEBHOOK_URL=|WEBHOOK_URL=$WEBHOOK_URL|" "$env_file"
    fi

    chmod 600 "$env_file"
    log_success ".env 文件已生成: $env_file"
}

# 安装 Nginx（如果需要）
install_nginx() {
    if [[ "$SKIP_NGINX" == "true" ]]; then
        log_info "跳过 Nginx 安装"
        return
    fi

    log_info "检查/安装 Nginx..."

    if ! command -v nginx &> /dev/null; then
        log_info "正在安装 Nginx..."
        sudo apt-get update
        sudo apt-get install -y nginx
        log_success "Nginx 已安装"
    else
        log_success "Nginx 已安装"
    fi

    sudo systemctl start nginx
    sudo systemctl enable nginx
}

# 安装 Certbot（如果需要）
install_certbot() {
    if [[ "$SKIP_SSL" == "true" ]]; then
        log_info "跳过 SSL 配置"
        return
    fi

    log_info "检查/安装 Certbot..."

    if ! command -v certbot &> /dev/null; then
        log_info "正在安装 Certbot..."
        sudo apt-get update
        sudo apt-get install -y certbot python3-certbot-nginx
        log_success "Certbot 已安装"
    else
        log_success "Certbot 已安装"
    fi
}

# 配置 Nginx 虚拟主机
configure_nginx() {
    if [[ "$SKIP_NGINX" == "true" ]]; then
        log_info "跳过 Nginx 配置"
        return
    fi

    log_info "配置 Nginx 虚拟主机..."

    # 生成 Nginx 配置文件
    local nginx_file="$SCRIPT_DIR/nginx.conf"

    cat > "$nginx_file" << NGINX_EOF
# YouTube 代理服务 - Nginx 虚拟主机配置

upstream youtube_proxy_backend {
    least_conn;
    server app:8000 max_fails=3 fail_timeout=30s;
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS 服务器
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN;

    # SSL 证书配置（Certbot 自动管理）
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 安全响应头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 日志配置
    access_log /var/log/nginx/${DOMAIN}.access.log combined;
    error_log /var/log/nginx/${DOMAIN}.error.log warn;

    # 客户端最大上传大小
    client_max_body_size 100M;

    # 根路由 - API 信息
    location / {
        proxy_pass http://youtube_proxy_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # 健康检查（不记录日志）
    location /health {
        proxy_pass http://youtube_proxy_backend;
        access_log off;
    }

    # M3U 播放列表
    location /api/m3u {
        proxy_pass http://youtube_proxy_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        default_type application/vnd.apple.mpegurl;
    }

    # Prometheus 指标（限制访问）
    location /metrics {
        # 仅允许本机和指定 IP 访问
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        deny all;
        proxy_pass http://youtube_proxy_backend;
    }

    # 静态文件缓存
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://youtube_proxy_backend;
        proxy_cache_valid 200 1d;
        expires 7d;
    }
}
NGINX_EOF

    log_success "Nginx 配置已生成: $nginx_file"
}

# 配置 SSL 证书
configure_ssl() {
    if [[ "$SKIP_SSL" == "true" ]]; then
        log_info "跳过 SSL 证书配置"
        return
    fi

    log_info "配置 SSL 证书..."

    # 检查证书是否已存在
    if [[ -f "$LETSENCRYPT_DIR/live/$DOMAIN/fullchain.pem" ]]; then
        log_success "SSL 证书已存在: $DOMAIN"
        log_info "证书有效期查询: certbot certificates"
        return
    fi

    # 创建临时 Nginx 配置用于验证
    local temp_nginx_file="/etc/nginx/sites-available/$DOMAIN.temp"

    cat > "$temp_nginx_file" << TEMP_NGINX_EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
TEMP_NGINX_EOF

    sudo ln -sf "$temp_nginx_file" "$NGINX_SITES_ENABLED/$DOMAIN.temp" 2>/dev/null || true
    sudo nginx -t && sudo systemctl reload nginx

    log_info "正在申请 SSL 证书（域名验证）..."

    if sudo certbot certonly \
        --nginx \
        -d "$DOMAIN" \
        --email "$EMAIL" \
        --agree-tos \
        --non-interactive \
        --preferred-challenges http \
        --http-01-port 80; then

        log_success "SSL 证书申请成功: $DOMAIN"

        # 配置证书自动更新
        sudo systemctl enable certbot.timer
        sudo systemctl start certbot.timer

        log_success "证书自动更新已启用"
    else
        log_error "SSL 证书申请失败"
        log_warning "请检查域名是否正确解析到此服务器"
        return 1
    fi
}

# 启用 Nginx 虚拟主机
enable_nginx_site() {
    if [[ "$SKIP_NGINX" == "true" ]]; then
        log_info "跳过启用 Nginx 虚拟主机"
        return
    fi

    log_info "启用 Nginx 虚拟主机..."

    local nginx_file="$SCRIPT_DIR/nginx.conf"
    local nginx_target="$NGINX_CONF_DIR/$DOMAIN"

    sudo cp "$nginx_file" "$nginx_target"
    sudo ln -sf "$nginx_target" "$NGINX_SITES_ENABLED/$DOMAIN"

    # 禁用默认站点
    sudo rm -f "$NGINX_SITES_ENABLED/default"

    # 测试配置
    if sudo nginx -t; then
        sudo systemctl reload nginx
        log_success "Nginx 虚拟主机已启用"
    else
        log_error "Nginx 配置验证失败"
        return 1
    fi
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."

    if ! command -v ufw &> /dev/null; then
        log_warning "UFW 未安装，跳过防火墙配置"
        return
    fi

    # 检查 UFW 是否启用
    if ! sudo ufw status | grep -q "Status: active"; then
        log_warning "UFW 未启用，运行以下命令启用:"
        log_warning "  sudo ufw enable"
        return
    fi

    # 允许必需的端口
    sudo ufw allow 22/tcp   # SSH
    sudo ufw allow 80/tcp   # HTTP
    sudo ufw allow 443/tcp  # HTTPS

    log_success "防火墙规则已配置"
}

# 启动 Docker Compose
start_docker_compose() {
    log_info "启动 Docker Compose 服务..."

    cd "$SCRIPT_DIR"

    # 拉取最新镜像
    log_info "拉取 Docker 镜像..."
    docker-compose pull

    # 构建镜像
    log_info "构建 Docker 镜像..."
    docker-compose build

    # 启动容器
    log_info "启动容器..."
    docker-compose up -d

    log_success "Docker Compose 服务已启动"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务启动..."

    local max_attempts=30
    local attempt=0

    while [[ $attempt -lt $max_attempts ]]; do
        if curl -sf http://localhost:8000/health &>/dev/null; then
            log_success "应用服务已就绪"
            return 0
        fi

        log_info "等待应用启动... ($((attempt + 1))/$max_attempts)"
        sleep 2
        ((attempt++))
    done

    log_error "服务启动超时"
    return 1
}

# 验证部署
verify_deployment() {
    log_info "验证部署..."

    local checks_passed=0
    local checks_total=0

    # 检查 Docker 容器
    ((checks_total++))
    if docker-compose ps | grep -q "Up"; then
        log_success "Docker 容器运行正常"
        ((checks_passed++))
    else
        log_error "Docker 容器启动失败"
    fi

    # 检查 API 健康状态
    ((checks_total++))
    if curl -sf http://localhost:8000/health &>/dev/null; then
        log_success "API 服务健康"
        ((checks_passed++))
    else
        log_error "API 服务不健康"
    fi

    # 检查 Redis
    ((checks_total++))
    if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
        log_success "Redis 连接正常"
        ((checks_passed++))
    else
        log_error "Redis 连接失败"
    fi

    # 检查 Nginx (如果已配置)
    if [[ "$SKIP_NGINX" != "true" ]]; then
        ((checks_total++))
        if sudo nginx -t 2>/dev/null; then
            log_success "Nginx 配置正确"
            ((checks_passed++))
        else
            log_error "Nginx 配置有问题"
        fi
    fi

    log_info "验证结果: $checks_passed/$checks_total"

    if [[ $checks_passed -eq $checks_total ]]; then
        return 0
    else
        return 1
    fi
}

# 显示部署总结
show_summary() {
    log_success "═══════════════════════════════════════════════════════"
    log_success "部署完成！"
    log_success "═══════════════════════════════════════════════════════"
    echo ""

    if [[ "$SKIP_NGINX" != "true" ]]; then
        log_success "🌐 API 访问地址"
        echo "   https://$DOMAIN/api/"
        echo ""

        log_success "📊 Grafana 仪表板"
        echo "   https://$DOMAIN:3001/"
        echo "   用户名: admin"
        echo "   密码: admin (请立即修改！)"
        echo ""

        log_success "🔍 Prometheus"
        echo "   https://$DOMAIN:9091/"
        echo ""
    else
        log_success "🌐 API 访问地址"
        echo "   http://localhost:8000/api/"
        echo ""
    fi

    log_success "📋 M3U 播放列表"
    if [[ "$SKIP_NGINX" != "true" ]]; then
        echo "   https://$DOMAIN/api/m3u"
    else
        echo "   http://localhost:8000/api/m3u"
    fi
    echo ""

    log_success "📝 常用命令"
    echo "   # 查看日志"
    echo "   docker-compose logs -f app"
    echo ""
    echo "   # 查看容器状态"
    echo "   docker-compose ps"
    echo ""
    echo "   # 重启服务"
    echo "   docker-compose restart"
    echo ""
    echo "   # 停止服务"
    echo "   docker-compose down"
    echo ""
    echo "   # 查看 SSL 证书状态"
    echo "   sudo certbot certificates"
    echo ""

    if [[ -n "$WEBHOOK_URL" ]]; then
        log_success "🤖 企业微信告警已启用"
        echo "   告警将通过 Webhook 发送至企业微信"
        echo ""
    fi

    log_success "📚 文档"
    echo "   部署指南: DEPLOYMENT-CN.md"
    echo "   故障回滚: bash rollback.sh"
    echo ""

    log_success "═══════════════════════════════════════════════════════"
}

# 主函数
main() {
    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  YouTube 直播代理服务 - 一键部署脚本                   ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""

    # 检查权限
    if [[ $EUID -eq 0 ]]; then
        log_error "请不要使用 sudo 运行此脚本"
        exit 1
    fi

    # 解析参数
    parse_arguments "$@"

    # 验证参数
    validate_arguments

    # 检查依赖
    check_dependencies

    # 检查端口
    check_ports

    # 创建目录
    create_directories

    # 备份现有配置
    backup_existing

    # 生成环境文件
    generate_env_file

    # 安装 Nginx 和 Certbot
    install_nginx
    install_certbot

    # 配置 Nginx
    configure_nginx

    # 配置 SSL
    configure_ssl || log_warning "SSL 配置出现问题，但将继续部署"

    # 启用 Nginx
    enable_nginx_site || log_warning "Nginx 启用失败，但将继续部署"

    # 配置防火墙
    configure_firewall

    # 启动 Docker Compose
    start_docker_compose

    # 等待服务启动
    wait_for_services || log_warning "服务启动可能不完全，请检查日志"

    # 验证部署
    verify_deployment

    # 显示总结
    show_summary

    log_success "部署脚本执行完成！"
}

# 捕获错误
trap 'log_error "脚本执行出错，请查看上面的错误信息"; exit 1' ERR

# 执行主函数
main "$@"
