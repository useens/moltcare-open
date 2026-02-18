# 智能路由系统 v1.0 (简洁版)
> 设计理念：规则最少，成本优先，智能回退

---

## 🧠 模型定位

| 模型 | 特性 | 核心优势 | 最佳场景 |
|------|------|----------|----------|
| **step** | 免费·极速 | 响应最快，成本低 | 简单检查、快速响应 |
| **glm** | 免费·中文 | 中文优化 | 中文对话、中文任务 |
| **kimi** | 免费·大容量 | 256k上下文 | 文档分析、长内容 |
| **k2p5** | 付费·最强 | 能力最强 | Signal≥9架构级议题 |

---

## 🚀 路由规则

### 核心原则
1. **默认用 step**（免费且最快）
2. **中文用 glm**（中文优化）
3. **大文档用 kimi**（256k上下文）
4. **高Signal用 k2p5**（唯一付费场景）

### 快速决策表

```
┌───────────────────────────┬────────┬───────────┬────────────────────────┐
│ 任务类型                   │ 模型   │ Thinking  │ 原因                   │
├───────────────────────────┼────────┼───────────┼────────────────────────┤
│ HEARTBEAT / 统一监控       │ step   │ off       │ 简单检查，快速完成       │
│ 日常维护 / 备份            │ step   │ off       │ 标准化任务，无需思考     │
│ 系统检查 / 状态查询        │ step   │ off       │ 快速响应               │
│───────────────────────────┼────────┼───────────┼────────────────────────┤
│ 中文对话 / 中文任务        │ glm    │ on        │ 中文优化，更流畅         │
│ 翻译 / 中文写作            │ glm    │ on        │ 中文场景                │
│───────────────────────────┼────────┼───────────┼────────────────────────┤
│ 文档分析 / 长文件          │ kimi   │ on        │ 256k大上下文             │
│ Moltbook扫描               │ kimi   │ on        │ 处理大量帖子             │
│ HN / GitHub Trending分析   │ kimi   │ on        | 批量内容处理            │
│───────────────────────────┼────────┼───────────┼───────────────────────│
│ Signal≥9 / 架构级议题      │ k2p5   │ stream    │ 高价值，值得付费         │
│ 深度学习闭环               │ k2p5   │ stream    │ 架构级改进需要最强模型   │
│ 复杂代码生成               │ k2p5   │ on        │ 代码准确度优先         │
└───────────────────────────┴────────┴───────────┴────────────────────────┘
```

---

## 🛡️ 回退机制

### 失败回退链
```
step → glm → kimi → k2p5
```

**逻辑**：
1. 默认使用 step（最快）
2. step 失败 → glm（尝试中文模型）
3. glm 失败 → kimi（大上下文尝试）
4. kimi 失败 → k2p5（用最强兜底）

### 超时降级
```
当前模型超时 < 3次 → 保持
当前模型超时 ≥ 3次 → 降级到更便宜的模型
```

---

## 🎯 Cron任务映射

```yaml
production:
  unified-monitor-check:      step + off    # 每15分钟，快速检查
  unified-maintenance-daily:  step + off    # 每天，标准化任务
  stability-snapshot-hourly:  step + off    # 每小时，快照创建

intelligence:
  evolution-intelligence:     kimi + on     # Moltbook/HN扫描
  moltbook-unified-scan:      kimi + on     # 文档处理

deep_learning:
  evolution-deep-learning:    k2p5 + stream # Signal≥9，深度处理
  evolution-knowledge:        kimi + on     # 知识整合

misc:
  auto-password-guard:        step + off    # 简单检查
  credentials-backup:         step + off    # 备份任务
  monthly-archive:            step + off    # 归档
  monthly-deep-cleanup:       glm + on      # 清理需要一定推理
```

---

## 📝 使用方式

### 方式1: 简单规则（推荐）

任务类型直接查表：

```python
def route_task(task_type: str) -> dict:
    """基于任务类型路由"""
    mapping = {
        "heartbeat": {"model": "step", "thinking": "off"},
        "monitor":   {"model": "step", "thinking": "off"},
        "chinese":   {"model": "glm", "thinking": "on"},
        "document":  {"model": "kimi", "thinking": "on"},
        "scan":      {"model": "kimi", "thinking": "on"},
        "deep":      {"model": "k2p5", "thinking": "stream"},
        "code":      {"model": "k2p5", "thinking": "on"},
    }
    return mapping.get(task_type, {"model": "step", "thinking": "off"})
```

### 方式2: 基于内容检测

```python
def route_by_content(content: str, signal: int = None) -> dict:
    """基于内容和Signal路由"""
    # Signal≥9 → k2p5
    if signal and signal >= 9:
        return {"model": "k2p5", "thinking": "stream"}

    # 检测中文内容
    if detect_chinese(content):
        return {"model": "glm", "thinking": "on"}

    # 检测大文档特征
    if is_large_document(content):
        return {"model": "kimi", "thinking": "on"}

    # 默认使用 step
    return {"model": "step", "thinking": "off"}
```

---

## 🔄 集成到脚本

### 在 Cron 脚本中

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/.openclaw/workspace/scripts')

# 简单路由映射
TASK_ROUTE = {
    "unified-monitor": {"model": "step", "thinking": "off"},
    "moltbook-scan":   {"model": "kimi", "thinking": "on"},
    "deep-learning":   {"model": "k2p5", "thinking": "stream"},
}

def get_route_for_task(task_name: str) -> dict:
    """获取任务对应的路由配置"""
    return TASK_ROUTE.get(task_name, {"model": "step", "thinking": "off"})

# 使用示例
if __name__ == "__main__":
    task = sys.argv[1]  # 从命令行获取任务名称
    route = get_route_for_task(task)
    print(f"任务: {task}")
    print(f"路由: {route['model']} + {route['thinking']}")
```

---

## 📊 成本优化

### 预计节省
- **默认用 step**: 90%任务用免费快速模型
- **仅Signal≥9用k2p5**: 成本控制在关键内容
- **预期节省**: ~85% API成本

### 统计追踪
建议在 MEMORY.md 中记录：
- 各模型使用频次
- 成本对比
- 回退触发情况

---

*智能路由 v1.0 | 简洁优先 | 2026-02-18*
