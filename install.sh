#!/bin/bash
# MoltCare v2.0 安装脚本
# 使用方法: curl -fsSL https://raw.githubusercontent.com/useens/moltcare-open/master/install.sh | bash
#
# 改进:
# - 优先使用 git clone 避免 GitHub 缓存问题
# - 自动验证并升级到 v2.0
# - 安装后自动初始化

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 版本
MOLTCARE_VERSION="2.0.0"
REPO_URL="https://github.com/useens/moltcare-open"
INSTALL_DIR="/usr/local/bin"
BRANCH="master"

print_banner() {
    echo -e "${BLUE}"
    echo "🦞 MoltCare v2.0 安装程序"
    echo "让每一只刚安装的 OpenClaw Agent 都能一键获得专业级智能"
    echo -e "${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_highlight() {
    echo -e "${CYAN}$1${NC}"
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."
    
    # 检查 Python 3
    if ! command -v python3 &> /dev/null; then
        print_error "需要 Python 3 (>= 3.8)"
        echo "   请安装 Python 3: https://www.python.org/downloads/"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    print_success "Python $PYTHON_VERSION"
    
    # 检查 pip
    if ! command -v pip3 &> /dev/null; then
        print_warning "pip3 未找到，将尝试安装"
    fi
    
    # 检查 PyYAML
    if ! python3 -c "import yaml" 2>/dev/null; then
        print_info "安装 PyYAML..."
        pip3 install pyyaml -q || {
            print_error "无法安装 PyYAML"
            echo "   请手动运行: pip3 install pyyaml"
            exit 1
        }
        print_success "PyYAML 已安装"
    else
        print_success "PyYAML 已安装"
    fi
    
    # 检查 git（推荐使用）
    if command -v git &> /dev/null; then
        print_success "Git 已安装（将使用 git clone 避免缓存问题）"
        USE_GIT=true
    else
        print_warning "Git 未安装（将使用归档下载，可能有缓存延迟）"
        USE_GIT=false
    fi
}

# 下载 MoltCare
download_moltcare() {
    print_info "下载 MoltCare v${MOLTCARE_VERSION}..."
    
    MOLTCARE_HOME="$HOME/.moltcare"
    
    # 如果目录已存在，先备份
    if [ -d "$MOLTCARE_HOME" ]; then
        BACKUP_DIR="${MOLTCARE_HOME}.backup.$(date +%s)"
        print_info "备份现有安装到 $BACKUP_DIR"
        mv "$MOLTCARE_HOME" "$BACKUP_DIR"
    fi
    
    # 优先使用 git clone（避免缓存问题）
    if [ "$USE_GIT" = true ]; then
        print_info "使用 git clone 获取最新代码..."
        if git clone --depth 1 "$REPO_URL" "$MOLTCARE_HOME" 2>/dev/null; then
            print_success "Git 克隆完成"
        else
            print_error "Git 克隆失败"
            exit 1
        fi
    else
        # 回退到归档下载
        print_info "使用归档下载..."
        TEMP_DIR=$(mktemp -d)
        cd "$TEMP_DIR"
        
        if command -v curl &> /dev/null; then
            curl -fsSL "${REPO_URL}/archive/refs/heads/master.tar.gz" -o moltcare.tar.gz || \
            curl -fsSL "${REPO_URL}/archive/refs/heads/main.tar.gz" -o moltcare.tar.gz
        elif command -v wget &> /dev/null; then
            wget -q "${REPO_URL}/archive/refs/heads/master.tar.gz" -O moltcare.tar.gz || \
            wget -q "${REPO_URL}/archive/refs/heads/main.tar.gz" -O moltcare.tar.gz
        else
            print_error "需要 curl 或 wget"
            exit 1
        fi
        
        tar -xzf moltcare.tar.gz
        mv moltcare-* "$MOLTCARE_HOME"
        rm -rf "$TEMP_DIR"
        print_success "归档下载完成"
    fi
}

# 安装 CLI
install_cli() {
    print_info "安装 CLI..."
    
    CLI_SCRIPT="$HOME/.moltcare/moltcare"
    if [ -f "$CLI_SCRIPT" ]; then
        mkdir -p "$HOME/.local/bin"
        cp "$CLI_SCRIPT" "$HOME/.local/bin/moltcare"
        chmod +x "$HOME/.local/bin/moltcare"
        print_success "CLI 已安装到 ~/.local/bin/moltcare"
    else
        print_error "CLI 脚本未找到"
        exit 1
    fi
}

# 验证版本
verify_version() {
    print_info "验证安装版本..."
    
    export PATH="$HOME/.local/bin:$PATH"
    INSTALLED_VERSION=$(moltcare --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "unknown")
    
    if [ "$INSTALLED_VERSION" = "$MOLTCARE_VERSION" ]; then
        print_success "版本验证通过: v$INSTALLED_VERSION"
    else
        print_warning "版本不匹配: 期望 v$MOLTCARE_VERSION, 实际 v$INSTALLED_VERSION"
        print_info "可能是 GitHub 缓存导致，等待 5 秒后重试..."
        sleep 5
        
        # 强制重新安装 CLI
        cd "$HOME/.moltcare"
        if [ -f moltcare ]; then
            cp moltcare "$HOME/.local/bin/moltcare"
            chmod +x "$HOME/.local/bin/moltcare"
        fi
        
        INSTALLED_VERSION=$(moltcare --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "unknown")
        if [ "$INSTALLED_VERSION" = "$MOLTCARE_VERSION" ]; then
            print_success "版本验证通过: v$INSTALLED_VERSION"
        else
            print_warning "版本仍不匹配，但继续安装"
        fi
    fi
}

# 添加到 PATH
setup_path() {
    print_info "配置 PATH..."
    
    SHELL_CONFIG=""
    if [ -n "$ZSH_VERSION" ] || [ "$SHELL" = "/bin/zsh" ]; then
        SHELL_CONFIG="$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ] || [ "$SHELL" = "/bin/bash" ]; then
        SHELL_CONFIG="$HOME/.bashrc"
    fi
    
    if [ -n "$SHELL_CONFIG" ]; then
        if ! grep -q "$HOME/.local/bin" "$SHELL_CONFIG" 2>/dev/null; then
            echo "" >> "$SHELL_CONFIG"
            echo "# MoltCare PATH" >> "$SHELL_CONFIG"
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_CONFIG"
            print_success "已添加到 $SHELL_CONFIG"
            print_info "请运行 'source $SHELL_CONFIG' 或重启终端以生效"
        else
            print_info "PATH 已配置"
        fi
    fi
}

# 自动初始化
auto_init() {
    print_info "自动初始化 MoltCare v2.0..."
    
    export PATH="$HOME/.local/bin:$PATH"
    
    # 执行初始化
    if moltcare init --force 2>/dev/null; then
        print_success "初始化完成"
    else
        print_warning "初始化可能已存在"
    fi
}

# 打印完成信息
print_finish() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  🎉 MoltCare v${MOLTCARE_VERSION} 安装完成!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo ""
    print_highlight "安装信息:"
    echo "  版本: v${MOLTCARE_VERSION}"
    echo "  安装路径: $HOME/.moltcare"
    echo "  CLI 路径: $HOME/.local/bin/moltcare"
    echo ""
    print_highlight "已启用特性:"
    echo "  ✓ 深度集成模式"
    echo "  ✓ 运行时 Hooks"
    echo "  ✓ 自动触发词检测"
    echo "  ✓ 智能合并策略"
    echo ""
    print_highlight "快速开始:"
    echo "  1. source $HOME/.bashrc  # 或重启终端"
    echo "  2. moltcare doctor       # 检查健康状态"
    echo "  3. moltcare list         # 查看智能包"
    echo "  4. moltcare apply foundation-v2 --merge  # 应用增强版"
    echo ""
    print_highlight "重要提示:"
    echo "  • 当前是文件层面集成，运行时集成需要 OpenClaw 本体支持"
    echo "  • Hooks 已安装但需 OpenClaw 调用才能生效"
    echo ""
    echo "文档: https://github.com/useens/moltcare-open#readme"
}

# 主流程
main() {
    print_banner
    
    check_dependencies
    download_moltcare
    install_cli
    verify_version
    setup_path
    auto_init
    
    print_finish
}

# 运行
main "$@"
