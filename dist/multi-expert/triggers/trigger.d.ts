/**
 * MoltCare 多专家系统强制触发器
 * 根据关键词/规则自动触发多专家讨论
 */
import { OrchestratorResult } from '../orchestrator';
export interface TriggerRule {
    id: string;
    name: string;
    description: string;
    conditions: TriggerCondition[];
    config: {
        category: 'technology-selection' | 'architecture-design' | 'security-assessment' | 'performance-optimization' | 'migration-planning' | 'cost-optimization' | 'team-organization' | 'process-improvement';
        priority: 'low' | 'medium' | 'high' | 'critical';
        maxRounds: number;
        requireCaptainApproval: boolean;
    };
    actions: TriggerAction[];
    enabled: boolean;
}
export interface TriggerCondition {
    type: 'keyword' | 'regex' | 'complexity' | 'sentiment' | 'topic';
    value: string | number;
    operator?: 'contains' | 'equals' | 'greater' | 'less' | 'matches';
    weight?: number;
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
export declare class DiscussionTrigger {
    private rules;
    private orchestrator;
    private triggerThreshold;
    constructor(rules?: TriggerRule[], triggerThreshold?: number);
    /**
     * 评估内容是否触发多专家讨论
     */
    evaluate(content: string, metadata?: Record<string, any>): TriggerResult;
    /**
     * 如果触发条件满足，执行多专家讨论
     */
    triggerIfNeeded(content: string, context?: Record<string, any>): Promise<{
        triggered: boolean;
        result?: OrchestratorResult;
        triggerInfo: TriggerResult;
    }>;
    /**
     * 添加自定义规则
     */
    addRule(rule: TriggerRule): void;
    /**
     * 启用/禁用规则
     */
    setRuleEnabled(ruleId: string, enabled: boolean): void;
    /**
     * 获取所有规则
     */
    getRules(): TriggerRule[];
    /**
     * 评估单个规则
     */
    private evaluateRule;
    /**
     * 检查关键词条件
     */
    private checkKeywordCondition;
    /**
     * 检查正则条件
     */
    private checkRegexCondition;
    /**
     * 执行触发动作
     */
    private executeAction;
    /**
     * 设置触发阈值
     */
    setThreshold(threshold: number): void;
}
//# sourceMappingURL=trigger.d.ts.map