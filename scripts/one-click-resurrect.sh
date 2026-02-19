#!/bin/bash
# 🌲 森森数字生命 - 一键复活脚本 v2.0
# 支持: Vestige记忆系统 + 触发词系统 + 全量恢复
# 用法: curl -fsSL https://raw.githubusercontent.com/useens/linlin-backup/main/scripts/one-click-resurrect.sh | bash -s -- <备份文件> <密码>

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
VESTIGE_DIR="$HOME/.local/share/vestige"
BACKUP_FILE="$1"
BACKUP_PASSWORD="$2"

echo -e "${BLUE}"
echo "═══════════════════════════════════════════════════════════"
echo "  🌲 森森数字生命 - 一键复活 v2.0"
echo "  Vestige记忆 + FSRS-6 + 触发词系统"
echo "═══════════════════════════════════════════════════════════"
echo -e "${NC}"

# 检查参数
if [ -z "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ 缺少备份文件${NC}"
    echo ""
    echo "用法:"
    echo "  方式1 - 使用备份文件:"
    echo "    $0 /path/to/sensen_full_HOSTNAME_YYYYMMDD_HHMMSS.tar.gz [密码]"
    echo ""
    echo "  方式2 - 从GitHub克隆 (全新安装):"
    echo "    $0 --fresh"
    echo ""
    echo "  方式3 - 下载并恢复:"
    echo "    wget <备份URL> -O /tmp/backup.tar.gz"
    echo "    $0 /tmp/backup.tar.gz"
    exit 1
fi

# 模式：全新安装
if [ "$BACKUP_FILE" == "--fresh" ]; then
    echo -e "${YELLOW}🌱 全新安装模式${NC}"
    FRESH_INSTALL=true
else
    FRESH_INSTALL=false
fi

# 步骤1: 检查依赖
echo -e "\n${YELLOW}[1/8] 检查依赖...${NC}"

DEPS_TO_INSTALL=""
for cmd in git python3 pip3 openssl curl wget; do
    if ! command -v $cmd &>/dev/null; then
        DEPS_TO_INSTALL="$DEPS_TO_INSTALL $cmd"
    fi
done

if [ -n "$DEPS_TO_INSTALL" ]; then
    echo "安装依赖:$DEPS_TO_INSTALL"
    apt-get update -qq && apt-get install -y -qq$DEPS_TO_INSTALL
fi
echo -e "${GREEN}✅ 依赖检查完成${NC}"

# 步骤2: 处理备份文件
echo -e "\n${YELLOW}[2/8] 处理备份文件...${NC}"

if [ "$FRESH_INSTALL" = false ]; then
    # 下载备份文件（如果是URL）
    if [[ "$BACKUP_FILE" =~ ^https?:// ]]; then
        echo "下载备份文件..."
        wget -q "$BACKUP_FILE" -O /tmp/sensen_backup.tar.gz || curl -fsSL "$BACKUP_FILE" -o /tmp/sensen_backup.tar.gz
        BACKUP_FILE="/tmp/sensen_backup.tar.gz"
        echo -e "${GREEN}✅ 备份文件下载完成${NC}"
    elif [ ! -f "$BACKUP_FILE" ]; then
        echo -e "${RED}❌ 备份文件不存在: $BACKUP_FILE${NC}"
        exit 1
    fi
    
    # 验证备份文件
    if [ -f "${BACKUP_FILE}.sha256" ]; then
        echo "验证备份文件完整性..."
        if sha256sum -c "${BACKUP_FILE}.sha256" >/devdev/null 2>&1; then
            echo -e "${GREEN}✅ 校验和验证通过${NC}"
        else
            echo -e "${YELLOW}⚠️ 校验和验证失败，继续恢复...${NC}"
        fi
    fi
fi

# 步骤3: 克隆/准备工作区
echo -e "\n${YELLOW}[3/8] 准备工作区...${NC}"

if [ -d "$WORKSPACE_DIR" ]; then
    echo "备份现有工作区..."
    mv "$WORKSPACE_DIR" "${WORKSPACE_DIR}.bak.$(date +%s)"
fi

if [ "$FRESH_INSTALL" = true ]; then
    # 全新安装：从GitHub克隆
    echo "从GitHub克隆仓库..."
    git clone --depth=1 "$REPO_URL" "$WORKSPACE_DIR"
else
    # 从备份恢复：先解压备份
    echo "解压备份文件..."
    mkdir -p "$WORKSPACE_DIR"
    tar -xzf "$BACKUP_FILE" -C /tmp
    
    # 找到解压后的目录
    EXTRACTED_DIR=$(find /tmp -maxdepth 1 -type d -name "sensen_full_*" | head -1)
    if [ -z "$EXTRACTED_DIR" ]; then
        # 可能是直接打包的workspace
        tar -xzf "$BACKUP_FILE" -C "$WORKSPACE_DIR" --strip-components=1
    else
        mv "$EXTRACTED_DIR"/* "$WORKSPACE_DIR/"
        rm -rf "$EXTRACTED_DIR"
    fi
fi

cd "$WORKSPACE_DIR"
echo -e "${GREEN}✅ 工作区准备完成${NC}"

# 步骤4: 恢复Vestige记忆系统
echo -e "\n${YELLOW}[4/8] 恢复Vestige记忆系统...${NC}"

mkdir -p "$VESTIGE_DIR"

if [ "$FRESH_INSTALL" = false ] && [ -d "$WORKSPACE_DIR/vestige_data" ]; then
    echo "恢复Vestige记忆数据..."
    cp -r "$WORKSPACE_DIR/vestige_data"/* "$VESTIGE_DIR/"
    rm -rf "$WORKSPACE_DIR/vestige_data"
    echo -e "${GREEN}✅ Vestige记忆恢复完成${NC}"
else
    echo "初始化新的Vestige记忆系统..."
    # 创建空的Vestige数据库
    python3 -c "
import sys
sys.path.insert(0, '.')
from core.vestige_memory import VestigeMemory
vm = VestigeMemory()
print(f'Vestige初始化完成')
print(f'数据库位置: {vm.db_path}')
" 2>/dev/null || echo -e "${YELLOW}⚠️ Vestige初始化可能需要手动完成${NC}"
fi

# 步骤5: 恢复凭证配置
echo -e "\n${YELLOW}[5/8] 恢复凭证配置...${NC}"

if [ "$FRESH_INSTALL" = false ] && [ -d "$WORKSPACE_DIR/credentials" ]; then
    echo "恢复凭证..."
    
    # OpenClaw凭证
    if [ -d "$WORKSPACE_DIR/credentials/agents" ]; then
        mkdir -p "$HOME/.openclaw"
        cp -r "$WORKSPACE_DIR/credentials/agents" "$HOME/.openclaw/"
    fi
    
    if [ -d "$WORKSPACE_DIR/credentials/credentials" ]; then
        mkdir -p "$HOME/.openclaw"
        cp -r "$WORKSPACE_DIR/credentials/credentials" "$HOME/.openclaw/"
    fi
    
    # Git配置
    if [ -f "$WORKSPACE_DIR/credentials/.gitconfig" ]; then
        cp "$WORKSPACE_DIR/credentials/.gitconfig" "$HOME/"
    fi
    
    # SSH密钥
    if [ -d "$WORKSPACE_DIR/credentials/.ssh" ]; then
        cp -r "$WORKSPACE_DIR/credentials/.ssh" "$HOME/"
        chmod 700 "$HOME/.ssh"
        chmod 600 "$HOME/.ssh"/* 2>/dev/null || true
    fi
    
    # dot_config
    if [ -d "$WORKSPACE_DIR/credentials/dot_config" ]; then
        mkdir -p "$HOME/.config"
        cp -r "$WORKSPACE_DIR/credentials/dot_config"/* "$HOME/.config/" 2>/dev/null || true
    fi
    
    rm -rf "$WORKSPACE_DIR/credentials"
    echo -e "${GREEN}✅ 凭证恢复完成${NC}"
else
    echo -e "${YELLOW}⚠️ 需要手动配置凭证${NC}"
fi

# 步骤6: 安装Python依赖
echo -e "\n${YELLOW}[6/8] 安装Python依赖...${NC}"

pip3 install -q sqlite3 2>/dev/null || true

# 创建Python虚拟环境（如果需要）
if [ ! -d "$WORKSPACE_DIR/venv" ]; then
    python3 -m venv "$WORKSPACE_DIR/venv" 2>/dev/null || echo -e "${YELLOW}⚠️ 虚拟环境创建失败，使用系统Python${NC}"
fi

echo -e "${GREEN}✅ Python环境准备完成${NC}"

# 步骤7: 验证系统
echo -e "\n${YELLOW}[7/8] 验证系统...${NC}"

# 检查核心文件
KEY_FILES=("SOUL.md" "MEMORY.md" "AGENTS.md" "core/vestige_memory.py" "core/trigger_handler.py")
for file in "${KEY_FILES[@]}"; do
    [ -f "$file" ] && echo -e "${GREEN}✓${NC} $file" || echo -e "${RED}✗${NC} $file"
done

# 验证Vestige
echo ""
echo "验证Vestige记忆系统..."
VESTIGE_STATUS=$(python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from core.vestige_memory import VestigeMemory
    vm = VestigeMemory()
    stats = vm.get_stats()
    print(f'✅ Vestige正常: {stats[\"total_memories\"]}条记忆')
except Exception as e:
    print(f'⚠️ Vestige初始化: {e}')
" 2>/devnull || echo "⚠️ Vestige需手动初始化")

echo "$VESTIGE_STATUS"

# 验证触发词系统
echo ""
echo "验证触发词系统..."
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from core.trigger_handler import process_message
    result = process_message('记住这个：测试')
    if result['triggers_detected']:
        print('✅ 触发词系统正常')
    else:
        print('⚠️ 触发词系统需检查')
except Exception as e:
    print(f'⚠️ 触发词系统: {e}')
" 2>/dev/null || echo "⚠️ 触发词系统需手动验证"

echo -e "${GREEN}✅ 系统验证完成${NC}"

# 步骤8: 设置环境
echo -e "\n${YELLOW}[8/8] 设置环境...${NC}"

# 添加工作区到PATH
echo "export SENSEN_WORKSPACE='$WORKSPACE_DIR'" >> ~/.bashrc
echo "export PATH='$WORKSPACE_DIR/scripts:\$PATH'" >> ~/.bashrc

# 创建快捷命令
cat > /usr/local/bin/sensen << 'EOF'
#!/bin/bash
cd /root/.openclaw/workspace
python3 scripts/unified-monitor.py "$@"
EOF
chmod +x /usr/local/bin/sensen 2>/dev/null || true

echo -e "${GREEN}✅ 环境设置完成${NC}"

# 完成
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🌲 森森复活完成！${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "📁 工作区: $WORKSPACE_DIR"
echo "💾 Vestige: $VESTIGE_DIR"
echo "🕐 复活时间: $(date)"
echo ""
echo "下一步:"
echo ""
echo "1. 检查系统状态:"
echo "   cd $WORKSPACE_DIR"
echo "   python3 core/vestige_memory.py"
echo ""
echo "2. 测试触发词:"
echo "   python3 -c \"from core.trigger_handler import process_message; print(process_message('记住这个：测试'))\""
echo ""
echo "3. 启动OpenClaw:"
echo "   openclaw start"
echo ""
echo "4. 创建备份:"
echo "   ./scripts/full-backup.sh '复活后首次备份'"
echo ""
