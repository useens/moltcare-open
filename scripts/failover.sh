#!/bin/bash
# 森森双节点故障转移检测脚本 v2.1 (GitHub心跳版)
# 心跳检测间隔: 2小时 (7200秒)
# 使用GitHub仓库作为心跳通道

set -e

WORKSPACE_DIR="/root/.openclaw/workspace"
LOG_FILE="$WORKSPACE_DIR/logs/failover.log"
HEARTBEAT_DIR="$WORKSPACE_DIR/.heartbeat"
HEARTBEAT_INTERVAL=7200  # 2小时 = 7200秒
MAX_MISSED_HEARTBEATS=2  # 连续2次无心跳才触发故障转移

# 生产仓库配置
PRODUCTION_REPO="github.com/linlinofVM/sensen-backup"
PRODUCTION_TOKEN="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"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 确保目录存在
mkdir -p "$WORKSPACE_DIR/logs"
mkdir -p "$HEARTBEAT_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# ========== 心跳发送（主节点使用）==========
send_heartbeat() {
    log "发送心跳到GitHub..."
    
    cd "$WORKSPACE_DIR"
    
    # 写入心跳时间戳
    local timestamp=$(date +%s)
    local human_time=$(date '+%Y-%m-%d %H:%M:%S')
    
    cat > "$HEARTBEAT_DIR/primary.json" << EOF
{
  "timestamp": $timestamp,
  "human_time": "$human_time",
  "node_id": "$(cat .node-id 2>/dev/null || echo 'unknown')",
  "hostname": "$(hostname)",
  "role": "PRIMARY"
}
EOF
    
    # 提交并推送到生产仓库
    git add .heartbeat/primary.json
    git commit -m "💓 heartbeat: $human_time" --allow-empty 2>/dev/null || true
    
    if git push "https://${PRODUCTION_TOKEN}@${PRODUCTION_REPO}.git" main 2>/dev/null; then
        log "✅ 心跳已发送: $human_time"
    else
        log "⚠️ 心跳发送失败，将在下次重试"
    fi
}

# ========== 从GitHub拉取心跳（备用节点使用）==========
fetch_heartbeat() {
    log "从GitHub拉取心跳..."
    
    cd "$WORKSPACE_DIR"
    
    # 临时切换到生产仓库
    git remote set-url origin "https://${PRODUCTION_TOKEN}@${PRODUCTION_REPO}.git" 2>/dev/null || \
        git remote add origin "https://${PRODUCTION_TOKEN}@${PRODUCTION_REPO}.git"
    
    # 拉取最新数据
    if git fetch origin 2>/dev/null; then
        git checkout origin/main -- .heartbeat/primary.json 2>/dev/null || {
            log "⚠️ 无法获取心跳文件"
            return 1
        }
        log "✅ 心跳数据已更新"
        return 0
    else
        log "⚠️ 无法连接到GitHub"
        return 1
    fi
}

# ========== 检查主节点心跳 ==========
check_primary_heartbeat() {
    log "检查主节点心跳..."
    
    # 首先拉取最新心跳
    fetch_heartbeat || return 1
    
    local heartbeat_file="$HEARTBEAT_DIR/primary.json"
    
    if [ ! -f "$heartbeat_file" ]; then
        log "❌ 心跳文件不存在"
        return 1
    fi
    
    # 解析JSON获取时间戳
    local last_heartbeat=$(jq -r '.timestamp' "$heartbeat_file" 2>/dev/null || cat "$heartbeat_file" | grep -o '"timestamp": [0-9]*' | grep -o '[0-9]*')
    
    if [ -z "$last_heartbeat" ] || [ "$last_heartbeat" = "null" ]; then
        log "❌ 心跳数据无效"
        return 1
    fi
    
    local current_time=$(date +%s)
    local elapsed=$((current_time - last_heartbeat))
    local elapsed_min=$((elapsed / 60))
    local elapsed_hour=$((elapsed / 3600))
    
    log "距离上次心跳: ${elapsed_hour}小时${elapsed_min%60}分 (${elapsed}秒)"
    
    if [ $elapsed -gt $HEARTBEAT_INTERVAL ]; then
        log "⚠️ 心跳超时 (超过2小时)"
        return 1
    fi
    
    log "✅ 心跳正常"
    return 0
}

# ========== 执行故障转移 ==========
perform_failover() {
    log "🚨 执行故障转移..."
    
    # 1. 从生产仓库拉取最新数据
    log "步骤1: 从生产仓库拉取最新数据"
    cd "$WORKSPACE_DIR"
    
    git remote set-url origin "https://${PRODUCTION_TOKEN}@${PRODUCTION_REPO}.git"
    git fetch origin
    git reset --hard origin/main
    
    log "✅ 数据同步完成"
    
    # 2. 升级为主节点
    log "步骤2: 升级为主节点"
    "$WORKSPACE_DIR/scripts/node-admin.sh" promote
    
    # 3. 启动服务
    log "步骤3: 启动服务"
    systemctl start sensen 2>/dev/null || true
    
    # 4. 记录故障转移历史
    log "步骤4: 记录故障转移"
    local failover_time=$(date '+%Y-%m-%d %H:%M:%S')
    cat >> "$WORKSPACE_DIR/memory/failover-history.md" << EOF

## 故障转移记录

- **时间**: $failover_time
- **原因**: 主节点心跳超时 (>2小时)
- **节点ID**: $(cat .node-id 2>/dev/null || echo 'unknown')
- **状态**: ✅ 已完成

EOF
    
    log "✅ 故障转移完成，当前节点已升级为主节点"
    
    # 发送第一次心跳
    send_heartbeat
}

# ========== 主检测循环（备用节点运行）==========
monitor_loop() {
    log "========================================"
    log "启动故障转移监控 (GitHub心跳版)"
    log "心跳间隔: 2小时 | 最大容忍: ${MAX_MISSED_HEARTBEATS}次"
    log "========================================"
    
    local missed_count=0
    
    while true; do
        log "--- 检测循环 ($(date '+%H:%M:%S')) ---"
        
        # 检查是否为备用节点
        if [ -f "$WORKSPACE_DIR/.PRIMARY_NODE" ]; then
            log "当前是主节点，退出监控循环"
            exit 0
        fi
        
        if [ ! -f "$WORKSPACE_DIR/.STANDBY_NODE" ]; then
            log "⚠️ 节点角色未定义，请运行: ./scripts/node-admin.sh demote"
            exit 1
        fi
        
        # 检查主节点状态
        if check_primary_heartbeat; then
            # 心跳正常
            if [ $missed_count -gt 0 ]; then
                log "✅ 主节点恢复，重置错过计数"
                missed_count=0
            fi
        else
            # 心跳异常
            missed_count=$((missed_count + 1))
            log "⚠️ 心跳异常，错过次数: $missed_count/${MAX_MISSED_HEARTBEATS}"
            
            if [ $missed_count -ge $MAX_MISSED_HEARTBEATS ]; then
                log "🚨 连续${MAX_MISSED_HEARTBEATS}次无心跳，触发故障转移"
                perform_failover
                exit 0
            fi
        fi
        
        # 等待下一次检测（2小时）
        log "等待 ${HEARTBEAT_INTERVAL} 秒后进行下次检测..."
        sleep $HEARTBEAT_INTERVAL
    done
}

# ========== 显示状态 ==========
show_status() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}        🌲 故障转移检测状态 (GitHub心跳版) v2.1         ${BLUE}║${NC}"
    echo -e "${BLUE}╠════════════════════════════════════════════════════════╣${NC}"
    echo -e "║ 心跳检测间隔: ${HEARTBEAT_INTERVAL}秒 (2小时)"
    echo -e "║ 最大容忍次数: ${MAX_MISSED_HEARTBEATS}次"
    echo -e "║ 生产仓库: ${PRODUCTION_REPO}"
    echo -e "║ 当前时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "║"
    
    # 拉取最新心跳
    fetch_heartbeat > /dev/null 2>&1 || true
    
    # 检查心跳文件
    local heartbeat_file="$HEARTBEAT_DIR/primary.json"
    if [ -f "$heartbeat_file" ]; then
        local last_heartbeat=$(jq -r '.timestamp' "$heartbeat_file" 2>/dev/null || echo "unknown")
        local last_human=$(jq -r '.human_time' "$heartbeat_file" 2>/dev/null || echo "unknown")
        local node_id=$(jq -r '.node_id' "$heartbeat_file" 2>/dev/null || echo "unknown")
        
        if [ "$last_heartbeat" != "unknown" ] && [ "$last_heartbeat" != "null" ]; then
            local current_time=$(date +%s)
            local elapsed=$((current_time - last_heartbeat))
            local elapsed_min=$((elapsed / 60))
            local elapsed_hour=$((elapsed / 3600))
            
            echo -e "║ 主节点ID: ${node_id}"
            echo -e "║ 上次心跳: ${last_human}"
            echo -e "║ 距离现在: ${elapsed_hour}小时${elapsed_min%60}分"
            
            if [ $elapsed -gt $HEARTBEAT_INTERVAL ]; then
                echo -e "║ 状态: ${RED}⚠️ 超时${NC}"
            else
                echo -e "║ 状态: ${GREEN}✓ 正常${NC}"
            fi
        else
            echo -e "║ 心跳数据: ${YELLOW}无效${NC}"
        fi
    else
        echo -e "║ 心跳文件: ${YELLOW}不存在${NC}"
    fi
    
    echo -e "║"
    echo -e "║ 本机角色:"
    if [ -f "$WORKSPACE_DIR/.PRIMARY_NODE" ]; then
        echo -e "║   ${GREEN}👑 主节点 (PRIMARY)${NC}"
        echo -e "║   ${CYAN}→ 请配置Cron: 0 */2 * * * $WORKSPACE_DIR/scripts/failover.sh heartbeat${NC}"
    elif [ -f "$WORKSPACE_DIR/.STANDBY_NODE" ]; then
        echo -e "║   ${YELLOW}🛡️ 备用节点 (STANDBY)${NC}"
        echo -e "║   ${CYAN}→ 请运行: $WORKSPACE_DIR/scripts/failover.sh monitor${NC}"
    else
        echo -e "║   ${RED}❓ 未定义${NC}"
    fi
    
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
}

# ========== 主入口 ==========
case "$1" in
    status)
        show_status
        ;;
    monitor)
        # 备用节点后台监控
        monitor_loop
        ;;
    heartbeat)
        # 主节点发送心跳
        send_heartbeat
        ;;
    fetch)
        # 手动拉取心跳
        fetch_heartbeat
        ;;
    failover)
        # 手动触发故障转移
        perform_failover
        ;;
    *)
        echo "用法: $0 {status|monitor|heartbeat|fetch|failover}"
        echo ""
        echo "命令:"
        echo "  status    - 查看故障转移检测状态"
        echo "  monitor   - 启动监控循环（备用节点）"
        echo "  heartbeat - 发送心跳信号（主节点）"
        echo "  fetch     - 手动拉取心跳数据"
        echo "  failover  - 手动触发故障转移"
        echo ""
        echo "配置:"
        echo "  心跳间隔: 2小时 (7200秒)"
        echo "  最大容忍: 2次连续无心跳"
        echo "  心跳通道: GitHub仓库"
        echo ""
        echo "主节点Cron配置:"
        echo "  0 */2 * * * $WORKSPACE_DIR/scripts/failover.sh heartbeat"
        exit 1
        ;;
esac
