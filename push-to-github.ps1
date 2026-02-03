# YouTube 直播代理服务 - GitHub 推送脚本 (PowerShell)
# 在 Windows PowerShell 中运行此脚本

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║   YouTube 代理服务 - GitHub 推送脚本 (PowerShell)     ║" -ForegroundColor Blue
Write-Host "╚═══════════════════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""

# 进入项目目录
$projectPath = "D:\WORK\AI_WORK\ytb_new"
if (-not (Test-Path $projectPath)) {
    Write-Host "[✗] 项目目录不存在: $projectPath" -ForegroundColor Red
    exit 1
}

Set-Location $projectPath
Write-Host "[*] 进入项目目录: $projectPath" -ForegroundColor Cyan

# 检查 Git 初始化
if (-not (Test-Path ".git")) {
    Write-Host "[✗] Git 仓库未初始化" -ForegroundColor Red
    exit 1
}

Write-Host "[✓] Git 仓库已初始化" -ForegroundColor Green

# 检查 Git 配置
$userName = git config user.name 2>$null
$userEmail = git config user.email 2>$null

if ([string]::IsNullOrEmpty($userName) -or [string]::IsNullOrEmpty($userEmail)) {
    Write-Host "[⚠] Git 用户配置不完整" -ForegroundColor Yellow
    Write-Host "    请运行以下命令配置 Git:" -ForegroundColor Yellow
    Write-Host "    git config --global user.name 'klkanglang911'" -ForegroundColor White
    Write-Host "    git config --global user.email 'klkanglang@gmail.com'" -ForegroundColor White
    exit 1
}

Write-Host "[✓] Git 配置正确" -ForegroundColor Green
Write-Host "    用户名: $userName" -ForegroundColor White
Write-Host "    邮箱: $userEmail" -ForegroundColor White

# 检查待推送的提交
Write-Host ""
Write-Host "[*] 检查待推送的提交..." -ForegroundColor Cyan
$commitCount = (git log origin/main..main --oneline 2>$null | Measure-Object -Line).Lines
if ($commitCount -eq 0) {
    Write-Host "[*] 所有提交已推送，无新的提交待推送" -ForegroundColor Yellow
    exit 0
}

Write-Host "[*] 待推送提交 ($commitCount 个):" -ForegroundColor Cyan
git log origin/main..main --oneline | ForEach-Object { Write-Host "    $_" -ForegroundColor White }

# 显示远程配置
Write-Host ""
Write-Host "[*] 远程仓库配置:" -ForegroundColor Cyan
git remote -v | ForEach-Object { Write-Host "    $_" -ForegroundColor White }

# 确认推送
Write-Host ""
$confirm = Read-Host "[?] 确认推送到 GitHub? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "[*] 已取消推送" -ForegroundColor Yellow
    exit 0
}

# 执行推送
Write-Host ""
Write-Host "[*] 正在推送代码到 GitHub..." -ForegroundColor Cyan
Write-Host ""

try {
    git push -u origin main
    $pushResult = $?

    if ($pushResult) {
        Write-Host ""
        Write-Host "[✓] 推送成功！" -ForegroundColor Green
        Write-Host ""
        Write-Host "[✓] 项目地址: https://github.com/klkanglang911/ytbnew" -ForegroundColor Green
        Write-Host ""
        Write-Host "[*] 后续步骤:" -ForegroundColor Cyan
        Write-Host "    1. 访问 https://github.com/klkanglang911/ytbnew 验证代码" -ForegroundColor White
        Write-Host "    2. 在 VPS 上克隆项目:" -ForegroundColor White
        Write-Host "       git clone https://github.com/klkanglang911/ytbnew.git" -ForegroundColor White
        Write-Host "       cd ytbnew" -ForegroundColor White
        Write-Host "    3. 执行快速部署脚本:" -ForegroundColor White
        Write-Host "       bash quick-deploy.sh" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "[✗] 推送失败！" -ForegroundColor Red
        Write-Host ""
        Write-Host "可能的原因:" -ForegroundColor Yellow
        Write-Host "  1. GitHub 认证失败 - 需要 Personal Access Token" -ForegroundColor White
        Write-Host "  2. SSH 密钥未配置" -ForegroundColor White
        Write-Host "  3. 网络连接问题" -ForegroundColor White
        Write-Host ""
        Write-Host "解决方案:" -ForegroundColor Yellow
        Write-Host "  1. 生成 Token: https://github.com/settings/tokens" -ForegroundColor White
        Write-Host "  2. 运行命令更新凭证:" -ForegroundColor White
        Write-Host "     git remote set-url origin https://USERNAME:TOKEN@github.com/klkanglang911/ytbnew.git" -ForegroundColor White
        Write-Host "  3. 重新尝试推送" -ForegroundColor White
        Write-Host ""
        exit 1
    }
} catch {
    Write-Host "[✗] 发生异常: $_" -ForegroundColor Red
    exit 1
}

Write-Host "按任意键继续..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
