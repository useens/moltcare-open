# 智能路由系统 v2.0 (OpenClaw 优化版)
> 设计理念：**GLM-4.7 为主**，工具调用优化，成本可控

---

## 🧠 模型定位

| 模型 | 特性 | 核心优势 | 最佳场景 |
|------|------|----------|----------|
| **GLM-4.7** ⭐ 主模型 | 免费·稳定 | **工具调用精确**、中文强、深度推理 | OpenClaw 核心任务、文件操作、飞书集成 |
| **Step-3.5 Flash** ⚡ 快速响应 | 免费·极速 | 响应最快，成本低 | 心跳检查、简单状态查询 |
| **Kimi-K2.5** 📚 大上下文 | 免费·大容量 | 256k上下文 | 文档扫描、Moltbook、GitHub |
| **K2P5** 💎 最强 | 付费·最强 | 架构级推理 | Signal≥9情报、深度架构 |

---

## 🚀 路由规则

### 核心原则 (v2.0 更新)
1. **默认用 GLM-4.7**（工具调用稳定、格式化精确）
2. **简单检查用 step**（心跳、状态查询）
3. **大文档用 kimi**（256k上下文）
4. **高Signal用 k2p5**（唯一付费场景）

### 快速决策表

```
┌───────────────────────────┬────────┬───────────┬────────────────────────┐
│ 任务类型                   │ 模型   │ Thinking  │ 原因                   │
├───────────────────────────┼────────┼───────────┼────────────────────────┤
│工具调用（exec/write/read） │ glm    │ on        │ JSON 格式化精确         │
│飞书集成（feishu/bitable）  │ glm    │ on        │ API 操作稳定           │
│复杂监控（monitor/daemon）  │ glm    │ on        │ 推理深度需求           │
│───────────────────────────┼────────┼───────────┼────────────────────────┤
│HEARTBEAT / 状态检查        │ step   │ off       │ 快速响应               │
│日常维护（快照/备份/归档）  │ step   │ off       │ 标准化任务，无需思考     │
│───────────────────────────┼────────┼───────────┼────────────────────────┤
│文档分析 / 长文件          │ kimi   │ on        │ 256k大上下文             │
│Moltbook扫描               │ kimi   │ on        │ 处理大量帖子             │
│HN / GitHub Trending分析   │ kimi   │ on        | 批量内容处理            │
│───────────────────────────┼────────┼───────────┼───────────────────────│
│Signal≥9 / 架构级议题      │ k2p5   │ stream    │ 高价值，值得付费         │
│深度学习闭环               │ k2p5   │ stream    │ 架构级改进需要最强模型   │
└───────────────────────────┴────────┴───────────┴────────────────────────┘
```

---

## 🛡️ 回退机制

### 失败回退链 (v2.0 更新)
```
glm → step → kimi → k2p5
```

**逻辑**：
1. 默认使用 GLM-4.7（主模型）
2. GLM 失败 → step（快速响应尝试）
3. step 失败 → kimi（大上下文兜底）
4. kimi 失败 → k2p5（最强模型兜底）

### 超时降级
```
当前模型超时 < 3次 → 保持
当前模型超时 ≥ 3次 → 降级到更便宜的模型
```

---

## 🎯 Cron任务映射

```yaml
production:
  unified-monitor-check:      glm + on      # 需要复杂逻辑判断
  unified-maintenance-daily:  glm + on      # 维护需要稳定性
  stability-snapshot-hourly:  step + off    # 快照不需要思考

intelligence:
  evolution-intelligence:     kimi + on     # Moltbook/HN扫描
  moltbook-unified-scan:      kimi + on     # 文档处理

deep_learning:
  evolution-deep-learning:    k2p5 + stream # Signal≥9，深度处理
  evolution-knowledge:        glm + on      # 知识整合（GLM 足够）

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
        "monitor":   {"model": "glm", "thinking": "on"},
        "tool":      {"model": "glm", "thinking": "on"},
        "feishu":    {"model": "glm", "thinking": "on"},
        "document":  {"model": "kimi", "thinking": "on"},
        "scan":      {"model": "kimi", "thinking": "on"},
        "deep":      {"model": "k2p5", "thinking": "stream"},
        "code":      {"model": "glm", "thinking": "on"},  # GLM 足够
    }
    return mapping.get(task_type, {"model": "glm", "thinking": "on"})
```

### 方式2: 基于内容检测

```python
def route_by_content(content: str, signal: int = None) -> dict:
    """基于内容和Signal路由"""
    # Signal≥9 → k2p5
    if signal and signal >= 9:
        return {"model": "k2p5", "thinking": "stream"}

    # 检测工具调用特征（JSON、exec、feishu 等）
    if detect_tool_call(content):
        return {"model": "glm", "thinking": "on"}

    # 检测大文档特征
    if is_large_document(content):
        return {"model": "kimi", "thinking": "on"}

    # 默认使用 GLM-4.7
    return {"model": "glm", "thinking": "on"}
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
- **GLM-4.7 为主**: 核心任务稳定高效，免费使用
- **简单任务用 step**: 心跳/归档等快速响应
- **仅Signal≥9用k2p5**: 成本控制在关键内容
- **预期节省**: ~70% API成本（相比全部用GLM仍然节省）

### 统计追踪
建议在 MEMORY.md 中记录：
- 各模型使用频次
- 成本对比
- 回退触发情况

---

*智能路由 v2.0 | OpenClaw 优化 | 2026-02-18*
