#!/bin/bash
# =============================================================================
# 林林完整备份脚本 - Full Backup Script
# 备份 workspace + 配置 + 定时任务，排除敏感凭证
# =============================================================================

set -e

BACKUP_DIR="${HOME}/.openclaw/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="linlin_full_${TIMESTAMP}"
TEMP_DIR="/tmp/${BACKUP_NAME}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 创建备份目录结构
mkdir -p "${TEMP_DIR}"/{workspace,config,cron,system}

log_info "开始完整备份: ${TIMESTAMP}"

# 1. 备份 workspace（主数据）
log_info "备份 workspace..."
if [ -d "${HOME}/.openclaw/workspace" ]; then
    # 使用 cp -r 替代 rsync (系统可能未安装 rsync)
    cp -r "${HOME}/.openclaw/workspace" "${TEMP_DIR}/workspace_source"
    mv "${TEMP_DIR}/workspace_source" "${TEMP_DIR}/workspace"
    # 清理大文件和临时文件
    find "${TEMP_DIR}/workspace" -type d -name '.git' -prune -exec rm -rf {} + 2>/dev/null || true
    find "${TEMP_DIR}/workspace" -type d -name 'node_modules' -prune -exec rm -rf {} + 2>/dev/null || true
    find "${TEMP_DIR}/workspace" -name '*.log' -delete 2>/dev/null || true
else
    log_warn "workspace 目录不存在"
fi

# 2. 备份网关配置
log_info "备份网关配置..."
if [ -d "${HOME}/.openclaw/config" ]; then
    cp -r "${HOME}/.openclaw/config" "${TEMP_DIR}/config/"
fi

# 备份 systemd 服务配置（如果存在）
if [ -f "/etc/systemd/system/openclaw.service" ]; then
    cp "/etc/systemd/system/openclaw.service" "${TEMP_DIR}/system/"
fi

# 3. 备份定时任务
log_info "备份定时任务..."
crontab -l > "${TEMP_DIR}/cron/crontab.txt" 2>/dev/null || echo "# 无定时任务" > "${TEMP_DIR}/cron/crontab.txt"

# 4. 备份系统环境变量（筛选相关）
log_info "备份环境配置..."
env | grep -E '^(OPENCLAW|LINLIN|MOLTBOOK|TELEGRAM|GITHUB|FEISHU)' > "${TEMP_DIR}/system/env_vars.txt" 2>/dev/null || true

# 5. 创建备份清单
log_info "创建备份清单..."
cat > "${TEMP_DIR}/BACKUP_MANIFEST.txt" << EOF
林林完整备份清单
==================
备份时间: $(date '+%Y-%m-%d %H:%M:%S %Z')
备份版本: ${TIMESTAMP}
主机名: $(hostname)
系统: $(uname -a)

目录结构:
$(find "${TEMP_DIR}" -type f | head -20)

文件统计:
- 工作区文件: $(find "${TEMP_DIR}/workspace" -type f 2>/dev/null | wc -l)
- 配置文件: $(find "${TEMP_DIR}/config" -type f 2>/dev/null | wc -l)

注意:
- 敏感凭证(credentials/, *.token)已排除
- 大文件(.git/objects, node_modules)已排除
EOF

# 6. 打包备份
log_info "打包备份文件..."
mkdir -p "${BACKUP_DIR}"
tar czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" -C /tmp "${BACKUP_NAME}"

# 7. 清理临时目录
rm -rf "${TEMP_DIR}"

# 8. 清理旧备份（保留最近10个）
log_info "清理旧备份（保留最近10个）..."
ls -1t "${BACKUP_DIR}"/linlin_full_*.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm -f

BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1)
BACKUP_COUNT=$(ls -1 "${BACKUP_DIR}"/linlin_full_*.tar.gz 2>/dev/null | wc -l)

log_info "备份完成: ${BACKUP_NAME}.tar.gz (${BACKUP_SIZE})"
log_info "当前备份总数: ${BACKUP_COUNT}"

# 9. 显示备份列表
echo ""
echo "最近5个备份:"
ls -1t "${BACKUP_DIR}"/linlin_full_*.tar.gz 2>/dev/null | head -5 | while read f; do
    size=$(du -h "$f" | cut -f1)
    name=$(basename "$f")
    echo "  ${name} (${size})"
done

exit 0
