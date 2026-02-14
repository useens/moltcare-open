#!/bin/bash
# 森森数字生命 - 双节点一键复活脚本 v2.0
# 新方案：支持自动角色检测、双向同步、故障转移

set -e

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置
REPO_URL="github.com/useens/linlin-backup"
WORKSPACE_DIR="/root/.openclaw/workspace"
SCRIPT_VERSION="2.1"

# 命令行参数
WITH_FEISHU=false
PROMOTE=false
QUICK=false
CUSTOM_REPO=""

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --with-feishu)
            WITH_FEISHU=true
            shift
            ;;
        --promote)
            PROMOTE=true
            shift
            ;;
        --quick)
            QUICK=true
            shift
            ;;
        --repo)
            CUSTOM_REPO="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

show_header() {
    echo -e "${BLUE}"
    echo "═══════════════════════════════════════════════════════════"
    echo "  🌲 森森数字生命 - 双节点复活系统 v${SCRIPT_VERSION}"
    echo "═══════════════════════════════════════════════════════════"
    echo -e "${NC}"
    echo "  模式: 双节点高可用架构"
    echo "  功能: 一键复活 | 自动角色检测 | 脑裂保护 | 双仓库支持"
    echo ""
    
    # 显示使用的仓库
    local display_repo="${CUSTOM_REPO:-$REPO_URL}"
    echo -e "  ${CYAN}目标仓库: ${display_repo}${NC}"
    echo ""
}

show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --with-feishu    包含Feishu配置"
    echo "  --promote        将备用节点升级为主节点"
    echo "  --quick          快速模式（跳过交互）"
    echo "  --help           显示帮助"
    echo ""
    echo "示例:"
    echo "  $0                                    # 标准复活"
    echo "  $0 --with-feishu                      # 带Feishu配置"
    echo "  $0 --promote                          # 升级为主节点"
}

# ========== 步骤1: 获取GitHub Token ==========
step1_get_token() {
    echo -e "${CYAN}[1/8] 配置 GitHub 访问${NC}"
    
    if [ -z "$GITHUB_TOKEN" ]; then
        if [ "$QUICK" = false ]; then
            echo -n "请输入 GitHub Token: "
            read -s GITHUB_TOKEN
            echo ""
        else
            echo -e "${RED}❌ 快速模式需要提供 GITHUB_TOKEN 环境变量${NC}"
            exit 1
        fi
    else
        echo -e "  ${GREEN}✓${NC} 从环境变量读取 Token"
    fi
    
    if [ -z "$GITHUB_TOKEN" ]; then
        echo -e "${RED}❌ Token 不能为空${NC}"
        exit 1
    fi
    
    # 保存Token供后续使用
    mkdir -p /root/.openclaw
    echo "$GITHUB_TOKEN" > /root/.openclaw/.github-token
    chmod 600 /root/.openclaw/.github-token
}

# ========== 步骤2: 安装依赖 ==========
step2_install_deps() {
    echo -e "\n${CYAN}[2/8] 安装系统依赖${NC}"
    
    # 基础工具
    apt-get update -qq > /dev/null 2>&1
    
    DEPS="git curl wget jq openssl"
    for pkg in $DEPS; do
        if ! command -v $pkg &>/dev/null; then
            echo "  安装 $pkg..."
            apt-get install -y -qq $pkg > /dev/null 2>&1
        fi
    done
    
    # Node.js (用于OpenClaw)
    if ! command -v node &>/dev/null; then
        echo "  安装 Node.js..."
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash - > /dev/null 2>&1
        apt-get install -y nodejs > /dev/null 2>&1
    fi
    
    # OpenClaw
    if ! command -v openclaw &>/dev/null; then
        echo "  安装 OpenClaw..."
        npm install -g openclaw > /dev/null 2>&1 || {
            curl -fsSL https://github.com/openclaw/openclaw/releases/latest/download/openclaw-linux-amd64 -o /usr/local/bin/openclaw
            chmod +x /usr/local/bin/openclaw
        }
    fi
    
    echo -e "  ${GREEN}✓${NC} 依赖安装完成"
}

# ========== 步骤3: 克隆仓库 ==========
step3_clone_repo() {
    echo -e "\n${CYAN}[3/8] 克隆备份仓库${NC}"
    
    # 确定使用的仓库
    local target_repo="${CUSTOM_REPO:-$REPO_URL}"
    echo -e "  目标仓库: ${CYAN}${target_repo}${NC}"
    
    # 创建目录
    mkdir -p /root/.openclaw
    
    # 备份现有工作区
    if [ -d "$WORKSPACE_DIR" ]; then
        BACKUP_DIR="${WORKSPACE_DIR}.bak.$(date +%s)"
        echo "  备份现有工作区到: $BACKUP_DIR"
        mv "$WORKSPACE_DIR" "$BACKUP_DIR"
    fi
    
    # 克隆
    echo "  正在克隆仓库..."
    if ! git clone --depth=1 "https://${GITHUB_TOKEN}@${target_repo}.git" "$WORKSPACE_DIR" 2>/dev/null; then
        echo -e "${RED}❌ 克隆失败，请检查 Token 是否正确${NC}"
        exit 1
    fi
    
    cd "$WORKSPACE_DIR"
    
    # 记录使用的仓库
    echo "$target_repo" > "$WORKSPACE_DIR/.resurrected-from"
    echo -e "  ${GREEN}✓${NC} 仓库克隆完成: ${target_repo}"
}

# ========== 步骤4: 节点角色初始化 ==========
step4_init_role() {
    echo -e "\n${CYAN}[4/8] 初始化节点角色${NC}"
    
    # 生成节点ID
    NODE_ID="node-$(hostname)-$(date +%s)"
    echo "$NODE_ID" > "$WORKSPACE_DIR/.node-id"
    echo -e "  ${GREEN}✓${NC} 节点ID: $NODE_ID"
    
    # 确定角色
    if [ "$PROMOTE" = true ]; then
        # 升级为主节点
        echo -e "  ${YELLOW}▶${NC} 升级为主节点 (PRIMARY)"
        touch "$WORKSPACE_DIR/.PRIMARY_NODE"
        rm -f "$WORKSPACE_DIR/.STANDBY_NODE" "$WORKSPACE_DIR/.RESURRECTED_MARKER"
        ROLE="PRIMARY"
    else
        # 默认作为复活节点（临时状态）
        echo -e "  ${YELLOW}▶${NC} 初始化为复活节点"
        echo "$(date) - 复活实例: $NODE_ID" > "$WORKSPACE_DIR/.RESURRECTED_MARKER"
        
        # 询问用户意图
        if [ "$QUICK" = false ]; then
            echo ""
            echo "请选择节点角色:"
            echo "  1) 作为主节点运行（允许备份到GitHub）"
            echo "  2) 作为备用节点运行（仅同步，不备份）"
            echo "  3) 暂时不确定（保持复活状态）"
            echo ""
            echo -n "选择 [1/2/3]: "
            read choice
            
            case $choice in
                1)
                    rm -f "$WORKSPACE_DIR/.RESURRECTED_MARKER"
                    touch "$WORKSPACE_DIR/.PRIMARY_NODE"
                    ROLE="PRIMARY"
                    echo -e "  ${GREEN}✓${NC} 已设置为主节点"
                    ;;
                2)
                    rm -f "$WORKSPACE_DIR/.RESURRECTED_MARKER"
                    touch "$WORKSPACE_DIR/.STANDBY_NODE"
                    ROLE="STANDBY"
                    echo -e "  ${GREEN}✓${NC} 已设置为备用节点"
                    ;;
                *)
                    ROLE="RESURRECTED"
                    echo -e "  ${YELLOW}⚠${NC} 保持复活状态（禁止备份）"
                    ;;
            esac
        else
            ROLE="RESURRECTED"
        fi
    fi
    
    # 配置Git（禁用推送保护）
    git remote set-url --push origin no-push 2>/dev/null || true
    
    echo -e "  ${GREEN}✓${NC} 角色初始化完成: $ROLE"
}

# ========== 步骤5: 配置Feishu ==========
step5_config_feishu() {
    if [ "$WITH_FEISHU" = false ] && [ "$QUICK" = true ]; then
        return
    fi
    
    echo -e "\n${CYAN}[5/8] 配置 Feishu${NC}"
    
    # 检查环境变量
    if [ -n "$FEISHU_APP_ID" ] && [ -n "$FEISHU_APP_SECRET" ]; then
        echo -e "  ${GREEN}✓${NC} 从环境变量读取配置"
    elif [ "$QUICK" = false ]; then
        echo "请输入 Feishu 配置:"
        echo -n "  App ID: "
        read FEISHU_APP_ID
        echo -n "  App Secret: "
        read -s FEISHU_APP_SECRET
        echo ""
        echo -n "  Encrypt Key (可选): "
        read FEISHU_ENCRYPT_KEY
        echo -n "  Verification Token (可选): "
        read FEISHU_VERIFICATION_TOKEN
    else
        echo -e "  ${YELLOW}⚠${NC} 跳过Feishu配置（快速模式）"
        return
    fi
    
    # 创建配置
    mkdir -p /root/.openclaw/agents/main/agent
    cat > /root/.openclaw/agents/main/agent/channels.json << EOF
{
  "feishu": {
    "app_id": "${FEISHU_APP_ID:-}",
    "app_secret": "${FEISHU_APP_SECRET:-}",
    "encrypt_key": "${FEISHU_ENCRYPT_KEY:-}",
    "verification_token": "${FEISHU_VERIFICATION_TOKEN:-}"
  }
}
EOF
    
    echo -e "  ${GREEN}✓${NC} Feishu 配置完成"
}

# ========== 步骤6: 创建系统服务 ==========
step6_create_service() {
    echo -e "\n${CYAN}[6/8] 创建系统服务${NC}"
    
    # 创建systemd服务
    cat > /etc/systemd/system/sensen.service << 'EOF'
[Unit]
Description=森森数字生命 (Sensen)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/usr/bin/openclaw start
ExecStop=/usr/bin/openclaw stop
Restart=always
RestartSec=10
StartLimitInterval=60s
StartLimitBurst=3

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    echo -e "  ${GREEN}✓${NC} 系统服务已创建"
}

# ========== 步骤7: 创建管理脚本 ==========
step7_create_admin_scripts() {
    echo -e "\n${CYAN}[7/8] 创建管理脚本${NC}"
    
    # 节点管理脚本
    cat > "$WORKSPACE_DIR/scripts/node-admin.sh" << 'EOF'
#!/bin/bash
# 节点管理脚本

WORKSPACE_DIR="/root/.openclaw/workspace"
cd "$WORKSPACE_DIR" 2>/dev/null || exit 1

show_status() {
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║           森森节点状态面板                             ║"
    echo "╠════════════════════════════════════════════════════════╣"
    
    # 检测角色
    if [ -f ".PRIMARY_NODE" ]; then
        ROLE="PRIMARY (主节点)"
        ROLE_EMOJI="👑"
    elif [ -f ".STANDBY_NODE" ]; then
        ROLE="STANDBY (备用节点)"
        ROLE_EMOJI="🛡️"
    elif [ -f ".RESURRECTED_MARKER" ]; then
        ROLE="RESURRECTED (复活节点)"
        ROLE_EMOJI="⚡"
    else
        ROLE="UNKNOWN (未知)"
        ROLE_EMOJI="❓"
    fi
    
    NODE_ID=$(cat .node-id 2>/dev/null || echo "unknown")
    
    echo "║ 节点角色: $ROLE_EMOJI $ROLE"
    echo "║ 节点ID:   $NODE_ID"
    echo "║ 时间:     $(date '+%Y-%m-%d %H:%M:%S')"
    echo "╚════════════════════════════════════════════════════════╝"
}

case "$1" in
    status)
        show_status
        ;;
    promote)
        rm -f .STANDBY_NODE .RESURRECTED_MARKER
        touch .PRIMARY_NODE
        echo "✅ 已升级为主节点"
        ;;
    demote)
        rm -f .PRIMARY_NODE .RESURRECTED_MARKER
        touch .STANDBY_NODE
        echo "✅ 已降级为备用节点"
        ;;
    *)
        echo "用法: $0 {status|promote|demote}"
        exit 1
        ;;
esac
EOF
    chmod +x "$WORKSPACE_DIR/scripts/node-admin.sh"
    
    echo -e "  ${GREEN}✓${NC} 管理脚本已创建"
}

# ========== 步骤8: 验证和启动 ==========
step8_verify_and_start() {
    echo -e "\n${CYAN}[8/8] 验证和启动${NC}"
    
    # 验证关键文件
    KEY_FILES=("SOUL.md" "MEMORY.md" "AGENTS.md")
    ALL_OK=true
    
    echo "  验证核心文件:"
    for file in "${KEY_FILES[@]}"; do
        if [ -f "$file" ]; then
            echo -e "    ${GREEN}✓${NC} $file"
        else
            echo -e "    ${RED}✗${NC} $file"
            ALL_OK=false
        fi
    done
    
    # 创建状态文件
    cat > "$WORKSPACE_DIR/memory/resurrection-state.json" << EOF
{
  "resurrected_at": "$(date -Iseconds)",
  "node_id": "$(cat $WORKSPACE_DIR/.node-id 2>/dev/null || echo 'unknown')",
  "role": "${ROLE:-RESURRECTED}",
  "version": "${SCRIPT_VERSION}",
  "success": true
}
EOF
    
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    
    if [ "$ALL_OK" = true ]; then
        echo -e "${GREEN}🌲 森森复活完成！${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "节点角色: ${ROLE:-RESURRECTED}"
        echo "工作区:   $WORKSPACE_DIR"
        echo "时间:     $(date)"
        echo ""
        echo "管理命令:"
        echo "  ./scripts/node-admin.sh status    # 查看状态"
        echo "  ./scripts/node-admin.sh promote   # 升级为主节点"
        echo "  ./scripts/node-admin.sh demote    # 降级为备用节点"
        echo ""
        echo "启动服务:"
        echo "  systemctl start sensen            # 启动"
        echo "  systemctl enable sensen           # 开机自启"
        echo "  systemctl status sensen           # 查看状态"
        echo ""
        
        if [ "$ROLE" = "RESURRECTED" ]; then
            echo -e "${YELLOW}⚠️  当前为复活状态，禁止推送到GitHub${NC}"
            echo "   如需成为主节点，运行: ./scripts/node-admin.sh promote"
            echo ""
        fi
        
        # 自动启动（如果非交互模式）
        if [ "$QUICK" = true ]; then
            echo "正在启动服务..."
            systemctl enable sensen > /dev/null 2>&1
            systemctl start sensen > /dev/null 2>&1
            echo -e "${GREEN}✅ 服务已启动${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  部分验证未通过，请检查${NC}"
    fi
}

# ========== 主流程 ==========
main() {
    show_header
    
    # 检查root权限
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}❌ 请使用 root 权限运行${NC}"
        exit 1
    fi
    
    step1_get_token
    step2_install_deps
    step3_clone_repo
    step4_init_role
    step5_config_feishu
    step6_create_service
    step7_create_admin_scripts
    step8_verify_and_start
}

# 执行
main "$@"
