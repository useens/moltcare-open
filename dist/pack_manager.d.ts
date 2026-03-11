/**
 * Pack Manager (TypeScript)
 * Pack 扫描和管理功能
 */
export interface PackManifest {
    name: string;
    version: string;
    title?: string;
    description?: string;
    author?: string;
    category?: string;
    priority?: number;
    isCore?: boolean;
    createdAt?: string;
    templates?: PackTemplate[];
    scripts?: {
        apply?: string;
        preApply?: string;
        postApply?: string;
    };
    dependencies?: string[];
    config?: {
        backupExisting?: boolean;
        allowOverwrite?: boolean;
        validateTarget?: boolean;
    };
}
export interface PackTemplate {
    file: string;
    target: string;
    required?: boolean;
    description?: string;
    variables?: Record<string, string>;
}
export interface PackInfo {
    name: string;
    version: string;
    title?: string;
    description?: string;
    author?: string;
    category?: string;
    isCore?: boolean;
    manifest: PackManifest;
    path: string;
    installed: boolean;
    installDate?: string;
}
export interface PackIndexEntry {
    version: string;
    installDate: string;
    manifest: PackManifest;
    path: string;
    active: boolean;
}
export interface PackIndex {
    updatedAt: string;
    packs: Record<string, PackIndexEntry>;
}
export declare class PackManager {
    private packsDir;
    private indexPath;
    private index;
    constructor(packsDir: string);
    /**
     * 加载索引
     */
    private loadIndex;
    /**
     * 保存索引
     */
    private saveIndex;
    /**
     * 净化pack名称（安全检查）
     */
    sanitizePackName(name: string): {
        valid: boolean;
        name?: string;
        error?: string;
    };
    /**
     * 扫描可用的 packs
     */
    scanPacks(): PackInfo[];
    /**
     * 获取指定 pack
     */
    getPack(name: string): PackInfo | undefined;
    /**
     * 检查 pack 是否已安装
     */
    isInstalled(name: string): boolean;
    /**
     * 获取所有 pack 名称
     */
    getPackNames(): string[];
    /**
     * 获取已分类的 packs
     */
    getPacksByCategory(): Record<string, PackInfo[]>;
    /**
     * 渲染模板
     */
    renderTemplate(templatePath: string, variables: Record<string, unknown>): string;
    /**
     * 安装 pack（标记为已安装）
     */
    install(name: string): boolean;
    /**
     * 获取所有已安装 pack 名称
     */
    getInstalledNames(): string[];
    /**
     * 获取索引
     */
    getIndex(): PackIndex;
}
//# sourceMappingURL=pack_manager.d.ts.map