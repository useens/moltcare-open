/**
 * MoltCare Configuration System (TypeScript)
 * 核心配置管理模块
 */
export interface MoltCareConfig {
    version: string;
    language: 'zh' | 'en';
    workspacePath: string;
    packsDir: string;
    logLevel: 'debug' | 'info' | 'warn' | 'error';
    autoUpdate: boolean;
    maxCacheSize: number;
    initialized: boolean;
    lastUpdated: string;
}
export declare const DEFAULT_CONFIG: MoltCareConfig;
export declare class ConfigManager {
    private configPath;
    private config;
    constructor(configPath?: string);
    private getDefaultConfigPath;
    /**
     * 获取配置目录路径
     */
    getConfigDir(): string;
    /**
     * 从文件加载配置
     */
    load(): boolean;
    /**
     * 保存配置到文件
     */
    save(): boolean;
    /**
     * 获取配置项
     */
    get<K extends keyof MoltCareConfig>(key: K): MoltCareConfig[K];
    /**
     * 设置配置项
     */
    set<K extends keyof MoltCareConfig>(key: K, value: MoltCareConfig[K]): void;
    /**
     * 获取所有配置
     */
    getAll(): MoltCareConfig;
    /**
     * 批量更新配置
     */
    update(updates: Partial<MoltCareConfig>): void;
    /**
     * 重置为默认配置
     */
    reset(): void;
    /**
     * 检查是否已初始化
     */
    isInitialized(): boolean;
    /**
     * 标记为已初始化
     */
    markInitialized(): void;
    /**
     * 获取配置文件路径
     */
    getConfigPath(): string;
    /**
     * 检查OpenClaw环境
     */
    checkOpenClawEnv(): {
        exists: boolean;
        workspacePath?: string;
        details: string[];
    };
}
export declare function getConfig(configPath?: string): ConfigManager;
export declare function resetConfig(): void;
//# sourceMappingURL=config.d.ts.map