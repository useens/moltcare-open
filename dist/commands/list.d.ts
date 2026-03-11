/**
 * List Command
 * 列出可用的 Packs
 */
export interface ListOptions {
    category?: string;
    installed?: boolean;
    json?: boolean;
}
/**
 * 执行 list 命令
 */
export declare function listCommand(options: ListOptions): Promise<void>;
//# sourceMappingURL=list.d.ts.map