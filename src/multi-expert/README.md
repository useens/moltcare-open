# MoltCare 多专家决策系统

MoltCare 核心特性 - 多专家协作决策引擎。

## 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                    MoltCare Multi-Expert                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │Researcher│  │Architect │  │ Engineer │  │ Captain  │        │
│  │  研究员   │  │  架构师   │  │  工程师   │  │  队长     │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       │             │             │             │               │
│       └─────────────┴─────────────┴─────────────┘               │
│                         │                                       │
│              ┌──────────┴──────────┐                           │
│              │ ExpertOrchestrator  │  ← 讨论编排器              │
│              │    专家讨论编排器     │                           │
│              └──────────┬──────────┘                           │
│                         │                                       │
│              ┌──────────┴──────────┐                           │
│              │  DecisionFormatter  │  ← 输出格式化              │
│              │    决策格式化器      │                           │
│              └──────────┬──────────┘                           │
│                         │                                       │
│              ┌──────────┴──────────┐                           │
│              │  DiscussionTrigger  │  ← 触发器                  │
│              │    强制触发器        │                           │
│              └─────────────────────┘                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 专家角色

### 🔍 Researcher（研究员）
- **职责**: 数据验证、信息收集、事实核查
- **思考角度**: 数据准确性、性能基准、社区健康度、文档质量
- **输出**: 基于证据的分析，识别信息来源可靠性

### 🧠 Architect（架构师）
- **职责**: 系统设计、可维护性评估、扩展性规划
- **思考角度**: 系统一致性、演进路径、技术风险、可逆性
- **输出**: 长期架构健康度评估

### 💻 Engineer（工程师）
- **职责**: 实现可行性、工期估算、成本分析
- **思考角度**: 开发效率、调试体验、运维成本、代码质量
- **输出**: 落地实施的实用性评估

### 👑 Captain（队长）
- **职责**: 整合决策、全局最优、权衡取舍
- **思考角度**: 风险收益、团队执行、时间压力
- **输出**: 最终决策建议和执行路径

## 快速开始

### 基础用法

```typescript
import { quickDiscuss, ExpertOrchestrator, DecisionFormatter } from './multi-expert';

// 快速讨论
const result = await quickDiscuss('是否迁移到微服务架构？', {
  maxRounds: 2,
  context: { teamSize: 10, existingTechStack: 'Monolith' }
});

console.log(result.markdown);
```

### 高级用法

```typescript
import { ExpertOrchestrator, DiscussionTrigger, DecisionFormatter } from './multi-expert';

// 1. 检查是否需要多专家讨论
const trigger = new DiscussionTrigger();
const evaluation = trigger.evaluate('我们需要选择新的数据库');

if (evaluation.triggered) {
  // 2. 配置编排器
  const orchestrator = new ExpertOrchestrator({
    maxRounds: 3,
    minRounds: 2,
    consensusThreshold: 0.7,
    discussionMode: 'adaptive',
    enableCaptainSynthesis: true
  });

  // 3. 执行讨论
  const result = await orchestrator.orchestrate(
    '数据库选型：PostgreSQL vs MySQL',
    { teamSize: 5, budget: 'limited' }
  );

  // 4. 格式化输出
  const formatted = DecisionFormatter.format(result, 'technology-selection');
  
  // 5. 导出报告
  const markdown = DecisionFormatter.toMarkdown(formatted);
  const json = DecisionFormatter.toJSON(formatted);
}
```

## 触发规则

系统自动根据关键词触发多专家讨论：

| 触发词 | 分类 | 优先级 |
|--------|------|--------|
| "多专家讨论" | 强制触发 | Critical |
| "架构"/"微服务"/"monolith" | 架构设计 | High |
| "选型"/"对比"/"framework" | 技术选型 | High |
| "安全"/"漏洞"/"security" | 安全评估 | Critical |
| "性能"/"优化"/"performance" | 性能优化 | High |
| "迁移"/"升级"/"migration" | 迁移规划 | High |

## 输出格式

### Markdown 报告

```markdown
# MoltCare 决策报告: [主题]

## 📋 执行摘要
| 项目 | 值 |
|------|-----|
| **决策** | ... |
| **信心指数** | 85% |
| **风险等级** | 🟡 中 |
| **建议行动** | ✅ 推进 |

## 🔍 详细分析
...

## 🚀 执行计划
...
```

### JSON 格式

```json
{
  "metadata": {
    "version": "1.0.0",
    "decisionId": "MCD-XXX",
    "category": "technology-selection"
  },
  "executiveSummary": {
    "decision": "...",
    "confidence": 0.85,
    "riskLevel": "medium",
    "recommendation": "proceed"
  },
  ...
}
```

## 目录结构

```
src/multi-expert/
├── experts/           # 专家角色
│   ├── base-expert.ts # 基类定义
│   ├── researcher.ts  # 研究员
│   ├── architect.ts   # 架构师
│   ├── engineer.ts    # 工程师
│   ├── captain.ts     # 队长
│   └── index.ts       # 导出
├── orchestrator/      # 讨论编排器
│   ├── orchestrator.ts
│   └── index.ts
├── formatter/         # 输出格式化
│   ├── formatter.ts
│   └── index.ts
├── triggers/          # 强制触发器
│   ├── trigger.ts
│   └── index.ts
├── examples/          # 示例
│   └── tech-selection-example.ts
├── index.ts           # 主入口
└── README.md          # 本文档
```

## 扩展开发

### 添加自定义专家

```typescript
import { BaseExpert, ExpertProfile, ExpertInput, ExpertOutput } from './multi-expert';

class SecurityExpert extends BaseExpert {
  constructor() {
    const profile: ExpertProfile = {
      id: 'security',
      name: '安全专家',
      role: 'SecurityExpert',
      expertise: ['渗透测试', '安全审计', '合规检查'],
      personality: '谨慎、细致、风险敏感',
      systemPrompt: '...'
    };
    super(profile);
  }

  async think(input: ExpertInput): Promise<ExpertOutput> {
    // 实现安全专家的分析逻辑
  }
}

// 注册到编排器
orchestrator.registerExpert(new SecurityExpert());
```

### 添加自定义触发规则

```typescript
import { DiscussionTrigger, TriggerRule } from './multi-expert';

const trigger = new DiscussionTrigger();

trigger.addRule({
  id: 'custom-rule',
  name: '自定义规则',
  conditions: [
    { type: 'keyword', value: '特定关键词', operator: 'contains', weight: 1.0 }
  ],
  config: {
    category: 'technology-selection',
    priority: 'high',
    maxRounds: 3,
    requireCaptainApproval: true
  },
  actions: [{ type: 'discuss' }],
  enabled: true
});
```

## License

MIT
