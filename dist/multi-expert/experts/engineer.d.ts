/**
 * 工程师专家 - Engineer
 * 负责实现评估、工期估算、成本分析
 */
import { BaseExpert, ExpertInput, ExpertOutput } from './base-expert';
export declare class EngineerExpert extends BaseExpert {
    constructor();
    think(input: ExpertInput): Promise<ExpertOutput>;
    private generateEngineerOpinion;
    private estimateCost;
}
//# sourceMappingURL=engineer.d.ts.map