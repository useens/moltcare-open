/**
 * Enhanced Configuration System - Phase 5 优化
 *
 * 功能:
 * - 多配置文件支持
 * - 配置合并和继承
 * - 环境变量支持
 * - 配置验证
 * - 实时重载
 * - 用户配置和项目配置分离
 */
import { EventEmitter } from 'events';
export type ConfigSource = 'default' | 'user' | 'project' | 'environment' | 'cli';
export interface ConfigItemMetadata {
    description: string;
    type: 'string' | 'number' | 'boolean' | 'array' | 'object';
    default?: unknown;
    envVar?: string;
    validate?: (value: unknown) => boolean | string;
    deprecated?: boolean;
    deprecatedMessage?: string;
}
export interface ConfigSchema {
    [key: string]: ConfigItemMetadata;
}
export interface ConfigChangeEvent {
    key: string;
    oldValue: unknown;
    newValue: unknown;
    source: ConfigSource;
}
export interface EnhancedMoltCareConfig {
    version: string;
    language: 'zh' | 'en' | 'ja' | 'ko' | 'de' | 'fr' | 'es' | 'ru' | 'ar';
    workspacePath: string;
    packsDir: string;
    logLevel: 'debug' | 'info' | 'warn' | 'error';
    autoUpdate: boolean;
    maxCacheSize: number;
    initialized: boolean;
    lastUpdated: string;
    theme: 'default' | 'dark' | 'light';
    editor: string;
    git: {
        enabled: boolean;
        autoCommit: boolean;
        commitMessage: string;
    };
    packs: {
        registry: string;
        cacheDir: string;
        parallelInstall: boolean;
    };
    templates: {
        engine: 'handlebars' | 'ejs' | 'mustache';
        strictMode: boolean;
        cacheEnabled: boolean;
    };
    network: {
        timeout: number;
        retryCount: number;
        proxy?: string;
    };
    advanced: {
        experimentalFeatures: boolean;
        debugMode: boolean;
        traceMode: boolean;
    };
}
export declare const DEFAULT_CONFIG: EnhancedMoltCareConfig;
export declare const CONFIG_SCHEMA: ConfigSchema;
export declare class EnhancedConfigManager extends EventEmitter {
    private config;
    private userConfigPath;
    private projectConfigPath;
    private sources;
    private watchers;
    private autoReload;
    constructor(options?: {
        userConfigPath?: string;
        projectConfigPath?: string;
        autoReload?: boolean;
    });
    private getDefaultUserConfigPath;
    /**
     * 加载所有配置源
     */
    load(): void;
    /**
     * 从文件加载配置
     */
    private loadFromFile;
    /**
     * 从环境变量加载配置
     */
    private loadFromEnvironment;
    /**
     * 解析配置值
     */
    private parseValue;
    /**
     * 合并配置
     */
    private merge;
    /**
     * 标记配置来源
     */
    private markSource;
    /**
     * 验证配置
     */
    validate(): {
        valid: boolean;
        errors: string[];
    };
    /**
     * 设置配置项
     */
    set<K extends keyof EnhancedMoltCareConfig>(key: K, value: EnhancedMoltCareConfig[K], source?: ConfigSource): void;
    /**
     * 获取配置项
     */
    get<K extends keyof EnhancedMoltCareConfig>(key: K): EnhancedMoltCareConfig[K];
    /**
     * 获取配置来源
     */
    getSource(key: string): ConfigSource | undefined;
    /**
     * 获取所有配置
     */
    getAll(): EnhancedMoltCareConfig;
    /**
     * 批量更新配置
     */
    update(updates: Partial<EnhancedMoltCareConfig>, source?: ConfigSource): void;
    /**
     * 保存用户配置
     */
    save(): boolean;
    /**
     * 获取与默认值不同的配置项
     */
    private getNonDefaultValues;
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
    getConfigPath(type?: 'user' | 'project'): string;
    /**
     * 设置配置文件路径
     */
    setConfigPath(type: 'user' | 'project', filePath: string): void;
    /**
     * 启用配置热重载
     */
    setupWatchers(): void;
    /**
     * 清理文件监听器
     */
    cleanupWatchers(): void;
    /**
     * 获取配置文档
     */
    getDocumentation(): string;
    /**
     * 导出配置
     */
    export(format?: 'yaml' | 'json'): string;
}
export declare function getEnhancedConfig(options?: {
    userConfigPath?: string;
    autoReload?: boolean;
}): EnhancedConfigManager;
export declare function resetEnhancedConfig(): void;
export default EnhancedConfigManager;
//# sourceMappingURL=config-enhanced.d.ts.map