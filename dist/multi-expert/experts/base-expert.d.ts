/**
 * 专家基类 - 所有专家角色的抽象基类
 * MoltCare 多专家决策系统核心
 */
export interface ExpertProfile {
    id: string;
    name: string;
    role: string;
    expertise: string[];
    personality: string;
    systemPrompt: string;
}
export interface ExpertInput {
    topic: string;
    context: Record<string, any>;
    previousRounds: DiscussionRound[];
    currentRound: number;
    maxRounds: number;
}
export interface ExpertOutput {
    expertId: string;
    expertName: string;
    opinion: string;
    keyPoints: string[];
    confidence: number;
    concerns?: string[];
    recommendations?: string[];
}
export interface DiscussionRound {
    roundNumber: number;
    opinions: ExpertOutput[];
    consensus?: string;
    disagreements?: string[];
}
export declare abstract class BaseExpert {
    protected profile: ExpertProfile;
    constructor(profile: ExpertProfile);
    getProfile(): ExpertProfile;
    getId(): string;
    getName(): string;
    /**
     * 核心思考方法 - 每个专家子类必须实现
     */
    abstract think(input: ExpertInput): Promise<ExpertOutput>;
    /**
     * 生成专家思考的系统提示词
     */
    protected generateSystemPrompt(): string;
    /**
     * 格式化输入为提示词
     */
    protected formatInput(input: ExpertInput): string;
}
//# sourceMappingURL=base-expert.d.ts.map