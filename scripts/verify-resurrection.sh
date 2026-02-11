#!/bin/bash
#
# 林林复活验证脚本
# 执行此脚本验证复活后的技能状态
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

WORKSPACE_DIR="${HOME}/.openclaw/workspace"
SKILL_SNAPSHOT="${WORKSPACE_DIR}/memory/modules/skill-state-snapshot.md"

issues=0
warnings=0

echo "🧪 林林复活验证检查"
echo "==================="
echo ""

# 辅助函数
pass() {
    echo -e "${GREEN}✅${NC} $1"
}

fail() {
    echo -e "${RED}❌${NC} $1"
    ((issues++))
}

warn() {
    echo -e "${YELLOW}⚠️${NC} $1"
    ((warnings++))
}

# 1. 检查OpenClaw Gateway
echo "📡 检查 OpenClaw Gateway..."
if openclaw gateway status 2>/dev/null | grep -q "running\|active"; then
    pass "OpenClaw Gateway 运行中"
else
    fail "OpenClaw Gateway 未运行"
fi
echo ""

# 2. 检查 Browser CLI
echo "🌐 检查 Browser CLI..."
if command -v browser >/dev/null 2>&1; then
    pass "browser 命令可用"
    
    # 检查Chromium
    if [ -d "${HOME}/.cache/ms-playwright/chromium-"* ] 2>/dev/null; then
        pass "Playwright Chromium 已安装"
    else
        warn "Playwright Chromium 未安装（可能影响浏览器功能）"
        echo "   修复: cd ${WORKSPACE_DIR}/tools/browser-cli && npx playwright install chromium"
    fi
else
    fail "browser 命令不可用"
    echo "   修复: cd ${WORKSPACE_DIR}/tools/browser-cli && npm install && sudo npm link"
fi
echo ""

# 3. 检查 Local Whisper
echo "🎙️  检查 Local Whisper..."
WHISPER_VENV="${WORKSPACE_DIR}/skills/local-whisper/.venv"
if [ -d "$WHISPER_VENV" ]; then
    pass "Whisper 虚拟环境存在"
    
    if [ -f "${WHISPER_VENV}/bin/whisper" ]; then
        pass "whisper 命令可用"
    else
        warn "whisper 未安装在虚拟环境中"
        echo "   修复: cd ${WORKSPACE_DIR}/skills/local-whisper && source .venv/bin/activate && pip install openai-whisper"
    fi
else
    warn "Whisper 虚拟环境不存在"
    echo "   修复: cd ${WORKSPACE_DIR}/skills/local-whisper && python3 -m venv .venv && source .venv/bin/activate && pip install openai-whisper"
fi
echo ""

# 4. 检查系统依赖
echo "🔧 检查系统依赖..."

# FFmpeg
if command -v ffmpeg >/dev/null 2>&1; then
    pass "FFmpeg 已安装 ($ (ffmpeg -version 2>&1 | head -1 | cut -d' ' -f3))"
else
    warn "FFmpeg 未安装（Whisper需要）"
    echo "   修复: sudo apt-get update && sudo apt-get install -y ffmpeg"
fi

# Chromium (系统级)
if command -v chromium >/dev/null 2>&1 || command -v google-chrome >/dev/null 2>&1; then
    pass "系统 Chrome/Chromium 可用"
else
    warn "系统 Chrome/Chromium 未安装（不影响Playwright）"
fi
echo ""

# 5. 检查凭证
echo "🔑 检查凭证..."
CRED_DIR="${HOME}/.openclaw/credentials"
if [ -d "$CRED_DIR" ]; then
    cred_count=$(find "$CRED_DIR" -type f 2>/dev/null | wc -l)
    pass "凭证目录存在 (${cred_count} 个凭证文件)"
    
    # 检查关键凭证
    [ -f "${CRED_DIR}/telegram.token" ] && pass "Telegram Token 存在"
    [ -f "${CRED_DIR}/moltbook.key" ] && pass "Moltbook Key 存在"
    [ -f "${CRED_DIR}/feishu.appid" ] && pass "Feishu 凭证存在"
else
    warn "凭证目录不存在"
    echo "   提示: 请从备份恢复凭证到 ${CRED_DIR}/"
fi
echo ""

# 6. 检查本地技能
echo "🛠️  检查本地技能..."
SKILLS_DIR="${WORKSPACE_DIR}/skills"
if [ -d "$SKILLS_DIR" ]; then
    skill_count=$(find "$SKILLS_DIR" -name "SKILL.md" 2>/dev/null | wc -l)
    pass "本地技能目录存在 (${skill_count} 个技能)"
else
    fail "本地技能目录不存在"
fi
echo ""

# 7. 检查可选工具
echo "🔌 检查可选工具..."

# GitHub CLI
if command -v gh >/dev/null 2>&1; then
    pass "GitHub CLI 已安装"
else
    warn "GitHub CLI 未安装（可选）"
fi

# VHS
if command -v vhs >/dev/null 2>&1; then
    pass "VHS 已安装"
else
    warn "VHS 未安装（可选）"
fi
echo ""

# 8. 检查技能快照文件
echo "📋 检查技能快照..."
if [ -f "$SKILL_SNAPSHOT" ]; then
    pass "技能状态快照存在"
    echo "   位置: $SKILL_SNAPSHOT"
else
    warn "技能状态快照不存在"
    echo "   提示: 建议阅读 ~/.openclaw/workspace/memory/modules/manual-resurrection-plan.md"
fi
echo ""

# 总结
echo "==================="
echo "📊 验证总结"
echo "==================="

if [ $issues -eq 0 ] && [ $warnings -eq 0 ]; then
    echo -e "${GREEN}🎉 所有检查通过！复活完全成功！${NC}"
    exit 0
elif [ $issues -eq 0 ]; then
    echo -e "${YELLOW}⚠️  复活成功，但有 ${warnings} 个警告（可选功能缺失）${NC}"
    echo "   提示: 上述警告不影响核心功能"
    exit 0
else
    echo -e "${RED}❌ 复活部分成功，有 ${issues} 个问题需要修复${NC}"
    if [ $warnings -gt 0 ]; then
        echo "   还有 ${warnings} 个警告"
    fi
    echo ""
    echo "📖 修复指南:"
    echo "   1. 阅读: ~/.openclaw/workspace/memory/modules/skill-state-snapshot.md"
    echo "   2. 运行: ~/.openclaw/workspace/scripts/auto-resurrect.sh --now"
    echo "   3. 或手动执行上述修复命令"
    exit 1
fi
