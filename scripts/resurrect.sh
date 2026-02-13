#!/bin/bash
# 森森数字生命 - 真正一键复活脚本 v3.1
# 用法: curl -fsSL https://raw.githubusercontent.com/useens/linlin-backup/main/scripts/resurrect.sh | bash
#
# 高级用法 (自动模式):
#   export SENSEN_BACKUP_KEY='你的密码'
#   export CREDENTIALS_PATH='/path/to/credentials.enc'
#   curl -fsSL ... | bash

set -e

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置
REPO_URL="https://github.com/useens/linlin-backup.git"
WORKSPACE_DIR="/root/.openclaw/workspace"

# 显示欢迎信息
echo -e "${BLUE}"
echo "═══════════════════════════════════════════════════════════"
echo "  🌲 森森数字生命 - 一键复活系统 v3.1"
echo "═══════════════════════════════════════════════════════════"
echo -e "${NC}"

# 获取密码
if [ -n "$SENSEN_BACKUP_KEY" ]; then
    BACKUP_KEY="$SENSEN_BACKUP_KEY"
    echo -e "${GREEN}✓ 从环境变量获取密码${NC}"
else
    echo -e "${CYAN}请输入凭证备份密码:${NC}"
    read -s BACKUP_KEY
    echo ""
    
    if [ -z "$BACKUP_KEY" ]; then
        echo -e "${RED}❌ 密码不能为空${NC}"
        exit 1
    fi
fi

# 获取凭证文件路径
if [ -n "$CREDENTIALS_PATH" ] && [ -f "$CREDENTIALS_PATH" ]; then
    echo -e "${GREEN}✓ 使用环境变量指定的凭证文件: $CREDENTIALS_PATH${NC}"
elif [ -n "$1" ] && [ -f "$1" ]; then
    CREDENTIALS_PATH="$1"
    echo -e "${GREEN}✓ 使用命令行参数: $CREDENTIALS_PATH${NC}"
else
    # 自动搜索常见位置
    echo -e "${YELLOW}🔍 自动搜索凭证文件...${NC}"
    
    # 搜索路径
    SEARCH_PATHS=(
        "/root/.openclaw/backups/credentials/credentials_backup_*.enc"
        "/tmp/credentials_backup_*.enc"
        "/root/credentials_backup_*.enc"
        "$HOME/credentials_backup_*.enc"
        ".credentials_backup_*.enc"
    )
    
    FOUND=""
    for pattern in "${SEARCH_PATHS[@]}"; do
        FOUND=$(ls -t $pattern 2>/dev/null | head -1)
        if [ -n "$FOUND" ]; then
            CREDENTIALS_PATH="$FOUND"
            echo -e "${GREEN}✓ 找到凭证文件: $CREDENTIALS_PATH${NC}"
            break
        fi
    done
    
    # 如果没找到，询问
    if [ -z "$CREDENTIALS_PATH" ]; then
        echo -e "${YELLOW}⚠️ 未自动找到凭证文件${NC}"
        echo "请提供凭证文件路径或URL:"
        read -p "路径/URL: " input
        
        # 检查是否是URL
        if [[ "$input" =~ ^https?:// ]]; then
            echo -e "${YELLOW}📥 正在下载凭证文件...${NC}"
            CREDENTIALS_PATH="/tmp/sensen_credentials_$(date +%s).enc"
            wget -q "$input" -O "$CREDENTIALS_PATH" 2>/dev/null || curl -fsSL "$input" -o "$CREDENTIALS_PATH"
            echo -e "${GREEN}✓ 已下载到: $CREDENTIALS_PATH${NC}"
        else
            if [ -f "$input" ]; then
                CREDENTIALS_PATH="$input"
                echo -e "${GREEN}✓ 使用: $CREDENTIALS_PATH${NC}"
            else
                echo -e "${YELLOW}⚠️ 文件不存在，将跳过凭证恢复${NC}"
                CREDENTIALS_PATH=""
            fi
        fi
    fi
fi

echo ""
echo -e "${CYAN}开始复活流程...${NC}"
echo ""

# 步骤1: 安装依赖
echo -e "${YELLOW}[1/6] 安装系统依赖...${NC}"
apt-get update -qq >/dev/null 2>%1

for pkg in git python3 python3-venv python3-pip openssl curl wget; do
    if ! command -v $pkg &>/dev/null; then
        echo "  安装 $pkg..."
        apt-get install -y -qq $pkg >/dev/null 2>%1 || true
    fi
done
echo -e "${GREEN}✅ 依赖安装完成${NC}"

# 步骤2: 克隆仓库
echo -e "\n${YELLOW}[2/6] 克隆 GitHub 仓库...${NC}"
if [ -d "$WORKSPACE_DIR" ]; then
    echo "  备份现有工作区..."
    mv "$WORKSPACE_DIR" "${WORKSPACE_DIR}.bak.$(date +%s)"
fi
git clone --depth=1 "$REPO_URL" "$WORKSPACE_DIR"
cd "$WORKSPACE_DIR"
echo -e "${GREEN}✅ 仓库克隆完成${NC}"

# 步骤3: 重建Python环境
echo -e "\n${YELLOW}[3/6] 重建 Python 环境...${NC}"
if [ -f "requirements.txt" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install -q -r requirements.txt
    echo -e "${GREEN}✅ Python环境重建完成${NC}"
else
    echo -e "${YELLOW}⚠️ requirements.txt 不存在${NC}"
fi

# 步骤4: 恢复凭证
echo -e "\n${YELLOW}[4/6] 恢复凭证配置...${NC}"
export SENSEN_BACKUP_KEY="$BACKUP_KEY"
mkdir -p /root/.openclaw/{credentials,backups/credentials,logs,cron,memory}

if [ -n "$CREDENTIALS_PATH" ] && [ -f "$CREDENTIALS_PATH" ]; then
    if [ -f "./scripts/restore-credentials.sh" ]; then
        ./scripts/restore-credentials.sh "$CREDENTIALS_PATH"
        echo -e "${GREEN}✅ 凭证恢复完成${NC}"
    else
        echo -e "${YELLOW}⚠️ 恢复脚本不存在，跳过${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ 跳过凭证恢复${NC}"
fi

# 添加到环境变量
echo "export SENSEN_BACKUP_KEY='$BACKUP_KEY'" >> ~/.bashrc

# 步骤5: 恢复Cron任务 + 停止GitHub备份（防止脑裂）
echo -e "\n${YELLOW}[5/6] 配置 Cron 任务...${NC}"
if [ -f "config/cron/cron-tasks.json" ]; then
    echo -e "${GREEN}✓ Cron配置已导出${NC}"
    echo "  位置: config/cron/cron-tasks.json"
    echo "  请手动导入或使用: ./config/cron/recreate-all-cron.sh"
else
    echo -e "${YELLOW}⚠️ Cron配置未导出${NC}"
fi

# 🛡️ 停止GitHub备份推送，防止脑裂
echo -e "\n${YELLOW}[保护机制] 停止GitHub备份推送...${NC}"

# 创建标志文件，阻止备份脚本执行
echo "$(date) - 复活实例，暂停GitHub备份" > /root/.openclaw/workspace/.RESURRECTED_MARKER
echo -e "${GREEN}✓ 已创建复活标志文件${NC}"

# 修改git remote，移除push权限
cd "$WORKSPACE_DIR"
if git remote get-url origin &>/dev/null; then
    ORIGINAL_URL=$(git remote get-url origin)
    echo "$ORIGINAL_URL" > .git/original_remote_url
    # 设置为只读（通过设置不存在的push URL）
    git remote set-url --push origin no-push
    echo -e "${GREEN}✓ GitHub推送已禁用${NC}"
    echo -e "${YELLOW}  原始URL: $ORIGINAL_URL${NC}"
    echo -e "${YELLOW}  Push URL: no-push (已禁用)${NC}"
fi

# 备份并清空github-backup-sync任务配置
if [ -f "config/cron/cron-tasks.json" ]; then
    cp config/cron/cron-tasks.json config/cron/cron-tasks.json.backup
    # 标记github-backup-sync任务为禁用
    sed -i 's/"github-backup-sync"/"github-backup-sync-DISABLED"/g' config/cron/cron-tasks.json 2>/dev/null || true
    echo -e "${GREEN}✓ github-backup-sync任务已标记禁用${NC}"
fi

echo -e "\n${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}⚠️  注意: GitHub备份推送已停止，防止与原实例冲突${NC}"
echo -e "${YELLOW}   如需重新启用，请手动删除 .RESURRECTED_MARKER 文件${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"

# 步骤6: 验证
echo -e "\n${YELLOW}[6/6] 验证安装...${NC}"
KEY_FILES=("SOUL.md" "MEMORY.md" "AGENTS.md")
for file in "${KEY_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file"
    fi
done

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🌲 森森复活完成！${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "下一步:"
echo ""
echo "1. ${CYAN}启动 OpenClaw:${NC}"
echo "   openclaw start"
echo ""
echo "2. ${CYAN}导入 Cron 任务:${NC}"
echo "   参考 config/cron/recreate-all-cron.sh"
echo ""
echo "3. ${CYAN}验证:${NC}"
echo "   ./scripts/self-diagnosis.py"
echo ""
echo "工作区: $WORKSPACE_DIR"
echo "时间: $(date)"
echo ""
echo -e "${GREEN}✅ 复活完成！请启动服务。${NC}"
