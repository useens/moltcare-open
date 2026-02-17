# 智能路由系统 v3.0 - 成本优先路由

**更新日期**: 2026-02-17  
**核心变更**: 删除三层架构，采用成本优先路由

---

## 核心原则

1. **只有 `kimi-coding/k2p5` 是付费的，其他都是免费**
2. **优先使用免费且稳定的模型** (step3.5flash, deepseekv3.2, glm4.7)
3. **高Signal内容 (≥9) 才使用付费 k2p5**
4. **避免使用排队慢的模型** (qwen3.5, kimi2.5, glm5)

---

## 模型梯队

| 梯队 | 模型 | 成本 | 稳定性 | 使用场景 |
|------|------|------|--------|----------|
| ⚡ 免费+稳定 | step3.5flash | 免费 | 高 | 快速响应、默认首选 |
| ⚡ 免费+稳定 | deepseekv3.2 | 免费 | 高 | 代码任务、技术任务 |
| ⚡ 免费+稳定 | glm4.7 | 免费 | 高 | 中文任务、通用对话 |
| ⏳ 免费+排队 | qwen3.5 | 免费 | 低 | **避免使用** |
| ⏳ 免费+排队 | kimi2.5 | 免费 | 低 | **避免使用** |
| ⏳ 免费+排队 | glm5 | 免费 | 低 | **避免使用** |
| 💎 付费 | k2p5 | 付费 | 高 | **仅 Signal≥9** |

---

## 路由策略

### 基于 Signal 评分 (主要方式)

```python
Signal 1-6:  step/ds/glm + off/concise    → 免费
Signal 7-8:  ds/glm + on                  → 免费
Signal 9-10: k2p5 + stream                → 付费 (唯一场景)
```

### 基于任务描述 (快速分类)

| 任务类型 | 路由 | 原因 |
|----------|------|------|
| 极简任务 (你好/状态) | step + off | 最快响应 |
| 代码任务 | ds + on | 代码能力强 |
| 中文任务 | glm + on | 中文优化 |
| 其他 | step + concise | 默认快速 |

---

## 使用方式

### 1. 基于 Signal 路由 (推荐)

```python
from scripts.smart_router import route_by_signal

# Moltbook扫描
for post in posts:
    signal = calculate_signal(post)
    routing = route_by_signal(signal)
    
    # 只有 Signal>=9 才会用付费k2p5
    print(f"{post['title']}: {routing['model']} ({routing['cost']})")
```

### 2. 基于任务描述

```python
from scripts.smart_router import smart_route

routing = smart_route("帮我写个Python脚本")
print(routing['model'])  # ds
print(routing['thinking'])  # on
```

### 3. 成本估算

```python
from scripts.smart_router import estimate_cost

# 模拟Signal分布
distribution = {
    3: 50,   # 50个低Signal
    5: 30,   # 30个中低
    7: 15,   # 15个中高
    9: 5,    # 5个高Signal (付费)
}

cost = estimate_cost(distribution)
# 输出: 95%任务免费，仅5%付费
```

---

## 成本优化效果

### 与原三层架构对比

| 指标 | 原三层架构 | 新成本优先路由 |
|------|-----------|---------------|
| 免费任务比例 | ~70% | **~95%** |
| 付费触发条件 | 任务类型匹配 | **Signal≥9** |
| 排队风险 | 高 (qwen/kimi25) | **低 (避开慢模型)** |
| 平均响应速度 | 中等 | **快 (优先step)** |

### 预估节省

假设每日处理:
- 100个任务
- 其中5个 Signal≥9 (5%)

**成本对比**:
- 原方案: 可能 20-30% 任务触发付费模型
- 新方案: 仅 5% 任务付费 (Signal≥9)

**节省**: 约 **60-70%** 模型成本

---

## 删除的内容

- ❌ `config/model-routing.yaml` (三层架构配置)
- ❌ 基于任务类型的复杂正则匹配
- ❌ 排队慢模型的常规使用

## 保留的内容

- ✅ `scripts/smart_router.py` (核心路由逻辑)
- ✅ Signal评分机制
- ✅ 模型别名系统

---

## 配置文件变更

```bash
# 原配置文件已备份
config/model-routing.yaml -> config/model-routing.yaml.bak.20260217_xxxxxx

# 当前唯一路由配置
scripts/smart_router.py
```

---

## 迁移指南

### 对于 Cron 任务

**之前**:
```python
# 可能使用qwen或kimi25
model = "nvidia-build/qwen/qwen3.5-397b-a17b"
```

**之后**:
```python
from smart_router import route_by_signal

routing = route_by_signal(signal_score)
model = routing['full_model']  # 自动选择免费稳定模型
```

### 对于子代理 Spawn

**之前**:
```bash
./spawn_with_routing.sh "任务"
# 可能路由到排队模型
```

**之后**:
```python
from smart_router import smart_route

routing = smart_route("任务")
# 确保使用 step/ds/glm (免费稳定)
```

---

## 验证命令

```bash
# 测试路由系统
python3 scripts/smart_router.py

# 验证模型选择
python3 -c "
from scripts.smart_router import route_by_signal
for s in [3, 7, 9]:
    r = route_by_signal(s)
    print(f'Signal {s}: {r[\"model\"]} - {r[\"cost\"]}')
"
```

---

*文档版本: v3.0*  
*更新者: 森森*  
*原则: 成本优先，稳定优先，避免排队*
