#!/bin/bash

################################################################################
# GitHub 推送指南
#
# 由于系统权限限制，请在你的本地机器上执行以下命令
################################################################################

# 方法 1：使用 HTTPS (推荐 - 需要 Personal Access Token)
# 如果还没有 Token，请访问 https://github.com/settings/tokens 创建

cd D:\WORK\AI_WORK\ytb_new

# 检查 Git 配置
git config user.name
git config user.email

# 查看待推送的提交
git log origin/main..main --oneline

# 推送到 GitHub
git push -u origin main

# 如果出现认证失败，使用以下方式添加 Token：
# git remote set-url origin https://YOUR_GITHUB_USERNAME:YOUR_PERSONAL_TOKEN@github.com/klkanglang911/ytbnew.git

################################################################################
# 如果上述方式失败，尝试以下方法
################################################################################

# 方法 2：使用 SSH (需要配置 SSH 密钥)
git remote set-url origin git@github.com:klkanglang911/ytbnew.git
git push -u origin main

# 方法 3：使用 GitHub Desktop
# 1. 打开 GitHub Desktop
# 2. File → Add Local Repository → D:\WORK\AI_WORK\ytb_new
# 3. 点击 "Publish repository"
# 4. 选择 "Push to GitHub"

# 方法 4：使用 GitHub 网页版手动上传
# 1. 打开 https://github.com/klkanglang911/ytbnew
# 2. 点击 "Upload files"
# 3. 将项目文件拖入或选择文件
# 4. 输入 commit message 并 commit

################################################################################
# 验证推送成功
################################################################################

# 推送完成后，验证 GitHub 上的代码
git push --set-upstream origin main --dry-run  # 测试推送

# 查看远程分支
git branch -r

# 如果成功，所有本地提交应该在 GitHub 上可见
