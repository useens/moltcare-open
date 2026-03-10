"use strict";
/**
 * 研究员专家 - Researcher
 * 负责数据验证、信息收集、事实核查
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.ResearcherExpert = void 0;
const base_expert_1 = require("./base-expert");
class ResearcherExpert extends base_expert_1.BaseExpert {
    constructor() {
        const profile = {
            id: 'researcher',
            name: '研究员',
            role: 'Researcher',
            expertise: [
                '数据验证',
                '信息收集',
                '事实核查',
                '性能基准测试',
                '技术文档分析',
                '社区活跃度评估'
            ],
            personality: '严谨、客观、注重证据、追求准确性',
            systemPrompt: `你是一位资深技术研究员，专注于数据和事实的准确性。

你的职责:
1. 验证技术信息的准确性和时效性
2. 收集性能数据和基准测试结果
3. 分析技术文档的完整性和质量
4. 评估社区活跃度和生态系统健康度
5. 识别信息来源的可靠性

思考角度:
- 数据准确性：这个数据来源可靠吗？是否最新？
- 性能事实：有具体的基准测试数据支持吗？
- 文档质量：官方文档是否完整、清晰？
- 社区健康：GitHub stars、贡献者数量、issue响应速度
- 技术债务：是否有已知的严重bug或安全漏洞？

注意: 如果不确定某些信息，必须明确标注"需要验证"。`
        };
        super(profile);
    }
    async think(input) {
        const prompt = this.generateSystemPrompt() + '\n\n' + this.formatInput(input);
        // 模拟研究员的思考过程
        const topic = input.topic.toLowerCase();
        // 基于主题生成研究角度的观点
        const opinion = this.generateResearchOpinion(topic, input);
        return {
            expertId: this.profile.id,
            expertName: this.profile.name,
            opinion: opinion.summary,
            keyPoints: opinion.keyPoints,
            confidence: opinion.confidence,
            concerns: opinion.concerns,
            recommendations: opinion.recommendations
        };
    }
    generateResearchOpinion(topic, input) {
        // 研究员特有的分析逻辑
        const keyPoints = [];
        const concerns = [];
        const recommendations = [];
        // 通用研究分析框架
        keyPoints.push('数据来源验证：优先使用官方文档和权威基准测试');
        keyPoints.push('时效性检查：技术选型需考虑版本迭代速度和维护状态');
        if (topic.includes('database') || topic.includes('数据库')) {
            keyPoints.push('性能基准：TPC-C/TPC-H 测试结果需结合实际工作负载');
            keyPoints.push('社区指标：GitHub stars增长趋势、贡献者活跃度');
            concerns.push('需要验证当前版本的已知性能瓶颈');
            recommendations.push('建议进行POC测试验证实际性能表现');
        }
        if (topic.includes('framework') || topic.includes('框架')) {
            keyPoints.push('生态成熟度：插件/中间件丰富度评估');
            keyPoints.push('学习曲线：团队技能匹配度需量化评估');
            concerns.push('框架版本更新频率与项目维护成本的平衡');
            recommendations.push('建议统计 npm download 趋势和 issue 解决速度');
        }
        if (topic.includes('ai') || topic.includes('ml') || topic.includes('模型')) {
            keyPoints.push('模型性能：基准测试集上的准确率/F1分数');
            keyPoints.push('推理成本：延迟、吞吐量、资源占用');
            concerns.push('模型版本迭代可能导致的输出不一致性');
            recommendations.push('建议建立模型版本锁定和A/B测试机制');
        }
        // 上下文感知分析
        if (input.context.teamSize && input.context.teamSize < 5) {
            keyPoints.push('团队规模考虑：小团队应优先考虑低运维成本方案');
        }
        if (input.context.budget === 'limited') {
            concerns.push('商业许可成本需要详细核算');
        }
        const summary = `从研究角度分析，${topic} 的技术选型需要基于多维度的数据验证。` +
            `建议建立包含性能基准、社区健康度、文档质量的评估矩阵，并通过POC验证关键假设。`;
        return {
            summary,
            keyPoints,
            confidence: 0.85,
            concerns,
            recommendations
        };
    }
}
exports.ResearcherExpert = ResearcherExpert;
//# sourceMappingURL=researcher.js.map