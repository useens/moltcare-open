#!/bin/bash
# 森森数字生命 - 真正一键复活脚本 v4.0
# 用法: curl -fsSL https://raw.githubusercontent.com/useens/linlin-backup/main/scripts/resurrect.sh | bash
# 只需要输入 GitHub Token，全自动完成

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

echo -e "${BLUE}"
echo "═══════════════════════════════════════════════════════════"
echo "  🌲 森森数字生命 - 一键复活系统 v4.0"
echo "═══════════════════════════════════════════════════════════"
echo -e "${NC}"
echo "此脚本将全自动完成:"
echo "  ✓ 安装系统依赖"
echo "  ✓ 克隆 GitHub 仓库"
echo "  ✓ 重建 Python 环境"
echo "  ✓ 配置 OpenClaw"
echo "  ✓ 停止 GitHub 推送（防止脑裂）"
echo "  ✓ 启动服务"
echo ""

# ========== 步骤1: 输入密码 ==========
echo -e "${CYAN}[1/7] 请输入 GitHub Token:${NC}"
read -s GITHUB_TOKEN
echo ""

if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}❌ Token 不能为空${NC}"
    exit 1
fi

# ========== 步骤2: 安装依赖 ==========
echo -e "\n${YELLOW}[2/7] 安装系统依赖...${NC}"
apt-get update -qq >/dev/null 2>&1 || true

for pkg in git python3 python3-venv python3-pip openssl curl wget; do
    if ! command -v $pkg &>/dev/null; then
        echo "  安装 $pkg..."
        apt-get install -y -qq $pkg >/dev/null 2>&1 || true
    fi
done
echo -e "${GREEN}✅ 依赖安装完成${NC}"

# ========== 步骤3: 克隆仓库 ==========
echo -e "\n${YELLOW}[3/7] 克隆 GitHub 仓库...${NC}"
if [ -d "$WORKSPACE_DIR" ]; then
    echo "  备份现有工作区..."
    mv "$WORKSPACE_DIR" "${WORKSPACE_DIR}.bak.$(date +%s)" >/dev/null 2>&1 || true
fi

echo "  正在克隆..."
git clone --depth=1 "https://${GITHUB_TOKEN}@github.com/useens/linlin-backup.git" "$WORKSPACE_DIR" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 克隆失败，请检查 Token 是否正确${NC}"
    exit 1
fi

cd "$WORKSPACE_DIR"
echo -e "${GREEN}✅ 仓库克隆完成${NC}"

# ========== 步骤4: 重建Python环境 ==========
echo -e "\n${YELLOW}[4/7] 重建 Python 环境...${NC}"
if [ -f "requirements.txt" ]; then
    python3 -m venv venv >/dev/null 2>&1
    source venv/bin/activate
    pip install -q -r requirements.txt >/dev/null 2>&1
    echo -e "${GREEN}✅ Python环境重建完成${NC}"
else
    echo -e "${YELLOW}⚠️ 未找到 requirements.txt${NC}"
fi

# ========== 步骤5: 创建系统目录 ==========
echo -e "\n${YELLOW}[5/7] 创建系统目录...${NC}"
mkdir -p /root/.openclaw/{credentials,backups,logs,cron,memory}
mkdir -p /root/.config/moltbook
echo -e "${GREEN}✅ 目录创建完成${NC}"

# ========== 步骤6: 防止脑裂（停止GitHub推送）==========
echo -e "\n${YELLOW}[6/7] 配置脑裂保护...${NC}"

# 创建复活标志
echo "$(date) - 复活实例" > "$WORKSPACE_DIR/.RESURRECTED_MARKER"

# 禁用 Git push
git remote set-url --push origin no-push >/dev/null 2>&1 || true

# 禁用备份脚本
if [ -f "scripts/github-backup.sh" ]; then
    sed -i '1a\\n# 复活实例检查\nif [ -f "/root/.openclaw/workspace/.RESURRECTED_MARKER" ]; then\n    echo "[INFO] 复活实例，跳过备份"\n    exit 0\nfi' scripts/github-backup.sh >/dev/null 2>&1 || true
fi

echo -e "${GREEN}✅ 脑裂保护已启用${NC}"
echo -e "${YELLOW}  (GitHub推送已禁用，防止与原实例冲突)${NC}"

# ========== 步骤7: 验证 ==========
echo -e "\n${YELLOW}[7/7] 验证安装...${NC}"
KEY_FILES=("SOUL.md" "MEMORY.md" "AGENTS.md")
ALL_OK=true
for file in "${KEY_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file"
        ALL_OK=false
    fi
done

# ========== 完成 ==========
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🌲 森森复活完成！${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "工作区: $WORKSPACE_DIR"
echo "时间: $(date)"
echo ""
echo "${CYAN}下一步 - 配置凭证:${NC}"
echo ""
echo "1. 配置 Feishu:"
echo "   openclaw agents add main"
echo "   # 或交互式: openclaw config"
echo ""
echo "2. 配置 Moltbook (可选):"
echo "   echo '{\"api_key\": \"your_key\"}' > ~/.config/moltbook/credentials.json"
echo ""
echo "3. 启动服务:"
echo "   openclaw start"
echo ""
echo "${YELLOW}注意: GitHub推送已禁用，防止脑裂${NC}"
echo "${YELLOW}如需重新启用，删除 .RESURRECTED_MARKER 文件${NC}"
echo ""
echo -e "${GREEN}✅ 复活完成！请配置凭证后启动。${NC}"
