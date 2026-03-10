/**
 * 专家讨论编排器 - Multi-Expert Orchestrator
 * 负责管理多轮专家讨论的流程
 */
import { BaseExpert, ExpertOutput, DiscussionRound } from '../experts';
export interface OrchestratorConfig {
    maxRounds: number;
    minRounds: number;
    consensusThreshold: number;
    enableCaptainSynthesis: boolean;
    discussionMode: 'sequential' | 'parallel' | 'adaptive';
}
export interface OrchestratorResult {
    topic: string;
    rounds: DiscussionRound[];
    finalDecision?: ExpertOutput;
    consensus: boolean;
    consensusLevel: number;
    duration: number;
    summary: {
        totalOpinions: number;
        expertParticipation: Record<string, number>;
        keyConsensusAreas: string[];
        keyDisagreements: string[];
    };
}
export declare class ExpertOrchestrator {
    private experts;
    private config;
    private rounds;
    constructor(config?: Partial<OrchestratorConfig>);
    /**
     * 初始化默认的4位专家
     */
    private initializeDefaultExperts;
    /**
     * 注册自定义专家
     */
    registerExpert(expert: BaseExpert): void;
    /**
     * 获取已注册的专家列表
     */
    getExperts(): BaseExpert[];
    /**
     * 执行多轮专家讨论
     */
    orchestrate(topic: string, context?: Record<string, any>): Promise<OrchestratorResult>;
    /**
     * 顺序讨论模式 - 每轮依次收集各专家意见
     */
    private runSequentialDiscussion;
    /**
     * 并行讨论模式 - 所有专家同时提供意见
     */
    private runParallelDiscussion;
    /**
     * 运行队长总结轮
     */
    private runCaptainSynthesis;
    /**
     * 检查是否达成共识
     */
    private checkConsensus;
    /**
     * 计算共识程度（0-1）
     */
    private calculateConsensusLevel;
    /**
     * 计算方差
     */
    private calculateVariance;
    /**
     * 构建最终结果
     */
    private buildResult;
    /**
     * 提取共识领域
     */
    private extractConsensusAreas;
    /**
     * 提取分歧点
     */
    private extractDisagreements;
    /**
     * 获取当前讨论历史
     */
    getDiscussionHistory(): DiscussionRound[];
    /**
     * 重置编排器状态
     */
    reset(): void;
}
//# sourceMappingURL=orchestrator.d.ts.map