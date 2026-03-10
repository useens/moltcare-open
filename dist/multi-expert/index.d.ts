/**
 * MoltCare 多专家决策系统 - 主入口
 *
 * 核心功能：
 * 1. 多角色专家协作 (研究员、架构师、工程师、队长)
 * 2. 可配置的讨论编排
 * 3. 标准化的决策输出
 * 4. 智能触发机制
 *
 * @module multi-expert
 */
export { BaseExpert, ExpertProfile, ExpertInput, ExpertOutput, DiscussionRound, ResearcherExpert, ArchitectExpert, EngineerExpert, CaptainExpert } from './experts';
export { ExpertOrchestrator, OrchestratorConfig, OrchestratorResult } from './orchestrator';
export { DecisionFormatter, MoltCareDecisionFormat } from './formatter';
export { DiscussionTrigger, TriggerRule, TriggerCondition, TriggerAction, TriggerResult, TriggerContext } from './triggers';
export { runTechSelectionExample } from './examples/tech-selection-example';
export interface QuickDiscussOptions {
    maxRounds?: number;
    category?: 'technology-selection' | 'architecture-design' | 'security-assessment' | 'performance-optimization' | 'migration-planning' | 'cost-optimization' | 'team-organization' | 'process-improvement';
    context?: Record<string, any>;
    outputFormat?: 'json' | 'markdown' | 'object';
}
/**
 * 快速发起多专家讨论
 *
 * @example
 * ```typescript
 * import { quickDiscuss } from './multi-expert';
 *
 * const result = await quickDiscuss('是否将数据库从MySQL迁移到PostgreSQL？', {
 *   maxRounds: 2,
 *   context: { teamSize: 8, timeline: 'aggressive' }
 * });
 *
 * console.log(result.markdown);
 * ```
 */
export declare function quickDiscuss(topic: string, options?: QuickDiscussOptions): Promise<{
    json: string;
    markdown?: undefined;
    object?: undefined;
} | {
    markdown: string;
    json?: undefined;
    object?: undefined;
} | {
    object: import("./formatter").MoltCareDecisionFormat;
    markdown: string;
    json: string;
}>;
/**
 * 检查内容是否需要多专家讨论
 */
export declare function shouldTriggerDiscussion(content: string): {
    shouldTrigger: boolean;
    confidence: number;
    reason: string;
};
//# sourceMappingURL=index.d.ts.map