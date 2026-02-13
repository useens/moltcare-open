#!/bin/bash
# 森森数字生命 - 一键复活脚本 (简化版)
# 用法: curl -fsSL https://raw.githubusercontent.com/useens/linlin-backup/main/scripts/one-click-resurrect.sh | bash -s -- <凭证备份URL或路径> <密码>
# 或: ./one-click-resurrect.sh /path/to/credentials.enc "密码"

set -e

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
REPO_URL="https://github.com/useens/linlin-backup.git"
WORKSPACE_DIR="/root/.openclaw/workspace"
CREDENTIALS_FILE="$1"
BACKUP_KEY="$2"

echo -e "${BLUE}"
echo "═══════════════════════════════════════════════════════════"
echo "  🌲 森森数字生命 - 一键复活"
echo "═══════════════════════════════════════════════════════════"
echo -e "${NC}"

# 检查参数
if [ -z "$CREDENTIALS_FILE" ]; then
    echo -e "${RED}❌ 缺少凭证备份文件${NC}"
    echo "用法: $0 <凭证备份文件> <密码>"
    echo ""
    echo "示例:"
    echo "  $0 /path/to/credentials_backup.enc 'your-password'"
    echo ""
    echo "或者先下载凭证文件:"
    echo "  wget <凭证备份URL> -O /tmp/credentials.enc"
    echo "  $0 /tmp/credentials.enc 'your-password'"
    exit 1
fi

if [ -z "$BACKUP_KEY" ]; then
    echo -e "${RED}❌ 缺少备份密码${NC}"
    echo "用法: $0 <凭证备份文件> <密码>"
    exit 1
fi

# 检查凭证文件
if [ ! -f "$CREDENTIALS_FILE" ]; then
    echo -e "${YELLOW}⚠️ 凭证文件不存在，尝试作为URL下载...${NC}"
    wget -q "$CREDENTIALS_FILE" -O /tmp/sensen_credentials.enc 2>/dev/null || curl -fsSL "$CREDENTIALS_FILE" -o /tmp/sensen_credentials.enc
    CREDENTIALS_FILE="/tmp/sensen_credentials.enc"
    echo -e "${GREEN}✅ 凭证文件已下载${NC}"
fi

# 步骤1: 检查依赖
echo -e "\n${YELLOW}[1/5] 检查依赖...${NC}"
if ! command -v git &>/dev/null; then
    echo "安装 git..."
    apt-get update -qq && apt-get install -y -qq git
fi
if ! command -v python3 &>/dev/null; then
    echo "安装 python3..."
    apt-get install -y -qq python3 python3-venv python3-pip
fi
if ! command -v openssl &>/dev/null; then
    echo "安装 openssl..."
    apt-get install -y -qq openssl
fi
echo -e "${GREEN}✅ 依赖检查完成${NC}"

# 步骤2: 克隆仓库
echo -e "\n${YELLOW}[2/5] 克隆仓库...${NC}"
if [ -d "$WORKSPACE_DIR" ]; then
    echo "备份现有工作区..."
    mv "$WORKSPACE_DIR" "${WORKSPACE_DIR}.bak.$(date +%s)"
fi
git clone --depth=1 "$REPO_URL" "$WORKSPACE_DIR"
cd "$WORKSPACE_DIR"
echo -e "${GREEN}✅ 仓库克隆完成${NC}"

# 步骤3: 设置环境
echo -e "\n${YELLOW}[3/5] 设置环境...${NC}"
export SENSEN_BACKUP_KEY="$BACKUP_KEY"
echo "export SENSEN_BACKUP_KEY='$BACKUP_KEY'" >> ~/.bashrc

# 创建必要目录
mkdir -p /root/.openclaw/{credentials,backups,logs,cron,memory}
mkdir -p /root/.config/moltbook
echo -e "${GREEN}✅ 环境设置完成${NC}"

# 步骤4: 恢复凭证
echo -e "\n${YELLOW}[4/5] 恢复凭证...${NC}"
if [ -f "$CREDENTIALS_FILE" ]; then
    ./scripts/restore-credentials.sh "$CREDENTIALS_FILE"
    echo -e "${GREEN}✅ 凭证恢复完成${NC}"
else
    echo -e "${YELLOW}⚠️ 跳过凭证恢复，需手动配置${NC}"
fi

# 步骤5: 验证
echo -e "\n${YELLOW}[5/5] 验证安装...${NC}"
KEY_FILES=("SOUL.md" "MEMORY.md" "AGENTS.md")
for file in "${KEY_FILES[@]}"; do
    [ -f "$file" ] && echo -e "${GREEN}✓${NC} $file" || echo -e "${RED}✗${NC} $file"
done
echo -e "${GREEN}✅ 验证完成${NC}"

# 完成
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🌲 森森复活完成！${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "下一步:"
echo ""
echo "1. 检查Feishu配置:"
echo "   cat /root/.openclaw/agents/main/agent/channels.json"
echo ""
echo "2. 启动OpenClaw:"
echo "   openclaw start"
echo ""
echo "3. 或者手动运行森森:"
echo "   cd $WORKSPACE_DIR"
echo "   ./scripts/self-diagnosis.py"
echo ""
echo "工作区: $WORKSPACE_DIR"
echo "复活时间: $(date)"
echo ""
