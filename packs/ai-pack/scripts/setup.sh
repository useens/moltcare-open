#!/bin/bash
# ai-pack 安装脚本

echo "🤖 配置 AI 辅助编程环境..."

# 创建 prompts 目录
mkdir -p prompts/code-review
mkdir -p prompts/code-generation
mkdir -p prompts/refactoring
mkdir -p prompts/documentation
echo "✓ 创建 prompts/ 目录结构"

# 创建代码审查 Prompt 模板
cat > prompts/code-review/basic.md << 'EOF'
## 角色
你是一位经验丰富的代码审查员，专注于代码质量、安全性和可维护性。

## 任务
审查以下代码并提供详细反馈。

## 审查维度
1. **正确性**: 代码是否正确实现了功能？
2. **安全性**: 是否存在安全漏洞？
3. **性能**: 是否有性能问题？
4. **可读性**: 代码是否易于理解？
5. **可维护性**: 是否易于修改和扩展？

## 输出格式
### 🔴 严重问题
### 🟡 改进建议
### 🟢 良好实践

## 代码
```{{language}}
{{code}}
```
EOF
echo "✓ 创建 prompts/code-review/basic.md"

# 创建安全审查 Prompt
cat > prompts/code-review/security.md << 'EOF'
## 角色
你是一位安全专家，专注于代码安全审计。

## 任务
审查以下代码的安全性。

## 重点关注
- SQL 注入风险
- XSS 漏洞
- 敏感信息泄露
- 权限控制缺陷
- 输入验证缺失

## 输出格式
1. 发现的漏洞（CVSS 评分）
2. 利用场景
3. 修复方案
4. 预防措施

## 代码
```{{language}}
{{code}}
```
EOF
echo "✓ 创建 prompts/code-review/security.md"

# 创建代码生成 Prompt
cat > prompts/code-generation/function.md << 'EOF'
生成一个 Python 函数，实现以下功能：

功能：{{description}}

输入：
- {{input_param}}: {{type}} - {{description}}

输出：
- {{return_type}} - {{description}}

要求：
1. 添加类型注解
2. 编写文档字符串
3. 处理边界情况
4. 包含使用示例
5. 遵循 PEP 8

请生成完整代码：
EOF
echo "✓ 创建 prompts/code-generation/function.md"

# 创建测试生成 Prompt
cat > prompts/code-generation/test.md << 'EOF'
为以下函数生成单元测试：

```python
{{function_code}}
```

要求：
1. 使用 pytest
2. 覆盖正常和异常情况
3. 使用参数化测试多种输入
4. 测试边界条件
5. 包含 setup/teardown（如需要）

请生成完整的测试代码：
EOF
echo "✓ 创建 prompts/code-generation/test.md"

# 创建重构 Prompt
cat > prompts/refactoring/clean-code.md << 'EOF'
## 任务
重构以下代码，使其更清晰、更可维护。

## 目标
- 提高可读性
- 减少复杂度
- 遵循设计原则（SOLID）
- 添加适当的抽象

## 代码
```{{language}}
{{code}}
```

## 输出
1. 重构后的代码
2. 重构说明（改了什么，为什么）
EOF
echo "✓ 创建 prompts/refactoring/clean-code.md"

# 创建文档生成 Prompt
cat > prompts/documentation/api-doc.md << 'EOF'
为以下函数生成 API 文档：

```python
{{function_code}}
```

要求：
1. 描述函数用途
2. 列出所有参数（类型、必需、说明）
3. 说明返回值
4. 提供使用示例
5. 列出可能抛出的异常

输出格式使用 Markdown：
EOF
echo "✓ 创建 prompts/documentation/api-doc.md"

# 创建 AI 命令快捷方式脚本
cat > scripts/ai-prompt.sh << 'EOF'
#!/bin/bash
# AI Prompt 快捷工具

PROMPTS_DIR="prompts"

case "$1" in
    review)
        cat "$PROMPTS_DIR/code-review/basic.md"
        ;;
    security)
        cat "$PROMPTS_DIR/code-review/security.md"
        ;;
    test)
        cat "$PROMPTS_DIR/code-generation/test.md"
        ;;
    doc)
        cat "$PROMPTS_DIR/documentation/api-doc.md"
        ;;
    refactor)
        cat "$PROMPTS_DIR/refactoring/clean-code.md"
        ;;
    *)
        echo "用法: ./scripts/ai-prompt.sh [review|security|test|doc|refactor]"
        echo ""
        echo "可用模板:"
        echo "  review    - 代码审查"
        echo "  security  - 安全审查"
        echo "  test      - 测试生成"
        echo "  doc       - 文档生成"
        echo "  refactor  - 代码重构"
        ;;
esac
EOF
chmod +x scripts/ai-prompt.sh
echo "✓ 创建 scripts/ai-prompt.sh"

# 创建 .aiignore 文件
cat > .aiignore << 'EOF'
# AI 工具忽略的文件
# 不要将以下内容发送给 AI 服务

# 敏感信息
.env
.env.local
.env.*.local
*.key
*.pem
secrets/
credentials/

# 用户数据
data/users/
data/private/

# 内部文档
docs/internal/
docs/architecture/
EOF
echo "✓ 创建 .aiignore"

echo ""
echo "🎉 ai-pack 配置完成!"
echo ""
echo "已创建:"
echo "  📁 prompts/              - Prompt 模板库"
echo "  📁 prompts/code-review/   - 代码审查模板"
echo "  📁 prompts/code-generation/ - 代码生成模板"
echo "  📁 prompts/refactoring/   - 重构模板"
echo "  📁 prompts/documentation/ - 文档模板"
echo "  📄 .aiignore             - AI 工具忽略文件"
echo ""
echo "使用方法:"
echo "  ./scripts/ai-prompt.sh review    # 获取代码审查 Prompt"
echo "  ./scripts/ai-prompt.sh security  # 获取安全审查 Prompt"
echo "  ./scripts/ai-prompt.sh test      # 获取测试生成 Prompt"
echo "  ./scripts/ai-prompt.sh doc       # 获取文档生成 Prompt"
echo ""
echo "查看指南:"
echo "  cat AI_CODING_GUIDE.md           # AI 编程最佳实践"
