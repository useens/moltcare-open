interface ReviewComment {
    line?: number;
    severity: 'error' | 'warning' | 'info';
    message: string;
    suggestion?: string;
}
interface FileReview {
    file: string;
    score: number;
    comments: ReviewComment[];
    issues: ReviewComment[];
}
/**
 * 代码评审器
 *
 * @description 自动检测代码中的常见问题
 * @author OracleSensen
 * @since Phase 2
 */
export declare class CodeReviewer {
    reviewFile(filePath: string): Promise<FileReview>;
    reviewDirectory(dir: string): Promise<FileReview[]>;
    generateReport(reviews: FileReview[], format?: 'markdown' | 'json'): string;
    /**
     * 计算代码评分
     */
    calculateScore(issues: ReviewComment[], lines: number): number;
}
export {};
//# sourceMappingURL=code-reviewer.d.ts.map