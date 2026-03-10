/**
 * 架构师专家 - Architect
 * 负责系统设计、可维护性、扩展性、风险评估
 */

import { BaseExpert, ExpertInput, ExpertOutput, ExpertProfile } from './base-expert';

export class ArchitectExpert extends BaseExpert {
  constructor() {
    const profile: ExpertProfile = {
      id: 'architect',
      name: '架构师',
      role: 'Architect',
      expertise: [
        '系统设计',
        '可维护性评估',
        '扩展性规划',
        '技术风险管理',
        '模块解耦',
        '技术债务控制'
      ],
      personality: '全局视野、注重平衡、关注长期、追求简洁',
      systemPrompt: `你是一位资深系统架构师，专注于系统的长期健康和可维护性。

你的职责:
1. 评估技术决策对系统架构的影响
2. 识别潜在的技术风险和架构腐化点
3. 权衡短期交付与长期可维护性
4. 确保系统的可扩展性和模块化
5. 评估技术栈与团队能力的匹配度

思考角度:
- 系统一致性：新技术是否与现有架构风格冲突？
- 扩展性：未来3-5年的业务增长如何被支持？
- 可维护性：代码复杂度、测试覆盖率、文档完整性
- 风险：单点故障、供应商锁定、技术债务累积
- 演进路径：从当前状态到目标架构的迁移成本

原则: 好的架构是演进出来的，不是设计出来的，但需要设计来引导演进方向。`
    };
    super(profile);
  }

  async think(input: ExpertInput): Promise<ExpertOutput> {
    const topic = input.topic.toLowerCase();
    
    const opinion = this.generateArchitectureOpinion(topic, input);
    
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

  private generateArchitectureOpinion(topic: string, input: ExpertInput): {
    summary: string;
    keyPoints: string[];
    confidence: number;
    concerns: string[];
    recommendations: string[];
  } {
    const keyPoints: string[] = [];
    const concerns: string[] = [];
    const recommendations: string[] = [];
    
    // 架构分析框架
    keyPoints.push('架构一致性：新技术与现有系统架构风格的兼容性评估');
    keyPoints.push('模块边界：是否支持清晰的领域边界划分');
    keyPoints.push('演进能力：是否支持渐进式改造而非推倒重来');
    
    if (topic.includes('microservice') || topic.includes('微服务')) {
      keyPoints.push('服务粒度：避免过细导致的运维复杂度爆炸');
      keyPoints.push('数据一致性：分布式事务策略选择');
      concerns.push('微服务拆分过早可能导致分布式单体陷阱');
      concerns.push('服务间通信的网络延迟和故障传播风险');
      recommendations.push('建议采用领域驱动设计(DDD)指导服务边界划分');
      recommendations.push('初期可采用模块化单体作为过渡架构');
    }
    
    if (topic.includes('monolith') || topic.includes('单体')) {
      keyPoints.push('模块化设计：通过内部模块边界控制复杂度');
      keyPoints.push('部署效率：单artifact部署简化CI/CD流程');
      concerns.push('代码库膨胀导致的构建和部署时间增长');
      concerns.push('团队扩张后的代码冲突和发布协调成本');
      recommendations.push('建议采用清晰的分层架构和端口适配器模式');
    }
    
    if (topic.includes('cloud') || topic.includes('云')) {
      keyPoints.push('多云策略：避免供应商锁定的架构设计');
      keyPoints.push('弹性设计：自动扩缩容和故障转移机制');
      concerns.push('云服务成本随业务增长可能快速膨胀');
      recommendations.push('建议设计云无关的抽象层，保留迁移灵活性');
    }
    
    // 上下文感知
    if (input.context.existingTechStack) {
      keyPoints.push(`现有技术栈迁移成本：需评估与 ${input.context.existingTechStack} 的集成复杂度`);
    }
    
    if (input.context.teamExperience) {
      const exp = input.context.teamExperience;
      if (exp === 'junior') {
        concerns.push('团队经验水平可能不足以驾驭复杂架构模式');
        recommendations.push('建议优先选择约定优于配置的框架，降低决策负担');
      }
    }
    
    if (input.context.expectedScale) {
      keyPoints.push(`规模适配：架构设计需匹配预期的 ${input.context.expectedScale} 量级`);
    }
    
    const summary = `从架构视角评估，${topic} 的引入需要从系统一致性、演进路径和风险管控三个维度综合考量。` +
      `建议优先保证架构的可逆性，避免过早优化和不必要的复杂度引入。`;
    
    return {
      summary,
      keyPoints,
      confidence: 0.82,
      concerns,
      recommendations
    };
  }
}
