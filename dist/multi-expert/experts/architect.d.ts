/**
 * 架构师专家 - Architect
 * 负责系统设计、可维护性、扩展性、风险评估
 */
import { BaseExpert, ExpertInput, ExpertOutput } from './base-expert';
export declare class ArchitectExpert extends BaseExpert {
    constructor();
    think(input: ExpertInput): Promise<ExpertOutput>;
    private generateArchitectureOpinion;
}
//# sourceMappingURL=architect.d.ts.map