# VM独立备份系统配置指南

## 目标
配置VM节点拥有独立的GitHub备份能力，实现真正的去中心化双备份架构。

---

## 架构设计

```
┌─────────────┐         ┌─────────────┐
│  主节点(云端) │         │ VM节点(本地)  │
│  129.154.x.x │  <───>  │  192.168.x.x │
└──────┬──────┘         └──────┬──────┘
       │                        │
       ▼                        ▼
┌─────────────┐         ┌─────────────┐
│ useens/     │         │ linlinofVM/ │
│ linlin-backup│         │ linlin-vm-backup│
└─────────────┘         └─────────────┘
       │                        │
       └──────────┬─────────────┘
                  ▼
         任一节点可帮对方复活
```

### 故障恢复流程

| 故障场景 | 恢复方式 |
|----------|----------|
| 主节点崩溃 | 从linlin-vm-backup拉取备份到备用节点 |
| VM崩溃 | 从linlin-backup拉取备份到新VM |
| 双节点崩溃 | 任一仓库均可恢复完整状态 |

---

## 部署步骤

### Step 1: 在VM上手动部署 (SSH暂不可用时)

由于SSH连接需要重新配置认证，请按以下步骤在VM本地执行：

#### 1.1 创建SSH密钥

```bash
# 在VM终端执行
mkdir -p ~/.ssh
ssh-keygen -t ed25519 -C "linlinofVM@vm.local" -f ~/.ssh/id_ed25519 -N ""
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub

# 查看公钥
cat ~/.ssh/id_ed25519.pub
```

#### 1.2 添加公钥到GitHub

1. 访问 https://github.com/settings/keys
2. 点击 "New SSH key"
3. 粘贴公钥内容
4. 标题填：VM Backup Key

#### 1.3 创建GitHub仓库

```bash
# 使用提供的Token创建仓库
curl -X POST \
  -H "Authorization: token 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" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/user/repos \
  -d '{
    "name": "linlin-vm-backup",
    "description": "VM节点备份仓库 - 去中心化双备份架构",
    "private": true,
    "auto_init": true
  }'
```

#### 1.4 初始化工作区

```bash
# 创建工作区
cd ~
mkdir -p .openclaw/workspace .openclaw/logs

# 初始化Git
cd .openclaw/workspace
git init
git config user.name "linlinofVM"
git config user.email "linlinofvm@vm.local"
git remote add origin git@github.com:linlinofVM/linlin-vm-backup.git

# 创建.gitignore
cat > .gitignore << 'EOF'
# Credentials
credentials/
*.key
*.pem
.env

# Large files
*.tar.gz
*.zip
*.log

# Temp files
*.tmp
.DS_Store
EOF

# 初始提交
git add .
git commit -m "VM backup initialization"
git push -u origin main
```

#### 1.5 安装备份脚本

```bash
# 创建备份脚本
cat > ~/.openclaw/vm-backup.sh << 'SCRIPT'
#!/bin/bash
set -e
WORKSPACE_DIR="$HOME/.openclaw/workspace"
LOG_FILE="$HOME/.openclaw/logs/vm-backup.log"
LOCK_FILE="/tmp/vm-backup.lock"

[ -f "$LOCK_FILE" ] && exit 0
touch "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

cd "$WORKSPACE_DIR" || exit 1
git add -A
git diff --cached --quiet && { log "无变更"; exit 0; }
git commit -m "VM backup: $(date '+%Y-%m-%d %H:%M:%S')"
git push origin HEAD
log "备份完成"
SCRIPT

chmod +x ~/.openclaw/vm-backup.sh
```

#### 1.6 设置定时任务

```bash
# 编辑crontab
crontab -e

# 添加以下行（每小时备份）
0 * * * * /home/user/.openclaw/vm-backup.sh
```

---

## 验证部署

```bash
# 测试SSH连接
ssh -T git@github.com
# 预期输出: Hi linlinofVM! You've successfully authenticated...

# 测试备份
~/.openclaw/vm-backup.sh

# 检查GitHub仓库
# 访问 https://github.com/linlinofVM/linlin-vm-backup
```

---

## 双节点备份同步策略

### 时间策略

| 节点 | 备份频率 | 说明 |
|------|----------|------|
| 主节点 | 每30分钟 | 主动态，更频繁 |
| VM | 每小时 | 备节点，较宽松 |

### 数据流向

```
主节点 ←→ 用户交互
   ↓ (每30分钟)
linlin-backup (GitHub)
   ↑ (需要时拉取)
VM ←→ 任务执行
   ↓ (每小时)
linlin-vm-backup (GitHub)
```

---

## 故障恢复脚本 (主节点 → 帮VM复活)

```bash
#!/bin/bash
# 在主节点上执行，帮助VM恢复

VM_HOST="user@vm-host"
VM_WORKSPACE="/home/user/.openclaw/workspace"

echo "🔄 帮助VM恢复..."

# 从VM的备份仓库拉取最新状态
TEMP_DIR=$(mktemp -d)
git clone git@github.com:linlinofVM/linlin-vm-backup.git "$TEMP_DIR"

# 推送到VM
rsync -avz --delete -e "ssh -p 4444" "$TEMP_DIR/" "${VM_HOST}:${VM_WORKSPACE}/"

# 清理
rm -rf "$TEMP_DIR"

echo "✅ VM恢复完成"
```

---

## 安全注意事项

⚠️ **Token安全**
- Token `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` 已泄露在本对话中
- 建议在部署完成后立即：
  1. 在GitHub撤销此Token
  2. 重新生成新的Token
  3. 仅保存在VM本地环境变量中

⚠️ **SSH密钥**
- 私钥 `~/.ssh/id_ed25519` 切勿离开VM
- 公钥可安全分享

---

## 状态检查

```bash
# VM备份健康检查
#!/bin/bash
LAST_BACKUP=$(cd ~/.openclaw/workspace && git log -1 --format=%ct 2>/dev/null || echo 0)
NOW=$(date +%s)
DIFF=$(( (NOW - LAST_BACKUP) / 60 ))

if [ $DIFF -gt 70 ]; then
    echo "⚠️ VM备份滞后 ${DIFF} 分钟"
else
    echo "✅ VM备份正常 (${DIFF} 分钟前)"
fi
```

---

*配置完成时间: $(date)*  
*版本: v1.0*
