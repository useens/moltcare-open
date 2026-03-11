/**
 * Enhanced MoltCare Error Handling System
 * 增强版错误处理系统 - Phase 5 优化
 *
 * 功能:
 * - 结构化错误代码和分类
 * - 智能模糊匹配建议
 * - 多语言错误消息支持
 * - 错误恢复建议
 * - 错误日志和追踪
 */
export declare enum ErrorSeverity {
    DEBUG = "debug",
    INFO = "info",
    WARN = "warn",
    ERROR = "error",
    FATAL = "fatal"
}
export declare enum ErrorCategory {
    CLI = "CLI",
    CONFIG = "CONFIG",
    PACK = "PACK",
    TEMPLATE = "TEMPLATE",
    FILE_SYSTEM = "FILE_SYSTEM",
    NETWORK = "NETWORK",
    VALIDATION = "VALIDATION",
    PERMISSION = "PERMISSION",
    RUNTIME = "RUNTIME",
    UNKNOWN = "UNKNOWN"
}
export declare const ErrorCodes: {
    readonly COMMAND_NOT_FOUND: "COMMAND_NOT_FOUND";
    readonly INVALID_ARGUMENT: "INVALID_ARGUMENT";
    readonly MISSING_ARGUMENT: "MISSING_ARGUMENT";
    readonly INVALID_OPTION: "INVALID_OPTION";
    readonly CONFIG_NOT_FOUND: "CONFIG_NOT_FOUND";
    readonly CONFIG_INVALID: "CONFIG_INVALID";
    readonly CONFIG_READ_ERROR: "CONFIG_READ_ERROR";
    readonly CONFIG_WRITE_ERROR: "CONFIG_WRITE_ERROR";
    readonly PACK_NOT_FOUND: "PACK_NOT_FOUND";
    readonly PACK_ALREADY_INSTALLED: "PACK_ALREADY_INSTALLED";
    readonly PACK_INVALID_MANIFEST: "PACK_INVALID_MANIFEST";
    readonly PACK_INCOMPATIBLE: "PACK_INCOMPATIBLE";
    readonly PACK_DEPENDENCY_ERROR: "PACK_DEPENDENCY_ERROR";
    readonly TEMPLATE_NOT_FOUND: "TEMPLATE_NOT_FOUND";
    readonly TEMPLATE_RENDER_FAILED: "TEMPLATE_RENDER_FAILED";
    readonly TEMPLATE_SYNTAX_ERROR: "TEMPLATE_SYNTAX_ERROR";
    readonly TEMPLATE_VARIABLE_MISSING: "TEMPLATE_VARIABLE_MISSING";
    readonly FILE_NOT_FOUND: "FILE_NOT_FOUND";
    readonly FILE_READ_ERROR: "FILE_READ_ERROR";
    readonly FILE_WRITE_ERROR: "FILE_WRITE_ERROR";
    readonly DIRECTORY_NOT_FOUND: "DIRECTORY_NOT_FOUND";
    readonly PATH_INVALID: "PATH_INVALID";
    readonly PERMISSION_DENIED: "PERMISSION_DENIED";
    readonly INSUFFICIENT_PERMISSIONS: "INSUFFICIENT_PERMISSIONS";
    readonly VALIDATION_FAILED: "VALIDATION_FAILED";
    readonly INVALID_INPUT: "INVALID_INPUT";
    readonly INITIALIZATION_FAILED: "INITIALIZATION_FAILED";
    readonly EXECUTION_FAILED: "EXECUTION_FAILED";
    readonly UNKNOWN: "UNKNOWN";
};
export type ErrorCode = typeof ErrorCodes[keyof typeof ErrorCodes];
export interface MoltCareErrorDetails {
    code: ErrorCode;
    message: string;
    category: ErrorCategory;
    severity: ErrorSeverity;
    suggestion?: string;
    details?: string[];
    didYouMean?: string[];
    originalError?: Error;
    context?: Record<string, unknown>;
    timestamp?: string;
    recoverable?: boolean;
    recoveryAction?: string;
}
export declare class MoltCareError extends Error {
    readonly details: MoltCareErrorDetails;
    constructor(details: Partial<MoltCareErrorDetails>);
}
export declare class ErrorHandler {
    private static readonly SIMILARITY_THRESHOLD;
    private static readonly MAX_SUGGESTIONS;
    /**
     * 格式化错误输出（带颜色）
     */
    static formatError(error: MoltCareError | Error | string): string;
    /**
     * 打印错误并退出
     */
    static exit(error: MoltCareError | Error | string, exitCode?: number): never;
    /**
     * 打印警告（不退出）
     */
    static warn(message: string, details?: string[]): void;
    /**
     * 打印信息
     */
    static info(message: string): void;
    /**
     * 查找相似的字符串
     */
    static findSimilar(target: string, candidates: string[], limit?: number): string[];
    /**
     * 获取本地化错误消息
     */
    static getLocalizedMessage(code: ErrorCode, lang?: string, ...args: string[]): string;
    /**
     * 获取本地化建议
     */
    static getLocalizedSuggestion(key: string, lang?: string): string;
    /**
     * 创建预定义错误 - Pack 不存在
     */
    static packNotFound(packName: string, availablePacks: string[]): MoltCareError;
    /**
     * 创建预定义错误 - Pack 已安装
     */
    static packAlreadyInstalled(packName: string): MoltCareError;
    /**
     * 创建预定义错误 - 配置不存在
     */
    static configNotFound(): MoltCareError;
    /**
     * 创建预定义错误 - 命令不存在
     */
    static commandNotFound(command: string, availableCommands: string[]): MoltCareError;
    /**
     * 创建预定义错误 - 缺少参数
     */
    static missingArgument(argument: string): MoltCareError;
    /**
     * 创建预定义错误 - 模板渲染失败
     */
    static templateRenderFailed(file: string, reason: string): MoltCareError;
    /**
     * 创建预定义错误 - 文件写入失败
     */
    static fileWriteFailed(file: string, reason: string): MoltCareError;
    /**
     * 创建预定义错误 - 权限不足
     */
    static permissionDenied(resource: string): MoltCareError;
    /**
     * 获取错误历史（用于调试）
     */
    static getErrorHistory(): MoltCareErrorDetails[];
    /**
     * 清空错误历史
     */
    static clearErrorHistory(): void;
    /**
     * 包装异步函数，自动捕获错误
     */
    static wrapAsync<T extends (...args: any[]) => Promise<any>>(fn: T, errorHandler?: (error: Error) => void): (...args: Parameters<T>) => Promise<ReturnType<T>>;
}
export default ErrorHandler;
//# sourceMappingURL=errors-enhanced.d.ts.map