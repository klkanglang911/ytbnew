@echo off
REM YouTube 直播代理服务 - GitHub 推送脚本
REM 在 Windows 本地机器上运行此脚本

setlocal enabledelayedexpansion

echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║   YouTube 代理服务 - GitHub 推送脚本                  ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

REM 进入项目目录
cd /d "D:\WORK\AI_WORK\ytb_new"

if errorlevel 1 (
    echo [错误] 无法进入项目目录
    exit /b 1
)

echo [*] 检查 Git 配置...
git config user.name >nul 2>&1
if errorlevel 1 (
    echo [错误] Git 未配置，请运行：
    echo   git config --global user.name "klkanglang911"
    echo   git config --global user.email "klkanglang@gmail.com"
    exit /b 1
)

echo [✓] Git 配置正确

echo.
echo [*] 检查待推送的提交...
git log origin/main..main --oneline
echo.

echo [*] 验证远程仓库...
git remote -v

echo.
echo [*] 准备推送到 GitHub...
echo   仓库: https://github.com/klkanglang911/ytbnew.git
echo   分支: main
echo.

REM 推送到 GitHub
echo [*] 正在推送代码...
git push -u origin main

if errorlevel 1 (
    echo [错误] 推送失败！
    echo.
    echo 可能的原因：
    echo   1. GitHub 认证失败 - 需要 Personal Access Token
    echo   2. SSH 密钥未配置
    echo   3. 网络连接问题
    echo.
    echo 解决方案：
    echo   1. 生成 Token: https://github.com/settings/tokens
    echo   2. 运行命令更新凭证：
    echo      git remote set-url origin https://USERNAME:TOKEN@github.com/klkanglang911/ytbnew.git
    echo   3. 重新尝试推送
    exit /b 1
)

echo.
echo [✓] 推送成功！
echo.
echo [*] 验证 GitHub 仓库...
timeout /t 2 /nobreak

REM 验证推送
git ls-remote origin main >nul 2>&1
if errorlevel 1 (
    echo [警告] 无法验证远程分支
) else (
    echo [✓] 代码已成功推送到 GitHub
    echo.
    echo [✓] 项目地址: https://github.com/klkanglang911/ytbnew
    echo.
)

echo [✓] 推送流程完成！
echo.
echo [*] 后续步骤：
echo   1. 访问 https://github.com/klkanglang911/ytbnew 验证代码
echo   2. 在 VPS 上克隆项目：
echo      git clone https://github.com/klkanglang911/ytbnew.git
echo   3. 执行快速部署脚本：
echo      bash quick-deploy.sh ytb.yourdomain.com admin@domain.com
echo.

pause
