#!/bin/bash
# 节点管理脚本 v2.1 (双仓库版)

WORKSPACE_DIR="/root/.openclaw/workspace"
cd "$WORKSPACE_DIR" 2>/dev/null || exit 1

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

show_status() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}           🌲 森森节点状态面板 v2.1                      ${BLUE}║${NC}"
    echo -e "${BLUE}╠════════════════════════════════════════════════════════╣${NC}"
    
    # 检测角色
    if [ -f ".PRIMARY_NODE" ]; then
        ROLE="PRIMARY (主节点)"
        ROLE_EMOJI="👑"
        ROLE_COLOR="$GREEN"
    elif [ -f ".STANDBY_NODE" ]; then
        ROLE="STANDBY (备用节点)"
        ROLE_EMOJI="🛡️"
        ROLE_COLOR="$YELLOW"
    elif [ -f ".RESURRECTED_MARKER" ]; then
        ROLE="RESURRECTED (复活节点)"
        ROLE_EMOJI="⚡"
        ROLE_COLOR="$YELLOW"
    else
        ROLE="UNKNOWN (未知)"
        ROLE_EMOJI="❓"
        ROLE_COLOR="$RED"
    fi
    
    NODE_ID=$(cat .node-id 2>/dev/null || echo "unknown")
    GIT_REMOTE=$(git remote get-url origin 2>/dev/null | sed 's/.*@//' | sed 's/https:\/\///' | sed 's/\.git//')
    
    echo -e "║ 节点角色: ${ROLE_COLOR}${ROLE_EMOJI} ${ROLE}${NC}"
    echo -e "║ 节点ID:   ${NODE_ID}"
    echo -e "║ Git仓库:  ${GIT_REMOTE:-未配置}"
    echo -e "║ 时间:     $(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
}

show_repos() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}           📦 配置仓库                                   ${BLUE}║${NC}"
    echo -e "${BLUE}╠════════════════════════════════════════════════════════╣${NC}"
    echo -e "║ 方案仓库: github.com/useens/linlin-backup              │"
    echo -e "║   用途: v2.0双节点复活方案                             │"
    echo -e "║   使用: 新节点部署、备用节点设置                        │"
    echo -e "║                                                        │"
    echo -e "║ 生产仓库: github.com/linlinofVM/sensen-backup          │"
    echo -e "║   用途: 生产环境数据备份                               │"
    echo -e "║   使用: 生产备份、故障恢复                             │"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
}

case "$1" in
    status)
        show_status
        ;;
    repos)
        show_repos
        ;;
    promote)
        rm -f .STANDBY_NODE .RESURRECTED_MARKER
        touch .PRIMARY_NODE
        echo -e "${GREEN}✅ 已升级为主节点${NC}"
        echo "现在可以推送到GitHub: git push origin main"
        ;;
    demote)
        rm -f .PRIMARY_NODE .RESURRECTED_MARKER
        touch .STANDBY_NODE
        echo -e "${YELLOW}✅ 已降级为备用节点${NC}"
        echo "GitHub推送已禁用，仅允许拉取同步"
        ;;
    *)
        echo "用法: $0 {status|repos|promote|demote}"
        exit 1
        ;;
esac
