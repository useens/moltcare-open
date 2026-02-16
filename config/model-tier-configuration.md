# 模型梯队与思考模式配置
# Model Tiers & Reasoning Configuration

## 模型梯队分类 (Model Tiers)

### Tier 1: 付费高端模型
**模型：**
- Kimi K2.5 (kimi-coding/k2p5)
- GLM-4 (z-ai/glm4.7)

**默认思考模式：** `off` (按需开启)
**理由：** 成本较高，仅在复杂任务时启用

### Tier 2: 付费中等模型
**模型：**
- Nemotron

**默认思考模式：** `off` (按需开启)
**理由：** 平衡成本与质量

### Tier 3: 免费模型
**模型：**
- GLM-4-7 (nvidia-build/z-ai/glm4.7)
- 其他免费 NVIDIA 构建模型

**默认思考模式：** **`on`** ⚡
**理由：** **成本为 0，最大化利用思考深度**

---

## 思考模式规则

| 模型梯队 | 是否免费 | 默认 thinking | 升级触发条件 |
|----------|----------|---------------|--------------|
| Tier 1付费 | ❌ 否 | `off` | 架构级任务/代码生成/复杂分析 |
| Tier 2付费 | ❌ 否 | `off` | 代码/推理任务 |
| **Tier 3免费** | ✅ **是** | **`on`** | **始终开启** |

---

## 实施规则

### 规则1：免费模型强制思考
```yaml
rules:
  - pattern: "model:tier:free"
    action: "enable_thinking"
    default: "on"
    enforcement: "always"
```

### 规则2：付费模型按需思考
```yaml
rules:
  - pattern: "model:tier:paid"
    action: "adaptive_thinking"
    default: "off"
    upgrade_to: "on"
    conditions:
      - "code_generation"
      - "architecture_task"
      - "complex_analysis"
```

---

## 模型映射

```yaml
model_tier_map:
  # Tier 3 - 免费模型
  "nvidia-build/z-ai/glm4.7":
    tier: 3
    free: true
    default_thinking: "on"

  "nvidia-build/*":  # 所有 nvidia-build 模型
    tier: 3
    free: true
    default_thinking: "on"

  # Tier 1 - 付费高端
  "kimi-coding/k2p5":
    tier: 1
    free: false
    default_thinking: "off"

  "z-ai/glm4.7":
    tier: 1
    free: false
    default_thinking: "off"
```

---

## 使用示例

### 示例1：GLM-4-7 (免费)
```python
model = "nvidia-build/z-ai/glm4.7"
thinking = "on"  # ✅ 自动启用
# 因为 tier=3，free=true
```

### 示例2：Kimi K2.5 (付费)
```python
model = "kimi-coding/k2p5"
thinking = "off"  # ✅ 默认关闭
# 除非任务需要深度思考
```

---

## 配置文件位置
- `/root/.openclaw/workspace/config/model-tier-configuration.md`

## 最后更新
2026-02-16 16:24:28

---

**核心原则：免费 = 无成本 = 最大化思考深度**
