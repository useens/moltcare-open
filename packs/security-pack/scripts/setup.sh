#!/bin/bash
# security-pack 安装脚本

echo "🔒 配置安全审计环境..."

# 检查 Python
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "✓ Python $PYTHON_VERSION"

# 安装安全工具
echo ""
echo "安装安全扫描工具..."

pip install --quiet bandit safety semgrep 2>/dev/null || {
    echo "⚠️  部分工具安装失败，尝试单独安装..."
    pip install bandit || echo "  ✗ bandit 安装失败"
    pip install safety || echo "  ✗ safety 安装失败"
    pip install semgrep || echo "  ✗ semgrep 安装失败"
}

# 创建 Bandit 配置
if [ ! -f ".bandit.yml" ]; then
    cat > .bandit.yml << 'EOF'
# MoltCare security-pack 生成的 Bandit 配置
skips: []
severity_level: LOW
confidence_level: LOW
exclude_dirs:
  - tests
  - venv
  - .venv
  - __pycache__
  - node_modules
EOF
    echo "✓ 创建 .bandit.yml"
fi

# 创建安全扫描脚本
if [ ! -f "scripts/security-scan.sh" ]; then
    mkdir -p scripts
    cat > scripts/security-scan.sh << 'EOF'
#!/bin/bash
# 安全扫描脚本
# MoltCare security-pack 自动生成

echo "🔒 运行安全扫描..."
echo ""

# Bandit 扫描
echo "📊 Bandit 扫描..."
if command -v bandit &> /dev/null; then
    bandit -r src/ -f json -o reports/bandit-report.json 2>/dev/null || true
    bandit -r src/ || true
else
    echo "⚠️  bandit 未安装"
fi

echo ""

# Safety 检查
echo "📊 Safety 依赖检查..."
if command -v safety &> /dev/null; then
    safety check || true
else
    echo "⚠️  safety 未安装"
fi

echo ""

# Semgrep 扫描
echo "📊 Semgrep 静态分析..."
if command -v semgrep &> /dev/null; then
    semgrep --config=auto src/ || true
else
    echo "⚠️  semgrep 未安装"
fi

echo ""
echo "✅ 安全扫描完成"
echo "查看 reports/ 目录获取详细报告"
EOF
    chmod +x scripts/security-scan.sh
    echo "✓ 创建 scripts/security-scan.sh"
fi

# 创建 reports 目录
mkdir -p reports
echo "✓ 创建 reports/ 目录"

# 创建 .gitignore 安全增强
if [ -f ".gitignore" ]; then
    if ! grep -q "# Security" .gitignore; then
        cat >> .gitignore << 'EOF'

# Security - security-pack 添加
.env
.env.local
.env.*.local
*.pem
*.key
secrets/
credentials/
.bandit-report.json
reports/bandit-report.json
reports/safety-report.json
EOF
        echo "✓ 更新 .gitignore 安全规则"
    fi
else
    cat > .gitignore << 'EOF'
# Security - security-pack 添加
.env
.env.local
.env.*.local
*.pem
*.key
secrets/
credentials/
reports/
EOF
    echo "✓ 创建 .gitignore"
fi

# 创建 pre-commit 安全钩子
if [ -f ".pre-commit-config.yaml" ]; then
    if ! grep -q "bandit" .pre-commit-config.yaml; then
        cat >> .pre-commit-config.yaml << 'EOF'

  # Security hooks - security-pack 添加
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.7
    hooks:
      - id: bandit
        args: ["-c", ".bandit.yml"]
        
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
EOF
        echo "✓ 更新 .pre-commit-config.yaml 安全钩子"
    fi
fi

echo ""
echo "🎉 security-pack 配置完成!"
echo ""
echo "安全工具:"
echo "  bandit  - Python 安全 linter"
echo "  safety  - 依赖漏洞检查"
echo "  semgrep - 静态代码分析"
echo ""
echo "使用方法:"
echo "  ./scripts/security-scan.sh    # 运行完整安全扫描"
echo "  bandit -r src/                # 手动运行 bandit"
echo "  safety check                  # 手动检查依赖"
echo ""
echo "查看文档:"
echo "  cat SECURITY_GUIDE.md         # 安全开发规范"
echo "  cat AUDIT_TEMPLATE.md         # 审计报告模板"
