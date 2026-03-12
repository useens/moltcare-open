# AI 辅助编程指南

> MoltCare ai-pack 自动生成

## 🤖 AI 编程最佳实践

### 1. 有效的 Prompt 技巧

#### ✅ 好的 Prompt 结构

```
角色 + 任务 + 上下文 + 约束 + 输出格式
```

**示例：**
```
角色: 你是一位资深的 Python 后端工程师

任务: 审查以下代码并提供改进建议

上下文: 
- 这是一个 Flask REST API 端点
- 需要处理高并发请求
- 使用 PostgreSQL 数据库

约束:
- 保持向后兼容
- 遵循 PEP 8 规范
- 添加类型注解

输出格式:
1. 问题列表（按严重程度排序）
2. 具体改进建议
3. 优化后的代码
```

#### ❌ 避免的 Prompt

```
# 太模糊
"帮我看看这段代码"

# 没有上下文
"修复这个 bug"

# 没有约束
"重写这个函数"
```

### 2. 代码审查 Prompt 模板

#### 通用审查

```markdown
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
- 问题描述
- 具体位置
- 修复建议

### 🟡 改进建议
- 建议内容
- 预期收益

### 🟢 良好实践
- 值得保持的做法

## 代码
```python
{{code}}
```
```

#### 安全审查

```markdown
审查以下代码的安全性：

重点关注：
- SQL 注入风险
- XSS 漏洞
- 敏感信息泄露
- 权限控制缺陷
- 输入验证缺失

代码：
```python
{{code}}
```

输出格式：
1. 发现的漏洞（CVSS 评分）
2. 利用场景
3. 修复方案
4. 预防措施
```

### 3. 代码生成 Prompt 模板

#### 函数生成

```markdown
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
```

#### 测试生成

```markdown
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
```

## 💡 AI 结对编程模式

### 模式 1: 驾驶-导航员

```
你（人类）：编写核心逻辑
AI：审查、建议、发现边界情况

示例对话：
你: 我打算这样实现用户认证...
AI: 考虑到了密码哈希吗？建议使用 bcrypt...
你: 好，我加上...
AI: 还要考虑速率限制，防止暴力破解...
```

### 模式 2: 探索-验证

```
AI：生成多个实现方案
你：评估、选择、细化

示例：
你: 如何优化这个查询？
AI: 方案 1: 添加索引... 方案 2: 使用缓存... 方案 3: 重构表结构...
你: 我选择方案 2，因为...
```

### 模式 3: 解释-学习

```
你：粘贴不理解的代码
AI：解释、教学、扩展

示例：
你: 这段代码什么意思？
AI: 这是一个装饰器模式...
你: 能解释下装饰器的工作原理吗？
AI: 装饰器本质上是一个高阶函数...
```

## 📝 Prompt 库

### 常用 Prompt 快捷方式

```bash
# 创建 prompt 别名
alias ai-review='cat > /tmp/code.py && ai-prompt "审查这段代码" /tmp/code.py'
alias ai-test='cat > /tmp/func.py && ai-prompt "为这函数生成测试" /tmp/func.py'
alias ai-doc='cat > /tmp/code.py && ai-prompt "为这段代码写文档" /tmp/code.py'
```

### Prompt 模板文件

```markdown
# prompts/review.md
## 代码审查

### 基本信息
- 语言: {{language}}
- 框架: {{framework}}
- 复杂度: {{complexity}}

### 审查重点
{{focus_areas}}

### 代码
```{{language}}
{{code}}
```

### 期望输出
{{expected_output}}
```

## 🔧 工具集成

### 与编辑器集成

#### VS Code
```json
// settings.json
{
  "ai.codeLens.enable": true,
  "ai.completion.enable": true,
  "ai.review.onSave": true
}
```

#### Vim/Neovim
```vim
" 使用 Copilot 或 Codeium
Plug 'github/copilot.vim'

" 自定义 AI 命令
command! AIReview :!ai-review %
command! AITest :!ai-test %
```

### 命令行工具

```python
#!/usr/bin/env python3
# ai-prompt.py - AI Prompt 命令行工具

import sys
import argparse
import pyperclip

def main():
    parser = argparse.ArgumentParser(description='AI Prompt 工具')
    parser.add_argument('template', help='Prompt 模板')
    parser.add_argument('file', nargs='?', help='代码文件')
    parser.add_argument('--copy', '-c', action='store_true', help='复制到剪贴板')
    
    args = parser.parse_args()
    
    # 读取模板
    template = load_template(args.template)
    
    # 读取代码
    if args.file:
        with open(args.file) as f:
            code = f.read()
        template = template.replace('{{code}}', code)
    
    # 输出
    if args.copy:
        pyperclip.copy(template)
        print("已复制到剪贴板")
    else:
        print(template)

if __name__ == '__main__':
    main()
```

## ⚠️ AI 编程注意事项

### 1. 不要完全信任 AI 代码

- 始终审查生成的代码
- 测试边界条件
- 验证安全性和性能

### 2. 保持代码所有权

- 理解 AI 生成的每一行代码
- 能够解释和修改
- 不要提交不理解的代码

### 3. 保护敏感信息

```
❌ 不要：
- 将 API keys 粘贴给 AI
- 提交内部架构细节
- 分享用户数据

✅ 可以：
- 使用匿名化的示例数据
- 描述问题而不暴露实现
- 审查后再提交
```

### 4. 知识产权

- 确认公司政策允许使用 AI
- 了解代码归属权
- 遵守开源许可证

## 📚 进阶技巧

### 1. 上下文管理

```markdown
# 长对话时定期总结上下文

当前上下文：
- 项目：Flask REST API
- 功能：用户认证系统
- 已完成：登录端点
- 正在做：JWT 刷新机制
- 问题：如何处理并发刷新？

请基于以上上下文回答：{{question}}
```

### 2. 迭代优化

```
第 1 轮：生成基础实现
第 2 轮：优化性能
第 3 轮：添加错误处理
第 4 轮：完善文档
```

### 3. 多角度审查

```
Prompt 1: 从安全角度审查
Prompt 2: 从性能角度审查
Prompt 3: 从可维护性角度审查
Prompt 4: 综合以上给出最终建议
```

---

*此指南由 MoltCare ai-pack 自动生成*
*AI 是工具，不是替代品*
