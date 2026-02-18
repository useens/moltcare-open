# 智能路由使用指南
> v1.0 | 2026-02-18 | 极简、高效、成本优先

---

## 🚀 快速开始

### 方式1: 在脚本中导入

```python
from scripts.route import route

# 获取路由配置
routing = route("unified-monitor")
print(routing)
# {
#     'model': 'step',
#     'full_model': 'nvidia-build/stepfun-ai/step-3.5-flash',
#     'thinking': 'off',
#     'reason': '任务类型: unified-monitor'
# }

# 基于Signal路由
routing = route("deep", signal=9)
# 自动使用 k2p5
```

### 方式2: 命令行使用

```bash
# 查询路由
python3 scripts/route.py <task_type> [signal]

# 输出示例
python3 scripts/route.py unified-monitor
python3 scripts/route.py moltbook-scan
python3 scripts/route.py deep-learning 9
python3 scripts/route.py chinese-task
```

### 方式3: Cron任务包装器

```bash
# 使用智能路由运行脚本
python3 scripts/run_with_route.sh <task_type> <command>

# 示例
python3 scripts/run_with_route.sh unified-monitor \
    python3 scripts/unified-monitor.py --fix

python3 scripts/run_with_route.sh moltbook-scan \
    python3 scripts/moltbook-unified-scan.py
```

### 方式4: Spawn子代理

```python
from scripts.run_with_route import spawn_with_route

# 使用智能路由spawn子代理
spawn_with_route(
    task="扫描Moltbook高Signal内容",
    task_type="moltbook-scan",
    agent="main"
)
```

---

## 📋 任务类型参考

| 任务类型 | 模型 | Thinking | 使用场景 |
|---------|------|----------|---------|
| `unified-monitor` / `heartbeat` | step | off | 监控检查、状态查询 |
| `maintenance` | step | off | 日常维护、备份 |
| `moltbook` / `scan` | kimi | on | Moltbook扫描、文档分析 |
| `hn` / `github` | kimi | on | HN、GitHub Trending分析 |
| `chinese` / `translate` | glm | on | 中文任务、翻译 |
| `deep` | k2p5 | stream | 深度学习、架构分析 |
| `code` | k2p5 | on | 复杂代码生成 |

---

## 🎯 Cron任务配置

智能路由已集成到以下Cron任务：

| 任务名 | 频率 | 模型 | 说明 |
|-------|------|------|------|
| 统一监控检查 | 每15分钟 | step | 快速健康检查 |
| Moltbook情报扫描 | 每4小时 | kimi | 文档分析 |
| 每日维护 | 每天02:00 | step | 标准化维护 |
| 夜间深度进化 | 每天00:00 | k2p5 | 高Signal深度处理 |

---

## 🛡️ 回退机制

### 自动回退链
```
step → glm → kimi → k2p5
```

Python代码：
```python
from scripts.route import fallback_on_failure

# 当前模型失败3次，获取下一个
next_route = fallback_on_failure("step", attempts=3)
# {'model': 'glm', 'full_model': '...', 'thinking': 'off', ...}
```

### 手动检查当前模型
```bash
python3 scripts/run_with_route.py current
# 输出：
# 当前模型: step
# 完整路径: nvidia-build/stepfun-ai/step-3.5-flash
# Thinking: off
# 来源: default
```

---

## 💰 成本优化

### 预计成本分配

| 模型 | 使用场景 | 预期占比 |
|------|---------|---------|
| **step** | 90%（监控、维护） | 免费 |
| **glm** | 5%（中文任务） | 免费 |
| **kimi** | 3%（文档扫描） | 免费 |
| **k2p5** | 2%（Signal≥9） | 付费 |

**预期节省：~85%** （对比全部使用k2p5）

---

## 📊 监控与统计

建议在 MEMORY.md 中记录：

```markdown
## 📊 智能路由统计

| 日期 | step | glm | kimi | k2p5 | 总成本 |
|------|------|------|------|------|-------|
| 2026-02-18 | 45 | 3 | 2 | 0 | $0.00 |
```

---

## 🔧 高级用法

### 自定义任务映射

```python
from scripts.route import ROUTE_RULES, MODELS

# 添加新规则
ROUTE_RULES["my-custom-task"] = {
    "model": "glm",
    "thinking": "on"
}

# 使用
routing = route("my-custom-task")
```

### 批量路由

```python
tasks = [
    ("unified-monitor", None),
    ("moltbook-scan", 7),
    ("deep-learn", 9),
]

for task_type, signal in tasks:
    routing = route(task_type, signal)
    print(f"{task_type}: {routing['model']}")
```

---

## 📚 相关文件

| 文件 | 用途 |
|------|------|
| `smart-router.md` | 完整设计文档 |
| `scripts/route.py` | 核心路由模块 |
| `scripts/run_with_route.py` | Python包装器 |
| `scripts/run-with-route.sh` | Shell包装器 |

---

*智能路由 v1.0 | 简洁优先 | 成本优化*
