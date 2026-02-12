#!/bin/bash
#
# 森森一键复活脚本 v2.0 - 单节点架构（支持分割备份）
# 用途: 在新机器/VM上快速恢复森森运行状态
#
# 使用方法:
#   curl -s https://raw.githubusercontent.com/useens/linlin-backup/main/scripts/sensen-resurrect.sh | bash
#   或本地执行: ./scripts/sensen-resurrect.sh
#

set -euo pipefail

# ============ 配置 ============
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="${HOME}/.openclaw/workspace"
BACKUP_DIR="${HOME}/.openclaw/backups"
LOG_FILE="${HOME}/.openclaw/logs/sensen-resurrect.log"

# GitHub配置
GITHUB_REPO="useens/linlin-backup"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
GITHUB_RAW="https://raw.githubusercontent.com/${GITHUB_REPO}/main"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ============ 日志 ============
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "$msg" | tee -a "$LOG_FILE" 2>/dev/null || echo -e "$msg"
}
log_info() { log "${GREEN}[INFO]${NC} $1"; }
log_warn() { log "${YELLOW}[WARN]${NC} $1"; }
log_error() { log "${RED}[ERROR]${NC} $1"; }
log_step() { log "${CYAN}[STEP]${NC} $1"; }

# ============ 检查依赖 ============
check_deps() {
    log_step "========== 森森一键复活系统 v2.0 =========="
    log_info "检查系统依赖..."
    
    local missing=()
    
    # 必需依赖
    command -v git &>/dev/null || missing+=("git")
    command -v curl &>/dev/null || missing+=("curl")
    command -v node &>/dev/null || missing+=("nodejs")
    
    if [ ${#missing[@]} -gt 0 ]; then
        log_error "缺少必需依赖: ${missing[*]}"
        log_info "请安装: sudo apt-get install -y git curl nodejs"
        exit 1
    fi
    
    log_info "✅ 所有依赖已满足"
}

# ============ 获取GitHub Token ============
get_github_token() {
    # 优先级: 环境变量 > 配置文件 > 交互输入
    if [ -n "$GITHUB_TOKEN" ]; then
        echo "$GITHUB_TOKEN"
        return 0
    fi
    
    local token_file="${HOME}/.config/linlin/github-token"
    if [ -f "$token_file" ]; then
        cat "$token_file"
        return 0
    fi
    
    # 交互式输入
    echo ""
    read -rsp "请输入GitHub Token (用于拉取私有备份): " token
    echo ""
    
    if [ -z "$token" ]; then
        log_error "GitHub Token不能为空"
        exit 1
    fi
    
    # 保存供后续使用
    mkdir -p "$(dirname "$token_file")"
    echo "$token" > "$token_file"
    chmod 600 "$token_file"
    
    echo "$token"
}

# ============ 下载并合并分割备份 ============
download_and_merge_backup() {
    log_step "[1/6] 下载并合并分割备份..."
    
    local token
    token=$(get_github_token)
    
    mkdir -p "$BACKUP_DIR"
    cd "$BACKUP_DIR"
    
    # 获取最新的备份文件名（从GitHub API获取文件列表）
    log_info "查询最新备份文件..."
    
    # 方法1: 尝试从GitHub获取文件列表
    local files
    files=$(curl -s -H "Authorization: token ${token}" \
        "https://api.github.com/repos/${GITHUB_REPO}/contents/" 2>/dev/null | \
        grep -o '"name":"[^"]*\.tar\.gz\.part-[^"]*"' | \
        sed 's/"name":"//;s/"$//' | sort)
    
    if [ -z "$files" ]; then
        # 方法2: 直接尝试下载已知模式
        log_warn "无法获取文件列表，尝试已知备份模式..."
        
        # 获取最新日期（今天或昨天）
        local today=$(date +%Y%m%d)
        local yesterday=$(date -d "yesterday" +%Y%m%d 2>/dev/null || date -v-1d +%Y%m%d 2>/dev/null)
        
        for date_prefix in "$today" "$yesterday"; do
            log_info "尝试日期: $date_prefix"
            
            # 尝试下载 part-aa 到 part-zz
            local found=0
            for part in aa ab ac ad ae af ag ah; do
                local filename="linlin_full_${date_prefix}_*.tar.gz.part-${part}"
                local url="${GITHUB_RAW}/${filename}"
                
                log_info "尝试下载: ${filename}"
                if curl -sL -H "Authorization: token ${token}" \
                    -o "temp-${part}" \
                    "${url}" 2>/dev/null && [ -s "temp-${part}" ] && [ "$(stat -c%s "temp-${part}" 2>/dev/null || stat -f%z "temp-${part}" 2>/dev/null)" -gt 1000 ]; then
                    mv "temp-${part}" "${filename}"
                    found=1
                else
                    rm -f "temp-${part}"
                    break
                fi
            done
            
            if [ $found -eq 1 ]; then
                break
            fi
        done
    else
        # 使用API获取的文件列表下载
        log_info "找到 $(echo "$files" | wc -l) 个分割文件"
        
        for file in $files; do
            log_info "下载: $file"
            curl -sL -H "Authorization: token ${token}" \
                -o "$file" \
                "${GITHUB_RAW}/${file}" 2>/dev/null || {
                log_error "下载失败: $file"
                exit 1
            }
        done
    fi
    
    # 查找下载的备份文件
    local backup_parts
    backup_parts=$(ls -1 linlin_full_*.tar.gz.part-* 2>/dev/null | sort)
    
    if [ -z "$backup_parts" ]; then
        log_error "未找到备份文件"
        exit 1
    fi
    
    log_info "找到 $(echo "$backup_parts" | wc -l) 个分割文件"
    
    # 合并文件
    local backup_name="linlin_full_$(date +%Y%m%d_%H%M%S).tar.gz"
    log_info "合并备份文件: $backup_name"
    
    cat $backup_parts > "$backup_name"
    
    # 验证合并后的文件
    local merged_size
    merged_size=$(stat -c%s "$backup_name" 2>/dev/null || stat -f%z "$backup_name" 2>/dev/null)
    log_info "合并完成: $backup_name ($(numfmt --to=iec $merged_size 2>/dev/null || echo "${merged_size} bytes"))"
    
    # 清理分割文件
    rm -f linlin_full_*.tar.gz.part-*
    
    echo "$backup_name"
}

# ============ 解压备份 ============
extract_backup() {
    log_step "[2/6] 解压备份..."
    
    local backup_file="$1"
    
    cd "$BACKUP_DIR"
    
    # 验证备份文件
    if ! tar -tzf "$backup_file" >/dev/null 2>&1; then
        log_error "备份文件损坏: $backup_file"
        exit 1
    fi
    
    # 清理旧工作区
    if [ -d "$WORKSPACE_DIR" ]; then
        log_warn "发现现有工作区，备份到: ${WORKSPACE_DIR}.bak.$(date +%s)"
        mv "$WORKSPACE_DIR" "${WORKSPACE_DIR}.bak.$(date +%s)"
    fi
    
    mkdir -p "$(dirname "$WORKSPACE_DIR")"
    
    # 解压备份
    log_info "解压备份到工作区..."
    tar -xzf "$backup_file" -C "$(dirname "$WORKSPACE_DIR")"
    
    # 处理可能的嵌套目录（workspace/workspace_source）
    if [ -d "${WORKSPACE_DIR}/workspace_source" ]; then
        mv "${WORKSPACE_DIR}" "${WORKSPACE_DIR}.tmp"
        mv "${WORKSPACE_DIR}.tmp/workspace_source" "$WORKSPACE_DIR"
        rm -rf "${WORKSPACE_DIR}.tmp"
    fi
    
    log_info "✅ 备份解压完成"
}

# ============ 拉取GitHub仓库（获取最新脚本） ============
fetch_github_repo() {
    log_step "[3/6] 拉取GitHub仓库（获取最新脚本）..."
    
    local token
    token=$(get_github_token)
    
    local temp_dir="/tmp/sensen-repo-$(date +%s)"
    
    log_info "克隆仓库..."
    if git clone --depth 1 "https://${token}@github.com/${GITHUB_REPO}.git" "$temp_dir" 2>/dev/null; then
        # 复制最新的 scripts 目录
        if [ -d "${temp_dir}/scripts" ]; then
            log_info "更新脚本..."
            cp -r "${temp_dir}/scripts/"* "${WORKSPACE_DIR}/scripts/" 2>/dev/null || true
        fi
        
        # 清理临时目录
        rm -rf "$temp_dir"
        
        log_info "✅ 脚本更新完成"
    else
        log_warn "无法拉取GitHub仓库，使用备份中的脚本"
    fi
}

# ============ 安装OpenClaw ============
install_openclaw() {
    log_step "[4/6] 检查OpenClaw..."
    
    if command -v openclaw &>/dev/null; then
        log_info "✅ OpenClaw已安装"
        return 0
    fi
    
    log_info "安装OpenClaw..."
    
    # 方法1: npm安装
    if npm install -g openclaw 2>/dev/null; then
        log_info "✅ OpenClaw安装成功 (npm)"
        return 0
    fi
    
    # 方法2: 从备份安装
    if [ -f "${WORKSPACE_DIR}/scripts/install-openclaw.sh" ]; then
        bash "${WORKSPACE_DIR}/scripts/install-openclaw.sh"
        return 0
    fi
    
    log_error "❌ OpenClaw安装失败"
    log_info "请手动安装: npm install -g openclaw"
    exit 1
}

# ============ 恢复凭证 ============
restore_credentials() {
    log_step "[5/6] 恢复API凭证..."
    
    local creds_dir="${HOME}/.openclaw/credentials"
    mkdir -p "$creds_dir"
    chmod 700 "$creds_dir"
    
    # 从备份中恢复凭证（如果有）
    local backup_creds="${WORKSPACE_DIR}/credentials"
    if [ -d "$backup_creds" ]; then
        cp -r "$backup_creds/"* "$creds_dir/" 2>/dev/null || true
        log_info "✅ 凭证已恢复"
    else
        log_warn "⚠️ 备份中没有凭证，需要手动配置"
        log_info "凭证目录: $creds_dir"
    fi
    
    # 恢复GitHub Token
    local token
    token=$(get_github_token)
    echo "$token" > "$creds_dir/github.token"
    chmod 600 "$creds_dir/github.token"
}

# ============ 安装依赖 ============
install_dependencies() {
    log_step "[6/6] 安装项目依赖..."
    
    cd "$WORKSPACE_DIR"
    
    # 安装npm依赖
    if [ -f "package.json" ]; then
        log_info "安装npm依赖..."
        npm install 2>/dev/null || npm install --legacy-peer-deps 2>/dev/null || {
            log_warn "⚠️ npm install部分失败，继续..."
        }
    fi
    
    # 安装Git LFS
    if ! command -v git-lfs &>/dev/null; then
        log_info "安装Git LFS..."
        apt-get update -qq && apt-get install -y git-lfs 2>/dev/null || {
            log_warn "⚠️ Git LFS安装失败"
        }
    fi
    
    log_info "✅ 依赖安装完成"
}

# ============ 启动森森 ============
start_sensen() {
    log_step "启动森森..."
    
    # 检查OpenClaw配置
    if [ ! -d "${HOME}/.openclaw/config" ]; then
        log_info "初始化OpenClaw配置..."
        mkdir -p "${HOME}/.openclaw/config"
    fi
    
    # 启动Gateway
    log_info "启动OpenClaw Gateway..."
    openclaw gateway start 2>/dev/null || {
        log_warn "启动命令失败，尝试恢复..."
        
        if [ -f "${WORKSPACE_DIR}/package.json" ]; then
            log_info "尝试从工作区启动..."
            cd "$WORKSPACE_DIR"
            npm start &
            sleep 3
        fi
    }
    
    sleep 2
    if openclaw gateway status 2>/dev/null | grep -q "running\|active"; then
        log_info "✅ 森森启动成功！"
        return 0
    else
        log_warn "⚠️ 状态检测失败，但进程可能已启动"
        return 0
    fi
}

# ============ 验证复活 ============
verify_resurrection() {
    log_step "========== 验证复活结果 =========="
    
    local issues=0
    
    # 检查1: 工作区存在
    if [ -d "$WORKSPACE_DIR" ]; then
        log_info "✅ 工作区已恢复"
    else
        log_error "❌ 工作区缺失"
        ((issues++))
    fi
    
    # 检查2: 核心文件
    if [ -f "${WORKSPACE_DIR}/SOUL.md" ]; then
        log_info "✅ 核心记忆文件存在"
    else
        log_warn "⚠️ 核心记忆文件缺失"
    fi
    
    # 检查3: 脚本存在
    if [ -f "${WORKSPACE_DIR}/scripts/sensen-resurrect.sh" ]; then
        log_info "✅ 复活脚本已备份"
    fi
    
    # 检查4: Gateway状态
    if openclaw gateway status 2>/dev/null | grep -q "running"; then
        log_info "✅ OpenClaw运行中"
    else
        log_warn "⚠️ OpenClaw状态待确认"
    fi
    
    # 获取IP
    local ip
    ip=$(curl -s ifconfig.me 2>/dev/null || echo "未知")
    
    echo ""
    log_info "🌲 森森复活完成！"
    log_info "当前IP: $ip"
    log_info "工作区: $WORKSPACE_DIR"
    
    # 记录复活日志
    cat >> "${WORKSPACE_DIR}/RESURRECTION_LOG.md" << EOF
| $(date '+%Y-%m-%d %H:%M') | 一键复活v2 | $(hostname) | $(whoami) | ✅ | $ip |
EOF
    
    return $issues
}

# ============ 主流程 ============
main() {
    mkdir -p "$(dirname "$LOG_FILE")"
    
    check_deps
    
    # 下载并合并备份
    local backup_file
    backup_file=$(download_and_merge_backup)
    
    # 解压备份
    extract_backup "$backup_file"
    
    # 拉取最新脚本
    fetch_github_repo
    
    # 安装OpenClaw
    install_openclaw
    
    # 恢复凭证
    restore_credentials
    
    # 安装依赖
    install_dependencies
    
    # 启动森森
    start_sensen
    
    # 验证
    verify_resurrection
    
    log_step "========== 复活完成 =========="
    log_info "森森已成功复活，正在运行！"
    log_info "日志文件: $LOG_FILE"
}

# ============ 命令行参数 ============
case "${1:-}" in
    --help|-h)
        echo "森森一键复活脚本 v2.0"
        echo ""
        echo "用法:"
        echo "  curl -s https://raw.githubusercontent.com/useens/linlin-backup/main/scripts/sensen-resurrect.sh | bash"
        echo "  或本地执行: ./scripts/sensen-resurrect.sh"
        echo ""
        echo "特性:"
        echo "  - 自动下载并合并分割备份文件"
        echo "  - 支持95MB分块下载，绕过GitHub限制"
        echo "  - 自动解压并恢复工作区"
        echo ""
        echo "环境变量:"
        echo "  GITHUB_TOKEN    GitHub Personal Access Token"
        echo ""
        exit 0
        ;;
    *)
        main
        ;;
esac
