"use strict";
/**
 * MoltCare 标准决策输出格式化器
 * 将多专家讨论结果格式化为统一的标准输出格式
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.DecisionFormatter = void 0;
class DecisionFormatter {
    static VERSION = '1.0.0';
    /**
     * 将编排器结果格式化为 MoltCare 标准格式
     */
    static format(result, category = 'technology-selection') {
        const decisionId = this.generateDecisionId();
        return {
            metadata: this.buildMetadata(result, category, decisionId),
            executiveSummary: this.buildExecutiveSummary(result),
            analysis: this.buildAnalysis(result),
            executionPlan: this.buildExecutionPlan(result),
            appendix: this.buildAppendix(result)
        };
    }
    /**
     * 格式化为 Markdown 报告（人类可读）
     */
    static toMarkdown(format) {
        const lines = [];
        // 标题
        lines.push(`# MoltCare 决策报告: ${format.metadata.topic}`);
        lines.push('');
        lines.push(`> **决策ID**: ${format.metadata.decisionId} | **版本**: ${format.metadata.version} | **时间**: ${format.metadata.timestamp}`);
        lines.push('');
        // 执行摘要
        lines.push('## 📋 执行摘要');
        lines.push('');
        lines.push(`| 项目 | 值 |`);
        lines.push(`|------|-----|`);
        lines.push(`| **决策** | ${format.executiveSummary.decision} |`);
        lines.push(`| **信心指数** | ${(format.executiveSummary.confidence * 100).toFixed(1)}% |`);
        lines.push(`| **风险等级** | ${this.translateRiskLevel(format.executiveSummary.riskLevel)} |`);
        lines.push(`| **紧急程度** | ${this.translateUrgency(format.executiveSummary.urgency)} |`);
        lines.push(`| **建议行动** | ${this.translateRecommendation(format.executiveSummary.recommendation)} |`);
        lines.push('');
        // 详细分析
        lines.push('## 🔍 详细分析');
        lines.push('');
        lines.push(`**共识度**: ${(format.analysis.consensusLevel * 100).toFixed(1)}%`);
        lines.push(`**共识状态**: ${format.analysis.consensusReached ? '✅ 已达成' : '⚠️ 未完全达成'}`);
        lines.push('');
        // 专家观点
        lines.push('### 专家观点汇总');
        lines.push('');
        lines.push('| 专家 | 角色 | 立场 | 信心指数 |');
        lines.push('|------|------|------|----------|');
        format.analysis.expertOpinions.forEach(op => {
            lines.push(`| ${op.expertName} | ${op.role} | ${this.translateStance(op.stance)} | ${(op.confidence * 100).toFixed(0)}% |`);
        });
        lines.push('');
        // 关键要点
        lines.push('### 关键要点');
        lines.push('');
        format.analysis.keyFactors.forEach((factor, idx) => {
            const emoji = factor.impact === 'positive' ? '✅' : factor.impact === 'negative' ? '⚠️' : '➖';
            lines.push(`${idx + 1}. ${emoji} **${factor.factor}** (权重: ${factor.weight})`);
            lines.push(`   - ${factor.evidence}`);
        });
        lines.push('');
        // 风险评估
        lines.push('### 风险评估');
        lines.push('');
        lines.push('| 风险 | 概率 | 影响 | 缓解措施 | 负责人 |');
        lines.push('|------|------|------|----------|--------|');
        format.analysis.riskAssessment.forEach(risk => {
            lines.push(`| ${risk.risk} | ${risk.probability} | ${risk.impact} | ${risk.mitigation} | ${risk.owner} |`);
        });
        lines.push('');
        // 执行计划
        lines.push('## 🚀 执行计划');
        lines.push('');
        format.executionPlan.phases.forEach((phase, idx) => {
            lines.push(`### 阶段 ${idx + 1}: ${phase.name}`);
            lines.push(`**持续时间**: ${phase.duration}`);
            lines.push('');
            lines.push('**任务**:');
            phase.tasks.forEach(task => lines.push(`- ${task}`));
            lines.push('');
            lines.push('**交付物**:');
            phase.deliverables.forEach(d => lines.push(`- ${d}`));
            lines.push('');
        });
        // 里程碑
        lines.push('### 关键里程碑');
        lines.push('');
        format.executionPlan.milestones.forEach((m, idx) => {
            lines.push(`${idx + 1}. **${m.name}** (${m.targetDate})`);
            if (m.goNoGoDecision)
                lines.push('   - 🚦 Go/No-Go 决策点');
            m.criteria.forEach(c => lines.push(`   - ✓ ${c}`));
            lines.push('');
        });
        // 回滚策略
        lines.push('### 回滚策略');
        lines.push('');
        lines.push(format.executionPlan.rollbackStrategy);
        lines.push('');
        // 成功标准
        lines.push('### 成功标准');
        lines.push('');
        format.executionPlan.successCriteria.forEach(c => lines.push(`- ${c}`));
        lines.push('');
        // 统计
        lines.push('## 📊 讨论统计');
        lines.push('');
        lines.push(`- **总轮次**: ${format.appendix.statistics.totalRounds}`);
        lines.push(`- **参与专家**: ${format.appendix.statistics.totalExperts} 位`);
        lines.push(`- **总观点数**: ${format.appendix.statistics.totalOpinions}`);
        lines.push(`- **平均信心度**: ${(format.appendix.statistics.averageConfidence * 100).toFixed(1)}%`);
        lines.push(`- **讨论耗时**: ${(format.appendix.statistics.discussionDuration / 1000).toFixed(2)}s`);
        lines.push('');
        // 详细讨论记录（折叠）
        lines.push('<details>');
        lines.push('<summary>📜 详细讨论记录</summary>');
        lines.push('');
        format.appendix.discussionRounds.forEach(round => {
            lines.push(`### 第 ${round.roundNumber} 轮讨论`);
            lines.push('');
            round.opinions.forEach(op => {
                lines.push(`**${op.expertName}** (信心: ${(op.confidence * 100).toFixed(0)}%)`);
                lines.push(`> ${op.opinion}`);
                lines.push('');
                lines.push('**关键要点**:');
                op.keyPoints.forEach(kp => lines.push(`- ${kp}`));
                if (op.concerns?.length) {
                    lines.push('');
                    lines.push('**关注点**:');
                    op.concerns.forEach(c => lines.push(`- ⚠️ ${c}`));
                }
                if (op.recommendations?.length) {
                    lines.push('');
                    lines.push('**建议**:');
                    op.recommendations.forEach(r => lines.push(`- 💡 ${r}`));
                }
                lines.push('');
                lines.push('---');
                lines.push('');
            });
        });
        lines.push('</details>');
        lines.push('');
        // 页脚
        lines.push('---');
        lines.push('');
        lines.push('*本报告由 MoltCare 多专家决策系统自动生成*');
        return lines.join('\n');
    }
    /**
     * 格式化为 JSON（机器可读）
     */
    static toJSON(format) {
        return JSON.stringify(format, null, 2);
    }
    // ========== 私有辅助方法 ==========
    static buildMetadata(result, category, decisionId) {
        return {
            version: this.VERSION,
            timestamp: new Date().toISOString(),
            decisionId,
            topic: result.topic,
            category
        };
    }
    static buildExecutiveSummary(result) {
        const captainOpinion = result.finalDecision;
        const confidence = result.consensusLevel;
        return {
            decision: captainOpinion?.opinion.substring(0, 200) + '...' || '未形成最终决策',
            confidence,
            riskLevel: this.calculateRiskLevel(result),
            urgency: 'medium-term',
            recommendation: this.determineRecommendation(confidence, result.consensus)
        };
    }
    static buildAnalysis(result) {
        const allOpinions = result.rounds.flatMap(r => r.opinions);
        return {
            consensusLevel: result.consensusLevel,
            consensusReached: result.consensus,
            expertOpinions: allOpinions.map(op => ({
                expertId: op.expertId,
                expertName: op.expertName,
                role: this.getRoleName(op.expertId),
                stance: this.determineStance(op.confidence, op.concerns?.length || 0),
                keyPoints: op.keyPoints,
                confidence: op.confidence
            })),
            keyFactors: this.extractKeyFactors(allOpinions),
            riskAssessment: this.extractRisks(allOpinions)
        };
    }
    static buildExecutionPlan(result) {
        const captainOpinion = result.finalDecision;
        return {
            phases: [
                {
                    name: '验证阶段',
                    duration: '1-2周',
                    tasks: ['技术POC', '性能基准测试', '团队技能评估'],
                    deliverables: ['POC报告', '技术验证结论'],
                    dependencies: []
                },
                {
                    name: '试点阶段',
                    duration: '2-4周',
                    tasks: ['小规模试点', '监控和反馈收集', '流程优化'],
                    deliverables: ['试点评估报告', '生产就绪检查清单'],
                    dependencies: ['验证阶段完成']
                },
                {
                    name: '推广阶段',
                    duration: '1-2月',
                    tasks: ['全面部署', '团队培训', '文档完善'],
                    deliverables: ['完整文档', '培训材料', '运维手册'],
                    dependencies: ['试点阶段成功']
                }
            ],
            milestones: [
                {
                    name: '技术验证完成',
                    targetDate: 'T+2周',
                    criteria: ['POC通过评审', '关键技术指标达标'],
                    goNoGoDecision: true
                },
                {
                    name: '试点成功',
                    targetDate: 'T+6周',
                    criteria: ['试点业务稳定运行', '无P0/P1故障'],
                    goNoGoDecision: true
                },
                {
                    name: '全面上线',
                    targetDate: 'T+10周',
                    criteria: ['100%流量切换', '监控指标正常'],
                    goNoGoDecision: false
                }
            ],
            rollbackStrategy: captainOpinion?.recommendations?.find(r => r.includes('回滚')) ||
                '保持旧系统并行运行，数据双写，逐步切流，保留一键回滚能力',
            successCriteria: [
                '系统性能指标提升或持平',
                '无重大生产故障',
                '团队掌握新技术栈',
                '运维成本可控'
            ]
        };
    }
    static buildAppendix(result) {
        const allOpinions = result.rounds.flatMap(r => r.opinions);
        return {
            discussionRounds: result.rounds,
            fullExpertOutputs: result.finalDecision ? [...allOpinions, result.finalDecision] : allOpinions,
            statistics: {
                totalRounds: result.rounds.length,
                totalExperts: new Set(allOpinions.map(o => o.expertId)).size,
                totalOpinions: allOpinions.length,
                averageConfidence: allOpinions.reduce((sum, o) => sum + o.confidence, 0) / allOpinions.length || 0,
                discussionDuration: result.duration
            }
        };
    }
    static generateDecisionId() {
        const timestamp = Date.now().toString(36).toUpperCase();
        const random = Math.random().toString(36).substring(2, 6).toUpperCase();
        return `MCD-${timestamp}-${random}`;
    }
    static calculateRiskLevel(result) {
        const allConcerns = result.rounds.flatMap(r => r.opinions.flatMap(o => o.concerns || []));
        if (allConcerns.length > 6)
            return 'high';
        if (allConcerns.length > 3)
            return 'medium';
        if (allConcerns.length > 0)
            return 'low';
        return 'low';
    }
    static determineRecommendation(confidence, consensus) {
        if (confidence >= 0.8 && consensus)
            return 'proceed';
        if (confidence >= 0.6)
            return 'proceed-with-caution';
        if (confidence >= 0.4)
            return 'delay';
        return 'reject';
    }
    static getRoleName(expertId) {
        const roles = {
            researcher: '研究员',
            architect: '架构师',
            engineer: '工程师',
            captain: '队长'
        };
        return roles[expertId] || '专家';
    }
    static determineStance(confidence, concernCount) {
        if (confidence >= 0.8 && concernCount === 0)
            return 'support';
        if (confidence >= 0.6 && concernCount <= 2)
            return 'conditional';
        if (confidence >= 0.4)
            return 'neutral';
        return 'oppose';
    }
    static extractKeyFactors(opinions) {
        const factors = [];
        // 从所有关键要点中提取因素
        const allKeyPoints = opinions.flatMap(o => o.keyPoints);
        if (allKeyPoints.some(kp => kp.includes('性能'))) {
            factors.push({
                factor: '性能表现',
                impact: 'positive',
                weight: 0.8,
                evidence: '专家分析表明性能指标符合预期'
            });
        }
        if (allKeyPoints.some(kp => kp.includes('成本'))) {
            factors.push({
                factor: '成本控制',
                impact: 'neutral',
                weight: 0.7,
                evidence: '需要详细评估总体拥有成本'
            });
        }
        if (allKeyPoints.some(kp => kp.includes('风险'))) {
            factors.push({
                factor: '实施风险',
                impact: 'negative',
                weight: 0.9,
                evidence: '多位专家识别出潜在风险点'
            });
        }
        return factors;
    }
    static extractRisks(opinions) {
        const allConcerns = opinions.flatMap(o => o.concerns || []);
        return allConcerns.slice(0, 5).map((concern, idx) => ({
            risk: concern,
            probability: idx < 2 ? 'medium' : 'low',
            impact: idx === 0 ? 'high' : 'medium',
            mitigation: '制定详细的缓解计划',
            owner: '待定'
        }));
    }
    // 翻译方法
    static translateRiskLevel(level) {
        const map = {
            low: '🟢 低',
            medium: '🟡 中',
            high: '🔴 高',
            critical: '⛔ 严重'
        };
        return map[level] || level;
    }
    static translateUrgency(urgency) {
        const map = {
            immediate: '🔥 立即',
            'short-term': '⚡ 短期',
            'medium-term': '📅 中期',
            'long-term': '📆 长期'
        };
        return map[urgency] || urgency;
    }
    static translateRecommendation(rec) {
        const map = {
            proceed: '✅ 推进',
            'proceed-with-caution': '⚠️ 谨慎推进',
            delay: '⏸️ 延迟',
            reject: '❌ 否决'
        };
        return map[rec] || rec;
    }
    static translateStance(stance) {
        const map = {
            support: '✅ 支持',
            neutral: '➖ 中立',
            oppose: '❌ 反对',
            conditional: '✓ 有条件支持'
        };
        return map[stance] || stance;
    }
}
exports.DecisionFormatter = DecisionFormatter;
//# sourceMappingURL=formatter.js.map