"use strict";
/**
 * 示例：使用多专家系统进行技术选型决策
 * 展示如何用MoltCare多专家系统做技术选型决策
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.runTechSelectionExample = runTechSelectionExample;
const orchestrator_1 = require("../orchestrator");
const formatter_1 = require("../formatter");
const triggers_1 = require("../triggers");
async function runTechSelectionExample() {
    console.log('═══════════════════════════════════════════════════════════');
    console.log('  MoltCare 多专家决策系统 - 技术选型示例');
    console.log('═══════════════════════════════════════════════════════════\n');
    // ========== 场景1：强制触发多专家讨论 ==========
    console.log('【场景1】用户明确要求多专家讨论技术选型\n');
    const trigger = new triggers_1.DiscussionTrigger();
    const userQuery = '多专家讨论：我们团队想从 Express 迁移到 NestJS，请各专家给出意见';
    console.log(`用户输入: "${userQuery}"\n`);
    // 评估是否触发
    const evaluation = trigger.evaluate(userQuery);
    console.log('触发器评估结果:');
    console.log(`  - 是否触发: ${evaluation.triggered ? '✅ 是' : '❌ 否'}`);
    console.log(`  - 信心度: ${(evaluation.confidence * 100).toFixed(1)}%`);
    console.log(`  - 建议分类: ${evaluation.suggestedCategory || '无'}`);
    console.log(`  - 原因: ${evaluation.reason}\n`);
    // ========== 场景2：执行多专家讨论 ==========
    console.log('【场景2】启动多专家讨论流程\n');
    // 初始化编排器
    const orchestrator = new orchestrator_1.ExpertOrchestrator({
        maxRounds: 2,
        minRounds: 2,
        consensusThreshold: 0.7,
        enableCaptainSynthesis: true,
        discussionMode: 'sequential'
    });
    // 定义讨论主题和上下文
    const topic = '从 Express 迁移到 NestJS 的技术选型决策';
    const context = {
        teamSize: 5,
        teamExperience: 'intermediate',
        existingTechStack: 'Express.js + MongoDB',
        projectScale: 'medium',
        timeline: 'relaxed',
        budget: 'normal',
        currentPainPoints: [
            '缺乏统一的架构规范',
            '代码可维护性下降',
            '新成员上手成本高'
        ]
    };
    console.log(`讨论主题: ${topic}`);
    console.log('上下文信息:');
    console.log(JSON.stringify(context, null, 2));
    console.log('\n开始多轮专家讨论...\n');
    // 执行讨论
    const result = await orchestrator.orchestrate(topic, context);
    // 输出每轮讨论结果
    result.rounds.forEach((round, idx) => {
        console.log(`\n─────────────────────────────────────────────────────────`);
        console.log(`  第 ${round.roundNumber} 轮讨论`);
        console.log(`─────────────────────────────────────────────────────────`);
        round.opinions.forEach(opinion => {
            console.log(`\n👤 ${opinion.expertName} (信心度: ${(opinion.confidence * 100).toFixed(0)}%)`);
            console.log(`   ${opinion.opinion.substring(0, 150)}...`);
            console.log(`\n   关键要点:`);
            opinion.keyPoints.slice(0, 3).forEach(kp => {
                console.log(`   • ${kp.substring(0, 80)}${kp.length > 80 ? '...' : ''}`);
            });
            if (opinion.concerns?.length) {
                console.log(`\n   关注点:`);
                opinion.concerns.slice(0, 2).forEach(c => {
                    console.log(`   ⚠️ ${c.substring(0, 80)}${c.length > 80 ? '...' : ''}`);
                });
            }
        });
    });
    // ========== 场景3：队长总结 ==========
    console.log('\n\n═══════════════════════════════════════════════════════════');
    console.log('  队长综合决策');
    console.log('═══════════════════════════════════════════════════════════\n');
    if (result.finalDecision) {
        const captain = result.finalDecision;
        console.log(`👑 ${captain.expertName} (信心度: ${(captain.confidence * 100).toFixed(0)}%)`);
        console.log(`\n${captain.opinion}\n`);
        console.log('综合建议:');
        captain.recommendations?.forEach((rec, idx) => {
            console.log(`  ${idx + 1}. ${rec}`);
        });
    }
    // ========== 场景4：格式化输出 ==========
    console.log('\n\n═══════════════════════════════════════════════════════════');
    console.log('  生成 MoltCare 标准格式报告');
    console.log('═══════════════════════════════════════════════════════════\n');
    // 格式化为标准格式
    const formatted = formatter_1.DecisionFormatter.format(result, 'technology-selection');
    console.log('决策报告元数据:');
    console.log(`  决策ID: ${formatted.metadata.decisionId}`);
    console.log(`  版本: ${formatted.metadata.version}`);
    console.log(`  时间: ${formatted.metadata.timestamp}`);
    console.log(`  分类: ${formatted.metadata.category}\n`);
    console.log('执行摘要:');
    console.log(`  决策: ${formatted.executiveSummary.decision.substring(0, 100)}...`);
    console.log(`  信心度: ${(formatted.executiveSummary.confidence * 100).toFixed(1)}%`);
    console.log(`  风险等级: ${formatted.executiveSummary.riskLevel}`);
    console.log(`  建议行动: ${formatted.executiveSummary.recommendation}\n`);
    console.log('专家立场汇总:');
    formatted.analysis.expertOpinions.forEach(op => {
        const stanceEmoji = op.stance === 'support' ? '✅' :
            op.stance === 'conditional' ? '✓' :
                op.stance === 'neutral' ? '➖' : '❌';
        console.log(`  ${op.expertName}: ${stanceEmoji} ${op.stance} (${(op.confidence * 100).toFixed(0)}%)`);
    });
    // ========== 场景5：Markdown报告 ==========
    console.log('\n\n═══════════════════════════════════════════════════════════');
    console.log('  Markdown 格式报告（预览）');
    console.log('═══════════════════════════════════════════════════════════\n');
    const markdown = formatter_1.DecisionFormatter.toMarkdown(formatted);
    console.log(markdown.substring(0, 2000));
    console.log('\n... (报告已截断，完整报告约 ' + markdown.length + ' 字符)');
    // ========== 场景6：自动触发测试 ==========
    console.log('\n\n═══════════════════════════════════════════════════════════');
    console.log('  场景6：自动触发测试');
    console.log('═══════════════════════════════════════════════════════════\n');
    const testQueries = [
        '帮我写个简单的Hello World',
        '我们需要设计一个微服务架构',
        'Redis和Memcached哪个好？',
        '系统性能太慢了怎么优化',
        '多专家讨论：数据库选型'
    ];
    console.log('测试不同输入的触发情况:\n');
    for (const query of testQueries) {
        const eval_ = trigger.evaluate(query);
        const status = eval_.triggered ? '🔥 触发' : '➖ 跳过';
        console.log(`${status} [${(eval_.confidence * 100).toFixed(0)}%] "${query.substring(0, 40)}..."`);
        if (eval_.triggered) {
            console.log(`      匹配规则: ${eval_.matchedRules.map(r => r.name).join(', ')}`);
        }
    }
    // ========== 统计信息 ==========
    console.log('\n\n═══════════════════════════════════════════════════════════');
    console.log('  讨论统计');
    console.log('═══════════════════════════════════════════════════════════\n');
    console.log(`总轮次: ${result.rounds.length}`);
    console.log(`总观点数: ${result.summary.totalOpinions}`);
    console.log(`共识度: ${(result.consensusLevel * 100).toFixed(1)}%`);
    console.log(`共识状态: ${result.consensus ? '✅ 已达成' : '⚠️ 未达成'}`);
    console.log(`讨论耗时: ${result.duration}ms`);
    console.log('\n专家参与度:');
    Object.entries(result.summary.expertParticipation).forEach(([name, count]) => {
        console.log(`  ${name}: ${count} 次发言`);
    });
    console.log('\n═══════════════════════════════════════════════════════════');
    console.log('  示例完成！');
    console.log('═══════════════════════════════════════════════════════════\n');
    return { result, formatted, markdown };
}
// 如果直接运行此文件
if (require.main === module) {
    runTechSelectionExample().catch(console.error);
}
//# sourceMappingURL=tech-selection-example.js.map