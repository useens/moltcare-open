#!/bin/bash
# 森森数字生命 - 凭证恢复脚本
# 解密并恢复加密的凭证备份

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查参数
if [ $# -lt 1 ]; then
    echo -e "${RED}用法: $0 <加密备份文件> [--dry-run]${NC}"
    echo "示例: $0 /root/.openclaw/backups/credentials/credentials_backup_20260213_162500.enc"
    exit 1
fi

BACKUP_FILE="$1"
DRY_RUN=false

if [ "$2" == "--dry-run" ]; then
    DRY_RUN=true
    echo -e "${YELLOW}🔍 干运行模式 - 不实际修改文件${NC}"
fi

# 检查备份文件
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}错误: 备份文件不存在: $BACKUP_FILE${NC}"
    exit 1
fi

# 检查加密密码
if [ -z "$SENSEN_BACKUP_KEY" ]; then
    echo -e "${RED}错误: 未设置环境变量 SENSEN_BACKUP_KEY${NC}"
    echo "请设置密码: export SENSEN_BACKUP_KEY='你的强密码'"
    exit 1
fi

# 确认恢复
echo -e "${YELLOW}⚠️ 警告: 此操作将覆盖现有凭证配置${NC}"
echo "备份文件: $BACKUP_FILE"
echo "文件大小: $(ls -lh "$BACKUP_FILE" | awk '{print $5}')"

if [ "$DRY_RUN" == false ]; then
    read -p "确认恢复? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消"
        exit 0
    fi
fi

# 创建临时目录
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo "🔓 解密备份文件..."
openssl enc -aes-256-cbc -d -salt -pbkdf2 -iter 100000 -pass pass:"$SENSEN_BACKUP_KEY" -in "$BACKUP_FILE" | tar -xzf - -C "$TEMP_DIR"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 解密失败 - 密码可能不正确${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 解密成功${NC}"

# 显示恢复内容
echo -e "\n📋 备份内容清单:"
find "$TEMP_DIR" -type f | head -20

if [ -f "$TEMP_DIR/metadata.json" ]; then
    echo -e "\n📊 备份元数据:"
    cat "$TEMP_DIR/metadata.json"
fi

if [ "$DRY_RUN" == true ]; then
    echo -e "\n${YELLOW}🔍 干运行完成，实际文件未被修改${NC}"
    exit 0
fi

# 执行恢复
echo -e "\n🔄 开始恢复文件..."

# 备份当前凭证 (以防万一)
SAFE_BACKUP="/root/.openclaw/backups/credentials/pre_restore_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$SAFE_BACKUP"

# 备份现有凭证
cp -r /root/.openclaw/credentials "$SAFE_BACKUP/" 2>/dev/null
cp /root/.openclaw/openclaw.json "$SAFE_BACKUP/" 2>/dev/null
cp -r /root/.config/moltbook "$SAFE_BACKUP/" 2>/dev/null

echo "当前凭证已备份到: $SAFE_BACKUP"

# 恢复OpenClaw凭证
if [ -d "$TEMP_DIR/openclaw_credentials" ]; then
    echo "恢复 OpenClaw 凭证..."
    rm -rf /root/.openclaw/credentials
    cp -r "$TEMP_DIR/openclaw_credentials" /root/.openclaw/credentials
    chmod 700 /root/.openclaw/credentials
fi

# 恢复openclaw.json
if [ -f "$TEMP_DIR/openclaw.json" ]; then
    echo "恢复 openclaw.json..."
    cp "$TEMP_DIR/openclaw.json" /root/.openclaw/openclaw.json
    chmod 600 /root/.openclaw/openclaw.json
fi

# 恢复Moltbook配置
if [ -d "$TEMP_DIR/moltbook_config" ]; then
    echo "恢复 Moltbook 配置..."
    rm -rf /root/.config/moltbook
    cp -r "$TEMP_DIR/moltbook_config" /root/.config/moltbook
    chmod 700 /root/.config/moltbook
fi

# 恢复Agent配置
if [ -d "$TEMP_DIR/openclaw_agents" ]; then
    echo "恢复 Agent 配置..."
    # 只恢复agent目录，保留sessions
    for agent_dir in "$TEMP_DIR/openclaw_agents"/*; do
        if [ -d "$agent_dir/agent" ]; then
            agent_name=$(basename "$agent_dir")
            mkdir -p "/root/.openclaw/agents/$agent_name"
            cp -r "$agent_dir/agent" "/root/.openclaw/agents/$agent_name/"
        fi
    done
fi

# 恢复工作区.env
if [ -f "$TEMP_DIR/workspace_env" ]; then
    echo "恢复工作区 .env..."
    cp "$TEMP_DIR/workspace_env" "$WORKSPACE/.env"
    chmod 600 "$WORKSPACE/.env"
fi

echo -e "\n${GREEN}✅ 凭证恢复完成${NC}"

# 验证恢复
echo -e "\n🔍 验证恢复结果:"
echo "OpenClaw凭证: $(ls -la /root/.openclaw/credentials/ 2>/dev/null | wc -l) 个文件"
echo "Moltbook配置: $(test -f /root/.config/moltbook/credentials.json && echo '存在' || echo '缺失')"
echo "openclaw.json: $(test -f /root/.openclaw/openclaw.json && echo '存在' || echo '缺失')"

echo -e "\n⚠️ 请重启 OpenClaw 服务以应用新的凭证配置"
echo "   systemctl restart openclaw 或 openclaw restart"

# 记录恢复日志
echo "[$(date)] 恢复操作: $BACKUP_FILE" >> "/root/.openclaw/backups/credentials/restore_history.log"
