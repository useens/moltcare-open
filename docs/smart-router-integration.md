# 智能路由集成指南
## 适用于Cron任务和子代理

---

## 工具概述

### 1. Shell包装器 (spawn_with_routing.sh)
在spawn子代理前自动选择模型

```bash
./spawn_with_routing.sh "你的任务" "main"
```

**输出**：
- 建议模型
- Thinking模式
- 生成完整的spawn命令

### 2. Python模块 (smart_router.py)
用于Cron任务和Python脚本内部调用

```python
from scripts.smart_router import SmartRouter, route_by_signal
```

---

## 使用场景

### 场景1: Cron任务内部动态分级

**文件**: scripts/evolution-unified.py

**集成方式**：

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/.openclaw/workspace/scripts')

from smart_router import route_by_signal

def run_phase(phase_name, contents):
    """进化任务主函数"""
    print(f"执行阶段: {phase_name}")

    for content in contents:
        # 获取Signal评分
        signal = content.get('signal', 5)

        # 动态路由选择模型和thinking
        routing = route_by_signal(signal)

        print(f"内容: {content['title']}")
        print(f"Signal: {signal}")
        print(f"路由: {routing['model']} + {routing['thinking']}")
        print(f"原因: {routing['reason']}")
        print()

        # 使用动态路由结果处理内容
        # ... 实际处理逻辑

        # 如果Signal>=9，记录高价值内容
        if signal >= 9:
            print(f"⭐ 高价值内容: {content['title']}")
```

**Signal分级标准**：
```python
# smart_router.py 中定义

Signal 1-4:  ds + off      # 低价值，基础处理
Signal 5-6:  ds + concise  # 中低价值，精简处理
Signal 7-8:  kimi + on     # 中高价值，完整分析
Signal 9-10: k2p5 + stream # 高价值，最强+流式
```

### 场景2: Subagent Spawn

**文件**: scripts/spawn_with_routing.sh

**使用方式1: 直接调用**

```bash
# 获取路由建议并生成命令
./spawn_with_routing.sh "研究最新的AI Agent架构" "main"

# 复制输出的spawn命令执行
openclaw sessions spawn \
  --task="研究最新的AI Agent架构" \
  --agent=main \
  --model=kimi-coding/k2p5 \
  --thinking=on
```

**使用方式2: 在OpenClaw内部集成Python**

```python
from scripts.smart_router import smart_route

def spawn_subagent_with_routing(task: str, agent_id: str = "main"):
    """spawn子代理时自动选择模型"""
    # 获取路由建议
    routing = smart_route(task)

    print(f"任务: {task}")
    print(f"建议模型: {routing['model']} ({routing['full_model']})")
    print(f"Thinking: {routing['thinking']}")

    # 使用OpenClaw的sessions_spawn工具
    # 注意：需要根据实际API调整
    sessions_spawn(
        task=task,
        model=routing['full_model'],
        thinking=routing['thinking']
    )

# 使用示例
spawn_subagent_with_routing(
    "帮我分析这个开源项目的架构设计"
)
```

### 场景3: 会话间智能路由

**在主会话中为子任务选择模型**

```python
from smart_router import smart_route

# 用户提出一个复杂任务
task = "设计一个100万用户的即时通讯系统"

# 自动路由
routing = smart_route(task)

if routing['model'] != 'ds':
    # 需要切换模型
    print(f"💡 复杂任务，建议切换到 {routing['model']}")
    print(f"原因: {routing['reason']}")
    print(f"Thinking模式: {routing['thinking']}")
    # 可以建议用户切换，或者spawn子代理处理
else:
    # 当前模型可以处理
    print("使用当前模型直接处理")
```

---

## Cron任务更新计划

### 待更新文件

1. **scripts/evolution-intelligence.py**
   - 导入: `from smart_router import route_by_signal`
   - Signal 1-6: ds + off (quick scan)
   - Signal 7-8: kimi + on (deep extract)
   - Signal 9-10: k2p5 + stream (architectural)

2. **scripts/moltbook-unified.py**
   - 导入智能路由模块
   - 根据帖子Signal评分动态选择模型

3. **scripts/evolution-knowledge.py**
   - 知识内化阶段使用分级处理
   - 高Signal内容用k2p5 + high
   - 普通内容用ds + on

### 更新流程

```bash
# 1. 确认路由模块可用
python3 scripts/smart_router.py

# 2. 修改进化脚本，集成路由逻辑
# 编辑 scripts/evolution-*.py

# 3. 测试Cron任务
# 手动运行验证效果
```

---

## 成本优化效果

### 优化前
- 所有Cron任务固定模型
- 不区别Signal价值
- 大量低价值内容占用高成本模型

### 优化后
- 根据Signal动态选择模型
- 高价值（Signal>9）用最强模型
- 高价值（7-8）用kimi完整分析
- 低价值（<7）用ds基础处理

**预计节省**：额外减少30-50%低价值任务的模型成本

---

## 文件清单

### 核心工具
- scripts/smart_router.py - Python智能路由模块
- scripts/smart_router_unified.sh - 统一路由Shell脚本
- scripts/spawn_with_routing.sh - 子代理路由包装器

### 配置规则
- config/unified-difficulty-rules.md - L1-L5分级规则

### 文档
- docs/smart-router-integration.md - 本文档

---

## 版本

v2.1 (2026-02-16) - Cron和子代理集成
