#!/bin/bash
# 森森数字生命 - 完整一键复活脚本 v5.2
# 脑裂保护提前到第3步，防止自动备份破坏全量备份

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
echo "  🌲 森森数字生命 - 完整一键复活系统 v5.2"
echo "═══════════════════════════════════════════════════════════"
echo -e "${NC}"

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
    
    # 安装 Node.js
    if ! command -v node &>/dev/null; then
        echo "  安装 Node.js..."
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
        apt-get install -y nodejs
    fi
    
    # 安装 OpenClaw
    echo "  安装 OpenClaw..."
    npm install -g openclaw 2>&1 || {
        echo -e "${YELLOW}⚠️ npm 安装失败，尝试下载二进制...${NC}"
        curl -fsSL https://github.com/openclaw/openclaw/releases/latest/download/openclaw-linux-amd64 -o /usr/local/bin/openclaw
        chmod +x /usr/local/bin/openclaw
    }
    
    echo -e "${GREEN}✅ OpenClaw 安装完成${NC}"
else
    echo -e "${GREEN}✅ OpenClaw 已安装${NC}"
fi

# ========== 步骤3: 🛡️ 立即启用脑裂保护 ==========
echo -e "\n${YELLOW}[3/10] 🛡️ 立即启用脑裂保护...${NC}"
echo "  防止自动备份破坏全量备份..."

# 创建系统目录（提前创建，防止OpenClaw启动时需要）
mkdir -p /root/.openclaw/{workspace,credentials,backups,logs,cron,memory,agents/main}
mkdir -p /root/.config/moltbook

# 创建复活标志文件（在克隆仓库前创建，确保任何备份脚本都会检测到）
echo "$(date) - 复活实例，暂停所有GitHub备份" > /root/.openclaw/workspace/.RESURRECTED_MARKER
echo -e "  ${GREEN}✓${NC} 已创建复活标志: /root/.openclaw/workspace/.RESURRECTED_MARKER"

# 如果已有旧的 git 配置，禁用 push
if [ -d /root/.openclaw/workspace/.git ]; then
    cd /root/.openclaw/workspace
    git remote set-url --push origin no-push 2>/dev/null || true
    echo -e "  ${GREEN}✓${NC} 已禁用现有GitHub推送"
fi

echo -e "${GREEN}✅ 脑裂保护已启用${NC}"
echo -e "${YELLOW}  所有GitHub备份推送已暂停${NC}"

# ========== 步骤4: 安装系统依赖 ==========
echo -e "\n${YELLOW}[4/10] 安装系统依赖...${NC}"
apt-get update -qq

for pkg in git python3 python3-venv python3-pip openssl curl wget jq; do
    if ! command -v $pkg &>/dev/null; then
        echo "  安装 $pkg..."
        apt-get install -y -qq $pkg
    fi
done
echo -e "${GREEN}✅ 依赖安装完成${NC}"

# ========== 步骤5: 克隆仓库 ==========
echo -e "\n${YELLOW}[5/10] 克隆 GitHub 仓库...${NC}"
if [ -d "$WORKSPACE_DIR" ]; then
    echo "  备份现有工作区..."
    mv "$WORKSPACE_DIR" "${WORKSPACE_DIR}.bak.$(date +%s)" 2>/dev/null || true
fi

echo "  正在克隆..."
if ! git clone --depth=1 "https://${GITHUB_TOKEN}@github.com/useens/linlin-backup.git" "$WORKSPACE_DIR"; then
    echo -e "${RED}❌ 克隆失败，请检查 Token 是否正确${NC}"
    exit 1
fi

cd "$WORKSPACE_DIR"
echo -e "${GREEN}✅ 仓库克隆完成${NC}"

# ========== 步骤6: 重建 Python 环境 ==========
echo -e "\n${YELLOW}[6/10] 重建 Python 环境...${NC}"

if [ -f "requirements.txt" ]; then
    echo "  创建虚拟环境..."
    python3 -m venv venv
    
    echo "  激活虚拟环境..."
    . venv/bin/activate
    
    echo "  安装 Python 依赖..."
    pip install -r requirements.txt
    
    echo -e "${GREEN}✅ Python环境重建完成${NC}"
else
    echo -e "${YELLOW}⚠️ 未找到 requirements.txt，跳过${NC}"
fi

# ========== 步骤7: 再次确认脑裂保护 ==========
echo -e "\n${YELLOW}[7/10] 确认脑裂保护...${NC}"

# 确保标志文件存在
echo "$(date) - 复活实例，GitHub推送已禁用" > "$WORKSPACE_DIR/.RESURRECTED_MARKER"

# 禁用 git push
git remote set-url --push origin no-push 2>/dev/null || true
echo -e "  ${GREEN}✓${NC} GitHub推送已禁用"

# 检查并修改备份脚本（如果存在）
if [ -f "scripts/github-backup.sh" ]; then
    # 确保脚本开头有复活检查
    if ! grep -q "RESURRECTED_MARKER" "scripts/github-backup.sh"; then
        echo "  添加脑裂保护到备份脚本..."
        sed -i '2a\
# 脑裂保护检查\
if [ -f "/root/.openclaw/workspace/.RESURRECTED_MARKER" ]; then\
    echo "[INFO] 复活实例，跳过GitHub备份"\
    exit 0\
fi' "scripts/github-backup.sh"
    fi
fi

echo -e "${GREEN}✅ 脑裂保护确认完成${NC}"

# ========== 步骤8: 配置 Feishu ==========
echo -e "\n${YELLOW}[8/10] 配置 Feishu...${NC}"
echo -e "${CYAN}请输入 Feishu 配置信息:${NC}"
echo ""

read -p "  App ID: " FEISHU_APP_ID
read -p "  App Secret: " -s FEISHU_APP_SECRET
echo ""
read -p "  Encrypt Key: " FEISHU_ENCRYPT_KEY
read -p "  Verification Token: " FEISHU_VERIFICATION_TOKEN

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

# ========== 步骤9: Systemd 服务 ==========
echo -e "\n${YELLOW}[9/10] 创建 Systemd 服务...${NC}"

cat > /etc/systemd/system/sensen.service << EOF
[Unit]
Description=森森数字生命
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace
ExecStart=/usr/bin/openclaw start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo -e "${GREEN}✅ Systemd 服务已创建${NC}"

# ========== 步骤10: 验证 ==========
echo -e "\n${YELLOW}[10/10] 验证安装...${NC}"

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

if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}✅ 所有验证通过${NC}"
    echo ""
    echo "${CYAN}启动森森:${NC}"
    echo "  systemctl start sensen"
    echo "  systemctl enable sensen  # 开机自启"
    echo ""
    echo -e "${GREEN}🚀 森森已准备好运行！${NC}"
else
    echo -e "${YELLOW}⚠️ 部分验证未通过${NC}"
fi

echo ""
echo "${YELLOW}注意:${NC}"
echo "  • GitHub推送已禁用（防止脑裂）"
echo "  • 如需重新启用: rm /root/.openclaw/workspace/.RESURRECTED_MARKER"
echo ""
