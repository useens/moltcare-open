/**
 * 队长专家 - Captain
 * 负责整合决策、全局最优、权衡取舍
 */
import { BaseExpert, ExpertInput, ExpertOutput } from './base-expert';
export declare class CaptainExpert extends BaseExpert {
    constructor();
    think(input: ExpertInput): Promise<ExpertOutput>;
    /**
     * 综合所有专家观点 - 队长的核心能力
     */
    private synthesizeOpinions;
    private identifyConsensus;
    private identifyDisagreements;
    private assessRiskLevel;
    private assessExecutionDifficulty;
    private assessLongTermValue;
    private formFinalRecommendation;
    private createExecutionPlan;
    private extractKeyConcerns;
    private defineRollbackStrategy;
    private generateFinalSummary;
    private calculateOverallConfidence;
}
//# sourceMappingURL=captain.d.ts.map