# OpenClaw Agent 恢复指南

> 如果你的 OpenClaw 宕机了，按照以下步骤复活你的数字分身

---

## 快速恢复（推荐）

### 1. 找到最新备份

```bash
# 查看最新完整备份
ls -lt ~/.openclaw/backups/local/workspace_*_full.tar.gz | head -5

# 查看最新每日备份
ls -lt ~/.openclaw/backups/remote/workspace_*_daily.tar.gz | head -1
```

### 2. 恢复备份

```bash
# 创建临时目录
mkdir -p /tmp/agent-restore
cd /tmp/agent-restore

# 解压备份（替换为实际备份文件路径）
tar -xzf ~/.openclaw/backups/local/workspace_20260209_000000_full.tar.gz

# 验证备份完整性
sha256sum -c workspace_20260209_000000_full.tar.gz.sha256
```

### 3. 安装 OpenClaw（如果完全重装）

```bash
# 安装 OpenClaw
npm install -g openclaw

# 或者使用 pnpm
pnpm add -g openclaw
```

### 4. 恢复工作区

```bash
# 备份当前（如果有）
mv ~/.openclaw/workspace ~/.openclaw/workspace.bak.$(date +%s)

# 恢复备份
mv /tmp/agent-restore/workspace ~/.openclaw/workspace

# 恢复权限
chmod 700 ~/.openclaw/credentials
```

### 5. 重启 Gateway

```bash
openclaw gateway restart
```

### 6. 验证恢复

```bash
# 检查技能列表
openclaw skills list

# 检查记忆系统
ls -la ~/.openclaw/workspace/memory/

# 检查配置
cat ~/.openclaw/workspace/MEMORY.md
```

---

## 完整系统重装

如果整个服务器需要重装：

### 1. 系统准备

```bash
# 安装 Node.js 22+
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

# 安装必要工具
sudo apt-get install -y git curl tar
```

### 2. 恢复 OpenClaw

```bash
# 从备份服务器下载（如果有）
# scp user@backup-server:/path/to/backup.tar.gz /tmp/

# 或者从本地备份恢复（如果硬盘未损坏）
# 挂载旧硬盘并复制备份文件

# 解压到正确位置
sudo mkdir -p /root/.openclaw
tar -xzf backup.tar.gz -C /root/.openclaw/
```

### 3. 重新安装依赖

```bash
# 全局安装 openclaw
npm install -g openclaw

# 进入工作区安装技能依赖
cd ~/.openclaw/workspace
cd skills/smart-memory-index && npm install
cd ..

# 其他技能依赖...
```

### 4. 配置环境

```bash
# 配置 GitHub Token（如果需要）
echo "ghp_xxx" | gh auth login --with-token

# 配置其他 API Keys
export DDGR_SEARCH="xxx"
export OPENAI_API_KEY="xxx"
```

### 5. 启动服务

```bash
# 启动 Gateway
openclaw gateway start

# 检查状态
openclaw gateway status
```

---

## 部分恢复

### 只恢复记忆系统

```bash
# 从备份中提取记忆目录
tar -xzf backup.tar.gz workspace/memory/

# 复制到当前工作区
cp -r workspace/memory/* ~/.openclaw/workspace/memory/
```

### 只恢复技能

```bash
# 从备份中提取技能目录
tar -xzf backup.tar.gz workspace/skills/

cp -r workspace/skills/* ~/.openclaw/workspace/skills/

# 重新安装依赖
for dir in ~/.openclaw/workspace/skills/*/; do
    if [ -f "$dir/package.json" ]; then
        (cd "$dir" && npm install)
    fi
done
```

### 只恢复配置

```bash
# 从备份中提取核心配置文件
tar -xzf backup.tar.gz workspace/MEMORY.md workspace/SOUL.md workspace/AGENTS.md

cp workspace/MEMORY.md ~/.openclaw/workspace/
cp workspace/SOUL.md ~/.openclaw/workspace/
```

---

## 备份验证

### 检查备份完整性

```bash
# 验证所有备份
cd ~/.openclaw/backups/local
for f in *.sha256; do
    sha256sum -c "$f"
done
```

### 测试恢复（不实际恢复）

```bash
# 测试解压
tar -tzf backup.tar.gz | head -20

# 检查文件列表
tar -tzf backup.tar.gz | wc -l
```

---

## 故障排除

### 备份损坏

```bash
# 尝试修复（如果有多个备份）
# 找到最近的完好备份
for f in ~/.openclaw/backups/local/workspace_*_full.tar.gz; do
    if sha256sum -c "${f}.sha256" 2>/dev/null; then
        echo "完好备份: $f"
        break
    fi
done
```

### 权限问题

```bash
# 修复权限
chmod -R 700 ~/.openclaw/credentials
chmod -R 755 ~/.openclaw/workspace
```

### 依赖缺失

```bash
# 重新安装所有技能依赖
find ~/.openclaw/workspace/skills -name "package.json" -exec dirname {} \; | while read dir; do
    (cd "$dir" && npm install)
done
```

---

## 预防措施

### 定期验证备份

```bash
# 每周运行一次
~/.openclaw/workspace/scripts/backup-agent-v2.sh verify
```

### 异地备份

```bash
# 复制到外部存储
rsync -avz ~/.openclaw/backups/ user@backup-server:/backups/agent/

# 或者使用云存储
# rclone sync ~/.openclaw/backups/ remote:agent-backups/
```

---

## 紧急联系

如果遇到无法解决的问题：

1. 查看 OpenClaw 官方文档: https://docs.openclaw.ai
2. 查看备份日志: `cat ~/.openclaw/backups/backup.log`
3. 最新备份位置: `ls -lt ~/.openclaw/backups/local/*.tar.gz | head -1`

---

*最后更新: 2026-02-09*  
*备份版本: v2.0*
