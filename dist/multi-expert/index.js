"use strict";
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
Object.defineProperty(exports, "__esModule", { value: true });
exports.runTechSelectionExample = exports.DiscussionTrigger = exports.DecisionFormatter = exports.ExpertOrchestrator = exports.CaptainExpert = exports.EngineerExpert = exports.ArchitectExpert = exports.ResearcherExpert = exports.BaseExpert = void 0;
exports.quickDiscuss = quickDiscuss;
exports.shouldTriggerDiscussion = shouldTriggerDiscussion;
// 导出专家角色
var experts_1 = require("./experts");
Object.defineProperty(exports, "BaseExpert", { enumerable: true, get: function () { return experts_1.BaseExpert; } });
Object.defineProperty(exports, "ResearcherExpert", { enumerable: true, get: function () { return experts_1.ResearcherExpert; } });
Object.defineProperty(exports, "ArchitectExpert", { enumerable: true, get: function () { return experts_1.ArchitectExpert; } });
Object.defineProperty(exports, "EngineerExpert", { enumerable: true, get: function () { return experts_1.EngineerExpert; } });
Object.defineProperty(exports, "CaptainExpert", { enumerable: true, get: function () { return experts_1.CaptainExpert; } });
// 导出编排器
var orchestrator_1 = require("./orchestrator");
Object.defineProperty(exports, "ExpertOrchestrator", { enumerable: true, get: function () { return orchestrator_1.ExpertOrchestrator; } });
// 导出格式化器
var formatter_1 = require("./formatter");
Object.defineProperty(exports, "DecisionFormatter", { enumerable: true, get: function () { return formatter_1.DecisionFormatter; } });
// 导出触发器
var triggers_1 = require("./triggers");
Object.defineProperty(exports, "DiscussionTrigger", { enumerable: true, get: function () { return triggers_1.DiscussionTrigger; } });
// 导出示例
var tech_selection_example_1 = require("./examples/tech-selection-example");
Object.defineProperty(exports, "runTechSelectionExample", { enumerable: true, get: function () { return tech_selection_example_1.runTechSelectionExample; } });
/**
 * 便捷函数：快速发起多专家讨论
 */
const orchestrator_2 = require("./orchestrator");
const formatter_2 = require("./formatter");
const triggers_2 = require("./triggers");
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
async function quickDiscuss(topic, options = {}) {
    const orchestrator = new orchestrator_2.ExpertOrchestrator({
        maxRounds: options.maxRounds || 2,
        enableCaptainSynthesis: true
    });
    const result = await orchestrator.orchestrate(topic, options.context || {});
    const formatted = formatter_2.DecisionFormatter.format(result, options.category || 'technology-selection');
    switch (options.outputFormat) {
        case 'json':
            return { json: formatter_2.DecisionFormatter.toJSON(formatted) };
        case 'markdown':
            return { markdown: formatter_2.DecisionFormatter.toMarkdown(formatted) };
        case 'object':
        default:
            return {
                object: formatted,
                markdown: formatter_2.DecisionFormatter.toMarkdown(formatted),
                json: formatter_2.DecisionFormatter.toJSON(formatted)
            };
    }
}
/**
 * 检查内容是否需要多专家讨论
 */
function shouldTriggerDiscussion(content) {
    const trigger = new triggers_2.DiscussionTrigger();
    const result = trigger.evaluate(content);
    return {
        shouldTrigger: result.triggered,
        confidence: result.confidence,
        reason: result.reason
    };
}
//# sourceMappingURL=index.js.map