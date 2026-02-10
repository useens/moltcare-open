# 林林v5.0 自我编程能力 v0.1

> 建立自我编程能力，遇到现有工具解决不了的问题时能自己写代码

## 概述

自我编程能力让林林能够：
1. 理解自然语言需求
2. 生成安全可靠的代码
3. 自动验证代码正确性
4. 执行生成的代码解决实际问题

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    自我编程系统 v0.1                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  需求解析器   │───▶│  代码生成器   │───▶│  代码验证器   │  │
│  │ Requirement  │    │   Code       │    │   Code       │  │
│  │   Parser     │    │  Generator   │    │  Validator   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    代码模板库                          │  │
│  │  [cpu] [memory] [disk] [network] [process] [port]    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. 代码生成器 (core/code_generator.py)

**功能:**
- 需求解析：将自然语言转化为技术规格
- 模板系统：基于指标类型选择代码模板
- 安全过滤：内置危险代码检测

**支持的指标类型:**
| 类型 | 描述 | 示例 |
|------|------|------|
| cpu | CPU使用率 | "检查CPU是否超过80%" |
| memory | 内存使用率 | "检查内存是否超过90%" |
| disk | 磁盘使用率 | "检查磁盘空间是否超过85%" |
| network | 网络状态 | "检查网络连接" |
| process | 进程状态 | "检查进程数量" |
| port | 端口监听 | "检查80端口" |
| load | 系统负载 | "检查系统负载" |

**使用示例:**
```python
from core.code_generator import CodeGenerator

generator = CodeGenerator()
result = generator.generate("检查CPU使用率是否超过80%", "check_cpu.py")

if result['success']:
    print(f"生成成功: {result['code']}")
```

### 2. 代码验证器 (core/code_validator.py)

**四层验证体系:**

1. **语法检查 (Syntax)**
   - 使用 AST 解析验证 Python 语法
   - 使用 py_compile 编译验证

2. **静态分析 (Static)**
   - 危险导入检测 (os.system, eval, exec等)
   - 危险函数调用检测
   - 敏感路径访问检测

3. **沙箱测试 (Sandbox)**
   - 在隔离环境运行代码
   - 资源限制 (CPU时间、内存)
   - 超时保护

4. **输出验证 (Output)**
   - 验证输出格式是否符合预期
   - 支持自定义验证模式

**使用示例:**
```python
from core.code_validator import CodeValidator

validator = CodeValidator()
result = validator.full_validate(code)

print(validator.get_validation_report(result))
```

## 安全约束

### 禁止的危险操作

以下模式将被自动拦截:

| 类型 | 示例 |
|------|------|
| 强制删除 | `rm -rf /` |
| 格式化 | `mkfs`, `format` |
| 危险写入 | `dd if=... of=/dev/...` |
| 代码执行 | `eval()`, `exec()` |
| 系统调用 | `os.system()`, `subprocess.call(shell=True)` |

### 安全流程

```
需求输入 → 生成代码 → 安全扫描 → 沙箱测试 → 人工审查 → 部署
              ↓           ↓           ↓
            失败        拦截        异常
              └───────────┴───────────┘
                        ↓
                    返回错误
```

## 使用指南

### 命令行使用

```bash
# 运行演示
python self_programming.py --demo

# 交互模式
python self_programming.py -i

# 创建指定检查
python self_programming.py -r "检查CPU使用率是否超过80%"

# 跳过测试直接生成
python self_programming.py -r "检查内存使用率" --no-test
```

### Python API

```python
from self_programming import SelfProgrammingSystem

system = SelfProgrammingSystem()

# 创建单个检查
result = system.create_health_check("检查磁盘空间是否超过85%")

# 批量创建
demo_reqs = [
    "检查CPU使用率是否超过80%",
    "检查内存使用率是否超过90%",
    "检查磁盘空间是否超过85%",
]
results = system.batch_create(demo_reqs)
```

## 示例输出

### 生成健康检查脚本示例

**输入:**
```
检查CPU使用率是否超过80%
```

**输出 (check_cpu.py):**
```python
#!/usr/bin/env python3
"""
CPU健康检查脚本
生成时间: 2024-01-15T10:30:00
原始需求: 检查CPU使用率是否超过80%
"""

import psutil
import sys

def check_cpu():
    """检查CPU使用率"""
    cpu_percent = psutil.cpu_percent(interval=1)
    threshold = 80
    operator = '>'
    
    condition_met = cpu_percent > threshold if operator == '>' else cpu_percent < threshold
    
    if condition_met:
        print(f"[WARNING] CPU使用率: {cpu_percent}% (阈值: >80%)")
        return 1
    else:
        print(f"[OK] CPU使用率: {cpu_percent}%")
        return 0

if __name__ == '__main__':
    sys.exit(check_cpu())
```

**验证报告:**
```
============================================================
代码验证报告
============================================================
总体结果: ✓ 通过
总耗时: 1234.56ms
阶段统计: 4/4 通过
------------------------------------------------------------
[✓] SYNTAX: 语法检查通过
[✓] STATIC: 静态分析通过 (0 个警告)
[✓] SANDBOX: 沙箱测试通过
[✓] OUTPUT: 输出验证通过
============================================================
```

## 项目结构

```
workspace/
├── core/
│   ├── code_generator.py    # 代码生成器
│   └── code_validator.py    # 代码验证器
├── sandbox/                  # 沙箱测试目录
├── examples/                 # 生成的示例脚本
├── docs/
│   └── self_programming.md  # 本文档
└── self_programming.py      # 主入口
```

## 开发计划

### v0.1 (当前)
- ✅ 基础代码生成框架
- ✅ 四层验证体系
- ✅ 7个健康检查模板
- ✅ 安全约束机制

### v0.2 (计划中)
- 更多模板类型 (日志分析、性能测试等)
- 需求理解增强 (支持复杂条件)
- 模板自定义功能
- 生成代码优化建议

### v0.3 (规划中)
- 支持bash脚本生成
- 代码迭代优化能力
- 学习用户反馈改进
- 多语言支持

## 注意事项

1. **安全优先**: 所有生成的代码必须经过验证才能运行
2. **沙箱限制**: 沙箱测试有一定资源限制，复杂脚本可能需要调整
3. **人工审查**: 关键场景建议人工审查生成的代码
4. **模板扩展**: 可通过修改 `CodeTemplateLibrary` 添加新模板

## 附录

### 需求关键词对照表

| 关键词 | 对应指标 |
|--------|----------|
| cpu, 处理器, CPU使用率 | cpu |
| memory, 内存, ram | memory |
| disk, 磁盘, 硬盘, 空间 | disk |
| network, 网络, 网卡 | network |
| process, 进程 | process |
| port, 端口 | port |
| load, 负载 | load |

### 阈值比较符

| 关键词 | 运算符 |
|--------|--------|
| 超过, 大于, 高于 | > |
| 低于, 小于 | < |
