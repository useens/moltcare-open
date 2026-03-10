/**
 * MoltCare 多专家系统强制触发器
 * 根据关键词/规则自动触发多专家讨论
 */

import { ExpertOrchestrator, OrchestratorResult } from '../orchestrator';

export interface TriggerRule {
  id: string;
  name: string;
  description: string;
  // 触发条件
  conditions: TriggerCondition[];
  // 触发后的配置
  config: {
    category: 'technology-selection' | 'architecture-design' | 'security-assessment' | 'performance-optimization' | 'migration-planning' | 'cost-optimization' | 'team-organization' | 'process-improvement';
    priority: 'low' | 'medium' | 'high' | 'critical';
    maxRounds: number;
    requireCaptainApproval: boolean;
  };
  // 动作
  actions: TriggerAction[];
  enabled: boolean;
}

export interface TriggerCondition {
  type: 'keyword' | 'regex' | 'complexity' | 'sentiment' | 'topic';
  value: string | number;
  operator?: 'contains' | 'equals' | 'greater' | 'less' | 'matches';
  weight?: number; // 条件权重，用于评分
}

export interface TriggerAction {
  type: 'discuss' | 'notify' | 'log' | 'escalate';
  target?: string;
  message?: string;
}

export interface TriggerResult {
  triggered: boolean;
  matchedRules: TriggerRule[];
  confidence: number;
  suggestedCategory?: string;
  reason: string;
}

export interface TriggerContext {
  content: string;
  source: 'user' | 'system' | 'auto';
  timestamp: Date;
  metadata?: Record<string, any>;
}

/**
 * 默认触发规则集
 */
const DEFAULT_RULES: TriggerRule[] = [
  {
    id: 'force-discussion',
    name: '强制多专家讨论',
    description: '用户明确要求多专家讨论',
    conditions: [
      { type: 'keyword', value: '多专家讨论', operator: 'contains', weight: 1.0 },
      { type: 'keyword', value: 'multi-expert', operator: 'contains', weight: 1.0 }
    ],
    config: {
      category: 'technology-selection',
      priority: 'critical',
      maxRounds: 3,
      requireCaptainApproval: true
    },
    actions: [
      { type: 'discuss' },
      { type: 'log', message: '强制触发多专家讨论' }
    ],
    enabled: true
  },
  {
    id: 'tech-selection',
    name: '技术选型触发',
    description: '检测到技术选型相关关键词',
    conditions: [
      { type: 'keyword', value: '选型', operator: 'contains', weight: 0.8 },
      { type: 'keyword', value: '选择', operator: 'contains', weight: 0.6 },
      { type: 'keyword', value: '对比', operator: 'contains', weight: 0.7 },
      { type: 'keyword', value: 'framework', operator: 'contains', weight: 0.7 },
      { type: 'keyword', value: '数据库', operator: 'contains', weight: 0.7 },
      { type: 'keyword', value: 'language', operator: 'contains', weight: 0.6 }
    ],
    config: {
      category: 'technology-selection',
      priority: 'high',
      maxRounds: 3,
      requireCaptainApproval: true
    },
    actions: [
      { type: 'discuss' }
    ],
    enabled: true
  },
  {
    id: 'architecture-design',
    name: '架构设计触发',
    description: '检测到架构设计相关关键词',
    conditions: [
      { type: 'keyword', value: '架构', operator: 'contains', weight: 0.9 },
      { type: 'keyword', value: '设计', operator: 'contains', weight: 0.6 },
      { type: 'keyword', value: '微服务', operator: 'contains', weight: 0.8 },
      { type: 'keyword', value: 'monolith', operator: 'contains', weight: 0.8 },
      { type: 'keyword', value: '分布式', operator: 'contains', weight: 0.8 },
      { type: 'keyword', value: 'architecture', operator: 'contains', weight: 0.9 }
    ],
    config: {
      category: 'architecture-design',
      priority: 'high',
      maxRounds: 3,
      requireCaptainApproval: true
    },
    actions: [
      { type: 'discuss' }
    ],
    enabled: true
  },
  {
    id: 'security-assessment',
    name: '安全评估触发',
    description: '检测到安全相关关键词',
    conditions: [
      { type: 'keyword', value: '安全', operator: 'contains', weight: 0.9 },
      { type: 'keyword', value: '漏洞', operator: 'contains', weight: 0.9 },
      { type: 'keyword', value: '攻击', operator: 'contains', weight: 0.9 },
      { type: 'keyword', value: '加密', operator: 'contains', weight: 0.8 },
      { type: 'keyword', value: '认证', operator: 'contains', weight: 0.7 },
      { type: 'keyword', value: 'security', operator: 'contains', weight: 0.9 }
    ],
    config: {
      category: 'security-assessment',
      priority: 'critical',
      maxRounds: 4,
      requireCaptainApproval: true
    },
    actions: [
      { type: 'discuss' },
      { type: 'escalate', target: 'security-team' }
    ],
    enabled: true
  },
  {
    id: 'performance-optimization',
    name: '性能优化触发',
    description: '检测到性能相关关键词',
    conditions: [
      { type: 'keyword', value: '性能', operator: 'contains', weight: 0.9 },
      { type: 'keyword', value: '优化', operator: 'contains', weight: 0.7 },
      { type: 'keyword', value: '慢', operator: 'contains', weight: 0.8 },
      { type: 'keyword', value: '延迟', operator: 'contains', weight: 0.8 },
      { type: 'keyword', value: '吞吐', operator: 'contains', weight: 0.8 },
      { type: 'keyword', value: 'performance', operator: 'contains', weight: 0.9 }
    ],
    config: {
      category: 'performance-optimization',
      priority: 'high',
      maxRounds: 3,
      requireCaptainApproval: true
    },
    actions: [
      { type: 'discuss' }
    ],
    enabled: true
  },
  {
    id: 'migration-planning',
    name: '迁移规划触发',
    description: '检测到迁移相关关键词',
    conditions: [
      { type: 'keyword', value: '迁移', operator: 'contains', weight: 0.9 },
      { type: 'keyword', value: '升级', operator: 'contains', weight: 0.7 },
      { type: 'keyword', value: '重构', operator: 'contains', weight: 0.8 },
      { type: 'keyword', value: '替换', operator: 'contains', weight: 0.7 },
      { type: 'keyword', value: 'migration', operator: 'contains', weight: 0.9 }
    ],
    config: {
      category: 'migration-planning',
      priority: 'high',
      maxRounds: 3,
      requireCaptainApproval: true
    },
    actions: [
      { type: 'discuss' }
    ],
    enabled: true
  },
  {
    id: 'complexity-threshold',
    name: '复杂度阈值触发',
    description: '问题复杂度超过阈值',
    conditions: [
      { type: 'complexity', value: 7, operator: 'greater', weight: 0.8 }
    ],
    config: {
      category: 'technology-selection',
      priority: 'medium',
      maxRounds: 3,
      requireCaptainApproval: true
    },
    actions: [
      { type: 'discuss' }
    ],
    enabled: true
  }
];

export class DiscussionTrigger {
  private rules: TriggerRule[];
  private orchestrator: ExpertOrchestrator;
  private triggerThreshold: number;

  constructor(rules?: TriggerRule[], triggerThreshold: number = 0.6) {
    this.rules = rules ? [...DEFAULT_RULES, ...rules] : [...DEFAULT_RULES];
    this.orchestrator = new ExpertOrchestrator();
    this.triggerThreshold = triggerThreshold;
  }

  /**
   * 评估内容是否触发多专家讨论
   */
  evaluate(content: string, metadata?: Record<string, any>): TriggerResult {
    const matchedRules: TriggerRule[] = [];
    let totalScore = 0;
    let maxPossibleScore = 0;
    let reasons: string[] = [];

    for (const rule of this.rules) {
      if (!rule.enabled) continue;

      const ruleResult = this.evaluateRule(rule, content);
      
      if (ruleResult.matched) {
        matchedRules.push(rule);
        totalScore += ruleResult.score;
        reasons.push(`${rule.name}: ${ruleResult.matchedConditions.join(', ')}`);
      }
      
      maxPossibleScore += rule.conditions.reduce((sum, c) => sum + (c.weight || 0.5), 0);
    }

    const confidence = maxPossibleScore > 0 ? totalScore / maxPossibleScore : 0;
    const triggered = confidence >= this.triggerThreshold || matchedRules.some(r => r.id === 'force-discussion');

    // 确定建议的分类
    const suggestedCategory = matchedRules.length > 0 
      ? matchedRules[0].config.category 
      : undefined;

    return {
      triggered,
      matchedRules,
      confidence,
      suggestedCategory,
      reason: reasons.join('; ') || '未匹配任何触发规则'
    };
  }

  /**
   * 如果触发条件满足，执行多专家讨论
   */
  async triggerIfNeeded(content: string, context: Record<string, any> = {}): Promise<{
    triggered: boolean;
    result?: OrchestratorResult;
    triggerInfo: TriggerResult;
  }> {
    const triggerInfo = this.evaluate(content, context);

    if (!triggerInfo.triggered) {
      return {
        triggered: false,
        triggerInfo
      };
    }

    // 使用匹配的第一个规则配置
    const primaryRule = triggerInfo.matchedRules[0];
    
    // 更新编排器配置
    this.orchestrator = new ExpertOrchestrator({
      maxRounds: primaryRule.config.maxRounds,
      enableCaptainSynthesis: primaryRule.config.requireCaptainApproval
    });

    // 执行讨论
    const result = await this.orchestrator.orchestrate(content, context);

    // 执行其他动作
    for (const action of primaryRule.actions) {
      await this.executeAction(action, content, result);
    }

    return {
      triggered: true,
      result,
      triggerInfo
    };
  }

  /**
   * 添加自定义规则
   */
  addRule(rule: TriggerRule): void {
    this.rules.push(rule);
  }

  /**
   * 启用/禁用规则
   */
  setRuleEnabled(ruleId: string, enabled: boolean): void {
    const rule = this.rules.find(r => r.id === ruleId);
    if (rule) {
      rule.enabled = enabled;
    }
  }

  /**
   * 获取所有规则
   */
  getRules(): TriggerRule[] {
    return [...this.rules];
  }

  /**
   * 评估单个规则
   */
  private evaluateRule(rule: TriggerRule, content: string): {
    matched: boolean;
    score: number;
    matchedConditions: string[];
  } {
    let score = 0;
    const matchedConditions: string[] = [];

    for (const condition of rule.conditions) {
      const weight = condition.weight || 0.5;
      
      switch (condition.type) {
        case 'keyword':
          if (this.checkKeywordCondition(condition, content)) {
            score += weight;
            matchedConditions.push(`关键词: ${condition.value}`);
          }
          break;
        case 'regex':
          if (this.checkRegexCondition(condition, content)) {
            score += weight;
            matchedConditions.push(`正则匹配`);
          }
          break;
        case 'complexity':
          // 复杂度评估需要额外上下文，简化处理
          break;
      }
    }

    // 规则匹配条件：至少一个条件满足且分数超过阈值
    const matched = score >= 0.5;

    return { matched, score, matchedConditions };
  }

  /**
   * 检查关键词条件
   */
  private checkKeywordCondition(condition: TriggerCondition, content: string): boolean {
    const contentLower = content.toLowerCase();
    const valueLower = String(condition.value).toLowerCase();
    
    switch (condition.operator) {
      case 'contains':
        return contentLower.includes(valueLower);
      case 'equals':
        return contentLower === valueLower;
      default:
        return contentLower.includes(valueLower);
    }
  }

  /**
   * 检查正则条件
   */
  private checkRegexCondition(condition: TriggerCondition, content: string): boolean {
    try {
      const regex = new RegExp(String(condition.value), 'i');
      return regex.test(content);
    } catch {
      return false;
    }
  }

  /**
   * 执行触发动作
   */
  private async executeAction(action: TriggerAction, content: string, result: OrchestratorResult): Promise<void> {
    switch (action.type) {
      case 'discuss':
        // 讨论已在 orchestrate 中完成
        break;
      case 'notify':
        console.log(`[Trigger] 通知: ${action.message || '多专家讨论已完成'}`);
        break;
      case 'log':
        console.log(`[Trigger] ${action.message || '触发器激活'}`);
        break;
      case 'escalate':
        console.log(`[Trigger] 升级到: ${action.target || '相关团队'}`);
        break;
    }
  }

  /**
   * 设置触发阈值
   */
  setThreshold(threshold: number): void {
    this.triggerThreshold = Math.max(0, Math.min(1, threshold));
  }
}
