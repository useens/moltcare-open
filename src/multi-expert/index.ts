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

// 导出专家角色
export {
  BaseExpert,
  ExpertProfile,
  ExpertInput,
  ExpertOutput,
  DiscussionRound,
  ResearcherExpert,
  ArchitectExpert,
  EngineerExpert,
  CaptainExpert
} from './experts';

// 导出编排器
export {
  ExpertOrchestrator,
  OrchestratorConfig,
  OrchestratorResult
} from './orchestrator';

// 导出格式化器
export {
  DecisionFormatter,
  MoltCareDecisionFormat
} from './formatter';

// 导出触发器
export {
  DiscussionTrigger,
  TriggerRule,
  TriggerCondition,
  TriggerAction,
  TriggerResult,
  TriggerContext
} from './triggers';

// 导出示例
export { runTechSelectionExample } from './examples/tech-selection-example';

/**
 * 便捷函数：快速发起多专家讨论
 */
import { ExpertOrchestrator } from './orchestrator';
import { DecisionFormatter } from './formatter';
import { DiscussionTrigger } from './triggers';

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
export async function quickDiscuss(topic: string, options: QuickDiscussOptions = {}) {
  const orchestrator = new ExpertOrchestrator({
    maxRounds: options.maxRounds || 2,
    enableCaptainSynthesis: true
  });

  const result = await orchestrator.orchestrate(topic, options.context || {});
  const formatted = DecisionFormatter.format(result, options.category || 'technology-selection');

  switch (options.outputFormat) {
    case 'json':
      return { json: DecisionFormatter.toJSON(formatted) };
    case 'markdown':
      return { markdown: DecisionFormatter.toMarkdown(formatted) };
    case 'object':
    default:
      return {
        object: formatted,
        markdown: DecisionFormatter.toMarkdown(formatted),
        json: DecisionFormatter.toJSON(formatted)
      };
  }
}

/**
 * 检查内容是否需要多专家讨论
 */
export function shouldTriggerDiscussion(content: string): {
  shouldTrigger: boolean;
  confidence: number;
  reason: string;
} {
  const trigger = new DiscussionTrigger();
  const result = trigger.evaluate(content);
  
  return {
    shouldTrigger: result.triggered,
    confidence: result.confidence,
    reason: result.reason
  };
}
