/**
 * MoltCare Error Handling
 * 统一错误格式和模糊匹配建议
 */
export interface MoltCareError {
    code: string;
    message: string;
    suggestion?: string;
    details?: string[];
    didYouMean?: string[];
}
export declare class ErrorHandler {
    private static readonly SIMILARITY_THRESHOLD;
    /**
     * 格式化错误输出
     */
    static formatError(error: MoltCareError | Error | string): string;
    /**
     * 打印错误并退出
     */
    static exit(error: MoltCareError | Error | string, code?: number): never;
    /**
     * 查找相似的字符串
     */
    static findSimilar(target: string, candidates: string[], limit?: number): string[];
    /**
     * 创建常见错误
     */
    static packNotFound(packName: string, availablePacks: string[]): MoltCareError;
    static packAlreadyInstalled(packName: string): MoltCareError;
    static invalidPackName(name: string, reason: string): MoltCareError;
    static configNotFound(): MoltCareError;
    static openClawNotFound(): MoltCareError;
    static templateRenderFailed(file: string, reason: string): MoltCareError;
    static fileWriteFailed(file: string, reason: string): MoltCareError;
}
/**
 * 预设错误代码
 */
export declare const ErrorCodes: {
    readonly PACK_NOT_FOUND: "PACK_NOT_FOUND";
    readonly PACK_ALREADY_INSTALLED: "PACK_ALREADY_INSTALLED";
    readonly INVALID_PACK_NAME: "INVALID_PACK_NAME";
    readonly CONFIG_NOT_FOUND: "CONFIG_NOT_FOUND";
    readonly CONFIG_INVALID: "CONFIG_INVALID";
    readonly OPENCLAW_NOT_FOUND: "OPENCLAW_NOT_FOUND";
    readonly TEMPLATE_RENDER_FAILED: "TEMPLATE_RENDER_FAILED";
    readonly FILE_WRITE_FAILED: "FILE_WRITE_FAILED";
    readonly PERMISSION_DENIED: "PERMISSION_DENIED";
    readonly NETWORK_ERROR: "NETWORK_ERROR";
    readonly UNKNOWN: "UNKNOWN";
};
//# sourceMappingURL=errors.d.ts.map