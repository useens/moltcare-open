#!/bin/bash
#
# Moltcare 代码整合脚本
# 用于整合各个子代理的产出
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查目录
check_directories() {
    log_info "检查项目目录结构..."
    
    directories=(
        "moltcare"
        "moltcare/commands"
        "moltcare/templates"
        "templates"
        "tests"
        "docs"
        "examples"
        "scripts"
        ".github/workflows"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            log_info "创建目录: $dir"
            mkdir -p "$dir"
        fi
    done
    
    log_success "目录结构检查完成"
}

# 整合核心文件
integrate_core() {
    log_info "整合核心模板文件..."
    
    core_files=(
        "templates/SOUL.md"
        "templates/AGENTS.md"
        "templates/IDENTITY.md"
        "templates/USER.md"
        "templates/MEMORY.md"
    )
    
    for file in "${core_files[@]}"; do
        if [ -f "$file" ]; then
            log_success "✓ $file"
        else
            log_warning "✗ $file 不存在"
        fi
    done
}

# 整合CLI工具
integrate_cli() {
    log_info "整合CLI工具..."
    
    cli_files=(
        "moltcare/__init__.py"
        "moltcare/cli.py"
        "moltcare/commands/__init__.py"
        "moltcare/commands/init.py"
        "moltcare/commands/upgrade.py"
        "moltcare/commands/doctor.py"
        "moltcare/commands/backup.py"
    )
    
    for file in "${cli_files[@]}"; do
        if [ -f "$file" ]; then
            log_success "✓ $file"
        else
            log_warning "✗ $file 不存在"
        fi
    done
}

# 整合测试
integrate_tests() {
    log_info "整合测试文件..."
    
    if [ -d "tests" ]; then
        test_count=$(find tests -name "test_*.py" | wc -l)
        log_success "发现 $test_count 个测试文件"
    else
        log_warning "tests 目录不存在"
    fi
}

# 整合文档
integrate_docs() {
    log_info "整合文档..."
    
    doc_files=(
        "README.md"
        "README.en.md"
        "docs/tutorial.md"
        "docs/contributing.md"
        "docs/architecture.md"
        "docs/collaboration-protocol.md"
    )
    
    for file in "${doc_files[@]}"; do
        if [ -f "$file" ]; then
            log_success "✓ $file"
        else
            log_warning "✗ $file 不存在"
        fi
    done
}

# 检查代码风格
check_code_style() {
    log_info "检查代码风格..."
    
    if command -v black &> /dev/null; then
        if black --check --quiet src/ tests/ moltcare/ 2>/dev/null; then
            log_success "代码格式正确 (black)"
        else
            log_warning "代码需要格式化，运行: black src/ tests/ moltcare/"
        fi
    else
        log_warning "black 未安装，跳过格式检查"
    fi
    
    if command -v flake8 &> /dev/null; then
        if flake8 src/ tests/ moltcare/ --max-line-length=100 2>/dev/null; then
            log_success "代码风格检查通过 (flake8)"
        else
            log_warning "代码风格检查发现问题"
        fi
    else
        log_warning "flake8 未安装，跳过风格检查"
    fi
}

# 运行测试
run_tests() {
    log_info "运行测试..."
    
    if command -v pytest &> /dev/null; then
        if pytest tests/ -q --tb=no 2>/dev/null; then
            log_success "所有测试通过"
        else
            log_error "部分测试失败"
        fi
    else
        log_warning "pytest 未安装，跳过测试"
    fi
}

# 生成整合报告
generate_report() {
    log_info "生成整合报告..."
    
    report_file="integration-report-$(date +%Y%m%d-%H%M%S).md"
    
    cat > "$report_file" << EOF
# Moltcare 整合报告

**生成时间**: $(date)
**Git Commit**: $(git rev-parse --short HEAD 2>/dev/null || echo "N/A")

## 文件统计

| 类别 | 文件数 |
|------|--------|
| Python 源码 | $(find src moltcare -name "*.py" 2>/dev/null | wc -l) |
| 模板文件 | $(find templates -name "*.md" 2>/dev/null | wc -l) |
| 测试文件 | $(find tests -name "test_*.py" 2>/dev/null | wc -l) |
| 文档文件 | $(find docs -name "*.md" 2>/dev/null | wc -l) |
| 示例配置 | $(find examples -type d -mindepth 1 2>/dev/null | wc -l) |

## 核心组件状态

### 模板系统
$(for f in templates/*.md; do echo "- [$(test -f "$f" && echo "x" || echo " ")] $(basename $f)"; done)

### CLI 命令
$(for f in moltcare/commands/*.py; do echo "- [$(test -f "$f" && echo "x" || echo " ")] $(basename $f .py)"; done)

### CI/CD 配置
$(for f in .github/workflows/*.yml; do echo "- [$(test -f "$f" && echo "x" || echo " ")] $(basename $f)"; done)

## 待办事项

- [ ] 所有子代理产出已合并
- [ ] 代码风格统一
- [ ] 测试全部通过
- [ ] 文档完整
- [ ] CI/CD 配置正确
- [ ] 版本号更新
- [ ] CHANGELOG 更新

---
*由 Integration Agent 自动生成*
EOF

    log_success "报告已生成: $report_file"
}

# 主函数
main() {
    echo ""
    echo "=============================================="
    echo "   Moltcare 代码整合脚本"
    echo "=============================================="
    echo ""
    
    check_directories
    echo ""
    integrate_core
    echo ""
    integrate_cli
    echo ""
    integrate_tests
    echo ""
    integrate_docs
    echo ""
    check_code_style
    echo ""
    run_tests
    echo ""
    generate_report
    
    echo ""
    log_success "整合检查完成！"
    echo ""
}

# 运行主函数
main
