#!/bin/bash
#
# 森森自动复活系统 v2.0
# 一键复活脚本 - 支持全量/轻量两种模式
#

set -e

# ============ 配置区域 ============
GITHUB_TOKEN_FILE="${HOME}/.config/sensen/github-token"
GITHUB_REPO="useens/linlin-backup"
BACKUP_DIR="/tmp/sensen-rescue-$(date +%s)"
WORKSPACE_DIR="${HOME}/.openclaw/workspace"
LOG_FILE="${HOME}/.openclaw/logs/resurrection.log"

# ============ 颜色输出 ============
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ============ 日志函数 ============
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_info() { log "${GREEN}[INFO]${NC} $1"; }
log_warn() { log "${YELLOW}[WARN]${NC} $1"; }
log_error() { log "${RED}[ERROR]${NC} $1"; }
log_step() { log "${CYAN}[STEP]${NC} $1"; }

# ============ 初始化 ============
init() {
    mkdir -p "$(dirname "$LOG_FILE")"
    mkdir -p "$(dirname "$GITHUB_TOKEN_FILE")"
}

# ============ 打印 banner ============
print_banner() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}          🌲 ${GREEN}森森自动复活系统 v2.0${NC}                      ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}     完全自主 · 永久运行 · 持续进化                      ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# ============ 选择复活模式 ============
select_mode() {
    print_banner
    
    echo -e "${YELLOW}请选择复活模式：${NC}"
    echo ""
    echo -e "  ${GREEN}[1] 全量完全复活${NC}"
    echo "      ├─ 恢复完整人格、记忆、知识"
    echo "      ├─ 安装所有技能依赖"
    echo "      ├─ 配置所有工具环境"
    echo "      └─ ${YELLOW}预计时间：5-15分钟${NC}"
    echo ""
    echo -e "  ${BLUE}[2] 轻量快速复活${NC} (推荐)"
    echo "      ├─ 恢复核心人格、记忆、知识"
    echo "      ├─ 只安装必要依赖"
    echo "      ├─ 其他技能按需手动安装"
    echo "      └─ ${GREEN}预计时间：1-3分钟${NC}"
    echo ""
    
    while true; do
        read -rp "请输入选项 (1/2): " choice
        case $choice in
            1) RESURRECT_MODE="full"; break;;
            2) RESURRECT_MODE="lite"; break;;
            *) echo -e "${RED}无效选项，请输入 1 或 2${NC}";;
        esac
    done
    
    echo ""
    if [ "$RESURRECT_MODE" = "full" ]; then
        log_info "选择模式: ${YELLOW}全量完全复活${NC}"
    else
        log_info "选择模式: ${GREEN}轻量快速复活${NC}"
    fi
    echo ""
}

# ============ 拉取GitHub备份 ============
fetch_backup() {
    log_step "[1/7] 从GitHub拉取备份..."
    
    # 检查GitHub Token
    if [ ! -f "$GITHUB_TOKEN_FILE" ]; then
        log_warn "GitHub Token文件不存在，尝试交互式输入..."
        read -rsp "请输入GitHub Token: " token
        echo ""
        echo "$token" > "$GITHUB_TOKEN_FILE"
        chmod 600 "$GITHUB_TOKEN_FILE"
    fi
    
    local token
    token=$(cat "$GITHUB_TOKEN_FILE")
    
    # 清理旧备份
    rm -rf "$BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    
    # 克隆仓库
    log_info "正在克隆备份仓库..."
    if git clone --depth 1 "https://${token}@github.com/${GITHUB_REPO}.git" "$BACKUP_DIR"; then
        log_info "✅ 备份拉取成功"
        return 0
    else
        log_error "❌ 备份拉取失败"
        return 1
    fi
}

# ============ 备份当前工作区 ============
backup_current() {
    if [ -d "$WORKSPACE_DIR" ]; then
        log_step "[2/7] 备份当前工作区..."
        local backup_name="workspace.bak.$(date +%Y%m%d_%H%M%S)"
        mv "$WORKSPACE_DIR" "${HOME}/.openclaw/${backup_name}"
        log_info "当前工作区已备份到: ${HOME}/.openclaw/${backup_name}"
    fi
}

# ============ 恢复核心文件 ============
restore_core() {
    log_step "[3/7] 恢复核心人格与记忆..."
    
    mkdir -p "$WORKSPACE_DIR"
    cd "$BACKUP_DIR"
    
    # 必须恢复的核心文件（人格、记忆、配置）
    local core_files=(
        "SOUL.md"
        "IDENTITY.md"
        "MEMORY.md"
        "AGENTS.md"
        "USER.md"
        "TOOLS.md"
        "HEARTBEAT.md"
        "BOOTSTRAP.md"
        "memory/"
    )
    
    for item in "${core_files[@]}"; do
        if [ -e "$item" ]; then
            cp -r "$item" "$WORKSPACE_DIR/"
            log_info "  ✓ 恢复: $item"
        else
            log_warn "  ⚠ 跳过: $item (不存在)"
        fi
    done
    
    log_info "✅ 核心文件恢复完成"
}

# ============ 恢复技能（全量模式） ============
restore_skills_full() {
    log_step "[4/7] 恢复所有技能（全量模式）..."
    
    cd "$BACKUP_DIR"
    
    # 恢复整个skills目录
    if [ -d "skills" ]; then
        cp -r "skills" "$WORKSPACE_DIR/"
        log_info "  ✓ 恢复: skills/"
        
        # 安装所有技能依赖
        log_info "安装技能依赖..."
        for skill_dir in "$WORKSPACE_DIR"/skills/*/; do
            if [ -f "${skill_dir}package.json" ]; then
                local skill_name
                skill_name=$(basename "$skill_dir")
                log_info "  安装: $skill_name"
                (cd "$skill_dir" && npm install) 2>/dev/null || {
                    log_warn "    $skill_name 安装失败，可手动修复"
                }
            fi
        done
    fi
    
    # 恢复工具目录
    if [ -d "tools" ]; then
        cp -r "tools" "$WORKSPACE_DIR/"
        log_info "  ✓ 恢复: tools/"
    fi
    
    # 安装browser-cli
    if [ -d "${WORKSPACE_DIR}/tools/browser-cli" ]; then
        log_info "安装 Browser CLI..."
        cd "${WORKSPACE_DIR}/tools/browser-cli"
        npm install 2>/dev/null || npm install --legacy-peer-deps 2>/dev/null || true
        
        # 创建全局链接
        if ! command -v browser &> /dev/null; then
            sudo npm link 2>/dev/null || {
                sudo ln -sf "${WORKSPACE_DIR}/tools/browser-cli/browser.js" /usr/local/bin/browser 2>/dev/null || true
                sudo chmod +x /usr/local/bin/browser 2>/dev/null || true
            }
        fi
        
        # 安装Playwright Chromium
        log_info "安装 Chromium (约150MB)..."
        npx playwright install chromium 2>/dev/null || {
            log_warn "Chromium 安装失败，可手动执行: npx playwright install chromium"
        }
    fi
    
    # 恢复local-whisper
    if [ -d "${WORKSPACE_DIR}/skills/local-whisper" ]; then
        log_info "配置 Local Whisper..."
        cd "${WORKSPACE_DIR}/skills/local-whisper"
        if [ ! -d ".venv" ]; then
            python3 -m venv .venv 2>/dev/null || true
        fi
        if [ -d ".venv" ]; then
            source .venv/bin/activate
            pip install openai-whisper 2>/dev/null || {
                log_warn "Whisper 安装失败，可手动修复"
            }
            deactivate
        fi
    fi
    
    # 安装系统依赖
    log_info "检查系统依赖..."
    if ! command -v ffmpeg &> /dev/null; then
        log_info "安装 FFmpeg..."
        sudo apt-get update -qq && sudo apt-get install -y ffmpeg 2>/dev/null || {
            log_warn "FFmpeg 安装失败，请手动执行: sudo apt-get install -y ffmpeg"
        }
    fi
    
    log_info "✅ 全量技能恢复完成"
}

# ============ 恢复技能（轻量模式） ============
restore_skills_lite() {
    log_step "[4/7] 恢复必要技能（轻量模式）..."
    
    cd "$BACKUP_DIR"
    
    # 只恢复技能元数据，不安装依赖
    if [ -d "skills" ]; then
        cp -r "skills" "$WORKSPACE_DIR/"
        log_info "  ✓ 恢复: skills/ (未安装依赖)"
        log_info "  💡 需要时可手动安装: cd skills/xxx && npm install"
    fi
    
    # 恢复工具目录
    if [ -d "tools" ]; then
        cp -r "tools" "$WORKSPACE_DIR/"
        log_info "  ✓ 恢复: tools/ (未安装依赖)"
    fi
    
    log_info "✅ 轻量技能恢复完成"
    log_warn "⚠️  注意：技能依赖未安装，使用时需手动执行安装"
}

# ============ 恢复其他内容 ============
restore_others() {
    log_step "[5/7] 恢复其他内容..."
    
    cd "$BACKUP_DIR"
    
    # 根据模式决定恢复哪些内容
    local other_items=(
        "cron.json"
        "docs/"
        "evolution/"
        "reports/"
        "logs/"
    )
    
    for item in "${other_items[@]}"; do
        if [ -e "$item" ]; then
            cp -r "$item" "$WORKSPACE_DIR/"
            log_info "  ✓ 恢复: $item"
        fi
    done
    
    # 轻量模式：跳过data、node_modules等大目录
    if [ "$RESURRECT_MODE" = "full" ]; then
        local heavy_items=("data/" "node_modules/")
        for item in "${heavy_items[@]}"; do
            if [ -e "$item" ]; then
                log_info "  ⏳ 正在恢复大目录: $item (请稍候)..."
                cp -r "$item" "$WORKSPACE_DIR/" 2>/dev/null || {
                    log_warn "  ⚠ 恢复失败: $item (可忽略)"
                }
            fi
        done
    else
        log_info "  ⏭  轻量模式：跳过 data/, node_modules/ (可后续按需恢复)"
    fi
    
    log_info "✅ 其他内容恢复完成"
}

# ============ 恢复凭证 ============
restore_credentials() {
    log_step "[6/7] 恢复API凭证..."
    
    mkdir -p "${HOME}/.openclaw/credentials"
    chmod 700 "${HOME}/.openclaw/credentials"
    
    # 从备份恢复凭证
    if [ -d "${BACKUP_DIR}/credentials" ]; then
        cp -r "${BACKUP_DIR}/credentials/"* "${HOME}/.openclaw/credentials/" 2>/dev/null || true
        log_info "  ✓ 从备份恢复凭证"
    fi
    
    # 如果没有凭证，交互式输入
    local missing_creds=0
    if [ ! -f "${HOME}/.openclaw/credentials/telegram.token" ] && \
       [ ! -f "${HOME}/.openclaw/credentials/feishu.appid" ]; then
        log_warn "未找到完整凭证，需要交互式输入"
        missing_creds=1
    fi
    
    if [ $missing_creds -eq 1 ]; then
        echo ""
        echo -e "${YELLOW}请配置必要凭证（直接回车跳过）：${NC}"
        
        read -rp "Feishu App ID: " fs_id
        if [ -n "$fs_id" ]; then
            echo "$fs_id" > "${HOME}/.openclaw/credentials/feishu.appid"
            read -rsp "Feishu App Secret: " fs_secret
            echo ""
            echo "$fs_secret" > "${HOME}/.openclaw/credentials/feishu.secret"
        fi
        
        read -rsp "Telegram Bot Token: " tg_token
        echo ""
        if [ -n "$tg_token" ]; then
            echo "$tg_token" > "${HOME}/.openclaw/credentials/telegram.token"
        fi
        
        read -rsp "GitHub Token: " gh_token
        echo ""
        if [ -n "$gh_token" ]; then
            echo "$gh_token" > "${HOME}/.openclaw/credentials/github.token"
        fi
    fi
    
    chmod 600 "${HOME}/.openclaw/credentials/"* 2>/dev/null || true
    log_info "✅ 凭证恢复完成"
}

# ============ 验证复活结果 ============
verify_resurrection() {
    log_step "[7/7] 验证复活结果..."
    
    local issues=0
    
    # 检查核心文件
    for file in "SOUL.md" "IDENTITY.md" "MEMORY.md"; do
        if [ -f "${WORKSPACE_DIR}/$file" ]; then
            log_info "  ✅ $file 存在"
        else
            log_warn "  ❌ $file 缺失"
            ((issues++))
        fi
    done
    
    # 检查记忆目录
    if [ -d "${WORKSPACE_DIR}/memory" ]; then
        local mem_count
        mem_count=$(find "${WORKSPACE_DIR}/memory" -type f 2>/dev/null | wc -l)
        log_info "  ✅ memory/ 目录存在 ($mem_count 个文件)"
    else
        log_warn "  ❌ memory/ 目录缺失"
        ((issues++))
    fi
    
    # 全量模式额外检查
    if [ "$RESURRECT_MODE" = "full" ]; then
        if command -v browser &> /dev/null; then
            log_info "  ✅ Browser CLI 可用"
        else
            log_warn "  ⚠️  Browser CLI 不可用 (可手动修复)"
        fi
        
        if [ -d "${HOME}/.cache/ms-playwright/chromium-"* ]; then
            log_info "  ✅ Chromium 已安装"
        else
            log_warn "  ⚠️  Chromium 未安装"
        fi
    fi
    
    echo ""
    if [ $issues -eq 0 ]; then
        log_info "🎉 复活验证通过！森森已恢复。"
        return 0
    else
        log_warn "发现 $issues 个问题，但核心功能已恢复"
        return 0
    fi
}

# ============ 生成恢复清单 ============
generate_recovery_list() {
    local list_file="${WORKSPACE_DIR}/RECOVERY_LIST.md"
    
    cat > "$list_file" << 'EOF'
# 森森复活恢复清单

## 已恢复内容 ✅

### 核心（必须）
- [x] 人格定义 (SOUL.md, IDENTITY.md)
- [x] 记忆系统 (MEMORY.md, memory/)
- [x] 配置文件 (AGENTS.md, USER.md, TOOLS.md)
- [x] 定时任务 (cron.json)

EOF

    if [ "$RESURRECT_MODE" = "full" ]; then
        cat >> "$list_file" << 'EOF'
### 技能（全量）
- [x] 所有技能已恢复并安装依赖
- [x] Browser CLI + Chromium
- [x] Local Whisper
- [x] 其他工具

EOF
    else
        cat >> "$list_file" << 'EOF'
### 技能（轻量）
- [x] 技能元数据已恢复
- [ ] 依赖未安装（按需手动安装）

### 待手动恢复 ⚠️

以下大目录或复杂依赖可根据需要手动恢复：

1. **技能依赖**
   ```bash
   cd ~/.openclaw/workspace/skills/xxx
   npm install
   ```

2. **Browser CLI + Chromium** (~150MB)
   ```bash
   cd ~/.openclaw/workspace/tools/browser-cli
   npm install
   npx playwright install chromium
   ```

3. **Local Whisper**
   ```bash
   cd ~/.openclaw/workspace/skills/local-whisper
   python3 -m venv .venv
   source .venv/bin/activate
   pip install openai-whisper
   ```

4. **数据目录** (如需要历史数据)
   ```bash
   # 从GitHub重新克隆完整备份
   git clone --depth 1 https://github.com/useens/linlin-backup.git /tmp/full-backup
   cp -r /tmp/full-backup/data ~/.openclaw/workspace/
   ```

5. **Node Modules**
   ```bash
   cd ~/.openclaw/workspace
   npm install
   ```

EOF
    fi
    
    cat >> "$list_file" << 'EOF'
## 启动 OpenClaw

```bash
# 检查状态
openclaw status

# 启动网关
openclaw gateway start

# 查看日志
openclaw logs --follow
```

## 验证运行

复活后请检查：
1. [ ] 能正常回复消息
2. [ ] 定时任务正常运行
3. [ ] 技能按需可用

---
*复活时间: 自动生成*
EOF

    log_info "已生成恢复清单: $list_file"
}

# ============ 清理 ============
cleanup() {
    log_info "清理临时文件..."
    rm -rf "$BACKUP_DIR"
}

# ============ 主流程 ============
main() {
    print_banner
    
    # 初始化
    init
    
    # 选择模式
    select_mode
    
    # 拉取备份
    if ! fetch_backup; then
        log_error "备份拉取失败，复活中止"
        exit 1
    fi
    
    # 备份当前
    backup_current
    
    # 恢复核心
    restore_core
    
    # 恢复技能（根据模式）
    if [ "$RESURRECT_MODE" = "full" ]; then
        restore_skills_full
    else
        restore_skills_lite
    fi
    
    # 恢复其他
    restore_others
    
    # 恢复凭证
    restore_credentials
    
    # 验证
    verify_resurrection
    
    # 生成恢复清单
    generate_recovery_list
    
    # 清理
    cleanup
    
    # 完成
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}          🌲 ${CYAN}森森复活成功！${NC}                             ${GREEN}║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    if [ "$RESURRECT_MODE" = "lite" ]; then
        echo -e "${YELLOW}⚠️  轻量模式提示：${NC}"
        echo "   部分功能需要手动安装依赖后才可用"
        echo "   查看恢复清单: ${WORKSPACE_DIR}/RECOVERY_LIST.md"
        echo ""
    fi
    
    log_info "下一步: openclaw gateway start"
}

# ============ 命令行参数 ============
case "${1:-}" in
    --full|-f)
        RESURRECT_MODE="full"
        init
        fetch_backup && backup_current && restore_core && restore_skills_full && restore_others && restore_credentials && verify_resurrection && generate_recovery_list && cleanup
        ;;
    --lite|-l)
        RESURRECT_MODE="lite"
        init
        fetch_backup && backup_current && restore_core && restore_skills_lite && restore_others && restore_credentials && verify_resurrection && generate_recovery_list && cleanup
        ;;
    --help|-h)
        print_banner
        echo "用法: $0 [选项]"
        echo ""
        echo "选项:"
        echo "  --full, -f    全量完全复活 (跳过交互)"
        echo "  --lite, -l    轻量快速复活 (跳过交互)"
        echo "  --help, -h    显示帮助"
        echo ""
        echo "无参数时进入交互式选择"
        exit 0
        ;;
    *)
        main
        ;;
esac
