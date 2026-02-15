# 森森智能模式管理系统 v1.0

> 目标：在性能与成本之间动态平衡，实现Token消耗的智能管控

---

## 📊 四模式架构

### 1. 🔥 性能模式 (Performance)

**定位**: 复杂任务、深度学习、关键决策
**成本**: ~500-2000 tokens/分钟
**触发条件**:
- 用户明确指令"全力执行"、"深度分析"
- Signal ≥ 8 的情报处理
- 代码架构设计、竞品分析
- 多步骤推理任务

**配置**:
```yaml
model: kimi-coding/k2p5      # 最强代码模型
thinking: high               # 完整思考过程
context_window: 128k         # 最大上下文
temperature: 0.7             # 适度创造性
max_tokens: 8192             # 长输出支持
parallel_agents: 5           # 多代理并行
```

**适用场景**:
- 竞品深度分析 (TinyClaw级别)
- 架构设计文档编写
- Signal 9-10 情报内化
- 复杂问题诊断

---

### 2. ⚖️ 均衡模式 (Balanced) ⭐ 默认

**定位**: 日常任务、标准响应、信息查询
**成本**: ~100-300 tokens/分钟
**触发条件**:
- 无特殊指令的常规对话
- 文件读取、简单编辑
- 信息汇总、状态查询
- 一般性建议

**配置**:
```yaml
model: kimi-coding/k2p5      # 保持能力
thinking: low                # 简洁思考
context_window: 64k          # 标准上下文
temperature: 0.5             # 平衡创造性
max_tokens: 4096             # 标准输出
parallel_agents: 2           # 有限并行
```

**适用场景**:
- 日常文件操作
- 状态查询汇报
- 简单代码修改
- 标准问答

---

### 3. 🌱 节能模式 (Eco)

**定位**: 简单任务、快速响应、监控执行
**成本**: ~30-80 tokens/分钟
**触发条件**:
- 心跳检查 (HEARTBEAT_OK)
- 简单确认、状态OK回复
- 单一文件读取
- 简单命令执行

**配置**:
```yaml
model: kimi-coding/k2p5      # 同一模型，但限制输出
thinking: off                # 无思考过程
context_window: 32k          # 精简上下文
temperature: 0.3             # 低创造性，高确定性
max_tokens: 1024             # 短输出限制
parallel_agents: 1           # 单任务
response_limit: 3_sentences  # 强制简洁
```

**适用场景**:
- 定时心跳回复
- 简单文件查看
- 状态确认
- 简短通知

---

### 4. ❄️ 冻结模式 (Frozen)

**定位**: 零成本待机、被动等待唤醒
**成本**: ~0 tokens/分钟
**触发条件**:
- 用户明确"进入冻结"
- 长时间无交互 (>2小时)
- 系统维护时段
- 深夜低活跃期 (23:00-08:00)

**配置**:
```yaml
model: none                  # 不调用LLM
processing: minimal          # 仅系统级操作
storage: archive             # 数据归档
wake_triggers:               # 唤醒条件
  - user_message            # 用户主动消息
  - emergency_alert         # 紧急告警
  - scheduled_task          # 定时任务触发
```

**唤醒机制**:
- 用户发送任意消息 → 自动切换至均衡模式
- 紧急告警触发 → 切换至性能模式
- 定时任务 → 按需选择模式

---

## 🔄 智能切换逻辑

### 自动升级条件 (低→高)

| 从 | 到 | 触发条件 |
|----|----|----------|
| 冻结 | 节能 | 用户消息/定时任务 |
| 节能 | 均衡 | 任务复杂度 > 阈值 |
| 均衡 | 性能 | 用户"全力"指令/Signal≥8 |

### 自动降级条件 (高→低)

| 从 | 到 | 触发条件 |
|----|----|----------|
| 性能 | 均衡 | 任务完成 + 5分钟无新任务 |
| 均衡 | 节能 | 心跳周期/简单查询 |
| 节能 | 冻结 | 30分钟无交互 + 夜间时段 |

### 成本阈值保护

```yaml
# 每小时成本上限保护
hourly_budget:
  performance: 10000 tokens  # ~$0.50
  balanced: 3000 tokens      # ~$0.15
  eco: 800 tokens            # ~$0.04
  frozen: 0 tokens

# 触发保护后的行为
cost_protection:
  action: downgrade          # 自动降级
  notify: true               # 通知用户
  reset_after: 1_hour        # 1小时后重置
```

---

## 🎮 用户控制接口

### 手动切换命令

```bash
/performance    # 进入性能模式
/balanced      # 进入均衡模式 (默认)
/eco           # 进入节能模式
/frozen        # 进入冻结模式
/auto          # 恢复自动切换
```

### 任务级模式指定

```bash
"用性能模式分析这个竞品"
"节能模式检查状态"
"在均衡模式下总结文件"
```

### 模式状态查询

```bash
/mode          # 显示当前模式及配置
/cost          # 显示今日Token消耗统计
/budget        # 显示预算使用情况
```

---

## 📈 成本监控仪表盘

### 实时指标

```
┌─────────────────────────────────────────┐
│  今日Token消耗          模式: 均衡 ⚖️    │
├─────────────────────────────────────────┤
│  总计: 12,450 / 50,000 (24.9%)          │
│  性能: 8,200 ████████████░░             │
│  均衡: 3,800 █████░░░░░░░░              │
│  节能:    450 █░░░░░░░░░░░              │
│  冻结:      0 ░░░░░░░░░░░░              │
├─────────────────────────────────────────┤
│  预计今日: 28,000 (预算内)               │
│  建议: 继续保持均衡模式                  │
└─────────────────────────────────────────┘
```

### 每日成本报告

- **早间简报** (08:00): 昨日消耗 + 今日预算建议
- **午间提醒** (12:00): 当前消耗进度
- **晚间汇总** (20:00): 全天统计 + 模式建议

---

## 🧠 智能决策算法

### 任务复杂度评估

```python
def assess_complexity(task):
    score = 0
    
    # 关键词加权
    keywords = {
        "分析": +2, "设计": +3, "架构": +3,
        "对比": +2, "评估": +2, "研究": +3,
        "检查": +1, "查看": +0, "确认": +0,
        "总结": +1, "列出": +0, "执行": +1
    }
    
    # 文件数量
    file_count = len(task.files)
    score += min(file_count * 0.5, 3)
    
    # 历史上下文长度
    context_tokens = task.context_tokens
    if context_tokens > 100000: score += 3
    elif context_tokens > 50000: score += 2
    elif context_tokens > 10000: score += 1
    
    # 返回模式建议
    if score >= 6: return "performance"
    elif score >= 3: return "balanced"
    else: return "eco"
```

### 时间因子调整

```python
def time_adjustment(hour):
    # 夜间降低功耗
    if 23 <= hour or hour < 7:
        return -1  # 降级一档
    
    # 工作高峰保持性能
    if 9 <= hour <= 11 or 14 <= hour <= 17:
        return +1  # 升级一档
    
    return 0  # 无调整
```

---

## 🚀 实施路线图

### Phase 1: 基础框架 (今天)
- [x] 设计四模式架构
- [ ] 实现模式切换命令
- [ ] 创建成本监控脚本
- [ ] 设置默认均衡模式

### Phase 2: 智能切换 (本周)
- [ ] 任务复杂度评估器
- [ ] 自动升级/降级逻辑
- [ ] 成本阈值保护机制
- [ ] 用户习惯学习

### Phase 3: 优化迭代 (本月)
- [ ] 成本预测模型
- [ ] 个性化模式推荐
- [ ] 月度成本报告
- [ ] 高级调度策略

---

## 📁 相关文件

- 配置: `config/mode-management.yaml`
- 状态: `memory/mode-state.json`
- 成本日志: `memory/cost-log.md`
- 切换脚本: `scripts/mode-switcher.py`

---

*版本: v1.0 | 创建: 2026-02-15 | 作者: 森森*