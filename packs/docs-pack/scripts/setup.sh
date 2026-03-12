#!/bin/bash
# docs-pack 安装脚本

echo "📚 配置文档环境..."

# 创建文档目录结构
mkdir -p docs/api
mkdir -p docs/guides
mkdir -p docs/examples
echo "✓ 创建 docs/ 目录结构"

# 创建 README 模板
if [ ! -f "README.md" ] || [ "$1" = "--force" ]; then
    cat > README.md << 'EOF'
# 项目名称

> 一句话描述项目核心价值

## 简介

详细介绍项目背景、解决的问题、主要特性。

## 安装

### 系统要求
- Python 3.8+
- 其他依赖

### 快速安装
```bash
pip install your-package
```

## 快速开始

```python
import your_package

# 基本用法
result = your_package.do_something()
print(result)
```

## 文档

- [使用指南](docs/guides/usage.md)
- [API 参考](docs/api/README.md)
- [示例](docs/examples/)

## 贡献

见 [CONTRIBUTING.md](CONTRIBUTING.md)

## 许可证

[MIT](LICENSE)
EOF
    echo "✓ 创建 README.md 模板"
fi

# 创建 CHANGELOG.md
if [ ! -f "CHANGELOG.md" ]; then
    cat > CHANGELOG.md << 'EOF'
# Changelog

## [Unreleased]

### Added
- 初始化项目

## [0.1.0] - $(date +%Y-%m-%d)

### Added
- 首个版本发布
EOF
    echo "✓ 创建 CHANGELOG.md"
fi

# 创建 CONTRIBUTING.md
if [ ! -f "CONTRIBUTING.md" ]; then
    cat > CONTRIBUTING.md << 'EOF'
# 贡献指南

感谢你的贡献！

## 开发流程

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 文档贡献

- 保持简洁清晰
- 添加代码示例
- 更新 CHANGELOG

## 行为准则

- 友善和尊重
- 接受建设性批评
- 关注社区利益
EOF
    echo "✓ 创建 CONTRIBUTING.md"
fi

# 创建 API 文档模板
cat > docs/api/README.md << 'EOF'
# API 参考

## 模块

### 函数名

**描述**
函数描述。

**参数**
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| param1 | str | 是 | 参数1 |
| param2 | int | 否 | 参数2，默认 0 |

**返回值**
| 类型 | 说明 |
|------|------|
| ReturnType | 返回值说明 |

**示例**
```python
result = function_name("value")
```
EOF
echo "✓ 创建 API 文档模板"

# 创建使用指南模板
cat > docs/guides/usage.md << 'EOF'
# 使用指南

## 安装

```bash
pip install your-package
```

## 基本用法

### 示例 1: 基础功能

```python
import your_package

# 初始化
client = your_package.Client()

# 使用
result = client.do_something()
print(result)
```

### 示例 2: 高级功能

```python
# 高级配置
config = {
    'option': 'value',
    'timeout': 30
}
client = your_package.Client(config)
```

## 常见问题

### Q: 如何解决问题 X？

A: 解决方案...

## 下一步

- 查看 [API 文档](../api/README.md)
- 浏览 [示例](../examples/)
EOF
echo "✓ 创建使用指南模板"

# 创建示例目录
mkdir -p docs/examples
cat > docs/examples/basic.py << 'EOF'
#!/usr/bin/env python3
"""基础示例."""

import your_package


def main():
    """运行基础示例."""
    # 初始化
    client = your_package.Client()
    
    # 执行操作
    result = client.do_something()
    
    # 输出结果
    print(f"结果: {result}")


if __name__ == "__main__":
    main()
EOF
chmod +x docs/examples/basic.py
echo "✓ 创建示例代码"

# 创建文档检查脚本
cat > scripts/check-docs.sh << 'EOF'
#!/bin/bash
# 文档检查脚本

echo "📚 检查文档..."

errors=0

# 检查必需文件
for file in README.md CHANGELOG.md CONTRIBUTING.md; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file 缺失"
        errors=$((errors + 1))
    fi
done

# 检查文档目录
if [ -d "docs" ]; then
    echo "  ✓ docs/ 目录存在"
else
    echo "  ✗ docs/ 目录缺失"
    errors=$((errors + 1))
fi

# 检查 README 关键部分
if [ -f "README.md" ]; then
    for section in "安装" "使用" "贡献" "许可证"; do
        if grep -q "$section" README.md; then
            echo "  ✓ README 包含: $section"
        else
            echo "  ⚠ README 缺少: $section"
        fi
    done
fi

echo ""
if [ $errors -eq 0 ]; then
    echo "✅ 所有文档检查通过"
else
    echo "⚠️  发现 $errors 个问题"
fi
EOF
chmod +x scripts/check-docs.sh
echo "✓ 创建文档检查脚本"

echo ""
echo "🎉 docs-pack 配置完成!"
echo ""
echo "已创建:"
echo "  📄 README.md - 项目说明"
echo "  📄 CHANGELOG.md - 变更日志"
echo "  📄 CONTRIBUTING.md - 贡献指南"
echo "  📁 docs/ - 文档目录"
echo "  📁 docs/api/ - API 文档"
echo "  📁 docs/guides/ - 使用指南"
echo "  📁 docs/examples/ - 示例代码"
echo ""
echo "使用方法:"
echo "  ./scripts/check-docs.sh      # 检查文档完整性"
echo "  cat DOCUMENTATION_GUIDE.md   # 查看文档规范"
echo ""
echo "下一步:"
echo "  1. 编辑 README.md 填写项目信息"
echo "  2. 编写 docs/guides/usage.md"
echo "  3. 添加 API 文档到 docs/api/"
