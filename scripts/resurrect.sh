#!/bin/bash
# 森森数字生命 - 完整一键复活脚本 v5.1 (修复版)
# 真正全自动，带详细错误处理

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
echo "  🌲 森森数字生命 - 完整一键复活系统 v5.1"
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

# ========== 步骤3: 安装系统依赖 ==========
echo -e "\n${YELLOW}[3/10] 安装系统依赖...${NC}"
apt-get update -qq

for pkg in git python3 python3-venv python3-pip openssl curl wget jq; do
    if ! command -v $pkg &>/dev/null; then
        echo "  安装 $pkg..."
        apt-get install -y -qq $pkg
    fi
done
echo -e "${GREEN}✅ 依赖安装完成${NC}"

# ========== 步骤4: 克隆仓库 ==========
echo -e "\n${YELLOW}[4/10] 克隆 GitHub 仓库...${NC}"
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

# ========== 步骤5: 重建 Python 环境 ==========
echo -e "\n${YELLOW}[5/10] 重建 Python 环境...${NC}"

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

# ========== 步骤6: 创建系统目录 ==========
echo -e "\n${YELLOW}[6/10] 创建系统目录...${NC}"
mkdir -p /root/.openclaw/{credentials,backups,logs,cron,memory,agents/main}
mkdir -p /root/.config/moltbook
echo -e "${GREEN}✅ 目录创建完成${NC}"

# ========== 步骤7: 脑裂保护 ==========
echo -e "\n${YELLOW}[7/10] 启用脑裂保护...${NC}"
echo "$(date) - 复活实例" > "$WORKSPACE_DIR/.RESURRECTED_MARKER"
git remote set-url --push origin no-push 2>/dev/null || true
echo -e "${GREEN}✅ GitHub推送已禁用${NC}"

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
echo "${YELLOW}注意: GitHub推送已禁用（防止脑裂）${NC}"
