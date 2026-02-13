#!/bin/bash
# 森森数字生命 - 凭证加密备份脚本
# 使用AES-256加密保存敏感凭证
# 备份位置: /root/.openclaw/backups/credentials/

BACKUP_DIR="/root/.openclaw/backups/credentials"
WORKSPACE="/root/.openclaw/workspace"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/credentials_backup_${DATE}.enc"
MANIFEST_FILE="$BACKUP_DIR/backup_manifest.json"
RETENTION_DAYS=30

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 创建备份目录
mkdir -p "$BACKUP_DIR"
mkdir -p "$BACKUP_DIR/restore_logs"

# 检查加密密码
if [ -z "$SENSEN_BACKUP_KEY" ]; then
    echo -e "${RED}错误: 未设置环境变量 SENSEN_BACKUP_KEY${NC}"
    echo "请在 ~/.bashrc 或 ~/.zshrc 中添加:"
    echo "export SENSEN_BACKUP_KEY='你的强密码'"
    exit 1
fi

echo -e "${GREEN}🔐 开始加密备份凭证...${NC}"

# 创建临时目录
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# 收集凭证文件
echo "📁 收集凭证文件..."

# OpenClaw凭证
cp -r /root/.openclaw/credentials "$TEMP_DIR/openclaw_credentials" 2>/dev/null || echo "⚠️ OpenClaw凭证目录不存在"
cp /root/.openclaw/openclaw.json "$TEMP_DIR/" 2>/dev/null || echo "⚠️ openclaw.json 不存在"
cp /root/.openclaw/openclaw.json.bak "$TEMP_DIR/" 2>/dev/null || true

# Moltbook凭证
cp -r /root/.config/moltbook "$TEMP_DIR/moltbook_config" 2>/dev/null || echo "⚠️ Moltbook配置不存在"

# Feishu凭证 (在agent目录中)
cp -r /root/.openclaw/agents "$TEMP_DIR/openclaw_agents" 2>/dev/null || echo "⚠️ Agent目录不存在"

# 如果有.env文件
cp "$WORKSPACE/.env" "$TEMP_DIR/workspace_env" 2>/dev/null || echo "⚠️ 工作区.env不存在"

# 创建元数据文件
cat > "$TEMP_DIR/metadata.json" << EOF
{
    "backup_time": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "workspace_version": "$(git -C $WORKSPACE describe --tags --always 2>/dev/null || echo 'unknown')",
    "files_included": [
        "openclaw_credentials/*",
        "openclaw.json",
        "moltbook_config/*",
        "openclaw_agents/*/agent/*",
        "workspace_env"
    ],
    "encryption": "AES-256-CBC",
    "tool": "openssl"
}
EOF

# 打包并加密
echo "🔒 打包并加密..."
cd "$TEMP_DIR"
tar -czf - . | openssl enc -aes-256-cbc -salt -pbkdf2 -iter 100000 -pass pass:"$SENSEN_BACKUP_KEY" > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 加密备份完成: $BACKUP_FILE${NC}"
    ls -lh "$BACKUP_FILE"
else
    echo -e "${RED}❌ 备份失败${NC}"
    exit 1
fi

# 更新清单
cat > "$MANIFEST_FILE" << EOF
{
    "last_backup": "$DATE",
    "backup_file": "$BACKUP_FILE",
    "file_size": "$(ls -lh $BACKUP_FILE | awk '{print $5}')",
    "retention_days": $RETENTION_DAYS,
    "restore_command": "./restore-credentials.sh credentials_backup_${DATE}.enc"
}
EOF

# 清理旧备份 (保留30天)
echo "🧹 清理旧备份 (保留${RETENTION_DAYS}天)..."
find "$BACKUP_DIR" -name "credentials_backup_*.enc" -mtime +$RETENTION_DAYS -delete

# 显示备份统计
echo -e "\n${GREEN}📊 备份统计:${NC}"
echo "备份文件: $BACKUP_FILE"
echo "文件大小: $(ls -lh $BACKUP_FILE | awk '{print $5}')"
echo "备份数量: $(find $BACKUP_DIR -name 'credentials_backup_*.enc' | wc -l)"
echo -e "${YELLOW}⚠️ 请妥善保管 SENSEN_BACKUP_KEY 环境变量${NC}"
echo -e "${YELLOW}⚠️ 恢复时需要相同的密码${NC}"

# 创建恢复说明
cat > "$BACKUP_DIR/README_RESTORE.md" << 'EOF'
# 凭证恢复说明

## 恢复步骤

1. 设置环境变量 (必须与备份时相同)
   ```bash
   export SENSEN_BACKUP_KEY='你的强密码'
   ```

2. 运行恢复脚本
   ```bash
   cd /root/.openclaw/workspace
   ./scripts/restore-credentials.sh /root/.openclaw/backups/credentials/credentials_backup_YYYYMMDD_HHMMSS.enc
   ```

3. 验证恢复
   - 检查 Feishu 连接
   - 检查 Moltbook 访问
   - 检查 OpenClaw 配置

## 注意事项

- 恢复脚本会覆盖现有凭证，请谨慎操作
- 建议在恢复前备份当前凭证
- 如果密码错误，无法解密文件

## 备份文件位置

- `/root/.openclaw/backups/credentials/`
- 保留最近30天的备份
EOF

echo -e "\n${GREEN}✅ 凭证备份完成${NC}"
