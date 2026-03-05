# 🤖 Nanobot Command Center - 节点模型配置

## 更新时间
2026-03-05 23:30

## 节点模型分配

### Step 3.5 Flash 组 (快速响应)
| 节点 | 默认模型 | Port | API Key前缀 |
|------|----------|------|-------------|
| NB01 | stepfun-ai/step-3.5-flash | 18801 | KK5wL7... |
| NB02 | stepfun-ai/step-3.5-flash | 18802 | J3b15L... |
| NB03 | stepfun-ai/step-3.5-flash | 18803 | IPtXI8... |
| NB04 | stepfun-ai/step-3.5-flash | 18804 | K7bWEy... |
| NB05 | stepfun-ai/step-3.5-flash | 18805 | NQj1GH... |

### DeepSeek V3.2 组 (深度推理)
| 节点 | 默认模型 | Port | API Key前缀 |
|------|----------|------|-------------|
| NB06 | deepseek-ai/deepseek-v3.2 | 18806 | CvbuEv... |
| NB07 | deepseek-ai/deepseek-v3.2 | 18807 | gWHf6K... |
| NB08 | deepseek-ai/deepseek-v3.2 | 18808 | oyDy6F... |
| NB09 | deepseek-ai/deepseek-v3.2 | 18809 | RBDc9C... |
| NB10 | deepseek-ai/deepseek-v3.2 | 18810 | BzaCTX... |

## 使用说明

### 自动选择模型 (推荐)
```bash
# NB01-NB05 自动使用 Step 3.5 Flash
python3 scripts/nb-relay.py send NB01 "任务内容"

# NB06-NB10 自动使用 DeepSeek V3.2
python3 scripts/nb-relay.py send NB06 "任务内容"
```

### 手动指定模型
```bash
# 指定使用 Step
python3 scripts/nb-relay.py send NB01 "任务内容" step

# 指定使用 DeepSeek
python3 scripts/nb-relay.py send NB06 "任务内容" ds
```

### 广播到所有节点
```bash
# 广播时使用各自的默认模型
python3 scripts/nb-relay.py broadcast "任务内容"

# 广播时强制使用 Step
python3 scripts/nb-relay.py broadcast "任务内容" step

# 广播时强制使用 DeepSeek
python3 scripts/nb-relay.py broadcast "任务内容" ds
```

## 模型特性

| 特性 | Step 3.5 Flash | DeepSeek V3.2 |
|------|------------------|---------------|
| **速度** | ⚡ 最快 (1-3秒) | 🐢 较慢 (3-11秒) |
| **稳定性** | 🟢 高 | 🟡 中 |
| **用途** | 快速响应、简单任务 | 深度推理、复杂任务 |
| **Context** | 131,072 | 131,072 |
| **Max Tokens** | 8192 | 8192 |

## 节点选择建议

- **需要快速响应** → 使用 NB01-NB05 (Step 3.5 Flash)
- **需要深度思考** → 使用 NB06-NB10 (DeepSeek V3.2)
- **负载均衡** → 让系统根据任务类型自动分配

## 配置更新记录

- 2026-03-05: NB01-NB05 默认模型设为 Step 3.5 Flash
- 2026-03-05: NB06-NB10 默认模型设为 DeepSeek V3.2
- 2026-03-05: nb-relay.py 自动模型选择逻辑更新

---

**当前状态**: ✅ 10个节点全部在线，模型配置完成
