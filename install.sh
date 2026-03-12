#!/bin/bash
# MoltCare 安装脚本
# 使用方法: curl -fsSL https://raw.githubusercontent.com/useens/moltcare/main/install.sh | bash

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 版本
MOLTCARE_VERSION="1.1.0"
REPO_URL="https://github.com/useens/moltcare"
INSTALL_DIR="/usr/local/bin"

print_banner() {
    echo -e "${BLUE}"
    echo "🦞 MoltCare 安装程序"
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
}

# 下载 MoltCare
download_moltcare() {
    print_info "下载 MoltCare v${MOLTCARE_VERSION}..."
    
    # 创建临时目录
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    # 下载最新版本
    if command -v curl &> /dev/null; then
        curl -fsSL "${REPO_URL}/archive/refs/heads/main.tar.gz" -o moltcare.tar.gz
    elif command -v wget &> /dev/null; then
        wget -q "${REPO_URL}/archive/refs/heads/main.tar.gz" -O moltcare.tar.gz
    else
        print_error "需要 curl 或 wget"
        exit 1
    fi
    
    # 解压
    tar -xzf moltcare.tar.gz
    
    print_success "下载完成"
}

# 安装文件
install_files() {
    print_info "安装文件..."
    
    # 创建安装目录
    MOLTCARE_HOME="$HOME/.moltcare"
    mkdir -p "$MOLTCARE_HOME"/{packs,workspace,scripts}
    
    # 复制智能包
    if [ -d "$TEMP_DIR/moltcare-main/packs" ]; then
        cp -r "$TEMP_DIR/moltcare-main/packs"/* "$MOLTCARE_HOME/packs/" 2>/dev/null || true
        print_success "智能包已安装"
    fi
    
    # 安装 CLI 脚本
    CLI_SCRIPT="$TEMP_DIR/moltcare-main/moltcare"
    if [ -f "$CLI_SCRIPT" ]; then
        # 安装到用户 bin 目录
        mkdir -p "$HOME/.local/bin"
        cp "$CLI_SCRIPT" "$HOME/.local/bin/moltcare"
        chmod +x "$HOME/.local/bin/moltcare"
        print_success "CLI 已安装到 ~/.local/bin/moltcare"
    fi
    
    # 清理临时文件
    rm -rf "$TEMP_DIR"
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

# 初始化配置
init_config() {
    print_info "初始化配置..."
    
    # 创建默认配置
    CONFIG_FILE="$HOME/.moltcare/config.yaml"
    if [ ! -f "$CONFIG_FILE" ]; then
        cat > "$CONFIG_FILE" << EOF
version: ${MOLTCARE_VERSION}
language: zh
workspacePath: ${HOME}/.moltcare/workspace
packsDir: ${HOME}/.moltcare/packs
logLevel: info
autoUpdate: true
initialized: true
EOF
        print_success "配置文件已创建"
    fi
}

# 打印完成信息
print_finish() {
    echo ""
    echo -e "${GREEN}🎉 MoltCare 安装完成!${NC}"
    echo ""
    echo "版本: $MOLTCARE_VERSION"
    echo "安装路径: $HOME/.moltcare"
    echo ""
    echo "快速开始:"
    echo "  1. 确保 PATH 包含 ~/.local/bin"
    echo "  2. 运行: moltcare init"
    echo "  3. 运行: moltcare list"
    echo "  4. 运行: moltcare apply foundation"
    echo ""
    echo "文档: https://github.com/useens/moltcare#readme"
}

# 主流程
main() {
    print_banner
    
    check_dependencies
    download_moltcare
    install_files
    setup_path
    init_config
    
    print_finish
}

# 运行
main "$@"
