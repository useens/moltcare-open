/**
 * 研究员专家 - Researcher
 * 负责数据验证、信息收集、事实核查
 */
import { BaseExpert, ExpertInput, ExpertOutput } from './base-expert';
export declare class ResearcherExpert extends BaseExpert {
    constructor();
    think(input: ExpertInput): Promise<ExpertOutput>;
    private generateResearchOpinion;
}
//# sourceMappingURL=researcher.d.ts.map