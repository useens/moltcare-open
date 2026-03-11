/**
 * Apply Command
 * 应用 Pack 模板到工作区
 */
export interface ApplyOptions {
    force?: boolean;
    dryRun?: boolean;
    yes?: boolean;
}
/**
 * 执行 apply 命令
 */
export declare function applyCommand(packName: string, options: ApplyOptions): Promise<void>;
//# sourceMappingURL=apply.d.ts.map