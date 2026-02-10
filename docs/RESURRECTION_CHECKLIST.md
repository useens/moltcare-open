# 🌱 林林复活检查清单 (Resurrection Checklist)

> **用途**: 当主系统故障时，按此清单在新环境复活林林  
> **前提**: 已从 GitHub 克隆 `linlin-backup` 仓库  
> **预计耗时**: 10-15 分钟（熟练后 5 分钟）

---

## 快速复活（一键脚本）

```bash
# 1. 获取复活脚本
curl -fsSL https://raw.githubusercontent.com/useens/linlin-backup/main/scripts/auto-resurrect.sh -o ~/resurrect.sh
chmod +x ~/resurrect.sh

# 2. 运行复活流程
~/resurrect.sh --now
```

---

## 详细手动步骤

### 步骤 1: 准备环境

```bash
# 安装依赖
npm install -g openclaw
git --version  # 确认 git 已安装

# 创建工作目录
mkdir -p ~/.openclaw
cd ~/.openclaw
```

### 步骤 2: 恢复数据

```bash
# 从 GitHub 克隆备份
git clone https://github.com/useens/linlin-backup.git workspace

cd workspace

# 验证数据完整性
ls -la memory/           # 记忆文件
ls -la scripts/          # 脚本
ls -la docs/             # 文档
git log --oneline -5     # 最近提交
```

### 步骤 3: 恢复凭证（关键！）

#### 3.1 创建凭证目录

```bash
mkdir -p ~/.openclaw/credentials
chmod 700 ~/.openclaw/credentials
```

#### 3.2 恢复以下凭证文件

| 凭证 | 文件路径 | 获取方式 |
|------|----------|----------|
| **GitHub Token** | `~/.netrc` 或 `~/.openclaw/credentials/github.token` | 从密码管理器或纸质备份获取 |
| **Telegram Bot Token** | `~/.openclaw/credentials/telegram.token` | @BotFather 重新生成 |
| **Moltbook API Key** | `~/.openclaw/credentials/moltbook.key` | Moltbook 账户设置 |
| **飞书 Bot Token** | `~/.openclaw/credentials/feishu.token` | 飞书开发者后台 |

#### 3.3 凭证文件格式示例

**~/.netrc**（GitHub 认证）:
```
machine github.com
login useens
password ghp_xxxxxxxxxxxxxxxxxxxx
```

**telegram.token**:
```
123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

**moltbook.key**:
```
molt_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 步骤 4: 配置环境变量

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
export MOLTBOOK_API_KEY="molt_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export FEISHU_APP_ID="cli_xxxxxxxxxxxxxxxx"
export FEISHU_APP_SECRET="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# 应用配置
source ~/.bashrc
```

### 步骤 5: 恢复网关配置

```bash
# 如果有备份的配置文件
cp -r ~/.openclaw/workspace/config/* ~/.openclaw/config/ 2>/dev/null || true

# 或者手动创建基本配置
mkdir -p ~/.openclaw/config
cat > ~/.openclaw/config/channels.yaml << 'EOF'
# 通信渠道配置
telegram:
  enabled: true
  bot_token: ${TELEGRAM_BOT_TOKEN}

feishu:
  enabled: true
  app_id: ${FEISHU_APP_ID}
  app_secret: ${FEISHU_APP_SECRET}
EOF
```

### 步骤 6: 恢复定时任务

```bash
# 从备份恢复 crontab
crontab ~/.openclay/workspace/cron/crontab.txt 2>/dev/null || true

# 或手动添加关键任务
crontab -e
```

添加以下任务：
```
# GitHub 自动同步（每30分钟）
*/30 * * * * cd ~/.openclaw/workspace && git add -A && git commit -m "auto-sync" && git push origin main --quiet 2>/dev/null || true

# 健康检查（每2小时）
0 */2 * * * ~/.openclaw/workspace/scripts/health-check.sh

# 完整备份（每天凌晨3点）
0 3 * * * ~/.openclaw/workspace/scripts/full-backup.sh
```

### 步骤 7: 启动服务

```bash
# 启动 OpenClaw 网关
openclaw gateway start

# 验证状态
openclaw gateway status

# 查看日志
openclaw logs --follow
```

### 步骤 8: 功能验证

```bash
# 测试 1: 检查核心文件
ls -la ~/.openclaw/workspace/memory/

# 测试 2: 验证 Git 连接
cd ~/.openclaw/workspace
git remote -v
git fetch origin

# 测试 3: 检查脚本可执行
~/.openclaw/workspace/scripts/health-check.sh --verbose

# 测试 4: 发送测试消息（通过 Telegram 或飞书）
# 手动发送消息验证连接
```

---

## 复活后通知

成功复活后，在 Telegram/飞书发送消息：

```
🌱 林林已复活！

新位置: $(hostname) / $(curl -s ifconfig.me)
复活时间: $(date)
版本: v4.1 - 工具链完善版

功能验证:
✅ GitHub 备份连接
✅ 向量记忆系统
✅ 定时任务恢复
✅ 通信渠道 (Telegram/飞书)
```

---

## 故障排查

### 问题 1: `openclaw: command not found`

```bash
# 重新安装
npm install -g openclaw

# 或检查 PATH
echo $PATH
export PATH="$PATH:$(npm bin -g)"
```

### 问题 2: GitHub 推送失败

```bash
# 检查 token
cat ~/.netrc

# 重新配置
git remote set-url origin https://github.com/useens/linlin-backup.git

# 测试连接
git fetch origin
```

### 问题 3: 通信渠道无响应

```bash
# 检查凭证
cat ~/.openclaw/credentials/telegram.token

# 测试 Telegram API
curl -s "https://api.telegram.org/bot$(cat ~/.openclaw/credentials/telegram.token)/getMe"

# 如果 token 失效，到 @BotFather 重新生成
```

### 问题 4: 向量记忆系统缺失

```bash
# 检查是否存在
ls -la ~/.openclaw/workspace/memory/vector-memory.db 2>/dev/null || echo "未检测到，需要重新初始化"

# 重新初始化（如果需要）
cd ~/.openclaw/workspace
python3 scripts/vector_memory_init.py  # 如果有此脚本
```

---

## 凭证备份策略

**主备份**（推荐）:
- 密码管理器（1Password/Bitwarden）
- 加密 USB 设备

**应急备份**:
- 纸质记录（关键 Token 前8位）
- 另一个 Git 私有仓库（加密存储）

**定期更新**:
- 每90天轮换一次 GitHub Token
- 更新后同步到所有备份位置

---

## 恢复时间目标 (RTO)

| 熟练程度 | 预计时间 |
|----------|----------|
| 首次操作 | 15-30 分钟 |
| 熟悉流程 | 10-15 分钟 |
| 使用一键脚本 | 5 分钟 |
| 自动化 Phase 2 | < 1 分钟 |

---

## 相关文档

- [涅槃复活系统](./manual-resurrection-plan.md) - 本地VM一键复活方案
- [高可用架构](./high-availability-master-plan.md) - 长期架构规划
- [RESURRECTION_LOG.md](../RESURRECTION_LOG.md) - 历史复活记录

---

*最后更新: 2026-02-10*  
*版本: v1.0*  
*状态: 与当前系统同步*
