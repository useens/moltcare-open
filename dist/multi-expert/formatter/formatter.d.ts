/**
 * MoltCare 标准决策输出格式化器
 * 将多专家讨论结果格式化为统一的标准输出格式
 */
import { OrchestratorResult } from '../orchestrator';
import { ExpertOutput, DiscussionRound } from '../experts';
export interface MoltCareDecisionFormat {
    metadata: {
        version: string;
        timestamp: string;
        decisionId: string;
        topic: string;
        category: DecisionCategory;
    };
    executiveSummary: {
        decision: string;
        confidence: number;
        riskLevel: 'low' | 'medium' | 'high' | 'critical';
        urgency: 'immediate' | 'short-term' | 'medium-term' | 'long-term';
        recommendation: 'proceed' | 'proceed-with-caution' | 'delay' | 'reject';
    };
    analysis: {
        consensusLevel: number;
        consensusReached: boolean;
        expertOpinions: ExpertOpinionSummary[];
        keyFactors: KeyFactor[];
        riskAssessment: RiskItem[];
    };
    executionPlan: {
        phases: ExecutionPhase[];
        milestones: Milestone[];
        rollbackStrategy: string;
        successCriteria: string[];
    };
    appendix: {
        discussionRounds: DiscussionRound[];
        fullExpertOutputs: ExpertOutput[];
        statistics: DecisionStatistics;
    };
}
type DecisionCategory = 'technology-selection' | 'architecture-design' | 'security-assessment' | 'performance-optimization' | 'migration-planning' | 'cost-optimization' | 'team-organization' | 'process-improvement';
interface ExpertOpinionSummary {
    expertId: string;
    expertName: string;
    role: string;
    stance: 'support' | 'neutral' | 'oppose' | 'conditional';
    keyPoints: string[];
    confidence: number;
}
interface KeyFactor {
    factor: string;
    impact: 'positive' | 'negative' | 'neutral';
    weight: number;
    evidence: string;
}
interface RiskItem {
    risk: string;
    probability: 'low' | 'medium' | 'high';
    impact: 'low' | 'medium' | 'high' | 'critical';
    mitigation: string;
    owner: string;
}
interface ExecutionPhase {
    name: string;
    duration: string;
    tasks: string[];
    deliverables: string[];
    dependencies: string[];
}
interface Milestone {
    name: string;
    targetDate: string;
    criteria: string[];
    goNoGoDecision: boolean;
}
interface DecisionStatistics {
    totalRounds: number;
    totalExperts: number;
    totalOpinions: number;
    averageConfidence: number;
    discussionDuration: number;
}
export declare class DecisionFormatter {
    private static readonly VERSION;
    /**
     * 将编排器结果格式化为 MoltCare 标准格式
     */
    static format(result: OrchestratorResult, category?: DecisionCategory): MoltCareDecisionFormat;
    /**
     * 格式化为 Markdown 报告（人类可读）
     */
    static toMarkdown(format: MoltCareDecisionFormat): string;
    /**
     * 格式化为 JSON（机器可读）
     */
    static toJSON(format: MoltCareDecisionFormat): string;
    private static buildMetadata;
    private static buildExecutiveSummary;
    private static buildAnalysis;
    private static buildExecutionPlan;
    private static buildAppendix;
    private static generateDecisionId;
    private static calculateRiskLevel;
    private static determineRecommendation;
    private static getRoleName;
    private static determineStance;
    private static extractKeyFactors;
    private static extractRisks;
    private static translateRiskLevel;
    private static translateUrgency;
    private static translateRecommendation;
    private static translateStance;
}
export {};
//# sourceMappingURL=formatter.d.ts.map