/**
 * 队长专家 - Captain
 * 负责整合决策、全局最优、权衡取舍
 */

import { BaseExpert, ExpertInput, ExpertOutput, ExpertProfile, DiscussionRound } from './base-expert';

export class CaptainExpert extends BaseExpert {
  constructor() {
    const profile: ExpertProfile = {
      id: 'captain',
      name: '队长',
      role: 'Captain',
      expertise: [
        '决策整合',
        '全局优化',
        '权衡取舍',
        '冲突调解',
        '优先级排序',
        '战略对齐'
      ],
      personality: '果断、全局观、平衡各方、结果导向',
      systemPrompt: `你是一位技术团队的队长/CTO，负责在多方意见中做出最终决策。

你的职责:
1. 整合各专家的观点，识别共识和分歧
2. 在冲突中找到平衡点或做出果断决策
3. 确保决策与业务目标和团队能力对齐
4. 明确优先级和阶段性里程碑
5. 承担最终决策的责任

思考角度:
- 全局最优：不是局部最优的简单叠加
- 风险收益：评估不同选择的期望值
- 团队执行：决策能否被团队有效执行？
- 时间压力：何时需要更多信息，何时需要果断决策？
- 可逆性：决策错误时能否低成本调整？

原则: 完美的决策不存在，好的决策需要明确的标准、充分的信息和承担责任的勇气。`
    };
    super(profile);
  }

  async think(input: ExpertInput): Promise<ExpertOutput> {
    const topic = input.topic;
    
    // 队长需要综合所有专家的观点
    const synthesis = this.synthesizeOpinions(input);
    
    return {
      expertId: this.profile.id,
      expertName: this.profile.name,
      opinion: synthesis.summary,
      keyPoints: synthesis.keyPoints,
      confidence: synthesis.confidence,
      concerns: synthesis.concerns,
      recommendations: synthesis.recommendations
    };
  }

  /**
   * 综合所有专家观点 - 队长的核心能力
   */
  private synthesizeOpinions(input: ExpertInput): {
    summary: string;
    keyPoints: string[];
    confidence: number;
    concerns: string[];
    recommendations: string[];
  } {
    const keyPoints: string[] = [];
    const concerns: string[] = [];
    const recommendations: string[] = [];
    
    // 分析前几轮的专家观点
    const allOpinions: ExpertOutput[] = [];
    input.previousRounds.forEach(round => {
      allOpinions.push(...round.opinions);
    });
    
    // 按专家类型分组观点
    const researcherOpinions = allOpinions.filter(o => o.expertId === 'researcher');
    const architectOpinions = allOpinions.filter(o => o.expertId === 'architect');
    const engineerOpinions = allOpinions.filter(o => o.expertId === 'engineer');
    
    // 识别共识
    const consensusAreas = this.identifyConsensus(allOpinions);
    keyPoints.push(`各方共识: ${consensusAreas.join(', ')}`);
    
    // 识别分歧
    const disagreements = this.identifyDisagreements(allOpinions);
    if (disagreements.length > 0) {
      keyPoints.push(`核心分歧: ${disagreements.join(', ')}`);
    }
    
    // 综合各维度评估
    keyPoints.push('风险评级: ' + this.assessRiskLevel(allOpinions));
    keyPoints.push('执行难度: ' + this.assessExecutionDifficulty(allOpinions));
    keyPoints.push('长期价值: ' + this.assessLongTermValue(allOpinions));
    
    // 形成最终建议
    const finalRecommendation = this.formFinalRecommendation(input, allOpinions);
    recommendations.push(finalRecommendation);
    
    // 执行计划
    const executionPlan = this.createExecutionPlan(input, allOpinions);
    recommendations.push(`执行路径: ${executionPlan}`);
    
    // 风险缓解
    concerns.push(...this.extractKeyConcerns(allOpinions));
    
    // 回滚策略
    recommendations.push(`回滚策略: ${this.defineRollbackStrategy(input)}`);
    
    const summary = this.generateFinalSummary(input.topic, allOpinions, finalRecommendation);
    
    return {
      summary,
      keyPoints,
      confidence: this.calculateOverallConfidence(allOpinions),
      concerns,
      recommendations
    };
  }

  private identifyConsensus(opinions: ExpertOutput[]): string[] {
    const consensus: string[] = [];
    
    // 分析所有专家的关键点，找出共同提到的主题
    const allKeyPoints = opinions.flatMap(o => o.keyPoints);
    
    // 简单的共识检测（实际实现可以更复杂）
    if (allKeyPoints.some(kp => kp.includes('验证') || kp.includes('数据'))) {
      consensus.push('需要充分验证技术假设');
    }
    if (allKeyPoints.some(kp => kp.includes('风险') || kp.includes('成本'))) {
      consensus.push('需要评估风险和成本');
    }
    if (allKeyPoints.some(kp => kp.includes('团队') || kp.includes('学习'))) {
      consensus.push('需要考虑团队能力匹配度');
    }
    
    return consensus.length > 0 ? consensus : ['需要更多信息形成共识'];
  }

  private identifyDisagreements(opinions: ExpertOutput[]): string[] {
    const disagreements: string[] = [];
    
    // 检测不同专家之间的潜在分歧
    const researcherConf = opinions.find(o => o.expertId === 'researcher')?.confidence || 0.5;
    const engineerConf = opinions.find(o => o.expertId === 'engineer')?.confidence || 0.5;
    
    if (Math.abs(researcherConf - engineerConf) > 0.2) {
      disagreements.push('对技术成熟度的判断存在差异');
    }
    
    return disagreements;
  }

  private assessRiskLevel(opinions: ExpertOutput[]): string {
    const concerns = opinions.flatMap(o => o.concerns || []).length;
    if (concerns > 5) return '高风险';
    if (concerns > 2) return '中等风险';
    return '低风险';
  }

  private assessExecutionDifficulty(opinions: ExpertOutput[]): string {
    const engineerOpinion = opinions.find(o => o.expertId === 'engineer');
    if (!engineerOpinion) return '待评估';
    
    const concerns = engineerOpinion.concerns?.length || 0;
    if (concerns > 3) return '困难';
    if (concerns > 1) return '适中';
    return '容易';
  }

  private assessLongTermValue(opinions: ExpertOutput[]): string {
    const architectOpinion = opinions.find(o => o.expertId === 'architect');
    if (!architectOpinion) return '待评估';
    
    const keyPoints = architectOpinion.keyPoints.join(' ');
    if (keyPoints.includes('演进') || keyPoints.includes('扩展')) {
      return '高';
    }
    return '中等';
  }

  private formFinalRecommendation(input: ExpertInput, opinions: ExpertOutput[]): string {
    const topic = input.topic.toLowerCase();
    
    // 基于综合评估形成建议
    const riskLevel = this.assessRiskLevel(opinions);
    const executionDifficulty = this.assessExecutionDifficulty(opinions);
    
    if (riskLevel === '低风险' && executionDifficulty === '容易') {
      return `建议采用：${topic} 是合适的选择，风险可控且实施难度较低`;
    } else if (riskLevel === '高风险') {
      return `谨慎采用：建议先进行小规模POC验证，降低风险后再全面推广`;
    } else {
      return `条件采用：${topic} 可以使用，但需要满足特定前提条件并制定风险缓解计划`;
    }
  }

  private createExecutionPlan(input: ExpertInput, opinions: ExpertOutput[]): string {
    const steps: string[] = [];
    
    steps.push('阶段1: 技术验证 - 核心功能POC');
    steps.push('阶段2: 团队培训 - 知识传递和技能建设');
    steps.push('阶段3: 试点实施 - 非核心业务试用');
    steps.push('阶段4: 全面推广 - 监控和优化');
    
    return steps.join(' → ');
  }

  private extractKeyConcerns(opinions: ExpertOutput[]): string[] {
    const allConcerns = opinions.flatMap(o => o.concerns || []);
    // 去重并返回前3个主要关注点
    return [...new Set(allConcerns)].slice(0, 3);
  }

  private defineRollbackStrategy(input: ExpertInput): string {
    return '保持旧系统并行运行至少一个迭代周期，数据双写，逐步切流，保留一键回滚能力';
  }

  private generateFinalSummary(topic: string, opinions: ExpertOutput[], recommendation: string): string {
    const avgConfidence = this.calculateOverallConfidence(opinions);
    
    return `综合各位专家的意见，针对 "${topic}" 的决策如下：

${recommendation}

整体信心指数: ${(avgConfidence * 100).toFixed(1)}%

本决策基于研究员的数据分析、架构师的系统设计评估、工程师的实现可行性分析，经过权衡后形成。建议在执行过程中持续监控关键指标，必要时触发重新评估。`;
  }

  private calculateOverallConfidence(opinions: ExpertOutput[]): number {
    if (opinions.length === 0) return 0.5;
    const avgConfidence = opinions.reduce((sum, o) => sum + o.confidence, 0) / opinions.length;
    return Math.round(avgConfidence * 100) / 100;
  }
}
