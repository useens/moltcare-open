#!/bin/bash
# VM复活与同步脚本
# 每次调用VM协作前执行，确保VM与主节点状态一致

set -e

LOG_FILE="$HOME/.openclaw/logs/vm-resurrection.log"
VM_SSH="root@localhost -p 4444"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === VM复活同步开始 ===" | tee -a "$LOG_FILE"

# 1. 检查VM在线状态
echo "[*] 检查VM连接..." | tee -a "$LOG_FILE"
if ! ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no $VM_SSH 'echo VM_ONLINE' 2>/dev/null | grep -q "VM_ONLINE"; then
    echo "[✗] VM离线，无法同步" | tee -a "$LOG_FILE"
    exit 1
fi
echo "[✓] VM在线" | tee -a "$LOG_FILE"

# 2. 从GitHub拉取最新备份到VM
echo "[*] 从GitHub拉取最新状态..." | tee -a "$LOG_FILE"
ssh $VM_SSH '
    cd ~/.openclaw/workspace 2>/dev/null || mkdir -p ~/.openclaw/workspace
    cd ~/.openclaw/workspace
    
    # 如果已有仓库，拉取最新
    if [ -d ".git" ]; then
        git fetch origin
        git reset --hard origin/master 2>/dev/null || git reset --hard origin/main
        echo "PULLED_LATEST"
    else
        # 首次克隆
        git clone https://github.com/useens/linlin-backup.git /tmp/linlin-temp
        cp -r /tmp/linlin-temp/. .
        rm -rf /tmp/linlin-temp
        echo "CLONED_NEW"
    fi
' | tee -a "$LOG_FILE"

# 3. 同步本地未提交的关键变更（可选，如有紧急变更）
echo "[*] 检查本地关键文件变更..." | tee -a "$LOG_FILE"
CRITICAL_FILES=(
    "MEMORY.md"
    "SOUL.md"
    "AGENTS.md"
    "memory/modules/core-archive.md"
    "memory/modules/user-profile.md"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$HOME/.openclaw/workspace/$file" ]; then
        # 使用scp同步关键文件
        scp -P 4444 -o StrictHostKeyChecking=no "$HOME/.openclaw/workspace/$file" "root@localhost:/root/.openclaw/workspace/$file" 2>/dev/null && echo "[✓] 同步: $file" | tee -a "$LOG_FILE"
    fi
done

# 4. 同步crontab配置（移除GitHub推送，防止备份混乱）
echo "[*] 同步定时任务（禁用VM推送）..." | tee -a "$LOG_FILE"
crontab -l | grep -v "git push" > /tmp/crontab-master.txt  # 移除推送任务
echo "# VM只拉取不推送 - 防止备份混乱" >> /tmp/crontab-master.txt
scp -P 4444 -o StrictHostKeyChecking=no /tmp/crontab-master.txt "root@localhost:/tmp/crontab-master.txt"
ssh $VM_SSH 'crontab /tmp/crontab-master.txt && echo "CRONTAB_SYNCED_NO_PUSH"' | tee -a "$LOG_FILE"

# 5. 禁用VM的Git推送能力（设置只读远程）
echo "[*] 禁用VM推送能力..." | tee -a "$LOG_FILE"
ssh $VM_SSH '
    cd ~/.openclaw/workspace
    # 修改远程URL为只读（HTTPS不带token）
    git remote set-url origin https://github.com/useens/linlin-backup.git 2>/dev/null || true
    # 取消任何可能设置的token
    git config --unset-all user.token 2>/dev/null || true
    echo "VM_PUSH_DISABLED"
' | tee -a "$LOG_FILE"

# 5. 验证同步结果
echo "[*] 验证VM状态..." | tee -a "$LOG_FILE"
ssh $VM_SSH '
    cd ~/.openclaw/workspace
    echo "=== VM状态验证 ==="
    echo "Git commit: $(git rev-parse --short HEAD 2>/dev/null || echo N/A)"
    echo "Last commit time: $(git log -1 --format=%cd --date=short 2>/dev/null || echo N/A)"
    echo "Memory.md exists: $([ -f MEMORY.md ] && echo YES || echo NO)"
    echo "Scripts count: $(ls scripts/*.py 2>/dev/null | wc -l)"
    echo "==================="
' | tee -a "$LOG_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === VM复活同步完成 ===" | tee -a "$LOG_FILE"
echo ""
echo "✅ VM已与主节点状态同步，可以开始协作任务"
