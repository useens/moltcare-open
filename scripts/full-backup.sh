#!/bin/bash
# 🌲 森森数字生命 - 全量备份脚本 v2.0
# 包含: Vestige记忆 + 触发词配置 + 核心文档 + 数据
# 用法: ./scripts/full-backup.sh [备份注释]

set -e

# 配置
WORKSPACE="/root/.openclaw/workspace"
BACKUP_DIR="$WORKSPACE/backups"
VESTIGE_DIR="$HOME/.local/share/vestige"
DATE=$(date +%Y%m%d_%H%M%S)
HOSTNAME=$(hostname)
BACKUP_NOTE="${1:-routine}"

# 颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
echo "═══════════════════════════════════════════════════════════"
echo "  🌲 森森全量备份 v2.0"
echo "  时间: $(date)"
echo "═══════════════════════════════════════════════════════════"
echo -e "${NC}"

mkdir -p "$BACKUP_DIR"

# ===== 1. 备份核心文档 =====
echo -e "${YELLOW}[1/6] 备份核心文档...${NC}"
BACKUP_NAME="sensen_full_${HOSTNAME}_${DATE}"
BACKUP_TMP="/tmp/${BACKUP_NAME}"
mkdir -p "$BACKUP_TMP"

# 复制核心文件
cp -r "$WORKSPACE"/*.md "$BACKUP_TMP/" 2>/dev/null || true
cp -r "$WORKSPACE/core" "$BACKUP_TMP/" 2>/dev/null || true
cp -r "$WORKSPACE/scripts" "$BACKUP_TMP/" 2>/dev/null || true
cp -r "$WORKSPACE/skills" "$BACKUP_TMP/" 2>/dev/null || true
cp -r "$WORKSPACE/memory" "$BACKUP_TMP/" 2>/dev/null || true
cp -r "$WORKSPACE/docs" "$BACKUP_TMP/" 2>/dev/null || true
cp -r "$WORKSPACE/data" "$BACKUP_TMP/" 2>/dev/null || true
cp -r "$WORKSPACE/config" "$BACKUP_TMP/" 2>/dev/null || true
cp -r "$WORKSPACE/reports" "$BACKUP_TMP/" 2>/dev/null || true
cp -r "$WORKSPACE/.archived" "$BACKUP_TMP/" 2>/dev/null || true

echo -e "${GREEN}✓ 核心文档备份完成${NC}"

# ===== 2. 备份Vestige记忆系统 =====
echo -e "${YELLOW}[2/6] 备份Vestige记忆系统...${NC}"
if [ -d "$VESTIGE_DIR" ]; then
    cp -r "$VESTIGE_DIR" "$BACKUP_TMP/vestige_data"
    VESTIGE_COUNT=$(python3 -c "from core.vestige_memory import VestigeMemory; print(VestigeMemory().get_stats()['total_memories'])" 2>/dev/null || echo "unknown")
    echo -e "${GREEN}✓ Vestige备份完成 (${VESTIGE_COUNT}条记忆)${NC}"
else
    echo -e "${YELLOW}⚠ Vestige目录不存在${NC}"
fi

# ===== 3. 备份凭证配置 =====
echo -e "${YELLOW}[3/6] 备份凭证配置...${NC}"
mkdir -p "$BACKUP_TMP/credentials"

# OpenClaw配置
if [ -d "$HOME/.openclaw" ]; then
    cp -r "$HOME/.openclaw/agents" "$BACKUP_TMP/credentials/" 2>/dev/null || true
    cp -r "$HOME/.openclaw/credentials" "$BACKUP_TMP/credentials/" 2>/dev/null || true
fi

# Git配置
cp "$HOME/.gitconfig" "$BACKUP_TMP/credentials/" 2>/dev/null || true

# SSH密钥 (如存在)
if [ -d "$HOME/.ssh" ]; then
    cp -r "$HOME/.ssh" "$BACKUP_TMP/credentials/" 2>/dev/null || true
fi

# 其他配置
cp -r "$HOME/.config" "$BACKUP_TMP/credentials/dot_config" 2>/dev/null || true

echo -e "${GREEN}✓ 凭证配置备份完成${NC}"

# ===== 4. 生成备份元数据 =====
echo -e "${YELLOW}[4/6] 生成备份元数据...${NC}"

cat > "$BACKUP_TMP/BACKUP_INFO.json" << EOF
{
  "backup_version": "2.0",
  "backup_time": "$(date -Iseconds)",
  "hostname": "$HOSTNAME",
  "backup_note": "$BACKUP_NOTE",
  "system_info": {
    "sensen_version": "v2.3",
    "memory_system": "Vestige+FSRS-6",
    "trigger_system": "enabled"
  },
  "components": {
    "vestige_memories": ${VESTIGE_COUNT:-0},
    "core_files": $(find "$BACKUP_TMP" -name "*.py" | wc -l),
    "markdown_docs": $(find "$BACKUP_TMP" -name "*.md" | wc -l),
    "scripts": $(find "$BACKUP_TMP/scripts" -type f 2>/dev/null | wc -l)
  },
  "restore_command": "./scripts/one-click-resurrect.sh <backup_file> <password>"
}
EOF

echo -e "${GREEN}✓ 元数据生成完成${NC}"

# ===== 5. 创建压缩包 =====
echo -e "${YELLOW}[5/6] 创建压缩包...${NC}"

BACKUP_FILE="$BACKUP_DIR/${BACKUP_NAME}.tar.gz"
cd /tmp
tar -czf "$BACKUP_FILE" "$BACKUP_NAME"
rm -rf "$BACKUP_TMP"

# 计算校验和
CHECKSUM=$(sha256sum "$BACKUP_FILE" | awk '{print $1}')
echo "$CHECKSUM" > "${BACKUP_FILE}.sha256"

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo -e "${GREEN}✓ 备份完成: $BACKUP_FILE (${BACKUP_SIZE})${NC}"

# ===== 6. 清理旧备份 =====
echo -e "${YELLOW}[6/6] 清理旧备份...${NC}"

# 保留最近10个全量备份
cd "$BACKUP_DIR"
ls -t sensen_full_*.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm -f
ls -t sensen_full_*.tar.gz.sha256 2>/dev/null | tail -n +11 | xargs -r rm -f

echo -e "${GREEN}✓ 旧备份清理完成${NC}"

# ===== 7. 推送到远程 =====
echo ""
echo -e "${YELLOW}[7/7] 推送到远程仓库...${NC}"
cd "$WORKSPACE"

# 检查Git配置
if [ -d ".git" ]; then
    git add -A 2>/dev/null || true
    git commit -m "🌲 全量备份: ${DATE} - ${BACKUP_NOTE}" 2>/dev/null || true
    git push origin main 2>/dev/null && echo -e "${GREEN}✓ GitHub推送完成${NC}" || echo -e "${YELLOW}⚠ GitHub推送失败${NC}"
else
    echo -e "${YELLOW}⚠ 未配置Git仓库${NC}"
fi

# ===== 完成报告 =====
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🌲 全量备份完成！${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "📦 备份文件: $BACKUP_FILE"
echo "📏 备份大小: $BACKUP_SIZE"
echo "🔐 校验和: ${CHECKSUM:0:16}..."
echo "📝 备份注释: $BACKUP_NOTE"
echo "💾 Vestige记忆: ${VESTIGE_COUNT:-0}条"
echo ""
echo "保留备份数: $(ls $BACKUP_DIR/sensen_full_*.tar.gz 2>/dev/null | wc -l)个"
echo ""
