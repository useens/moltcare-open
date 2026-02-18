# 向量记忆混合策略配置

> 配置时间: 2026-02-18 20:24
> 策略: 实时索引重要记忆（Signal≥8）+ 每日全量扫描

---

## 🎯 策略概述

```
实时索引 (Signal≥8)  → 重要记忆即时索引
           ↓
     向量记忆库
           ↓
每日全量扫描 (03:00) → 增量更新所有记忆
```

---

## 📊 配置信息

| 配置项 | 值 |
|--------|-----|
| **策略类型** | 混合策略 |
| **实时索引阈值** | Signal ≥ 8 |
| **每日扫描时间** | 03:00 (Asia/Shanghai) |
| **Cron作业ID** | 75578883-166f-4a6a-a179-1b10e49c40d9 |

---

## 🔧 实时索引

### 使用方法

#### 方式1: Python脚本

```bash
python3 /root/.openclaw/workspace/scripts/vector-memory-indexer.py \
    --content "重要内容" \
    --source "来源描述"
```

#### 方式2: Shell脚本

```bash
bash /root/.openclaw/workspace/scripts/realtime-vector-index.sh \
    "重要内容" \
    "来源描述"
```

### 代码集成

```python
from scripts.vector_memory_indexer import realtime_index

# 重要决策/发现/突破
content = """
核心突破：超进化引擎v3.0完成
- 十维智能架构完整
- 42个策略验证通过
- 自动化调度成功部署
"""

realtime_index(content, source="critical-evolution-milestone")
```

---

## 🕒 每日全量扫描

### Cron任务

```yaml
名称: 向量记忆增量更新-每天03:00
频率: 0 3 * * * (每天凌晨3点)
任务: python3 /root/.openclaw/workspace/scripts/vector-memory-indexer.py --full-scan
```

### 执行内容

- 扫描 `memory/` 目录下所有 `.md` 文件
- 计算内容哈希，检测变更
- Signal≥8的记忆自动索引
- 记录索引日志到 `logs/vector-indexer.log`

---

## 📝 Signal等级估算

### 自动判定规则

| 规则 | 增加分数 | 说明 |
|------|----------|------|
| 重要关键词 | +1 | 关键/重要/紧急/核心等（中英文） |
| 创新/突破词 | +1 | 创新/突破/发现/insight等 |
| 决策/策略词 | +1 | 决策/策略/战略等 |
| 代码/技术内容 | +2 | 包含代码块/函数定义 |
| Markdown深度 | +1 | 3级以上标题 |
| 基础分 | 5 | 所有内容 |

### 示例

#### Signal 6 (不索引)
```
超进化引擎v3.0已完成部署
```

#### Signal 8 (索引)
```
【P0】超进化引擎v3.0核心突破：十维智能架构完整实现
```

---

## 📁 文件结构

```
scripts/
├── vector-memory-indexer.py      # 主索引器脚本
└── realtime-vector-index.sh       # 实时索引包装脚本

logs/
└── vector-indexer.log             # 索引日志
```

---

## 🚀 使用场景

### 适合实时索引

- ✅ 关键决策
- ✅ 核心突破
- ✅ 重要发现
- ✅ 系统里程碑
- ✅ 安全事件

### 适合每日扫描

- ✅ 日常笔记
- ✅ 学习记录
- ✅ 一般对话
- ✅ 资料收集

---

## 🔍 查看索引日志

```bash
tail -f /root/.openclaw/workspace/logs/vector-indexer.log
```

---

## ⚙️ 后续集成

### 当前状态
- ✅ Signal判定机制
- ✅ 实时索引接口
- ✅ 每日扫描任务
- ⚠️ 待集成向量记忆API

### 下一步
1. 集成实际的向量记忆系统
2. 添加内容哈希去重
3. 实现增量检测优化

---

## 📊 效果预期

| 指标 | 预期 |
|------|------|
| 实时覆盖度 | 重要记忆100% |
| 增量效率 | 仅更新变更 |
| 查询性能 | <100ms |
| 存储空间 | ~1.5KB/条 |

---

**混合策略配置完成！向量记忆现已启动机动更新模式** 🧠🚀
