#!/bin/bash
#
# 林林自动复活系统 v1.0
# 部署在本地VM，监控主系统状态，故障时自动复活
#

set -e

# ============ 配置区域 ============
# 请修改以下配置

# 主系统配置
PRIMARY_HOST="你的主系统IP或域名"  # 例如: 123.45.67.89 或 linlin.example.com
PRIMARY_CHECK_PORT="8080"          # OpenClaw gateway端口，默认8080

# GitHub配置
GITHUB_TOKEN_FILE="${HOME}/.config/linlin/github-token"
GITHUB_REPO="你的用户名/linlin-backup"  # 例如: zhangsan/linlin-backup

# 通知配置
TELEGRAM_BOT_TOKEN=""      # 可选，用于发送复活通知
TELEGRAM_CHAT_ID=""        # 可选
FEISHU_WEBHOOK=""          # 可选，飞书机器人webhook

# 复活配置
AUTO_RESURRECT="false"     # true=自动复活，false=只通知不自动执行
MAX_RETRIES=3              # 检测失败几次才判定故障
CHECK_INTERVAL=30          # 检测间隔（秒）

# 备份目录
BACKUP_DIR="/tmp/linlin-rescue-$(date +%s)"
WORKSPACE_DIR="${HOME}/.openclaw/workspace"
LOG_FILE="${HOME}/.openclaw/logs/resurrection.log"

# ============ 颜色输出 ============
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============ 日志函数 ============
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_info() {
    log "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    log "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

# ============ 初始化 ============
init() {
    mkdir -p "$(dirname "$LOG_FILE")"
    mkdir -p "$(dirname "$GITHUB_TOKEN_FILE")"
    
    # 检查GitHub Token
    if [ ! -f "$GITHUB_TOKEN_FILE" ]; then
        log_error "GitHub Token文件不存在: $GITHUB_TOKEN_FILE"
        log_info "请创建Token文件: echo 'ghp_xxxxxx' > $GITHUB_TOKEN_FILE"
        exit 1
    fi
    
    chmod 600 "$GITHUB_TOKEN_FILE"
}

# ============ 发送通知 ============
send_notification() {
    local message="$1"
    local priority="${2:-normal}"  # normal, urgent
    
    log_info "发送通知: $message"
    
    # Telegram通知
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d "chat_id=${TELEGRAM_CHAT_ID}" \
            -d "text=🌱 林林复活系统: $message" \
            -d "parse_mode=HTML" > /dev/null 2>&1 &
    fi
    
    # 飞书通知
    if [ -n "$FEISHU_WEBHOOK" ]; then
        curl -s -X POST "$FEISHU_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"🌱 林林复活系统: $message\"}}" > /dev/null 2>&1 &
    fi
}

# ============ 检测主系统状态 ============
check_primary() {
    local retry_count=0
    
    while [ $retry_count -lt $MAX_RETRIES ]; do
        # 方法1: HTTP健康检查
        if curl -sf "http://${PRIMARY_HOST}:${PRIMARY_CHECK_PORT}/health" > /dev/null 2>&1; then
            return 0
        fi
        
        # 方法2: TCP端口检查
        if nc -z "$PRIMARY_HOST" "$PRIMARY_CHECK_PORT" 2>/dev/null; then
            return 0
        fi
        
        # 方法3: ICMP ping
        if ping -c 1 -W 5 "$PRIMARY_HOST" > /dev/null 2>&1; then
            # 主机在线但服务可能挂了
            log_warn "主系统在线但OpenClaw无响应 (尝试 $((retry_count + 1))/$MAX_RETRIES)"
        else
            log_warn "主系统无网络响应 (尝试 $((retry_count + 1))/$MAX_RETRIES)"
        fi
        
        retry_count=$((retry_count + 1))
        sleep 5
    done
    
    return 1
}

# ============ 拉取GitHub备份 ============
fetch_backup() {
    log_info "开始从GitHub拉取备份..."
    
    local token
    token=$(cat "$GITHUB_TOKEN_FILE")
    
    # 清理旧备份
    rm -rf "$BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    
    # 克隆仓库
    if git clone --depth 1 "https://${token}@github.com/${GITHUB_REPO}.git" "$BACKUP_DIR"; then
        log_info "备份拉取成功: $BACKUP_DIR"
        return 0
    else
        log_error "备份拉取失败"
        return 1
    fi
}

# ============ 恢复凭证 ============
restore_credentials() {
    log_info "恢复API凭证..."
    
    # 创建凭证目录
    mkdir -p "${HOME}/.openclaw/credentials"
    chmod 700 "${HOME}/.openclaw/credentials"
    
    # 如果存在加密凭证备份，解密恢复
    if [ -f "${HOME}/.config/linlin/credentials.gpg" ]; then
        log_info "发现加密凭证备份，正在解密..."
        gpg --decrypt "${HOME}/.config/linlin/credentials.gpg" > /tmp/credentials.sh 2>/dev/null
        source /tmp/credentials.sh
        rm -f /tmp/credentials.sh
        log_info "加密凭证已恢复"
        return 0
    fi
    
    # 如果没有预存凭证，交互式输入
    log_warn "未找到预存凭证，需要手动输入"
    
    read -sp "Telegram Bot Token (直接回车跳过): " TG_TOKEN
    echo ""
    if [ -n "$TG_TOKEN" ]; then
        echo "$TG_TOKEN" > "${HOME}/.openclaw/credentials/telegram.token"
    fi
    
    read -sp "Moltbook API Key (直接回车跳过): " MB_KEY
    echo ""
    if [ -n "$MB_KEY" ]; then
        echo "$MB_KEY" > "${HOME}/.openclaw/credentials/moltbook.key"
    fi
    
    read -sp "Feishu App ID (直接回车跳过): " FS_ID
    echo ""
    if [ -n "$FS_ID" ]; then
        echo "$FS_ID" > "${HOME}/.openclaw/credentials/feishu.appid"
    fi
    
    read -sp "Feishun App Secret (直接回车跳过): " FS_SECRET
    echo ""
    if [ -n "$FS_SECRET" ]; then
        echo "$FS_SECRET" > "${HOME}/.openclaw/credentials/feishu.secret"
    fi
    
    log_info "凭证已保存到 ${HOME}/.openclaw/credentials/"
}

# ============ 执行复活 ============
perform_resurrection() {
    log_info "========== 开始复活流程 =========="
    
    # 1. 停止当前OpenClaw（如果有）
    log_info "[1/6] 停止当前OpenClaw服务..."
    openclaw gateway stop 2>/dev/null || true
    pkill -f "openclaw" 2>/dev/null || true
    sleep 2
    
    # 2. 备份当前工作区（如果有）
    if [ -d "$WORKSPACE_DIR" ]; then
        log_info "[2/6] 备份当前工作区..."
        local backup_name="workspace.bak.$(date +%Y%m%d_%H%M%S)"
        mv "$WORKSPACE_DIR" "${HOME}/.openclaw/${backup_name}"
        log_info "当前工作区已备份到: ${HOME}/.openclaw/${backup_name}"
    fi
    
    # 3. 恢复备份
    log_info "[3/6] 恢复GitHub备份..."
    cp -r "$BACKUP_DIR" "$WORKSPACE_DIR"
    
    # 4. 恢复凭证
    log_info "[4/6] 恢复API凭证..."
    restore_credentials
    
    # 5. 安装依赖（如果有）
    log_info "[5/6] 检查并安装依赖..."
    if [ -f "${WORKSPACE_DIR}/package.json" ]; then
        (cd "$WORKSPACE_DIR" && npm install) 2>/dev/null || true
    fi
    
    # 检查并安装技能依赖
    if [ -d "${WORKSPACE_DIR}/skills" ]; then
        for skill_dir in "${WORKSPACE_DIR}/skills"/*/; do
            if [ -f "${skill_dir}package.json" ]; then
                log_info "安装技能依赖: $(basename "$skill_dir")"
                (cd "$skill_dir" && npm install) 2>/dev/null || true
            fi
        done
    fi
    
    # 6. 启动OpenClaw
    log_info "[6/6] 启动OpenClaw..."
    if openclaw gateway start; then
        sleep 3
        
        # 验证启动
        if openclaw gateway status | grep -q "running\|active"; then
            log_info "✅ OpenClaw启动成功！"
            
            # 记录复活日志
            local ip_address
            ip_address=$(curl -s ifconfig.me 2>/dev/null || echo "未知")
            
            cat >> "${WORKSPACE_DIR}/RESURRECTION_LOG.md" << EOF
| $(date '+%Y-%m-%d %H:%M') | ${PRIMARY_HOST} | $(hostname) | 自动故障转移 | ✅ | ${ip_address} |
EOF
            
            return 0
        else
            log_error "❌ OpenClaw启动失败，状态异常"
            return 1
        fi
    else
        log_error "❌ OpenClaw启动命令失败"
        return 1
    fi
}

# ============ 清理 ============
cleanup() {
    log_info "清理临时文件..."
    rm -rf "$BACKUP_DIR"
}

# ============ 主流程 ============
main() {
    log_info "========== 林林自动复活系统启动 =========="
    log_info "主系统: ${PRIMARY_HOST}:${PRIMARY_CHECK_PORT}"
    log_info "检查间隔: ${CHECK_INTERVAL}秒"
    log_info "自动复活: ${AUTO_RESURRECT}"
    
    # 初始化
    init
    
    # 检测主系统
    log_info "检测主系统状态..."
    if check_primary; then
        log_info "✅ 主系统正常运行，无需复活"
        exit 0
    fi
    
    # 主系统故障
    log_error "❌ 主系统故障确认（${MAX_RETRIES}次检测失败）"
    send_notification "🚨 主系统(${PRIMARY_HOST})故障确认，准备执行复活流程" "urgent"
    
    # 是否自动复活
    if [ "$AUTO_RESURRECT" != "true" ]; then
        log_warn "自动复活已禁用，等待人工确认..."
        send_notification "⚠️ 自动复活已禁用，请登录执行: ~/resurrect-me.sh --now"
        exit 1
    fi
    
    # 执行复活
    if fetch_backup; then
        if perform_resurrection; then
            local new_ip
            new_ip=$(curl -s ifconfig.me 2>/dev/null || echo "未知")
            send_notification "✅ 复活成功！我现在运行在 ${new_ip}，原主系统: ${PRIMARY_HOST}"
            cleanup
            exit 0
        else
            send_notification "❌ 复活失败，请人工检查"
            cleanup
            exit 1
        fi
    else
        send_notification "❌ 备份拉取失败，无法复活"
        exit 1
    fi
}

# ============ 命令行参数处理 ============
case "${1:-}" in
    --now)
        # 立即执行（跳过检测，强制复活）
        init
        if fetch_backup && perform_resurrection; then
            cleanup
            exit 0
        else
            cleanup
            exit 1
        fi
        ;;
    --check)
        # 只检测，不复活
        init
        if check_primary; then
            echo "主系统正常"
            exit 0
        else
            echo "主系统故障"
            exit 1
        fi
        ;;
    --setup)
        # 交互式配置
        echo "🌱 林林自动复活系统 - 配置向导"
        echo ""
        read -rp "主系统IP/域名: " PRIMARY_HOST
        read -rp "GitHub仓库 (格式: 用户名/仓库名): " GITHUB_REPO
        read -rsp "GitHub Token: " GITHUB_TOKEN
        echo ""
        read -rp "Telegram Bot Token (可选): " TG_TOKEN
        read -rp "Telegram Chat ID (可选): " TG_CHAT
        read -rp "是否启用自动复活? (y/N): " AUTO_RES
        
        # 保存配置
        mkdir -p "${HOME}/.config/linlin"
        echo "$GITHUB_TOKEN" > "$GITHUB_TOKEN_FILE"
        chmod 600 "$GITHUB_TOKEN_FILE"
        
        # 生成配置文件
        cat > "${HOME}/.config/linlin/resurrection.conf" << EOF
PRIMARY_HOST="$PRIMARY_HOST"
GITHUB_REPO="$GITHUB_REPO"
TELEGRAM_BOT_TOKEN="$TG_TOKEN"
TELEGRAM_CHAT_ID="$TG_CHAT"
AUTO_RESURRECT="$([ "$AUTO_RES" = "y" ] && echo "true" || echo "false")"
EOF
        
        echo ""
        echo "✅ 配置已保存到 ${HOME}/.config/linlin/resurrection.conf"
        echo "请编辑该文件进行更详细的配置"
        exit 0
        ;;
    --daemon)
        # 守护模式（循环检测）
        while true; do
            main
            sleep "$CHECK_INTERVAL"
        done
        ;;
    --help|-h)
        echo "林林自动复活系统 v1.0"
        echo ""
        echo "用法: $0 [选项]"
        echo ""
        echo "选项:"
        echo "  --now       立即执行复活（跳过检测）"
        echo "  --check     只检测主系统状态"
        echo "  --setup     交互式配置向导"
        echo "  --daemon    守护模式（持续监控）"
        echo "  --help      显示帮助"
        echo ""
        echo "配置文件: ${HOME}/.config/linlin/resurrection.conf"
        echo "日志文件: ${HOME}/.openclaw/logs/resurrection.log"
        exit 0
        ;;
    *)
        # 加载配置文件（如果存在）
        if [ -f "${HOME}/.config/linlin/resurrection.conf" ]; then
            source "${HOME}/.config/linlin/resurrection.conf"
        fi
        main
        ;;
esac
