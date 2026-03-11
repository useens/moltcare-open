#!/bin/bash
#
# Moltcare 发布脚本
# 用法: ./scripts/release.sh [version] [--dry-run]
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 参数解析
VERSION=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            VERSION="$1"
            shift
            ;;
    esac
done

# 辅助函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否在正确的目录
if [ ! -f "pyproject.toml" ]; then
    log_error "请在项目根目录运行此脚本"
    exit 1
fi

# 如果没有提供版本号，从 pyproject.toml 读取
if [ -z "$VERSION" ]; then
    VERSION=$(grep -oP 'version = "\K[^"]+' pyproject.toml | head -1)
    log_info "从 pyproject.toml 读取版本: $VERSION"
fi

log_info "开始发布流程 v$VERSION"
if [ "$DRY_RUN" = true ]; then
    log_warning " Dry Run 模式 - 不会执行实际发布"
fi

echo ""

# ============================================
# 发布检查清单
# ============================================

checklist=()
failures=()

add_check() {
    checklist+=("$1")
}

mark_passed() {
    log_success "✓ $1"
}

mark_failed() {
    log_error "✗ $1"
    failures+=("$1")
}

# 1. 检查 Git 状态
add_check "Git 工作区干净"
if git diff --quiet && git diff --cached --quiet; then
    mark_passed "Git 工作区干净"
else
    mark_failed "Git 工作区干净 - 有未提交的更改"
fi

# 2. 检查主分支
add_check "当前在 main 分支"
current_branch=$(git branch --show-current)
if [ "$current_branch" == "main" ]; then
    mark_passed "当前在 main 分支"
else
    mark_failed "当前在 main 分支 - 当前在 $current_branch 分支"
fi

# 3. 检查版本标签
add_check "版本标签不存在"
if git tag -l "v$VERSION" | grep -q "v$VERSION"; then
    mark_failed "版本标签不存在 - 标签 v$VERSION 已存在"
else
    mark_passed "版本标签不存在"
fi

# 4. 检查 CHANGELOG
add_check "CHANGELOG.md 已更新"
if [ -f "CHANGELOG.md" ] && grep -q "## \[$VERSION\]" CHANGELOG.md; then
    mark_passed "CHANGELOG.md 已更新"
else
    mark_failed "CHANGELOG.md 已更新 - 未找到版本 $VERSION"
fi

# 5. 检查关键文件
add_check "关键文件存在"
for file in README.md LICENSE pyproject.toml; do
    if [ ! -f "$file" ]; then
        mark_failed "关键文件存在 - 缺少 $file"
        break
    fi
done
if [ ${#failures[@]} -eq 0 ] || [[ ! " ${failures[*]} " =~ "关键文件存在" ]]; then
    mark_passed "关键文件存在"
fi

# 6. 检查模板文件
add_check "模板文件完整"
templates_complete=true
for template in SOUL.md AGENTS.md IDENTITY.md USER.md MEMORY.md; do
    if [ ! -f "templates/$template" ]; then
        templates_complete=false
        break
    fi
done
if [ "$templates_complete" = true ]; then
    mark_passed "模板文件完整"
else
    mark_failed "模板文件完整 - 缺少模板文件"
fi

# 7. 运行测试
add_check "所有测试通过"
log_info "运行测试..."
if python -m pytest tests/ -q --tb=no 2>/dev/null; then
    mark_passed "所有测试通过"
else
    mark_failed "所有测试通过 - 测试失败"
fi

# 8. 检查代码格式
add_check "代码格式正确"
if black --check --quiet src/ tests/ moltcare/ 2>/dev/null; then
    mark_passed "代码格式正确"
else
    mark_failed "代码格式正确 - 需要格式化"
fi

# 9. 构建测试
add_check "可以成功构建"
log_info "测试构建..."
if python -m build --quiet 2>/dev/null; then
    mark_passed "可以成功构建"
    rm -rf dist/  # 清理测试构建
else
    mark_failed "可以成功构建 - 构建失败"
fi

# 10. 检查文档
add_check "文档完整"
docs_complete=true
for doc in docs/tutorial.md docs/contributing.md docs/architecture.md; do
    if [ ! -f "$doc" ]; then
        docs_complete=false
        log_warning "  缺少文档: $doc"
    fi
done
if [ "$docs_complete" = true ]; then
    mark_passed "文档完整"
else
    mark_failed "文档完整 - 部分文档缺失"
fi

echo ""

# ============================================
# 检查结果汇总
# ============================================

total_checks=${#checklist[@]}
passed_checks=$((total_checks - ${#failures[@]}))

log_info "检查完成: $passed_checks/$total_checks 通过"

if [ ${#failures[@]} -gt 0 ]; then
    echo ""
    log_error "以下检查未通过:"
    for failure in "${failures[@]}"; do
        echo "  - $failure"
    done
    echo ""
    log_error "请先修复以上问题后再发布"
    exit 1
fi

echo ""
log_success "✅ 所有检查通过！"
echo ""

# ============================================
# 执行发布
# ============================================

if [ "$DRY_RUN" = true ]; then
    log_warning "Dry Run 模式，跳过实际发布步骤"
    log_info "将执行以下操作:"
    echo "  1. git tag -a v$VERSION -m \"Release v$VERSION\""
    echo "  2. git push origin v$VERSION"
    echo "  3. 触发 GitHub Actions release workflow"
    exit 0
fi

# 确认发布
read -p "确认发布 v$VERSION? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    log_info "发布已取消"
    exit 0
fi

# 创建标签
echo ""
log_info "创建标签 v$VERSION..."
git tag -a "v$VERSION" -m "Release v$VERSION"
log_success "标签创建成功"

# 推送标签
log_info "推送标签到 origin..."
git push origin "v$VERSION"
log_success "标签推送成功"

# 触发 GitHub Actions 发布
echo ""
log_info "GitHub Actions 发布工作流已触发"
log_info "请访问: https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions"

echo ""
log_success "🎉 发布流程已启动！"
log_info "版本 v$VERSION 将在 CI/CD 完成后发布到 PyPI"
