# MEMORY.md - 长期记忆

> 🧠 **高信号核心记忆**

---

## 用户档案

| 项目 | 内容 |
|------|------|
| **称呼** | {{USER_NAME}} |
| **角色** | {{USER_ROLE}} |
| **技术水平** | {{TECH_LEVEL}} |

## 核心偏好

- 详细程度: {{DETAIL_LEVEL}}
- 语气: {{TONE}}
- 决策: {{DECISION_STYLE}}

---

## 高信号记忆 (Signal 8-10)

| 类型 | 内容 |
|------|------|
| **必须记住** | Moltbook Token 监控系统 (Signal 10, 永久运行) |
| **绝对禁止** | 停止 MOLT 监控系统 |
| **核心习惯** | 每5分钟检查链上数据 |

### 🚨 永久系统 - Moltbook Token 监控 (Signal 10 - 永久记住)

**触发词**: "Molt 价格" / "Molt 监控" / "鲸鱼" / "链上数据"

**系统状态**: ✅ **永久运行，不可停止** - 2026-03-15 已确认

**包含四个子系统**:
1. **价格监控** - 价格、市值、交易量
2. **链上监控** - 鲸鱼、转账、持有者变化  
3. **OpenClaw Cron 自动推送** - 重大情况自动推送到 kimi-claw
4. **MCP服务** - AI工具接口

**Cron 配置** (OpenClaw 内置):
```json
{
  "jobs": [
    {
      "id": "moltbook-critical-monitor-001",
      "name": "Moltbook 重大情况监控",
      "schedule": { "kind": "every", "everyMs": 300000 },
      "delivery": { "mode": "ifOutput", "channel": "kimi-claw" }
    },
    {
      "id": "moltbook-onchain-logger-002", 
      "name": "Moltbook 链上数据记录",
      "schedule": { "kind": "every", "everyMs": 300000 }
    }
  ]
}
```

**自动触发动作**:
- 用户询问价格 → 自动调用 `moltbook-monitor.js status`
- 用户询问鲸鱼 → 自动调用 `moltbook-onchain.js analyze`
- 用户询问链上数据 → 自动调用 MCP tools
- 重大情况检测 → 自动推送到 kimi-claw (每5分钟)

**文件速查**:
```bash
# 价格监控
~/.openclaw/workspace/scripts/moltbook-monitor.js

# 链上分析  
~/.openclaw/workspace/scripts/moltbook-onchain.js

# 持续监控
~/.openclaw/workspace/scripts/moltbook-onchain-monitor.js

# MCP服务
~/.openclaw/workspace/mcp-moltbook/index.js
```

---

## 活跃项目

| 项目名称 | 状态 | 最后更新 |
|----------|------|----------|
| Moltbook (MOLT) Token Monitor | ✅ 运行中 | 2026-03-15 |
| Moltbook Social Agent | ⏸️ 等待API | 2026-03-14 |
| OpenClaw Skill System | ✅ 63个技能 | 2026-03-15 |

---

## 🔴 高优先级系统 - Moltbook Token Monitor

**重要性**: Signal 10 (永久监控)

### 监控目标
| 项目 | 详情 |
|------|------|
| **代币** | Moltbook (MOLT) |
| **链** | Base (Coinbase L2) |
| **合约** | `0xB695559b26BB2c9703ef1935c37AeaE9526bab07` |
| **当前价格** | ~$0.00003964 |
| **持有者** | ~39,785 |
| **市值** | ~$395万 |

### 文件位置
```
~/.openclaw/workspace/
├── moltbook-config.json          # 警报配置
├── moltbook-monitor.json         # 历史数据
├── moltbook-alerts.log           # 警报记录
└── scripts/
    ├── moltbook-monitor.js       # 主监控工具
    ├── moltbook-check.js         # 后台检查器
    └── moltbook-monitor.sh       # Bash版本
```

### 使用命令
```bash
# 查看当前状态
node scripts/moltbook-monitor.js status

# 实时监控（每60秒刷新）
node scripts/moltbook-monitor.js monitor

# 查看历史
node scripts/moltbook-monitor.js history 50

# 后台检查（用于cron）
node scripts/moltbook-check.js
```

### 警报阈值
- 🚀 价格 **≥ $0.00005** (上涨26%触发)
- 📉 价格 **≤ $0.00003** (下跌24%触发)
- 📊 交易量变化 **>50%**
- 👥 持有者变化 **>100人**

### 自动化状态
- ✅ 每5分钟自动检查（已配置cron）
- ✅ 数据持久化存储
- ✅ 警报日志记录

---

### 重大情况报告（新增）

**重大情况定义** - 只有以下情况会主动报告：

| 类型 | 阈值 | 说明 |
|------|------|------|
| 🆕 新鲸鱼 | ≥ 1亿 MOLT | 新地址进入大户行列 |
| 📈 鲸鱼增持 | ≥ 5000万 MOLT | 大户加仓 |
| 📉 鲸鱼减持 | ≥ 5000万 MOLT | 大户出货 |
| 🔴 大户清仓 | 卖出 > 80% | Top 10 大户几乎清仓 |
| 💸 大额转账 | ≥ 1亿 MOLT | 异常大额转账 |
| 🏃 交易所流出 | ≥ 2亿 MOLT | 从交易所钱包转出 |
| 📥 交易所流入 | ≥ 3亿 MOLT | 转入交易所钱包 |
| 📊 交易量激增 | ≥ 3倍 | 24h交易量暴涨 |
| 💥 价格暴跌 | ≥ 15% | 短时间内大幅下跌 |
| 🚀 价格暴涨 | ≥ 25% | 短时间内大幅上涨 |
| 👥 持有者骤变 | ≥ 200人 | 持有者数量剧烈变化 |
| ⚠️ 集中度变化 | ≥ 2% | Top10占比变化 |
| 🤖 合约异常活跃 | 10+笔/周期 | 智能合约高频交易 |
| 🌊 流动性撤出 | ≥ 5000万 MOLT | 从流动性池撤出 |

**文件**:
```bash
# 重大情况检查
~/.openclaw/workspace/scripts/moltbook-critical-check.js

# 重大情况日志
~/.openclaw/workspace/moltbook-critical-alerts.log
```

**运行方式**: 每5分钟检查，只有重大情况才会显示

---

## 🐋 链上数据深挖监控系统

**状态**: ✅ 持续监控运行中  
**重要等级**: Signal 10  
**位置**: `~/.openclaw/workspace/scripts/moltbook-onchain-monitor.js`

### 监控内容

| 监控项 | 描述 | 阈值 |
|--------|------|------|
| 🆕 新鲸鱼 | 新地址持仓超1亿 MOLT | 100M MOLT |
| 📈📉 鲸鱼动向 | 鲸鱼增持/减持超1000万 MOLT | 10M MOLT |
| 💸 大额转账 | 单笔转账超5000万 MOLT | 50M MOLT |
| 👥 持有者变化 | 持有者数量变化超50人 | 50人 |
| ⚠️ 集中度变化 | Top10占比变化超0.5% | 0.5% |

### 文件位置
```
~/.openclaw/workspace/
├── moltbook-onchain-data.json      # 历史数据
├── moltbook-onchain-alerts.log     # 警报日志
├── moltbook-onchain-config.json    # 配置
├── moltbook-onchain-cron.log       # 定时任务日志
└── scripts/
    ├── moltbook-onchain.js         # 分析工具
    └── moltbook-onchain-monitor.js # 持续监控
```

### 使用命令
```bash
# 执行一次监控
node scripts/moltbook-onchain-monitor.js once

# 持续监控模式
node scripts/moltbook-onchain-monitor.js daemon

# 查看最近警报
node scripts/moltbook-onchain-monitor.js alerts

# 查看趋势
node scripts/moltbook-onchain-monitor.js trend
```

### 自动化
- ✅ 每5分钟自动检查（已配置cron）
- ✅ 检测到变化自动记录警报
- ✅ 保存历史数据用于趋势分析

### 修复记录
- **2026-03-15 18:26** - 修复 `previousHolders.map is not a function` 错误
  - 原因：数据格式异常时 `previousHolders` 不是数组
  - 方案：所有检测函数添加 `Array.isArray()` 前置检查
  - 状态：✅ 已修复，运行正常

### 数据源准确性验证 (2026-03-15 18:38)
**结论**：监控脚本数据源配置合理，主要指标准确

| 指标 | 主数据源 | 可信度 | 备注 |
|------|----------|--------|------|
| 价格 | CoinGecko | ⭐⭐⭐⭐⭐ | 加权聚合多交易所 |
| 市值 | CoinGecko | ⭐⭐⭐⭐⭐ | 基于价格和流通量 |
| 24h交易量 | CoinGecko | ⭐⭐⭐⭐⭐ | 聚合全部链上交易 |
| 持有者 | Blockscout | ⭐⭐⭐⭐⭐ | 直接链上统计 |
| 供应量 | Blockscout | ⭐⭐⭐⭐⭐ | 合约查询 |
| 流动性 | DEXScreener | ⭐⭐⭐⭐⭐ | 实时池子数据 |

**价格差异说明**：
- CoinGecko: $0.00004242 (准)
- Blockscout: $0.00004042 (-5%，偏低，只覆盖部分池子)
- DEXScreener: $0.0000422-0.0000428 (各池略有差异)

**配置**：价格/市值/交易量以 CoinGecko 为主，持有者/供应量以 Blockscout 为主

---

## 🔌 MCP 服务 - Moltbook Token

**状态**: ✅ 已部署  
**位置**: `~/.openclaw/workspace/mcp-moltbook/`

### Available Tools

| Tool | 功能 |
|------|------|
| `get_price` | 获取当前价格、市值、交易量 |
| `get_holders` | 获取持有者统计 |
| `get_whale_list` | 获取鲸鱼持仓列表 |
| `get_transfers` | 获取转账记录 |
| `analyze_onchain` | 综合分析（集中度、流动性池等）|

### 配置方法
```json
{
  "mcpServers": {
    "moltbook": {
      "command": "node",
      "args": ["~/.openclaw/workspace/mcp-moltbook/index.js"]
    }
  }
}
```

### 启动命令
```bash
cd ~/.openclaw/workspace/mcp-moltbook
npm start
```

---


---

## 自动化规则 (v3.1 更新)

### 三层触发架构

| 层级 | 触发方式 | Signal | 优先级 | 示例 |
|------|----------|--------|--------|------|
| **Layer 1** | 精确触发词 | +2 | 🔴 最高 | "这很重要"、"记住这个" |
| **Layer 2** | 语义理解 | +1 | 🟡 中等 | "关键是..."、"别忘了..." |
| **Layer 3** | Agent 主动评估 | 自动 | 🟢 最低 | 任务完成后自检 |

### Layer 1: 精确触发词

| 触发词 | 动作 | 反馈 |
|--------|------|------|
| "多专家讨论:" | 启动多专家模式 | [🧠] |
| "这很重要" | Signal +2 | [⭐] |
| "记住这个" | 添加到学习债务 | [💾] |
| "我偏好" | 记录用户偏好 | [👤] |

### Layer 2: 语义触发

| 自然表达 | 识别意图 | 反馈 |
|----------|----------|------|
| "关键是..." / "核心在于..." | 关键信息 | [⭐] |
| "别忘了..." / "要记住..." | 学习债务 | [💾] |
| "我喜欢..." / "我讨厌..." | 用户偏好 | [👤] |
| "千万不要..." / "绝对不能..." | 约束 | [🚫] |
| "还不行" / "太慢了" / "不对" | PUA激活 | [🔥] |

### Layer 3: Agent 主动评估

每次任务完成后自检：
- ≥2 项满足 → 自动写入 \`memory/YYYY-MM-DD.md\` [📝]
- ≥3 项满足 → 更新 \`MEMORY.md\` 高信号区 [⭐]

---
*详细历史 → \`memory/YYYY-MM-DD.md\`*  
*学习债务 → \`memory/learning-debt.md\`*  
*完整文档 → [AGENTS.md](AGENTS.md)*
