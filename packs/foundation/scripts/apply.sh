#!/bin/bash
#
# Foundation Pack - Apply Script
# 将基础认知包模板应用到目标Agent工作区
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
PACK_NAME="foundation"
PACK_VERSION="1.0.0"
PACK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 日志函数 (必须在验证函数之前定义)
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 安全验证函数 - 防止路径遍历攻击
validate_path() {
    local path="$1"
    local param_name="$2"
    
    # 检查空路径
    if [[ -z "$path" ]]; then
        log_error "${param_name} 不能为空"
        return 1
    fi
    
    # 禁止包含 '..' 的路径
    if [[ "$path" == *".."* ]]; then
        log_error "${param_name} 包含非法的 '..' 路径遍历序列: $path"
        return 1
    fi
    
    # 禁止绝对路径 (以 / 开头)
    if [[ "$path" =~ ^/ ]]; then
        log_error "${param_name} 不能使用绝对路径: $path"
        return 1
    fi
    
    # 禁止以 ~ 开头的路径 (可能被扩展为用户目录)
    if [[ "$path" =~ ^~ ]]; then
        log_error "${param_name} 不能使用 '~' 开头的路径: $path"
        return 1
    fi
    
    # 禁止控制字符
    if [[ "$path" =~ [[:cntrl:]] ]]; then
        log_error "${param_name} 包含控制字符"
        return 1
    fi
    
    return 0
}

# 解析命令行参数
TARGET_WORKSPACE="${1:-$(pwd)}"

# 安全验证目标工作区路径 (SEC-002 修复)
if ! validate_path "$TARGET_WORKSPACE" "TARGET_WORKSPACE"; then
    log_error "路径验证失败，操作已中止"
    exit 1
fi

# 解析为绝对路径 (用于后续操作)
TARGET_WORKSPACE="$(cd "$TARGET_WORKSPACE" 2>/dev/null && pwd)" || {
    log_error "无法解析目标工作区路径: $TARGET_WORKSPACE"
    exit 1
}

# 显示Banner
echo "================================"
echo "  MoltCare Foundation Pack"
echo "  Version: $PACK_VERSION"
echo "================================"
echo ""

# 验证目标工作区
if [[ ! -d "$TARGET_WORKSPACE" ]]; then
    log_error "目标工作区不存在: $TARGET_WORKSPACE"
    exit 1
fi

log_info "目标工作区: $TARGET_WORKSPACE"

# 创建必要的目录
mkdir -p "$TARGET_WORKSPACE/memory"
mkdir -p "$TARGET_WORKSPACE/scripts"
mkdir -p "$TARGET_WORKSPACE/reports"
mkdir -p "$TARGET_WORKSPACE/docs"

log_info "目录结构已创建"

# 模板处理函数
process_template() {
    local template_file="$1"
    local target_file="$2"
    local required="$3"
    local description="$4"
    
    log_info "处理模板: $description"
    
    if [[ ! -f "$template_file" ]]; then
        if [[ "$required" == "true" ]]; then
            log_error "必需模板缺失: $template_file"
            exit 1
        else
            log_warn "可选模板缺失: $template_file"
            return 0
        fi
    fi
    
    # 备份现有文件
    if [[ -f "$target_file" ]]; then
        local backup_name="$(basename "$target_file").backup.$(date +%Y%m%d%H%M%S)"
        cp "$target_file" "$TARGET_WORKSPACE/$backup_name"
        log_info "已备份现有文件到: $backup_name"
    fi
    
    # 读取模板内容并替换变量
    local content
    content=$(cat "$template_file")
    
    # 替换变量
    content="${content//\{\{PACK_VERSION\}\}/$PACK_VERSION}"
    content="${content//\{\{APPLY_TIMESTAMP\}\}/$(date -Iseconds)}"
    content="${content//\{\{AGENT_NAME\}\}/MoltCare Agent}"
    content="${content//\{\{AGENT_ID\}\}/$(uuidgen 2>/dev/null || echo "unknown-$(date +%s)")}"
    content="${content//\{\{RUNTIME_MODE\}\}/完全自主运行}"
    content="${content//\{\{AGENT_STATUS\}\}/🟢 在线}"
    content="${content//\{\{GATEWAY_STATUS\}\}/🟢 active}"
    content="${content//\{\{GATEWAY_REMARK\}\}/运行稳定}"
    content="${content//\{\{DAEMON_STATUS\}\}/⏸️ 已暂停}"
    content="${content//\{\{DAEMON_REMARK\}\}/按需启动}"
    content="${content//\{\{AGENTS_VERSION\}\}/v1.0.0}"
    
    # USER.md 变量
    content="${content//\{\{USER_NAME\}\}/[待填写]}"
    content="${content//\{\{USER_ROLE\}\}/[待填写]}"
    content="${content//\{\{USER_DOMAIN\}\}/[待填写]}"
    content="${content//\{\{TECH_LEVEL\}\}/[待填写]}"
    content="${content//\{\{DETAIL_LEVEL\}\}/适中}"
    content="${content//\{\{TONE\}\}/友好}"
    content="${content//\{\{TECH_DEPTH\}\}/实践}"
    content="${content//\{\{OUTPUT_FORMAT\}\}/文本}"
    content="${content//\{\{SPECIAL_REQUIREMENTS\}\}/[待填写]}"
    content="${content//\{\{SHOW_THINKING\}\}/是}"
    content="${content//\{\{L1_ACTION\}\}/自动}"
    content="${content//\{\{L4_ACTION\}\}/确认}"
    content="${content//\{\{EXTERNAL_ACTION\}\}/必须确认}"
    content="${content//\{\{IMPORTANT_NOTIFY\}\}/即时}"
    content="${content//\{\{DAILY_REPORT\}\}/静默}"
    content="${content//\{\{ERROR_ALERT\}\}/即时}"
    content="${content//\{\{FAMILIAR_TECH\}\}/[待填写]}"
    content="${content//\{\{INTEREST_AREAS\}\}/[待填写]}"
    content="${content//\{\{LEARNING_GOALS\}\}/[待填写]}"
    content="${content//\{\{EXPLICIT_BANS\}\}/[待填写]}"
    content="${content//\{\{NEED_CONFIRM\}\}/[待填写]}"
    content="${content//\{\{PRIVACY_BOUNDARIES\}\}/[待填写]}"
    content="${content//\{\{DATE\}\}/$(date +%Y-%m-%d)}"
    content="${content//\{\{EVENT\}\}/[待填写]}"
    content="${content//\{\{SIGNAL\}\}/[待填写]}"
    content="${content//\{\{PREF\}\}/[待填写]}"
    content="${content//\{\{OLD\}\}/[待填写]}"
    content="${content//\{\{NEW\}\}/[待填写]}"
    
    # MEMORY.md 变量
    content="${content//\{\{timestamp\}\}/$(date -Iseconds)}"
    content="${content//\{\{learning_debt_count\}\}/0}"
    content="${content//\{\{config_version\}\}/$PACK_VERSION}"
    content="${content//\{\{today_interactions\}\}/0}"
    content="${content//\{\{tool_calls\}\}/0}"
    content="${content//\{\{expert_discussions\}\}/0}"
    content="${content//\{\{errors\}\}/0}"
    
    # 写入目标文件
    echo "$content" > "$target_file"
    log_success "已生成: $target_file"
}

# 读取manifest.json并应用模板
if [[ ! -f "$PACK_DIR/manifest.json" ]]; then
    log_error "manifest.json 不存在于: $PACK_DIR"
    exit 1
fi

log_info "读取 manifest.json..."

# 应用 SOUL.md
process_template \
    "$PACK_DIR/templates/SOUL.md" \
    "$TARGET_WORKSPACE/SOUL.md" \
    "true" \
    "Agent灵魂定义 - 多专家决策核心原则"

# 应用 AGENTS.md
process_template \
    "$PACK_DIR/templates/AGENTS.md" \
    "$TARGET_WORKSPACE/AGENTS.md" \
    "true" \
    "Agent操作手册 - 工作流和触发词"

# 应用 USER.md（如果不存在则创建）
if [[ ! -f "$TARGET_WORKSPACE/USER.md" ]]; then
    process_template \
        "$PACK_DIR/templates/USER.md" \
        "$TARGET_WORKSPACE/USER.md" \
        "false" \
        "用户画像模板 - 带示例和配置指南"
else
    log_warn "USER.md 已存在，跳过（保留现有用户配置）"
fi

# 应用 MEMORY.md（如果不存在则创建）
if [[ ! -f "$TARGET_WORKSPACE/MEMORY.md" ]]; then
    process_template \
        "$PACK_DIR/templates/MEMORY.md" \
        "$TARGET_WORKSPACE/MEMORY.md" \
        "false" \
        "系统记忆仪表盘 - 任务和学习债务管理"
else
    log_warn "MEMORY.md 已存在，跳过"
fi

# 创建应用记录
cat > "$TARGET_WORKSPACE/.foundation-applied" << EOF
{
  "pack": "$PACK_NAME",
  "version": "$PACK_VERSION",
  "appliedAt": "$(date -Iseconds)",
  "workspace": "$TARGET_WORKSPACE",
  "templates": [
    "SOUL.md",
    "AGENTS.md",
    "USER.md",
    "MEMORY.md"
  ]
}
EOF

log_success "应用记录已保存: .foundation-applied"

echo ""
echo "================================"
log_success "Foundation Pack 应用完成!"
echo "================================"
echo ""
echo "已生成文件:"
echo "  - SOUL.md    (核心原则 + 多专家决策机制)"
echo "  - AGENTS.md  (操作手册 + 触发词系统)"
echo "  - USER.md    (用户画像模板 + 配置指南)"
echo "  - MEMORY.md  (系统仪表盘 + 任务管理)"
echo ""
echo "下一步:"
echo "  1. 阅读 SOUL.md 了解核心原则"
echo "  2. 阅读 AGENTS.md 了解工作流"
echo "  3. 个性化编辑 USER.md（有示例哦）"
echo "  4. 使用 MEMORY.md 跟踪任务和学习债务"
echo ""
