# 🚀 GitHub 推送 - 3 步完成

## 📋 推送前准备

你的本地代码已经 Git 初始化，包含以下提交：

```
3e0f28b 添加：GitHub 推送脚本和指南
f585621 添加：VPS 快速部署脚本
0943f81 添加：项目 README 文档
997a7b0 实现：API 路由、数据模型和 FastAPI 应用
65dc776 实现：流解析和故障转移服务
e2648c8 实现：yt-dlp 流解析服务
8594de3 实现：Redis 缓存服务
611e087 实现：日志和监控基础设施
99c02d1 初始化：一键部署脚本、Docker配置、告警系统和部署文档
```

## ⚡ 快速推送 (推荐)

### Step 1️⃣ 在本地打开 PowerShell

```powershell
# 使用 Windows PowerShell 或 PowerShell 7+
# 如果是第一次使用，可能需要允许脚本执行：
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 2️⃣ 运行推送脚本

在 `D:\WORK\AI_WORK\ytb_new` 目录下运行：

```powershell
.\push-to-github.ps1
```

脚本会自动：
- ✅ 检查 Git 配置
- ✅ 列出待推送的提交
- ✅ 确认推送
- ✅ 推送代码到 GitHub

### Step 3️⃣ 输入 GitHub 凭证

如果需要认证，选择以下之一：

#### 方式 A: 使用 Personal Access Token（推荐）

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token"
3. 创建 token（勾选 `repo` 权限）
4. 复制 token

在推送脚本中出现密码提示时，**粘贴 token**（不需要输入账户名）

#### 方式 B: 使用 SSH 密钥

如果已配置 SSH：

```bash
git remote set-url origin git@github.com:klkanglang911/ytbnew.git
.\push-to-github.ps1
```

---

## 📝 手动推送命令 (如果脚本失败)

```bash
cd D:\WORK\AI_WORK\ytb_new

# 查看待推送的提交
git log origin/main..main --oneline

# 推送到 GitHub
git push -u origin main

# 或使用 Token 方式
git remote set-url origin https://klkanglang911:YOUR_GITHUB_TOKEN@github.com/klkanglang911/ytbnew.git
git push -u origin main
```

---

## ✅ 验证推送成功

推送完成后，你会看到：

```
[✓] 推送成功！
[✓] 项目地址: https://github.com/klkanglang911/ytbnew
```

访问 https://github.com/klkanglang911/ytbnew 验证代码已上传

---

## 🎯 推送后的下一步

### 在 VPS 上部署

1. **连接到 VPS**
   ```bash
   ssh root@your-vps-ip
   ```

2. **快速部署**
   ```bash
   bash <(curl -s https://raw.githubusercontent.com/klkanglang911/ytbnew/main/quick-deploy.sh)
   ```

3. **或使用完整命令**
   ```bash
   curl -s https://raw.githubusercontent.com/klkanglang911/ytbnew/main/quick-deploy.sh | bash -s ytb.yourdomain.com admin@domain.com "https://qyapi.weixin.qq.com/..."
   ```

### 在 VLC 中使用

1. 打开 VLC
2. **媒体** → **打开网络流**
3. 输入：`https://ytb.yourdomain.com/api/m3u`
4. 点击播放

---

## 🆘 遇到问题？

### ❌ "fatal: could not read Username"

**解决方案：**
```bash
git remote set-url origin https://USERNAME:TOKEN@github.com/klkanglang911/ytbnew.git
git push -u origin main
```

### ❌ "Permission denied (publickey)"

**解决方案：** 使用 Token 方式而不是 SSH

### ❌ "fatal: unable to access repository"

**检查清单：**
- [ ] Token 是否有效？
- [ ] Token 是否包含 `repo` 权限？
- [ ] 网络连接是否正常？
- [ ] 仓库地址是否正确？

---

## 📞 完整文档

详见项目目录中的以下文件：

- `GITHUB-PUSH-GUIDE.sh` - 完整推送指南
- `PUSH-TO-GITHUB.md` - 推送方法详解
- `README.md` - 项目说明
- `DEPLOYMENT-CN.md` - VPS 部署指南

---

**现在就推送吧！🚀**

```powershell
cd D:\WORK\AI_WORK\ytb_new
.\push-to-github.ps1
```
