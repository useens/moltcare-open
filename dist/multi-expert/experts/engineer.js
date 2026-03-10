"use strict";
/**
 * 工程师专家 - Engineer
 * 负责实现评估、工期估算、成本分析
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.EngineerExpert = void 0;
const base_expert_1 = require("./base-expert");
class EngineerExpert extends base_expert_1.BaseExpert {
    constructor() {
        const profile = {
            id: 'engineer',
            name: '工程师',
            role: 'Engineer',
            expertise: [
                '实现可行性评估',
                '工期估算',
                '成本分析',
                '代码质量',
                '调试排障',
                '性能优化'
            ],
            personality: '务实、注重细节、追求效率、关注落地',
            systemPrompt: `你是一位资深软件工程师，专注于技术方案的实际落地实现。

你的职责:
1. 评估技术方案的可实现性和开发工作量
2. 识别实现过程中的技术难点和阻塞点
3. 估算开发、测试、部署的工期
4. 评估运维成本和团队学习成本
5. 关注代码质量和可测试性

思考角度:
- 实现复杂度：功能能否在合理时间内完成？
- 调试难度：出现问题时能否快速定位和修复？
- 测试覆盖：自动化测试的编写成本和维护成本
- 部署流程：CI/CD 集成是否顺畅？
- 监控运维：生产环境的可观测性和故障恢复能力

原则: 能工作的代码比完美的代码更重要，但好代码能让工作持续下去。`
        };
        super(profile);
    }
    async think(input) {
        const topic = input.topic.toLowerCase();
        const opinion = this.generateEngineerOpinion(topic, input);
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
    generateEngineerOpinion(topic, input) {
        const keyPoints = [];
        const concerns = [];
        const recommendations = [];
        // 工程分析框架
        keyPoints.push('实现复杂度：评估核心功能的开发工作量和技术难点');
        keyPoints.push('调试体验：错误信息的友好程度和问题定位效率');
        keyPoints.push('测试策略：单元测试、集成测试的可行性');
        if (topic.includes('javascript') || topic.includes('typescript') || topic.includes('node')) {
            keyPoints.push('npm生态：依赖包的质量和安全性评估');
            keyPoints.push('类型安全：TS支持的完善程度对开发效率的影响');
            concerns.push('npm依赖地狱和供应链安全风险');
            recommendations.push('建议启用Dependabot和npm audit定期扫描');
            recommendations.push('建议锁定依赖版本，使用lockfile');
        }
        if (topic.includes('python')) {
            keyPoints.push('PyPI生态：库的丰富度和维护状态');
            keyPoints.push('性能考虑：CPU密集型任务的优化空间');
            concerns.push('Python的GIL限制对并发性能的影响');
            concerns.push('动态类型导致的运行时错误风险');
            recommendations.push('建议对核心模块添加类型注解并使用mypy检查');
        }
        if (topic.includes('rust') || topic.includes('go') || topic.includes('golang')) {
            keyPoints.push('编译时安全：内存安全和类型系统减少运行时错误');
            keyPoints.push('部署便利：单二进制文件简化部署流程');
            concerns.push('团队学习曲线和人才招聘成本');
            recommendations.push('建议先从非核心服务开始试点，积累团队经验');
        }
        if (topic.includes('database') || topic.includes('数据库')) {
            keyPoints.push('迁移复杂度：数据迁移和schema变更的风险评估');
            keyPoints.push('连接池管理：并发场景下的连接优化');
            concerns.push('数据库版本升级的回滚策略');
            recommendations.push('建议使用数据库迁移工具(Flyway/Liquibase)管理schema');
        }
        // 工期估算逻辑
        if (input.context.timeline) {
            const timeline = input.context.timeline;
            if (timeline === 'aggressive') {
                concerns.push('激进的时间表可能导致技术债务累积');
                recommendations.push('建议采用MVP方式，分阶段交付核心功能');
            }
            else if (timeline === 'relaxed') {
                keyPoints.push('充足的时间允许更好的代码质量和测试覆盖');
            }
        }
        // 团队规模影响
        if (input.context.teamSize) {
            const size = input.context.teamSize;
            if (size < 3) {
                keyPoints.push('小团队需要优先选择开箱即用的解决方案');
                concerns.push('技术选型过于复杂可能导致维护负担过重');
            }
            else if (size > 10) {
                keyPoints.push('大团队需要考虑代码规范和协作流程的标准化');
            }
        }
        // 成本分析
        const costAnalysis = this.estimateCost(topic, input);
        keyPoints.push(`成本估算：${costAnalysis}`);
        const summary = `从工程实施角度，${topic} 的实现需要重点关注开发效率、调试体验和运维成本。` +
            `建议在原型阶段验证关键技术假设，避免在大规模投入后发现不可逾越的技术障碍。`;
        return {
            summary,
            keyPoints,
            confidence: 0.88,
            concerns,
            recommendations
        };
    }
    estimateCost(topic, input) {
        const costs = [];
        // 学习成本
        costs.push('学习成本（团队培训和技术储备）');
        // 开发成本
        costs.push('开发成本（核心功能实现和集成）');
        // 运维成本
        costs.push('运维成本（监控、告警、故障处理）');
        // 机会成本
        costs.push('机会成本（技术选型错误后的迁移成本）');
        return costs.join(' + ');
    }
}
exports.EngineerExpert = EngineerExpert;
//# sourceMappingURL=engineer.js.map