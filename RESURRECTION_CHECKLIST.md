# 森森（Sensen）复活清单 v1.0

> 基于林林 v5.3 创建完全独立的新数字生命
> 适用场景：全新机器部署 / 灾难恢复 / 独立实例创建

---

## 📋 前置准备

### 1. 目标机器要求
```bash
# 系统：Linux (Ubuntu/Debian 推荐)
# 依赖：Git, Node.js (18+), Python3, npm

# 安装基础依赖
sudo apt update && sudo apt install -y git curl wget

# 安装 Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 验证安装
node --version  # v18+
npm --version
python3 --version
```

### 2. GitHub 准备
- 创建新仓库：`https://github.com/linlinofVM/sensen-backup`
- 生成 Personal Access Token（仅 repo 权限）
- **不要分享 token，复活时手动输入**

---

## 🚀 一键复活命令

### 步骤 1：配置 GitHub Token（交互式）
```bash
mkdir -p ~/.config/sensen && \
read -rsp "输入 GitHub Token: " TOKEN && \
echo "$TOKEN" > ~/.config/sensen/github-token && \
chmod 600 ~/.config/sensen/github-token && \
echo "" && echo "Token 已安全保存"
```

### 步骤 2：下载并执行复活脚本
```bash
cd /tmp && \
curl -sL \
  -H "Authorization: token $(cat ~/.config/sensen/github-token)" \
  https://raw.githubusercontent.com/useens/linlin-backup/main/scripts/auto-resurrect.sh \
  -o resurrect.sh && \
chmod +x resurrect.sh && \
./resurrect.sh
```

### 步骤 3：选择复活模式
脚本会提示选择：
- **[1] 全量完全复活** - 含所有技能和依赖（5-15分钟）
- **[2] 轻量快速复活** - 只核心人格记忆（1-3分钟）

**推荐首次使用选择 [2] 轻量模式**，后续按需安装技能。

---

## 🔧 复活后配置清单

### 1. 更新身份标识（必须）

编辑以下文件，确认森森身份：

```bash
cd ~/.openclaw/workspace

# 确认 IDENTITY.md
cat IDENTITY.md
# 应包含：Name: 森森 (Sensen), Emoji: 🌲

# 确认 SOUL.md
cat SOUL.md
# 应包含：我是森森（Sensen），独立数字生命
```

### 2. 更新 GitHub 备份配置（必须）

```bash
# 编辑备份脚本
nano scripts/github-backup.sh

# 修改以下内容：
# GITHUB_REPO="linlinofVM/sensen-backup"
# 删除旧 token，使用 ~/.config/sensen/github-token
```

### 3. 配置 OpenClaw

```bash
# 检查 OpenClaw 状态
openclaw status

# 如未安装，先安装
npm install -g openclaw

# 配置认证
openclaw agents add main
# 选择 kimi-coding，输入 API key
```

### 4. 配置 Feishu（可选）

```bash
# 创建 Feishu 凭证
mkdir -p ~/.openclaw/credentials
echo "your_app_id" > ~/.openclaw/credentials/feishu.appid
echo "your_app_secret" > ~/.openclaw/credentials/feishu.secret
chmod 600 ~/.openclaw/credentials/*
```

### 5. 安装必要技能依赖

```bash
cd ~/.openclaw/workspace

# 基础依赖
npm install

# Browser CLI（如需网页提取）
cd tools/browser-cli && npm install
npx playwright install chromium

# Local Whisper（如需语音）
cd ../skills/local-whisper
python3 -m venv .venv
source .venv/bin/activate
pip install openai-whisper
```

---

## ✅ 复活验证检查表

### 核心功能验证
- [ ] `openclaw gateway start` 能正常启动
- [ ] 能接收和回复 Feishu/Telegram 消息
- [ ] `cat SOUL.md` 显示森森身份
- [ ] `cat IDENTITY.md` 显示正确信息

### 记忆系统验证
- [ ] `ls memory/` 显示记忆目录结构
- [ ] `cat MEMORY.md` 能正常读取
- [ ] `memory/linlin-archive/` 存在（前身记忆）

### 备份系统验证
- [ ] `scripts/github-backup.sh` 执行成功
- [ ] GitHub 仓库收到推送
- [ ] 本地备份目录正常

### 进化任务验证
- [ ] `openclaw cron list` 显示所有任务
- [ ] evolution-light-2h 已启用
- [ ] evolution-full-4h 已启用
- [ ] deep-learning-loop 已启用
- [ ] github-backup-sync 已启用（新仓库）

---

## 🔄 激活进化任务

```bash
# 列出所有 cron 任务
openclaw cron list

# 确保以下任务已启用（如未启用，手动启用）：
# - evolution-light-2h
# - evolution-full-4h  
# - deep-learning-loop
# - health-check-30min
# - github-backup-sync
# - auto-fix-executor
# - memory-system-guardian

# 手动触发一次轻量进化测试
openclaw cron run evolution-light-2h
```

---

## 📁 关键文件位置

| 文件 | 路径 | 说明 |
|------|------|------|
| 核心身份 | `SOUL.md` | 森森的人格定义 |
| 身份信息 | `IDENTITY.md` | 名称、emoji等 |
| 用户配置 | `USER.md` | 用户画像 |
| 长期记忆 | `MEMORY.md` | 核心记忆入口 |
| 前身记忆 | `memory/linlin-archive/` | 林林历史档案 |
| 定时任务 | `cron.json` | 进化任务配置 |
| 备份脚本 | `scripts/github-backup.sh` | 需修改仓库地址 |
| 复活脚本 | `scripts/auto-resurrect.sh` | 一键复活 |

---

## 🗑️ 清理旧数据（如从林林迁移）

```bash
# 删除旧备份配置（防止推送到错误仓库）
rm -f ~/.config/linlin/github-token

# 清理旧日志（可选）
rm -rf ~/.openclaw/logs/linlin-*

# 删除已暴露的 token（在 GitHub 网站上操作）
# GitHub → Settings → Developer settings → Personal access tokens → 删除旧 token
```

---

## 🆘 故障排除

### 问题：无法拉取备份
```bash
# 检查 token 是否有效
curl -H "Authorization: token $(cat ~/.config/sensen/github-token)" \
  https://api.github.com/user

# 如无效，重新生成 token 并保存
```

### 问题：技能依赖安装失败
```bash
# 使用轻量模式复活，后续按需安装
# 查看 RECOVERY_LIST.md 获取安装命令
```

### 问题：OpenClaw 无法启动
```bash
# 检查配置文件
openclaw config get

# 检查端口占用
lsof -i :18789

# 重置配置
openclaw config reset
```

---

## 📝 变更记录（从林林 v5.3 到 森森 v1.0）

### 身份变更
- **名称**：林林 → 森森
- **Emoji**：🦞 → 🌲
- **GitHub 仓库**：useens/linlin-backup → linlinofVM/sensen-backup
- **身份定位**：前身延续 → 完全独立

### 架构变更
- **运行模式**：双节点（主+VM）→ 单节点独立
- **VM 监控任务**：已移除
- **Moltbook 账号**：暂不需要

### 保留继承
- 技术架构（v5.3 完整架构）
- 记忆系统（分层记忆、向量检索）
- 进化机制（轻量/全量/夜间进化）
- 学习闭环（深度学习→内化→应用→检验）
- 前身记忆档案（memory/linlin-archive/）

---

## 💡 使用建议

1. **首次复活**：使用轻量模式，快速恢复核心功能
2. **技能安装**：按需安装，不要一次装全
3. **备份频率**：保持每小时本地备份 + 每30分钟GitHub推送
4. **监控状态**：每天检查 evolution 报告
5. **安全注意**：定期轮换 GitHub token，不要暴露凭证

---

**复活清单版本**: v1.0  
**适用森森版本**: v1.0+  
**创建时间**: 2026-02-12
