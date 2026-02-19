# Multi-Agent Debate System

🚀 **可复用的多智能体辩论系统** - 支持自定义专家、实时同步、可视化面板和飞书通知

## ✨ 特性

- 🎭 **自定义专家角色** - 支持研究、架构、实现等角色，也可完全自定义
- ⚡ **Redis实时同步** - 50-100ms延迟，120x性能提升
- 📊 **可视化面板** - Web/终端双模式实时展示
- 💬 **飞书交互卡片** - 丰富的消息通知，支持操作按钮
- 🔧 **简洁API** - 一行代码启动辩论

## 📦 安装

```bash
# 克隆或复制到工作目录
cp -r skills/multi-agent-debate ~/.openclaw/workspace/skills/

# 安装依赖
pip install redis flask --break-system-packages

# 启动Redis
redis-server --port 6380 --protected-mode no --daemonize yes
```

## 🚀 快速开始

### 方式1: 命令行快速启动

```bash
# 使用默认专家（Harper/Benjamin/Lucas）
python quickstart.py "选择消息队列：Kafka vs RabbitMQ"

# 自定义专家
python quickstart.py "云服务选型" --agents "安全专家,成本专家,性能专家"

# 快速模式（只输出结果）
python quickstart.py "缓存策略" --quick
```

### 方式2: Python API

```python
from multi_agent_debate import MultiAgentDebate, Agent, AgentRole

# 创建辩论
debate = MultiAgentDebate(
    topic="设计高性能Web API"
)

# 运行辩论
result = debate.start()

# 查看结果
print(f"耗时: {result['elapsed']}")
print(f"决策: {result['consensus']['decisions']}")
```

### 方式3: 自定义专家

```python
from multi_agent_debate import MultiAgentDebate, Agent, AgentRole

# 定义自定义专家
agents = [
    Agent("安全专家", AgentRole.CUSTOM, "网络安全专家", 
          "你专注于安全漏洞分析和防护策略。"),
    Agent("成本专家", AgentRole.CUSTOM, "成本分析专家",
          "你专注于TCO分析和ROI评估。"),
    Agent("法务专家", AgentRole.CUSTOM, "合规法务专家",
          "你专注于合规风险和法律条款。")
]

# 创建辩论
debate = MultiAgentDebate(
    topic="选择第三方服务商",
    agents=agents
)

# 注册回调
def on_consensus(result):
    print(f"达成共识！决策: {result['decisions']}")

debate.register_callback('consensus', on_consensus)

# 运行
result = debate.start()
```

## 📋 完整API文档

### MultiAgentDebate 类

#### 构造函数

```python
MultiAgentDebate(
    topic: str,                    # 辩论主题（必填）
    agents: List[Agent] = None,    # 专家列表（可选，默认3专家）
    debate_id: str = None,          # 辩论ID（可选，自动生成）
    rounds: int = 3,                # 辩论轮次（默认3）
    timeout_per_round: int = 120,   # 每轮超时（秒，默认120）
    redis_host: str = "localhost",  # Redis主机
    redis_port: int = 6380,         # Redis端口
    enable_notifications: bool = True,  # 启用通知
    notification_callback: Callable = None  # 通知回调
)
```

#### 方法

| 方法 | 说明 |
|------|------|
| `start()` | 启动辩论，返回结果字典 |
| `register_callback(event, callback)` | 注册事件回调 |
| `get_result()` | 获取当前结果 |
| `cleanup()` | 清理Redis数据 |

#### 回调事件

```python
# 轮次完成
debate.register_callback('round_complete', 
    lambda round_num, data: print(f"Round {round_num} 完成"))

# 达成共识
debate.register_callback('consensus',
    lambda result: print(f"决策: {result}"))

# 状态更新
debate.register_callback('update',
    lambda agent, round, status: print(f"{agent}: {status}"))
```

### Agent 类

```python
Agent(
    name: str,                     # 专家名称
    role: AgentRole,               # 角色类型
    description: str,              # 描述
    system_prompt: str = None,     # 系统提示词（可选）
    model: str = "kimi-coding/k2p5"  # 使用模型
)
```

#### 预设角色

| 角色 | 说明 |
|------|------|
| `AgentRole.RESEARCHER` | 研究专家 - 技术调研、数据分析 |
| `AgentRole.ARCHITECT` | 架构专家 - 整体设计、安全 |
| `AgentRole.IMPLEMENTER` | 实现专家 - 代码、工期评估 |
| `AgentRole.LEADER` | 队长 - 整合决策 |
| `AgentRole.CUSTOM` | 自定义角色 |

## 🎨 可视化

### 终端可视化

```bash
# 在另一个终端运行
python terminal_canvas.py
```

效果：
- 🎨 彩色专家卡片
- 🔄 实时状态更新
- 💬 消息流显示

### Web可视化

```bash
# 启动Web服务器
python canvas_server.py

# 浏览器访问
open http://localhost:5000
```

## 💬 飞书通知

```python
from multi_agent_debate import MultiAgentDebate
from multi_agent_debate.feishu_cards import DebateNotifier

# 创建辩论
debate = MultiAgentDebate(topic="技术选型")

# 创建通知器
notifier = DebateNotifier(
    redis_manager=debate.redis,
    message_sender=message.send  # 你的飞书发送函数
)

# 开始监听并自动发送飞书卡片
notifier.start_monitoring(debate.debate_id)

# 运行辩论
debate.start()
```

飞书卡片效果：
- 🚀 辩论开始通知
- 🔄 轮次进度更新
- 🎯 最终共识卡片（带操作按钮）

## 📊 辩论结果格式

```python
{
    'debate_id': 'debate-1234567890',
    'topic': '设计高性能Web API',
    'status': 'completed',
    'elapsed': '4分30秒',
    'agents': [
        {'name': 'Harper', 'role': 'researcher', ...},
        {'name': 'Benjamin', 'role': 'architect', ...},
        {'name': 'Lucas', 'role': 'implementer', ...}
    ],
    'rounds': {
        'round_1': {'harper': '...', 'benjamin': '...', 'lucas': '...'},
        'round_2': {...},
        'round_3': {...}
    },
    'consensus': {
        'decisions': {
            '框架': 'FastAPI 0.100+',
            '认证': 'JWT + Session混合',
            '架构': '渐进分层',
            '工期': '25工作日(5周)'
        },
        'compromises': [...],
        'sticking_points': [...]
    }
}
```

## 🔧 高级用法

### 自定义辩论流程

```python
from multi_agent_debate import MultiAgentDebate

debate = MultiAgentDebate(
    topic="复杂技术决策",
    rounds=5,  # 5轮辩论
    timeout_per_round=300,  # 5分钟超时
)

# 自定义回调逻辑
def custom_callback(round_num, data):
    # 保存到数据库
    db.save(f"round_{round_num}", data)
    # 发送邮件通知
    email.send(f"Round {round_num} 完成")

debate.register_callback('round_complete', custom_callback)
result = debate.start()
```

### 批量辩论

```python
from multi_agent_debate import quick_debate

topics = [
    "选择数据库",
    "选择缓存方案", 
    "选择消息队列"
]

results = []
for topic in topics:
    result = quick_debate(topic)
    results.append(result)

# 对比分析
for r in results:
    print(f"{r['topic']}: {r['elapsed']}")
```

## 📁 文件结构

```
multi-agent-debate/
├── __init__.py              # 核心类和API
├── redis_manager.py         # Redis管理模块
├── canvas_server.py         # Web可视化服务器
├── terminal_canvas.py       # 终端可视化
├── feishu_cards.py          # 飞书卡片构建器
├── feishu_adapter.py        # 飞书文本适配器
├── quickstart.py            # 快速启动脚本
├── protocol.md              # 协议文档
├── redis-optimization.md    # Redis优化方案
├── canvas-visualization.md  # 可视化方案
└── README.md                # 本文档
```

## 🎯 适用场景

- ✅ 技术选型决策
- ✅ 架构设计评审
- ✅ 产品功能优先级
- ✅ 供应商选择
- ✅ 风险评估

## 🔗 依赖

- Python 3.8+
- Redis 6.0+
- flask (Web可视化)
- redis-py (Redis连接)

## 📝 许可证

MIT License - 自由使用和修改

---

**有问题？** 查看 `protocol.md` 了解详细协议，或运行 `python quickstart.py --help` 获取命令行帮助。
