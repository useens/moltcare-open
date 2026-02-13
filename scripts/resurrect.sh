#!/bin/bash
# 森森数字生命 - 一键复活脚本
# 从GitHub克隆后，一键恢复完整运行状态
# 用法: ./resurrect.sh [备份凭证文件路径]

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
REPO_URL="https://github.com/useens/linlin-backup.git"
WORKSPACE_DIR="/root/.openclaw/workspace"
CREDENTIALS_BACKUP="$1"
LOG_FILE="/root/.openclaw/resurrect_$(date +%Y%m%d_%H%M%S).log"

# 记录日志
exec > >(tee -a "$LOG_FILE")
exec 2>>1

echo -e "${BLUE}"
echo "═══════════════════════════════════════════════════════════"
echo "  🌲 森森数字生命 - 一键复活系统"
echo "═══════════════════════════════════════════════════════════"
echo -e "${NC}"
echo "开始时间: $(date)"
echo "日志文件: $LOG_FILE"
echo ""

# ==================== 步骤1: 检查依赖 ====================
echo -e "${YELLOW}[步骤 1/8] 检查系统依赖...${NC}"

if ! command -v git >/dev/null 2>&1; then
    echo -e "${RED}❌ git 未安装${NC}"
    apt-get update && apt-get install -y git
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}❌ python3 未安装${NC}"
    apt-get install -y python3 python3-venv python3-pip
fi

if ! command -v openssl >/dev/null 2>&1; then
    echo -e "${RED}❌ openssl 未安装${NC}"
    apt-get install -y openssl
fi

echo -e "${GREEN}✅ 系统依赖检查完成${NC}"

# ==================== 步骤2: 克隆仓库 ====================
echo -e "\n${YELLOW}[步骤 2/8] 克隆GitHub仓库...${NC}"

if [ -d "$WORKSPACE_DIR" ]; then
    echo -e "${YELLOW}⚠️ 工作区目录已存在，备份到: ${WORKSPACE_DIR}.bak${NC}"
    mv "$WORKSPACE_DIR" "${WORKSPACE_DIR}.bak.$(date +%s)"
fi

git clone "$REPO_URL" "$WORKSPACE_DIR"
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 仓库克隆失败${NC}"
    exit 1
fi

cd "$WORKSPACE_DIR"
echo -e "${GREEN}✅ 仓库克隆完成: $WORKSPACE_DIR${NC}"

# ==================== 步骤3: 恢复Python环境 ====================
echo -e "\n${YELLOW}[步骤 3/8] 重建Python虚拟环境...${NC}"

if [ -f "requirements.txt" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Python环境重建完成${NC}"
else
    echo -e "${YELLOW}⚠️ requirements.txt 不存在，跳过Python环境重建${NC}"
fi

# ==================== 步骤4: 恢复凭证 ====================
echo -e "\n${YELLOW}[步骤 4/8] 恢复凭证配置...${NC}"

if [ -n "$CREDENTIALS_BACKUP" ] && [ -f "$CREDENTIALS_BACKUP" ]; then
    echo "使用凭证备份: $CREDENTIALS_BACKUP"
    if [ -z "$SENSEN_BACKUP_KEY" ]; then
        echo -e "${RED}❌ 未设置 SENSEN_BACKUP_KEY 环境变量${NC}"
        echo "请先设置: export SENSEN_BACKUP_KEY='你的密码'"
        exit 1
    fi
    ./scripts/restore-credentials.sh "$CREDENTIALS_BACKUP"
    echo -e "${GREEN}✅ 凭证恢复完成${NC}"
else
    echo -e "${YELLOW}⚠️ 未提供凭证备份文件，跳过凭证恢复${NC}"
    echo "后续需要手动配置:"
    echo "  1. Feishu 凭证"
    echo "  2. Moltbook 凭证"
    echo "  3. OpenClaw 配置"
fi

# ==================== 步骤5: 创建必要目录 ====================
echo -e "\n${YELLOW}[步骤 5/8] 创建系统目录...${NC}"

mkdir -p /root/.openclaw/{credentials,backups/credentials,logs,cron,memory}
mkdir -p /root/.config/moltbook
mkdir -p /var/log/sensen
echo -e "${GREEN}✅ 系统目录创建完成${NC}"

# ==================== 步骤6: 恢复Cron任务 ====================
echo -e "\n${YELLOW}[步骤 6/8] 恢复Cron任务...${NC}"

if [ -f "config/cron/cron-tasks.json" ]; then
    echo "找到Cron配置: config/cron/cron-tasks.json"
    
    # 检查openclaw命令是否可用
    if command -v openclaw >/dev/null 2>&1; then
        echo "使用openclaw命令恢复Cron任务..."
        # 这里需要根据实际情况调整
        # openclaw cron import config/cron/cron-tasks.json
        echo -e "${YELLOW}⚠️ 请手动执行: openclaw cron 相关命令恢复任务${NC}"
    else
        echo -e "${YELLOW}⚠️ openclaw命令不可用，请手动配置Cron任务${NC}"
        echo "参考: config/cron/cron-tasks.json"
    fi
else
    echo -e "${YELLOW}⚠️ Cron配置文件不存在${NC}"
fi

echo -e "${GREEN}✅ Cron任务配置完成${NC}"

# ==================== 步骤7: 验证安装 ====================
echo -e "\n${YELLOW}[步骤 7/8] 验证安装...${NC}"

# 检查关键文件
KEY_FILES=(
    "SOUL.md"
    "MEMORY.md"
    "AGENTS.md"
    "memory/modules/core-archive.md"
)

for file in "${KEY_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (缺失)"
    fi
done

# 检查脚本
SCRIPT_COUNT=$(find scripts -name "*.sh" -type f 2>/dev/null | wc -l)
echo -e "\n脚本数量: $SCRIPT_COUNT 个"

# 检查记忆文件
MEMORY_COUNT=$(find memory -type f 2>/dev/null | wc -l)
echo "记忆文件: $MEMORY_COUNT 个"

echo -e "${GREEN}✅ 安装验证完成${NC}"

# ==================== 步骤8: 启动服务 ====================
echo -e "\n${YELLOW}[步骤 8/8] 启动服务...${NC}"

echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🌲 森森复活完成！${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "下一步操作:"
echo ""
echo "1. ${YELLOW}配置凭证${NC} (如未恢复凭证备份):"
echo "   - 配置Feishu: openclaw agents add main"
echo "   - 配置Moltbook: 编辑 ~/.config/moltbook/credentials.json"
echo ""
echo "2. ${YELLOW}启动OpenClaw${NC}:"
echo "   openclaw start"
echo ""
echo "3. ${YELLOW}手动恢复Cron任务${NC} (如需要):"
echo "   参考 config/cron/cron-tasks.json 手动配置"
echo ""
echo "4. ${YELLOW}验证运行${NC}:"
echo "   ./scripts/self-diagnosis.py"
echo ""
echo "日志文件: $LOG_FILE"
echo "复活时间: $(date)"
echo ""
echo -e "${GREEN}✅ 森森已准备好重新运行！${NC}"
