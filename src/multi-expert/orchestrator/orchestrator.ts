/**
 * 专家讨论编排器 - Multi-Expert Orchestrator
 * 负责管理多轮专家讨论的流程
 */

import {
  BaseExpert,
  ExpertInput,
  ExpertOutput,
  DiscussionRound,
  ResearcherExpert,
  ArchitectExpert,
  EngineerExpert,
  CaptainExpert
} from '../experts';

export interface OrchestratorConfig {
  maxRounds: number;
  minRounds: number;
  consensusThreshold: number; // 0-1，共识阈值
  enableCaptainSynthesis: boolean;
  discussionMode: 'sequential' | 'parallel' | 'adaptive';
}

export interface OrchestratorResult {
  topic: string;
  rounds: DiscussionRound[];
  finalDecision?: ExpertOutput;
  consensus: boolean;
  consensusLevel: number; // 0-1
  duration: number; // 毫秒
  summary: {
    totalOpinions: number;
    expertParticipation: Record<string, number>;
    keyConsensusAreas: string[];
    keyDisagreements: string[];
  };
}

export class ExpertOrchestrator {
  private experts: BaseExpert[] = [];
  private config: OrchestratorConfig;
  private rounds: DiscussionRound[] = [];

  constructor(config?: Partial<OrchestratorConfig>) {
    this.config = {
      maxRounds: config?.maxRounds || 3,
      minRounds: config?.minRounds || 2,
      consensusThreshold: config?.consensusThreshold || 0.7,
      enableCaptainSynthesis: config?.enableCaptainSynthesis !== false,
      discussionMode: config?.discussionMode || 'adaptive'
    };
    
    this.initializeDefaultExperts();
  }

  /**
   * 初始化默认的4位专家
   */
  private initializeDefaultExperts(): void {
    this.experts = [
      new ResearcherExpert(),
      new ArchitectExpert(),
      new EngineerExpert()
      // Captain 在最终轮才加入
    ];
  }

  /**
   * 注册自定义专家
   */
  registerExpert(expert: BaseExpert): void {
    this.experts.push(expert);
  }

  /**
   * 获取已注册的专家列表
   */
  getExperts(): BaseExpert[] {
    return [...this.experts];
  }

  /**
   * 执行多轮专家讨论
   */
  async orchestrate(topic: string, context: Record<string, any> = {}): Promise<OrchestratorResult> {
    const startTime = Date.now();
    this.rounds = [];

    // 根据讨论模式选择执行策略
    if (this.config.discussionMode === 'parallel') {
      await this.runParallelDiscussion(topic, context);
    } else {
      await this.runSequentialDiscussion(topic, context);
    }

    // 添加队长总结轮（如果启用）
    let finalDecision: ExpertOutput | undefined;
    if (this.config.enableCaptainSynthesis) {
      finalDecision = await this.runCaptainSynthesis(topic, context);
    }

    const duration = Date.now() - startTime;
    
    return this.buildResult(topic, finalDecision, duration);
  }

  /**
   * 顺序讨论模式 - 每轮依次收集各专家意见
   */
  private async runSequentialDiscussion(topic: string, context: Record<string, any>): Promise<void> {
    for (let roundNum = 1; roundNum <= this.config.maxRounds; roundNum++) {
      const input: ExpertInput = {
        topic,
        context,
        previousRounds: this.rounds,
        currentRound: roundNum,
        maxRounds: this.config.maxRounds
      };

      // 收集本轮所有专家意见
      const opinions: ExpertOutput[] = [];
      
      for (const expert of this.experts) {
        const opinion = await expert.think(input);
        opinions.push(opinion);
      }

      const round: DiscussionRound = {
        roundNumber: roundNum,
        opinions
      };

      this.rounds.push(round);

      // 检查是否达成早期共识
      if (roundNum >= this.config.minRounds && this.checkConsensus(round)) {
        console.log(`[Orchestrator] 第${roundNum}轮达成早期共识，提前结束讨论`);
        break;
      }

      // 自适应模式：分析是否需要额外轮次
      if (this.config.discussionMode === 'adaptive' && roundNum >= this.config.minRounds) {
        const consensusLevel = this.calculateConsensusLevel(round);
        if (consensusLevel >= this.config.consensusThreshold) {
          console.log(`[Orchestrator] 共识度 ${(consensusLevel * 100).toFixed(1)}% 超过阈值，结束讨论`);
          break;
        }
      }
    }
  }

  /**
   * 并行讨论模式 - 所有专家同时提供意见
   */
  private async runParallelDiscussion(topic: string, context: Record<string, any>): Promise<void> {
    // 并行模式下只进行一轮深入讨论
    const input: ExpertInput = {
      topic,
      context,
      previousRounds: [],
      currentRound: 1,
      maxRounds: 1
    };

    // 并行收集所有专家意见
    const opinionPromises = this.experts.map(expert => expert.think(input));
    const opinions = await Promise.all(opinionPromises);

    const round: DiscussionRound = {
      roundNumber: 1,
      opinions
    };

    this.rounds.push(round);
  }

  /**
   * 运行队长总结轮
   */
  private async runCaptainSynthesis(topic: string, context: Record<string, any>): Promise<ExpertOutput> {
    const captain = new CaptainExpert();
    
    const input: ExpertInput = {
      topic,
      context,
      previousRounds: this.rounds,
      currentRound: this.rounds.length + 1,
      maxRounds: this.rounds.length + 1
    };

    return await captain.think(input);
  }

  /**
   * 检查是否达成共识
   */
  private checkConsensus(round: DiscussionRound): boolean {
    const confidenceScores = round.opinions.map(o => o.confidence);
    const avgConfidence = confidenceScores.reduce((a, b) => a + b, 0) / confidenceScores.length;
    
    // 共识条件：平均信心度超过阈值，且分歧不大
    const confidenceVariance = this.calculateVariance(confidenceScores);
    
    return avgConfidence >= this.config.consensusThreshold && confidenceVariance < 0.1;
  }

  /**
   * 计算共识程度（0-1）
   */
  private calculateConsensusLevel(round: DiscussionRound): number {
    const confidenceScores = round.opinions.map(o => o.confidence);
    const avgConfidence = confidenceScores.reduce((a, b) => a + b, 0) / confidenceScores.length;
    
    // 信心度越高且分歧越小，共识度越高
    const variance = this.calculateVariance(confidenceScores);
    const agreementFactor = Math.max(0, 1 - variance * 5);
    
    return avgConfidence * agreementFactor;
  }

  /**
   * 计算方差
   */
  private calculateVariance(values: number[]): number {
    if (values.length < 2) return 0;
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const squaredDiffs = values.map(v => Math.pow(v - mean, 2));
    return squaredDiffs.reduce((a, b) => a + b, 0) / values.length;
  }

  /**
   * 构建最终结果
   */
  private buildResult(topic: string, finalDecision: ExpertOutput | undefined, duration: number): OrchestratorResult {
    const allOpinions = this.rounds.flatMap(r => r.opinions);
    
    // 统计专家参与度
    const participation: Record<string, number> = {};
    allOpinions.forEach(o => {
      participation[o.expertName] = (participation[o.expertName] || 0) + 1;
    });

    // 提取共识和分歧领域
    const consensusAreas = this.extractConsensusAreas(allOpinions);
    const disagreements = this.extractDisagreements(allOpinions);

    // 计算最终共识度
    const lastRound = this.rounds[this.rounds.length - 1];
    const consensusLevel = lastRound ? this.calculateConsensusLevel(lastRound) : 0;

    return {
      topic,
      rounds: this.rounds,
      finalDecision,
      consensus: consensusLevel >= this.config.consensusThreshold,
      consensusLevel,
      duration,
      summary: {
        totalOpinions: allOpinions.length,
        expertParticipation: participation,
        keyConsensusAreas: consensusAreas,
        keyDisagreements: disagreements
      }
    };
  }

  /**
   * 提取共识领域
   */
  private extractConsensusAreas(opinions: ExpertOutput[]): string[] {
    const areas: string[] = [];
    
    // 分析所有关键点的共同主题
    const allKeyPoints = opinions.flatMap(o => o.keyPoints);
    
    if (allKeyPoints.some(kp => kp.includes('风险'))) areas.push('风险意识');
    if (allKeyPoints.some(kp => kp.includes('验证') || kp.includes('测试'))) areas.push('验证必要性');
    if (allKeyPoints.some(kp => kp.includes('团队') || kp.includes('学习'))) areas.push('团队能力考量');
    if (allKeyPoints.some(kp => kp.includes('成本'))) areas.push('成本控制');
    
    return areas;
  }

  /**
   * 提取分歧点
   */
  private extractDisagreements(opinions: ExpertOutput[]): string[] {
    const disagreements: string[] = [];
    
    // 检测信心度的显著差异
    const confidenceScores = opinions.map(o => o.confidence);
    const variance = this.calculateVariance(confidenceScores);
    
    if (variance > 0.05) {
      disagreements.push('对解决方案的信心程度存在差异');
    }
    
    return disagreements;
  }

  /**
   * 获取当前讨论历史
   */
  getDiscussionHistory(): DiscussionRound[] {
    return [...this.rounds];
  }

  /**
   * 重置编排器状态
   */
  reset(): void {
    this.rounds = [];
  }
}
