#!/bin/bash
# 最简单的 GitHub 推送脚本
# 用法：在你的本地机器上运行此脚本

set -e

echo "🚀 YouTube 直播代理 - GitHub 一键推送"
echo ""

# 进入项目目录
cd "D:\WORK\AI_WORK\ytb_new" 2>/dev/null || cd "/mnt/d/WORK/AI_WORK/ytb_new" 2>/dev/null || {
    echo "❌ 找不到项目目录"
    echo "请确保项目在: D:\WORK\AI_WORK\ytb_new"
    exit 1
}

echo "✓ 项目目录: $(pwd)"
echo ""

# 检查 Git
if ! command -v git &> /dev/null; then
    echo "❌ Git 未安装"
    exit 1
fi

echo "✓ Git 版本: $(git --version)"
echo ""

# 显示待推送提交
echo "📋 待推送提交:"
git log origin/main..main --oneline 2>/dev/null | head -10 || echo "  (可能所有提交已推送或远程不存在)"
echo ""

# 推送
echo "🔄 正在推送代码到 GitHub..."
echo "   远程: $(git remote get-url origin)"
echo ""

if git push -u origin main 2>&1; then
    echo ""
    echo "✅ 推送成功！"
    echo ""
    echo "📍 项目地址: https://github.com/klkanglang911/ytbnew"
    echo ""
    echo "✨ 后续步骤:"
    echo "   1. VPS 上执行: git clone https://github.com/klkanglang911/ytbnew.git"
    echo "   2. 运行: bash quick-deploy.sh"
    echo ""
else
    echo ""
    echo "⚠️  推送遇到问题"
    echo ""
    echo "💡 可能需要认证，请使用以下方式:"
    echo ""
    echo "方式 1: 使用 Personal Access Token"
    echo "  1. 访问 https://github.com/settings/tokens"
    echo "  2. 创建新 token（勾选 repo 权限）"
    echo "  3. 运行命令:"
    echo "     git remote set-url origin https://YOUR_USERNAME:YOUR_TOKEN@github.com/klkanglang911/ytbnew.git"
    echo "  4. 重新运行推送:"
    echo "     git push -u origin main"
    echo ""
    echo "方式 2: 使用 SSH"
    echo "  1. 配置 SSH 密钥: ssh-keygen -t ed25519"
    echo "  2. 添加公钥到 GitHub: https://github.com/settings/keys"
    echo "  3. 切换到 SSH 地址:"
    echo "     git remote set-url origin git@github.com:klkanglang911/ytbnew.git"
    echo "  4. 重新推送:"
    echo "     git push -u origin main"
    exit 1
fi
