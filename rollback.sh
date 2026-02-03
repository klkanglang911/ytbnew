#!/bin/bash

################################################################################
# YouTube 直播代理服务 - 故障回滚脚本
# 用途：快速回滚到上一个正常版本
# 用法：bash rollback.sh
################################################################################

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="/var/log/youtube-proxy/backups"
DATA_DIR="/var/lib/youtube-proxy"

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

show_help() {
    echo "使用: bash rollback.sh [option]"
    echo ""
    echo "选项:"
    echo "  --list                 列出可用的备份"
    echo "  --backup-file <file>   从指定的备份文件回滚"
    echo "  --latest               回滚到最新备份（默认）"
    echo "  --help                 显示此帮助信息"
}

# 列出可用备份
list_backups() {
    log_info "可用的备份文件："
    echo ""

    if [[ ! -d "$BACKUP_DIR" ]]; then
        log_error "备份目录不存在: $BACKUP_DIR"
        exit 1
    fi

    local backups=($(ls -t "$BACKUP_DIR"/app-backup-*.tar.gz 2>/dev/null || true))

    if [[ ${#backups[@]} -eq 0 ]]; then
        log_error "没有找到备份文件"
        exit 1
    fi

    for i in "${!backups[@]}"; do
        local backup_file="${backups[$i]}"
        local backup_name=$(basename "$backup_file")
        local backup_size=$(du -h "$backup_file" | cut -f1)
        local backup_date=$(stat -c %y "$backup_file" 2>/dev/null | cut -d' ' -f1-2 || stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$backup_file")

        printf "%2d) %s (%s) - %s\n" "$((i + 1))" "$backup_name" "$backup_size" "$backup_date"
    done

    echo ""
}

# 执行回滚
perform_rollback() {
    local backup_file="$1"

    if [[ ! -f "$backup_file" ]]; then
        log_error "备份文件不存在: $backup_file"
        exit 1
    fi

    log_warning "准备回滚到: $(basename $backup_file)"
    echo ""
    read -p "是否确认回滚？(yes/no): " confirm

    if [[ "$confirm" != "yes" ]]; then
        log_info "已取消回滚"
        exit 0
    fi

    log_info "停止 Docker Compose 服务..."
    cd "$SCRIPT_DIR"
    docker-compose down || log_warning "停止服务时出错"

    log_info "正在恢复配置..."
    tar -xzf "$backup_file" -C "$SCRIPT_DIR" \
        --exclude=.git \
        --exclude=.env \
        --exclude=logs

    log_success "配置已恢复"

    log_info "重新启动服务..."
    docker-compose pull
    docker-compose up -d

    log_info "等待服务启动..."
    sleep 10

    if curl -sf http://localhost:8000/health &>/dev/null; then
        log_success "服务已恢复正常"
        log_info "回滚完成！"
    else
        log_error "服务启动失败，请检查日志:"
        docker-compose logs app | tail -50
        exit 1
    fi
}

# 主函数
main() {
    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  YouTube 代理服务 - 故障回滚脚本                       ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""

    # 检查权限
    if [[ $EUID -eq 0 ]]; then
        log_error "请不要使用 sudo 运行此脚本"
        exit 1
    fi

    case "${1:-}" in
        --list)
            list_backups
            ;;
        --backup-file)
            if [[ -z "${2:-}" ]]; then
                log_error "必须指定备份文件"
                show_help
                exit 1
            fi
            perform_rollback "$2"
            ;;
        --latest)
            list_backups
            local latest_backup=$(ls -t "$BACKUP_DIR"/app-backup-*.tar.gz 2>/dev/null | head -1)
            if [[ -z "$latest_backup" ]]; then
                log_error "没有找到备份文件"
                exit 1
            fi
            perform_rollback "$latest_backup"
            ;;
        --help)
            show_help
            ;;
        *)
            list_backups
            echo "请选择备份文件编号 (1-${#backups[@]}), 或使用 --help 查看选项:"
            read -p "输入编号: " choice

            if ! [[ "$choice" =~ ^[0-9]+$ ]] || [[ $choice -lt 1 ]] || [[ $choice -gt ${#backups[@]} ]]; then
                log_error "无效的选择"
                exit 1
            fi

            local selected_backup="${backups[$((choice - 1))]}"
            perform_rollback "$selected_backup"
            ;;
    esac
}

# 执行
main "$@"
