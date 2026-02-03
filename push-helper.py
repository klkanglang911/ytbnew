#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube 直播代理 - GitHub 推送助手
通过此脚本可以快速推送代码到 GitHub
"""

import subprocess
import sys
import os

def run_command(cmd, description=""):
    """执行命令"""
    if description:
        print(f"[*] {description}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            print(f"[✗] 命令失败: {result.stderr}")
            return False
        if result.stdout:
            print(result.stdout.strip())
        return True
    except subprocess.TimeoutExpired:
        print(f"[✗] 命令超时")
        return False
    except Exception as e:
        print(f"[✗] 错误: {e}")
        return False

def main():
    print("╔═══════════════════════════════════════════════════════╗")
    print("║   YouTube 代理服务 - GitHub 推送助手                  ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print()

    # 检查项目目录
    project_dir = r"D:\WORK\AI_WORK\ytb_new"
    if not os.path.exists(project_dir):
        project_dir = "/mnt/d/WORK/AI_WORK/ytb_new"

    if not os.path.exists(project_dir):
        print("[✗] 找不到项目目录")
        sys.exit(1)

    os.chdir(project_dir)
    print(f"[✓] 项目目录: {project_dir}")
    print()

    # 检查 Git
    print("[*] 检查 Git...")
    if not run_command("git --version", ""):
        print("[✗] Git 未安装")
        sys.exit(1)

    # 检查远程
    print()
    print("[*] 远程仓库配置:")
    run_command("git remote -v", "")

    # 显示待推送提交
    print()
    print("[*] 待推送提交:")
    run_command("git log origin/main..main --oneline 2>/dev/null || echo '  (无新提交或远程不存在)'", "")

    # 推送
    print()
    confirm = input("[?] 确认推送到 GitHub? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("[*] 已取消推送")
        sys.exit(0)

    print()
    print("[*] 正在推送...")
    if run_command("git push -u origin main", "推送代码"):
        print()
        print("✅ 推送成功！")
        print()
        print("[✓] 项目地址: https://github.com/klkanglang911/ytbnew")
        print()
        print("📋 后续步骤:")
        print("   1. VPS 克隆项目:")
        print("      git clone https://github.com/klkanglang911/ytbnew.git")
        print("   2. 快速部署:")
        print("      bash quick-deploy.sh")
        print()
    else:
        print()
        print("[⚠] 推送失败")
        print()
        print("可能需要认证。请按照以下步骤操作:")
        print()
        print("1️⃣  获取 GitHub Token")
        print("   访问: https://github.com/settings/tokens")
        print("   创建新 token，勾选 repo 权限")
        print()
        print("2️⃣  配置凭证")
        print("   运行命令:")
        print("   git remote set-url origin https://USERNAME:TOKEN@github.com/klkanglang911/ytbnew.git")
        print()
        print("   示例:")
        print("   git remote set-url origin https://klkanglang911:ghp_xxxxxxxxxxxx@github.com/klkanglang911/ytbnew.git")
        print()
        print("3️⃣  重新推送")
        print("   git push -u origin main")
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()
