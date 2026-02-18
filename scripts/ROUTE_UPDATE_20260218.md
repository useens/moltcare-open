# 路由系统更新 - 2026-02-18

## 📊 更新背景

基于对 **GLM-4.7** vs **Step-3.5 Flash** 的分析，GLM-4.7 更适合 OpenClaw 的核心场景：

| GLM-4.7 优势 | OpenClaw 需求 |
|-------------|--------------|
| 更稳定的 JSON 工具格式化 | 40+ 工具的精确参数传递 |
| 更强的中文能力 | 中文交互和文档 |
| 更深的推理能力 | 复杂任务、多会话管理 |
| 上下文连贯性 | 长期守护任务（心跳、daemon） |

---

## 🔄 路由规则调整

### 更新前（Step 为主）
```python
"unified-monitor": {"model": "step", "thinking": "off"},
"heartbeat": {"model": "step", "thinking": "off"},
"monitor": {"model": "step", "thinking": "off"},
...
默认模型: step
```

### 更新后（GLM-4.7 为主）
```python
# OpenClaw 核心工具任务
"tool": {"model": "glm", "thinking": "on"},
"exec": {"model": "glm", "thinking": "on"},
"write": {"model": "glm", "thinking": "on"},
"feishu": {"model": "glm", "thinking": "on"},
"bitable": {"model": "glm", "thinking": "on"},

# 需要复杂逻辑的监控
"monitor": {"model": "glm", "thinking": "on"},
"unified-monitor": {"model": "glm", "thinking": "on"},
"daemon": {"model": "glm", "thinking": "on"},

# 简单检查（快速响应）
"heartbeat": {"model": "step", "thinking": "off"},
"status": {"model": "step", "thinking": "off"},
"check": {"model": "step", "thinking": "off"},

默认模型: glm
```

---

## 🎯 新的路由策略

| 模型 | 使用场景 | 特点 |
|------|---------|------|
| **GLM-4.7** ⭐ 主模型 | 工具调用、文件操作、飞书集成、复杂监控、默认任务 | 工具调用稳定、格式化精确、中文优化 |
| **Step-3.5 Flash** ⚡ 快速响应 | 心跳检查、简单状态检查、快照/备份/归档 | 极速响应、无复杂逻辑 |
| **Kimi-K2.5** 📚 大上下文 | 文档扫描、Moltbook、GitHub、HN | 256k 上下文、大文档分析 |
| **K2P5** 💎 最强 | Signal≥9 情报、深度架构 | 付费场景、最强推理 |

---

## 📈 回退链（更新）

**更新前:** `["step", "glm", "kimi", "k2p5"]`

**更新后:** `["glm", "step", "kimi", "k2p5"]`

---

## ✅ 测试结果

| 任务类型 | 路由结果 | ✅ |
|---------|---------|---|
| `unified-monitor` | glm + thinking: on | ✅ |
| `heartbeat` | step + thinking: off | ✅ |
| `feishu-bitable` | glm + thinking: on | ✅ |
| `moltbook-scan` | kimi + thinking: on | ✅ |
| `random-task` | glm + thinking: on | ✅ |
| `scan` (Signal 9) | k2p5 + thinking: stream | ✅ |

---

## 📝 修改的文件

- `scripts/route.py`
  - 模型定义顺序（GLM 排第一）
  - 路由规则（核心任务转向 GLM）
  - 默认模型（step → glm）
  - 回退链（glm → step → kimi → k2p5）

---

## 🚀 使用方式

```bash
# 方式 1：通过 run-with-route.sh
bash scripts/run-with-route.sh <task-type> <actual-command>

# 方式 2：直接获取路由配置
python3 scripts/route.py <task-type> [signal]

# 示例
bash scripts/run-with-route.sh unified-monitor python3 scripts/unified-monitor.py --fix
python3 scripts/route.py moltbook-scan
```

---

*路由更新完成 | 2026-02-18 17:20*
