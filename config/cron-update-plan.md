# Cron任务模型优化更新方案
## 更新时间：2026-02-16

### 优化目标
| 当前状态 | 优化后 |
|---------|-------|
| 全部使用k2p5（全付费） | 免费ds/kimi为主，仅高Signal用k2p5 |
| 预计成本降低 | 60-70% |

### 具体更新计划

#### 1. evolution-intelligence（夜间进化#1）
**当前配置**：
- model: kimi-coding/k2p5
- thinking: medium

**更新为**：
- model: nvidia-build/moonshotai/kimi-k2.5
- thinking: on
- fallback: Signal>9 → k2p5

**原因**：情报收集主要是数据扫描，kimi的256k上下文更适合处理大量Moltbook/HN数据

#### 2. moltbook-unified-scan
**当前配置**：
- model: kimi-coding/k2p5
- thinking: medium

**更新为**：
- model: nvidia-build/moonshotai/kimi-k2.5
- thinking: on
- fallback: Signal>8或代码相关 → k2p5

**原因**：文档分析任务，免费kimi足够

#### 3. evolution-knowledge（夜间进化#2）
**当前配置**：
- model: kimi-coding/k2p5
- thinking: medium

**更新为**：
- model: nvidia-build/deepseek-ai/deepseek-v3.2
- thinking: on
- fallback: 架构设计 → k2p5

**原因**：知识内化和交叉关联需要强推理能力，ds免费且推理强

#### 4. unified-monitor-check（保持优化）
**当前配置**：
- model: kimi-coding/k2p5
- thinking: off

**更新为**：
- model: nvidia-build/deepseek-ai/deepseek-v3.2
- thinking: off

**原因**：监控任务简单快速，用免费ds即可

#### 5. unified-maintenance-daily（保持优化）
**当前配置**：
- model: kimi-coding/k2p5
- thinking: off

**更新为**：
- model: nvidia-build/deepseek-ai/deepseek-v3.2
- thinking: off

**原因**：日常维护脚本，无需复杂推理

#### 6. evolution-deep-learning（保持付费）
**当前配置**：
- model: kimi-coding/k2p5
- thinking: high

**更新为**：
- model: kimi-coding/k2p5
- thinking: high
- condition: Signal 9-10 才触发
- else: 降级到ds免费模型

**原因**：Signal 9-10架构级内容，需要最强模型，但低Signal可用ds

### 执行命令示例

```bash
# 更新evolution-intelligence
cron update evolution-intelligence --model=nvidia-build/moonshotai/kimi-k2.5 --thinking=on

# 更新moltbook-unified-scan
cron update moltbook-unified-scan --model=nvidia-build/moonshotai/kimi-k2.5 --thinking=on

# 更新evolution-knowledge
cron update evolution-knowledge --model=nvidia-build/deepseek-ai/deepseek-v3.2 --thinking=on

# 更新unified-monitor-check
cron update unified-monitor-check --model=nvidia-build/deepseek-ai/deepseek-v3.2 --thinking=off

# 更新unified-maintenance-daily
cron update unified-maintenance-daily --model=nvidia-build/deepseek-ai/deepseek-v3.2 --thinking=off
```

### 成本对比

| 任务 | 当前(每天) | 优化后(每天) | 节省 |
|------|-----------|-------------|------|
| evolution-intelligence | k2p5 | kimi free | 100% |
| evolution-knowledge | k2p5 | ds free | 100% |
| moltbook-scan (4次/天) | 4×k2p5 | 4×kimi free | 100% |
| unified-monitor (48次/天) | 48×k2p5 | 48×ds free | 100% |
| deep-learning (1次/天) | k2p5 | Signal>9才k2p5 | ~70% |
| **日总计** | **~55次k2p5** | **~5次k2p5** | **~90%** |

**月节省预估**：从 ~1500元 降至 ~150元
