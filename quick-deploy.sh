#!/bin/bash

################################################################################
# YouTube 直播代理 - VPS 快速部署脚本
#
# 使用说明：
# 在 VPS 上运行：
#   bash quick-deploy.sh ytb.yourdomain.com admin@domain.com https://qyapi.weixin.qq.com/...
#
# 或交互式部署（推荐首次使用）：
#   bash quick-deploy.sh
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[*]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# 显示欢迎信息
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════╗"
echo "║      YouTube 直播代理服务 - VPS 快速部署              ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 获取参数或交互式输入
if [ -z "$1" ]; then
    # 交互式模式
    log_info "进入交互式部署模式"
    echo ""

    read -p "请输入域名 (例: ytb.example.com): " DOMAIN
    if [ -z "$DOMAIN" ]; then
        log_error "域名不能为空"
        exit 1
    fi

    read -p "请输入 SSL 证书邮箱 (例: admin@example.com): " EMAIL
    if [ -z "$EMAIL" ]; then
        log_error "邮箱不能为空"
        exit 1
    fi

    read -p "请输入企业微信 Webhook URL (可选，直接回车跳过): " WEBHOOK
else
    # 命令行参数模式
    DOMAIN="$1"
    EMAIL="${2:-}"
    WEBHOOK="${3:-}"

    if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
        log_error "使用方式: bash quick-deploy.sh <domain> <email> [webhook-url]"
        exit 1
    fi
fi

# 显示部署信息
echo ""
log_info "部署配置信息："
echo "  域名: $DOMAIN"
echo "  邮箱: $EMAIL"
echo "  Webhook: ${WEBHOOK:-(未配置)}"
echo ""

# 确认部署
read -p "确认部署？(yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    log_warn "已取消部署"
    exit 0
fi

echo ""
log_info "开始部署..."
echo ""

# Step 1: 更新系统
log_info "Step 1/5: 更新系统..."
sudo apt-get update -qq

# Step 2: 安装 Docker
log_info "Step 2/5: 安装 Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    bash get-docker.sh >/dev/null 2>&1
    sudo usermod -aG docker $USER
    log_success "Docker 已安装"
else
    log_success "Docker 已存在"
fi

# Step 3: 安装 Docker Compose
log_info "Step 3/5: 安装 Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    log_success "Docker Compose 已安装"
else
    log_success "Docker Compose 已存在"
fi

# Step 4: 克隆项目
log_info "Step 4/5: 克隆项目..."
if [ ! -d "youtube-proxy" ]; then
    git clone https://github.com/klkanglang911/ytbnew.git youtube-proxy
    cd youtube-proxy
else
    cd youtube-proxy
    git pull origin main
fi
log_success "项目已准备就绪"

# Step 5: 执行一键部署脚本
log_info "Step 5/5: 执行部署脚本..."
echo ""

if [ -z "$WEBHOOK" ]; then
    bash deploy.sh --domain "$DOMAIN" --email "$EMAIL"
else
    bash deploy.sh --domain "$DOMAIN" --email "$EMAIL" --webhook "$WEBHOOK"
fi

echo ""
log_success "═══════════════════════════════════════════════════════"
log_success "部署完成！"
log_success "═══════════════════════════════════════════════════════"
echo ""

log_info "访问服务："
echo "  🌐 API: https://$DOMAIN/api/"
echo "  📊 Grafana: https://$DOMAIN:3001/"
echo "  🔍 Prometheus: https://$DOMAIN:9091/"
echo "  📺 M3U 播放列表: https://$DOMAIN/api/m3u"
echo ""

log_info "后续步骤："
echo "  1. 在 VLC 中导入 M3U: https://$DOMAIN/api/m3u"
echo "  2. 修改 Grafana 密码: 访问 https://$DOMAIN:3001/ 并登录"
echo "  3. 查看日志: docker-compose logs -f app"
echo ""

log_info "需要帮助？"
echo "  📚 完整部署指南: DEPLOYMENT-CN.md"
echo "  🆘 故障排查: bash rollback.sh"
echo "  📧 联系方式: klkanglang@gmail.com"
echo ""
