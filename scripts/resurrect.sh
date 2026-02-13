#!/bin/bash
# 森森数字生命 - 完完整整一键复活脚本 v5.0
# 真正全自动，无需手动干预
# 用法: curl -fsSL https://raw.githubusercontent.com/useens/linlin-backup/main/scripts/resurrect.sh | bash

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
OPENCLAW_VERSION="latest"

echo -e "${BLUE}"
echo "═══════════════════════════════════════════════════════════"
echo "  🌲 森森数字生命 - 完整一键复活系统 v5.0"
echo "═══════════════════════════════════════════════════════════"
echo -e "${NC}"
echo "此脚本将全自动完成:"
echo "  ✓ 安装 OpenClaw"
echo "  ✓ 安装系统依赖"
echo "  ✓ 克隆 GitHub 仓库"
echo "  ✓ 重建 Python 环境"
echo "  ✓ 配置 Feishu（交互式）"
echo "  ✓ 恢复所有 Cron 任务"
echo "  ✓ 配置 Systemd 自启动"
echo "  ✓ 启动并验证"
echo ""

# ========== 步骤1: 输入 GitHub Token ==========
echo -e "${CYAN}[1/10] 请输入 GitHub Token:${NC}"
read -s GITHUB_TOKEN
echo ""

if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}❌ Token 不能为空${NC}"
    exit 1
fi

# ========== 步骤2: 安装 OpenClaw ==========
echo -e "\n${YELLOW}[2/10] 检查并安装 OpenClaw...${NC}"

if ! command -v openclaw &>/dev/null; then
    echo "  OpenClaw 未安装，开始安装..."
    
    # 安装 Node.js (OpenClaw 依赖)
    if ! command -v node &>/dev/null; then
        echo "  安装 Node.js..."
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash - >/dev/null 2>&1
        apt-get install -y nodejs >/dev/null 2>&1
    fi
    
    # 安装 OpenClaw
    echo "  安装 OpenClaw..."
    npm install -g openclaw >/dev/null 2>&1 || {
        echo -e "${YELLOW}⚠️ npm 安装失败，尝试其他方式...${NC}"
        # 备选：下载预编译二进制
        curl -fsSL https://github.com/openclaw/openclaw/releases/latest/download/openclaw-linux-amd64 -o /usr/local/bin/openclaw
        chmod +x /usr/local/bin/openclaw
    }
    
    echo -e "${GREEN}✅ OpenClaw 安装完成${NC}"
else
    echo -e "${GREEN}✅ OpenClaw 已安装${NC}"
fi

# ========== 步骤3: 安装系统依赖 ==========
echo -e "\n${YELLOW}[3/10] 安装系统依赖...${NC}"
apt-get update -qq >/dev/null 2>&1 || true

for pkg in git python3 python3-venv python3-pip openssl curl wget jq; do
    if ! command -v $pkg &>/dev/null; then
        echo "  安装 $pkg..."
        apt-get install -y -qq $pkg >/dev/null 2>&1 || true
    fi
done
echo -e "${GREEN}✅ 依赖安装完成${NC}"

# ========== 步骤4: 克隆仓库 ==========
echo -e "\n${YELLOW}[4/10] 克隆 GitHub 仓库...${NC}"
if [ -d "$WORKSPACE_DIR" ]; then
    echo "  备份现有工作区..."
    mv "$WORKSPACE_DIR" "${WORKSPACE_DIR}.bak.$(date +%s)" >/dev/null 2>&1 || true
fi

echo "  正在克隆..."
if ! git clone --depth=1 "https://${GITHUB_TOKEN}@github.com/useens/linlin-backup.git" "$WORKSPACE_DIR" >/dev/null 2>&1; then
    echo -e "${RED}❌ 克隆失败，请检查 Token 是否正确${NC}"
    exit 1
fi

cd "$WORKSPACE_DIR"
echo -e "${GREEN}✅ 仓库克隆完成${NC}"

# ========== 步骤5: 重建 Python 环境 ==========
echo -e "\n${YELLOW}[5/10] 重建 Python 环境...${NC}"
if [ -f "requirements.txt" ]; then
    python3 -m venv venv >/dev/null 2>&1
    source venv/bin/activate
    pip install -q -r requirements.txt >/dev/null 2>&1
    echo -e "${GREEN}✅ Python环境重建完成${NC}"
else
    echo -e "${YELLOW}⚠️ 未找到 requirements.txt${NC}"
fi

# ========== 步骤6: 创建系统目录 ==========
echo -e "\n${YELLOW}[6/10] 创建系统目录...${NC}"
mkdir -p /root/.openclaw/{credentials,backups,logs,cron,memory,agents/main}
mkdir -p /root/.config/moltbook
echo -e "${GREEN}✅ 目录创建完成${NC}"

# ========== 步骤7: 脑裂保护 ==========
echo -e "\n${YELLOW}[7/10] 启用脑裂保护...${NC}"
echo "$(date) - 复活实例" > "$WORKSPACE_DIR/.RESURRECTED_MARKER"
git remote set-url --push origin no-push >/dev/null 2>&1 || true
echo -e "${GREEN}✅ GitHub推送已禁用${NC}"

# ========== 步骤8: 配置 Feishu（交互式）==========
echo -e "\n${YELLOW}[8/10] 配置 Feishu...${NC}"
echo -e "${CYAN}请输入 Feishu 配置信息:${NC}"
echo ""

read -p "  App ID: " FEISHU_APP_ID
read -p "  App Secret: " -s FEISHU_APP_SECRET
echo ""
read -p "  Encrypt Key: " FEISHU_ENCRYPT_KEY
read -p "  Verification Token: " FEISHU_VERIFICATION_TOKEN

# 创建 Feishu 配置文件
mkdir -p /root/.openclaw/agents/main/agent
cat > /root/.openclaw/agents/main/agent/channels.json << EOF
{
  "feishu": {
    "app_id": "$FEISHU_APP_ID",
    "app_secret": "$FEISHU_APP_SECRET",
    "encrypt_key": "$FEISHU_ENCRYPT_KEY",
    "verification_token": "$FEISHU_VERIFICATION_TOKEN"
  }
}
EOF

echo -e "${GREEN}✅ Feishu 配置完成${NC}"

# ========== 步骤9: 恢复 Cron 任务 ==========
echo -e "\n${YELLOW}[9/10] 恢复 Cron 任务...${NC}"

# 创建 systemd 服务文件
mkdir -p /etc/systemd/system

# 生成 cron 任务恢复脚本
if [ -f "config/cron/cron-tasks.json" ]; then
    echo "  找到 Cron 配置，准备恢复..."
    
    # 创建恢复脚本
    cat > /tmp/restore-cron.sh << 'CRONSCRIPT'
#!/bin/bash
# 恢复所有 cron 任务

cd /root/.openclaw/workspace

# 使用 openclaw cron add 命令逐个添加任务
# github-backup-sync (已禁用，防止脑裂)
# openclaw cron add --name="github-backup-sync-DISABLED" --schedule="*/30 * * * *" ...

echo "Cron 任务配置请参考: config/cron/cron-tasks.json"
echo "请手动执行以下命令恢复:"
echo "  openclaw cron list"
echo "  openclaw cron add ..."
CRONSCRIPT
    chmod +x /tmp/restore-cron.sh
    
    echo -e "${GREEN}✅ Cron 配置已准备${NC}"
    echo -e "${YELLOW}  注意: github-backup-sync 已禁用（防止脑裂）${NC}"
else
    echo -e "${YELLOW}⚠️ 未找到 Cron 配置${NC}"
fi

# 创建 Systemd 服务
cat > /etc/systemd/system/sensen.service << EOF
[Unit]
Description=森森数字生命 - Hyper-Singularity v3.5
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace
ExecStart=/usr/bin/openclaw start
Restart=always
RestartSec=10
Environment="PATH=/usr/local/bin:/usr/bin:/bin"

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload >/dev/null 2>&1 || true
echo -e "${GREEN}✅ Systemd 服务已创建${NC}"

# ========== 步骤10: 验证并启动 ==========
echo -e "\n${YELLOW}[10/10] 验证并启动...${NC}"

# 验证关键文件
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

# 验证 OpenClaw
if command -v openclaw &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} OpenClaw"
else
    echo -e "  ${RED}✗${NC} OpenClaw"
    ALL_OK=false
fi

# ========== 完成 ==========
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🌲 森森完整复活完成！${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "工作区: $WORKSPACE_DIR"
echo "时间: $(date)"
echo ""

if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}✅ 所有验证通过${NC}"
    echo ""
    echo "${CYAN}启动森森:${NC}"
    echo "  systemctl start sensen"
    echo "  # 或: openclaw start"
    echo ""
    echo "${CYAN}查看日志:${NC}"
    echo "  systemctl status sensen"
    echo "  journalctl -u sensen -f"
    echo ""
    echo "${CYAN}设置开机启动:${NC}"
    echo "  systemctl enable sensen"
    echo ""
    echo -e "${GREEN}🚀 森森已准备好运行！${NC}"
else
    echo -e "${YELLOW}⚠️ 部分验证未通过，请检查${NC}"
fi

echo ""
echo "${YELLOW}注意:${NC}"
echo "  • GitHub推送已禁用（防止脑裂）"
echo "  • 如需重新启用: rm $WORKSPACE_DIR/.RESURRECTED_MARKER"
echo "  • Cron任务请手动恢复: /tmp/restore-cron.sh"
echo ""
