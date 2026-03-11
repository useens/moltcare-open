/**
 * Enhanced Template System - Phase 5 优化
 *
 * 功能:
 * - Handlebars 模板引擎集成
 * - 内置 helpers 和 partials
 * - 变量验证和类型检查
 * - 条件渲染支持
 * - 模板缓存
 * - 多语言模板支持
 */
import Handlebars from 'handlebars';
export interface TemplateMetadata {
    name: string;
    description?: string;
    version?: string;
    variables: TemplateVariable[];
    partials?: string[];
    helpers?: string[];
}
export interface TemplateVariable {
    name: string;
    type: 'string' | 'number' | 'boolean' | 'array' | 'object';
    required: boolean;
    default?: unknown;
    description?: string;
    validation?: {
        pattern?: string;
        min?: number;
        max?: number;
        enum?: string[];
    };
}
export interface RenderOptions {
    variables: Record<string, unknown>;
    partials?: Record<string, string>;
    helpers?: Record<string, Handlebars.HelperDelegate>;
    strict?: boolean;
    cache?: boolean;
}
export interface RenderResult {
    content: string;
    success: boolean;
    errors?: string[];
    warnings?: string[];
    missingVariables?: string[];
}
export declare class TemplateEngine {
    private static instance;
    private handlebars;
    private registeredHelpers;
    private registeredPartials;
    private constructor();
    static getInstance(): TemplateEngine;
    /**
     * 注册内置 helpers
     */
    private registerBuiltInHelpers;
    /**
     * 注册内置 partials
     */
    private registerBuiltInPartials;
    /**
     * 注册 helper
     */
    registerHelper(name: string, fn: Handlebars.HelperDelegate): void;
    /**
     * 注册 partial
     */
    registerPartial(name: string, content: string): void;
    /**
     * 从文件注册 partial
     */
    registerPartialFromFile(name: string, filePath: string): void;
    /**
     * 获取已注册的 helpers
     */
    getRegisteredHelpers(): string[];
    /**
     * 获取已注册的 partials
     */
    getRegisteredPartials(): string[];
    /**
     * 编译模板
     */
    compile(source: string, cacheKey?: string): Handlebars.TemplateDelegate;
    /**
     * 从文件编译模板
     */
    compileFromFile(filePath: string, useCache?: boolean): Handlebars.TemplateDelegate;
    /**
     * 渲染模板
     */
    render(source: string, options: RenderOptions): RenderResult;
    /**
     * 从文件渲染模板
     */
    renderFile(filePath: string, options: RenderOptions): RenderResult;
    /**
     * 提取模板中的变量
     */
    extractVariables(source: string): string[];
    /**
     * 检查是否是 helper 调用
     */
    private isHelper;
    /**
     * 验证变量
     */
    validateVariables(variables: Record<string, unknown>, definitions: TemplateVariable[]): {
        valid: boolean;
        errors: string[];
    };
    /**
     * 加载模板配置
     */
    loadTemplateConfig(filePath: string): TemplateMetadata;
    /**
     * 批量渲染模板
     */
    renderBatch(templates: Array<{
        source: string;
        output: string;
    } | {
        file: string;
        output: string;
    }>, variables: Record<string, unknown>, options?: {
        dryRun?: boolean;
        overwrite?: boolean;
    }): Array<{
        output: string;
        success: boolean;
        error?: string;
    }>;
    /**
     * 清空模板缓存
     */
    clearCache(): void;
    /**
     * 获取缓存统计
     */
    getCacheStats(): {
        size: number;
        keys: string[];
    };
}
export declare const templateEngine: TemplateEngine;
export default templateEngine;
//# sourceMappingURL=template-engine.d.ts.map