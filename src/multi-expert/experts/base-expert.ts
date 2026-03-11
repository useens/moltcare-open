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
  confidence: number; // 0-1
  concerns?: string[];
  recommendations?: string[];
}

export interface DiscussionRound {
  roundNumber: number;
  opinions: ExpertOutput[];
  consensus?: string;
  disagreements?: string[];
}

export abstract class BaseExpert {
  protected profile: ExpertProfile;

  constructor(profile: ExpertProfile) {
    this.profile = profile;
  }

  getProfile(): ExpertProfile {
    return this.profile;
  }

  getId(): string {
    return this.profile.id;
  }

  getName(): string {
    return this.profile.name;
  }

  /**
   * 核心思考方法 - 每个专家子类必须实现
   */
  abstract think(input: ExpertInput): Promise<ExpertOutput>;

  /**
   * 生成专家思考的系统提示词
   */
  protected generateSystemPrompt(): string {
    return `${this.profile.systemPrompt}

你是 **${this.profile.name}** (${this.profile.role})。
专业领域: ${this.profile.expertise.join(', ')}
性格特点: ${this.profile.personality}

思考原则:
1. 从你的专业角度提供独特见解
2. 基于事实和数据，避免主观臆断
3. 明确指出风险和机会
4. 与其他专家观点形成互补或建设性冲突
5. 输出必须结构化，包含关键要点和信心指数

输出格式:
- 观点摘要
- 关键要点 (bullet points)
- 信心指数 (0-1)
- 关注点/风险 (可选)
- 建议 (可选)`;
  }

  /**
   * 格式化输入为提示词
   */
  protected formatInput(input: ExpertInput): string {
    let prompt = `# 讨论主题\n${input.topic}\n\n`;
    
    prompt += `# 上下文信息\n${JSON.stringify(input.context, null, 2)}\n\n`;
    
    if (input.previousRounds && input.previousRounds.length > 0) {
      prompt += `# 前几轮讨论摘要\n`;
      input.previousRounds.forEach(round => {
        prompt += `## 第${round.roundNumber}轮\n`;
        round.opinions.forEach(op => {
          prompt += `- ${op.expertName}: ${op.opinion.substring(0, 200)}...\n`;
        });
      });
      prompt += '\n';
    }
    
    prompt += `# 当前轮次\n${input.currentRound} / ${input.maxRounds}\n\n`;
    prompt += `请从${this.profile.role}的角度提供专业意见。`;
    
    return prompt;
  }
}
