/**
 * Init Command
 * 初始化 MoltCare 配置和环境
 */
export interface InitOptions {
    force?: boolean;
    yes?: boolean;
    workspace?: string;
}
/**
 * 执行 init 命令
 */
export declare function initCommand(options: InitOptions): Promise<void>;
//# sourceMappingURL=init.d.ts.map