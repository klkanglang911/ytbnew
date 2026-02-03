#!/bin/bash
# 🚀 YouTube 直播代理 - 终极推送指南

echo "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓"
echo "┃  YouTube 代理服务 - 推送到 GitHub                  ┃"
echo "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
echo ""

# ============================================================
# 最简单的方案：使用 GitHub 命令行工具（如果已安装）
# ============================================================

if command -v gh &> /dev/null; then
    echo "✅ 检测到 GitHub CLI，使用最简单的推送方法"
    echo ""
    echo "运行以下命令推送:"
    echo ""
    echo "  cd D:\\WORK\\AI_WORK\\ytb_new"
    echo "  gh repo clone klkanglang911/ytbnew . --force"
    echo "  git push -u origin main"
    echo ""
    exit 0
fi

# ============================================================
# 备选方案：纯 Git 推送（需要认证）
# ============================================================

echo "📋 方案 1: 使用 Personal Access Token（最简单）"
echo ""
echo "Step 1: 生成 GitHub Token"
echo "  1. 访问 https://github.com/settings/tokens"
echo "  2. 点击 'Generate new token'"
echo "  3. 勾选 'repo' 权限"
echo "  4. 复制 Token"
echo ""
echo "Step 2: 设置推送凭证"
echo "  在 Windows PowerShell 或 Git Bash 中运行:"
echo ""
echo "  cd D:\\WORK\\AI_WORK\\ytb_new"
echo ""
echo "  # 替换 YOUR_TOKEN 为你的实际 Token"
echo "  git remote set-url origin https://klkanglang911:YOUR_TOKEN@github.com/klkanglang911/ytbnew.git"
echo ""
echo "Step 3: 推送代码"
echo "  git push -u origin main"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 方案 2: 使用 SSH（如果已配置）"
echo ""
echo "  cd D:\\WORK\\AI_WORK\\ytb_new"
echo "  git remote set-url origin git@github.com:klkanglang911/ytbnew.git"
echo "  git push -u origin main"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 方案 3: 一行命令推送（最快）"
echo ""
echo "  cd D:\\WORK\\AI_WORK\\ytb_new && git push -u origin main"
echo ""
echo "如果提示需要认证，请使用方案 1 配置 Token"
echo ""
