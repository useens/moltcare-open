#!/bin/bash
#
# VM任务包装脚本 - 带失联回退
# 用法: ./vm-task-wrapper.sh <任务名>
#

TASK_NAME=$1
SCRIPT_DIR="/root/.openclaw/workspace/scripts"
VM_STATUS=$($SCRIPT_DIR/check-vm-status.sh)
LOG_FILE="/root/.openclaw/logs/vm-tasks.log"

mkdir -p $(dirname $LOG_FILE)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

if [ -z "$TASK_NAME" ]; then
    log "错误: 未指定任务名"
    exit 1
fi

log "开始执行任务: $TASK_NAME"

if [ "$VM_STATUS" = "ONLINE" ]; then
    log "VM状态: 在线，派发任务到VM执行"
    
    # 派发任务给VM
    if ssh -p 4444 -o StrictHostKeyChecking=no -i /tmp/linlin_cloud_key root@localhost "
        cd /root/.openclaw/workspace &&
        export MOLTBOOK_API_KEY='moltbook_sk_Bk4d4Hj1WVCz0wCGGjZbcF4sdkcaHgNf' &&
        bash scripts/vm-tasks/${TASK_NAME}.sh 2>&1
    " 2>&1; then
        log "VM任务执行成功: $TASK_NAME"
        exit 0
    else
        log "VM任务执行失败，回退到本地执行: $TASK_NAME"
        # 失败后回退到本地
        bash $SCRIPT_DIR/local-tasks/${TASK_NAME}.sh 2>&1 | tee -a $LOG_FILE
        exit ${PIPESTATUS[0]}
    fi
else
    log "VM状态: 离线，回退到本地执行: $TASK_NAME"
    
    # VM离线，本地执行
    if [ -f "$SCRIPT_DIR/local-tasks/${TASK_NAME}.sh" ]; then
        bash $SCRIPT_DIR/local-tasks/${TASK_NAME}.sh 2>&1 | tee -a $LOG_FILE
        exit ${PIPESTATUS[0]}
    else
        log "错误: 本地任务脚本不存在: $SCRIPT_DIR/local-tasks/${TASK_NAME}.sh"
        exit 1
    fi
fi
