"use strict";
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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ErrorHandler = exports.MoltCareError = exports.ErrorCodes = exports.ErrorCategory = exports.ErrorSeverity = void 0;
const chalk_1 = __importDefault(require("chalk"));
const fastest_levenshtein_1 = require("fastest-levenshtein");
const config_js_1 = require("../config.js");
// 错误严重级别
var ErrorSeverity;
(function (ErrorSeverity) {
    ErrorSeverity["DEBUG"] = "debug";
    ErrorSeverity["INFO"] = "info";
    ErrorSeverity["WARN"] = "warn";
    ErrorSeverity["ERROR"] = "error";
    ErrorSeverity["FATAL"] = "fatal";
})(ErrorSeverity || (exports.ErrorSeverity = ErrorSeverity = {}));
// 错误分类
var ErrorCategory;
(function (ErrorCategory) {
    ErrorCategory["CLI"] = "CLI";
    ErrorCategory["CONFIG"] = "CONFIG";
    ErrorCategory["PACK"] = "PACK";
    ErrorCategory["TEMPLATE"] = "TEMPLATE";
    ErrorCategory["FILE_SYSTEM"] = "FILE_SYSTEM";
    ErrorCategory["NETWORK"] = "NETWORK";
    ErrorCategory["VALIDATION"] = "VALIDATION";
    ErrorCategory["PERMISSION"] = "PERMISSION";
    ErrorCategory["RUNTIME"] = "RUNTIME";
    ErrorCategory["UNKNOWN"] = "UNKNOWN";
})(ErrorCategory || (exports.ErrorCategory = ErrorCategory = {}));
// 错误代码常量
exports.ErrorCodes = {
    // CLI 错误
    COMMAND_NOT_FOUND: 'COMMAND_NOT_FOUND',
    INVALID_ARGUMENT: 'INVALID_ARGUMENT',
    MISSING_ARGUMENT: 'MISSING_ARGUMENT',
    INVALID_OPTION: 'INVALID_OPTION',
    // 配置错误
    CONFIG_NOT_FOUND: 'CONFIG_NOT_FOUND',
    CONFIG_INVALID: 'CONFIG_INVALID',
    CONFIG_READ_ERROR: 'CONFIG_READ_ERROR',
    CONFIG_WRITE_ERROR: 'CONFIG_WRITE_ERROR',
    // Pack 错误
    PACK_NOT_FOUND: 'PACK_NOT_FOUND',
    PACK_ALREADY_INSTALLED: 'PACK_ALREADY_INSTALLED',
    PACK_INVALID_MANIFEST: 'PACK_INVALID_MANIFEST',
    PACK_INCOMPATIBLE: 'PACK_INCOMPATIBLE',
    PACK_DEPENDENCY_ERROR: 'PACK_DEPENDENCY_ERROR',
    // 模板错误
    TEMPLATE_NOT_FOUND: 'TEMPLATE_NOT_FOUND',
    TEMPLATE_RENDER_FAILED: 'TEMPLATE_RENDER_FAILED',
    TEMPLATE_SYNTAX_ERROR: 'TEMPLATE_SYNTAX_ERROR',
    TEMPLATE_VARIABLE_MISSING: 'TEMPLATE_VARIABLE_MISSING',
    // 文件系统错误
    FILE_NOT_FOUND: 'FILE_NOT_FOUND',
    FILE_READ_ERROR: 'FILE_READ_ERROR',
    FILE_WRITE_ERROR: 'FILE_WRITE_ERROR',
    DIRECTORY_NOT_FOUND: 'DIRECTORY_NOT_FOUND',
    PATH_INVALID: 'PATH_INVALID',
    // 权限错误
    PERMISSION_DENIED: 'PERMISSION_DENIED',
    INSUFFICIENT_PERMISSIONS: 'INSUFFICIENT_PERMISSIONS',
    // 验证错误
    VALIDATION_FAILED: 'VALIDATION_FAILED',
    INVALID_INPUT: 'INVALID_INPUT',
    // 运行时错误
    INITIALIZATION_FAILED: 'INITIALIZATION_FAILED',
    EXECUTION_FAILED: 'EXECUTION_FAILED',
    // 其他
    UNKNOWN: 'UNKNOWN',
};
// 错误消息多语言支持
const ErrorMessages = {
    zh: {
        [exports.ErrorCodes.COMMAND_NOT_FOUND]: '未知命令: {0}',
        [exports.ErrorCodes.MISSING_ARGUMENT]: '缺少必要参数: {0}',
        [exports.ErrorCodes.INVALID_ARGUMENT]: '参数无效: {0}',
        [exports.ErrorCodes.CONFIG_NOT_FOUND]: 'MoltCare 尚未初始化，请先运行 "moltcare init"',
        [exports.ErrorCodes.CONFIG_INVALID]: '配置文件格式无效',
        [exports.ErrorCodes.PACK_NOT_FOUND]: '智能包 "{0}" 不存在',
        [exports.ErrorCodes.PACK_ALREADY_INSTALLED]: '智能包 "{0}" 已安装',
        [exports.ErrorCodes.PACK_INVALID_MANIFEST]: '智能包 "{0}" 的 manifest 文件无效',
        [exports.ErrorCodes.TEMPLATE_NOT_FOUND]: '模板文件不存在: {0}',
        [exports.ErrorCodes.TEMPLATE_RENDER_FAILED]: '模板渲染失败: {0}',
        [exports.ErrorCodes.FILE_NOT_FOUND]: '文件不存在: {0}',
        [exports.ErrorCodes.DIRECTORY_NOT_FOUND]: '目录不存在: {0}',
        [exports.ErrorCodes.PERMISSION_DENIED]: '权限不足: {0}',
        [exports.ErrorCodes.VALIDATION_FAILED]: '验证失败: {0}',
        [exports.ErrorCodes.UNKNOWN]: '发生未知错误',
    },
    en: {
        [exports.ErrorCodes.COMMAND_NOT_FOUND]: 'Unknown command: {0}',
        [exports.ErrorCodes.MISSING_ARGUMENT]: 'Missing required argument: {0}',
        [exports.ErrorCodes.INVALID_ARGUMENT]: 'Invalid argument: {0}',
        [exports.ErrorCodes.CONFIG_NOT_FOUND]: 'MoltCare not initialized, please run "moltcare init" first',
        [exports.ErrorCodes.CONFIG_INVALID]: 'Invalid configuration format',
        [exports.ErrorCodes.PACK_NOT_FOUND]: 'Pack "{0}" not found',
        [exports.ErrorCodes.PACK_ALREADY_INSTALLED]: 'Pack "{0}" already installed',
        [exports.ErrorCodes.PACK_INVALID_MANIFEST]: 'Invalid manifest for pack "{0}"',
        [exports.ErrorCodes.TEMPLATE_NOT_FOUND]: 'Template file not found: {0}',
        [exports.ErrorCodes.TEMPLATE_RENDER_FAILED]: 'Template render failed: {0}',
        [exports.ErrorCodes.FILE_NOT_FOUND]: 'File not found: {0}',
        [exports.ErrorCodes.DIRECTORY_NOT_FOUND]: 'Directory not found: {0}',
        [exports.ErrorCodes.PERMISSION_DENIED]: 'Permission denied: {0}',
        [exports.ErrorCodes.VALIDATION_FAILED]: 'Validation failed: {0}',
        [exports.ErrorCodes.UNKNOWN]: 'An unknown error occurred',
    },
};
// 解决建议多语言支持
const Suggestions = {
    zh: {
        init: '运行 "moltcare init" 初始化配置',
        list_packs: '运行 "moltcare list" 查看所有可用智能包',
        force_option: '使用 --force 选项强制重新安装',
        dry_run: '使用 --dry-run 预览更改',
        check_path: '检查路径是否正确',
        check_permission: '检查文件权限和磁盘空间',
        check_manifest: '检查 manifest.json 文件格式',
    },
    en: {
        init: 'Run "moltcare init" to initialize configuration',
        list_packs: 'Run "moltcare list" to see all available packs',
        force_option: 'Use --force option to force reinstall',
        dry_run: 'Use --dry-run to preview changes',
        check_path: 'Check if the path is correct',
        check_permission: 'Check file permissions and disk space',
        check_manifest: 'Check manifest.json file format',
    },
};
// 错误历史记录（用于调试）
const errorHistory = [];
const MAX_ERROR_HISTORY = 50;
class MoltCareError extends Error {
    details;
    constructor(details) {
        const fullDetails = {
            code: details.code || exports.ErrorCodes.UNKNOWN,
            message: details.message || 'Unknown error',
            category: details.category || ErrorCategory.UNKNOWN,
            severity: details.severity || ErrorSeverity.ERROR,
            timestamp: new Date().toISOString(),
            recoverable: details.recoverable ?? false,
            ...details,
        };
        super(fullDetails.message);
        this.details = fullDetails;
        this.name = 'MoltCareError';
        // 记录错误历史
        errorHistory.push(fullDetails);
        if (errorHistory.length > MAX_ERROR_HISTORY) {
            errorHistory.shift();
        }
    }
}
exports.MoltCareError = MoltCareError;
class ErrorHandler {
    static SIMILARITY_THRESHOLD = 0.6;
    static MAX_SUGGESTIONS = 3;
    /**
     * 格式化错误输出（带颜色）
     */
    static formatError(error) {
        let err;
        if (typeof error === 'string') {
            err = {
                code: exports.ErrorCodes.UNKNOWN,
                message: error,
                category: ErrorCategory.UNKNOWN,
                severity: ErrorSeverity.ERROR,
                timestamp: new Date().toISOString(),
            };
        }
        else if (error instanceof MoltCareError) {
            err = error.details;
        }
        else if (error instanceof Error) {
            err = {
                code: exports.ErrorCodes.UNKNOWN,
                message: error.message,
                category: ErrorCategory.RUNTIME,
                severity: ErrorSeverity.ERROR,
                timestamp: new Date().toISOString(),
                originalError: error,
            };
        }
        else {
            err = error;
        }
        const lines = [];
        const isFatal = err.severity === ErrorSeverity.FATAL;
        const icon = isFatal ? '💥' : '✗';
        const color = isFatal ? chalk_1.default.red.bold : chalk_1.default.red;
        // 错误头部
        lines.push('');
        lines.push(color(`${icon} [${err.code}] ${err.message}`));
        lines.push(chalk_1.default.gray('─'.repeat(Math.min(60, err.message.length + err.code.length + 10))));
        // 详细信息
        if (err.details && err.details.length > 0) {
            lines.push('');
            lines.push(chalk_1.default.white('详情:'));
            err.details.forEach(detail => {
                lines.push(chalk_1.default.gray(`  • ${detail}`));
            });
        }
        // 上下文信息（DEBUG 模式）
        if (err.context && Object.keys(err.context).length > 0) {
            const config = (0, config_js_1.getConfig)();
            if (config.get('logLevel') === 'debug') {
                lines.push('');
                lines.push(chalk_1.default.gray('上下文:'));
                Object.entries(err.context).forEach(([key, value]) => {
                    lines.push(chalk_1.default.gray(`  ${key}: ${JSON.stringify(value)}`));
                });
            }
        }
        // 解决建议
        if (err.suggestion) {
            lines.push('');
            lines.push(chalk_1.default.yellow('💡 建议:'));
            lines.push(chalk_1.default.yellow(`  ${err.suggestion}`));
        }
        // 模糊匹配建议
        if (err.didYouMean && err.didYouMean.length > 0) {
            lines.push('');
            lines.push(chalk_1.default.cyan('🔍 您是否想找:'));
            err.didYouMean.forEach(item => {
                lines.push(chalk_1.default.cyan(`  • ${item}`));
            });
        }
        // 恢复操作
        if (err.recoverable && err.recoveryAction) {
            lines.push('');
            lines.push(chalk_1.default.green('🔄 恢复操作:'));
            lines.push(chalk_1.default.green(`  ${err.recoveryAction}`));
        }
        // 时间戳（DEBUG 模式）
        if (err.timestamp) {
            const config = (0, config_js_1.getConfig)();
            if (config.get('logLevel') === 'debug') {
                lines.push('');
                lines.push(chalk_1.default.gray(`时间戳: ${err.timestamp}`));
            }
        }
        lines.push('');
        return lines.join('\n');
    }
    /**
     * 打印错误并退出
     */
    static exit(error, exitCode = 1) {
        console.error(this.formatError(error));
        process.exit(exitCode);
    }
    /**
     * 打印警告（不退出）
     */
    static warn(message, details) {
        console.warn(chalk_1.default.yellow(`⚠️  ${message}`));
        if (details) {
            details.forEach(d => console.warn(chalk_1.default.gray(`   ${d}`)));
        }
    }
    /**
     * 打印信息
     */
    static info(message) {
        console.log(chalk_1.default.blue(`ℹ️  ${message}`));
    }
    /**
     * 查找相似的字符串
     */
    static findSimilar(target, candidates, limit = 3) {
        if (!target || candidates.length === 0)
            return [];
        const scored = candidates.map(candidate => {
            const dist = (0, fastest_levenshtein_1.distance)(target.toLowerCase(), candidate.toLowerCase());
            const maxLen = Math.max(target.length, candidate.length);
            const similarity = maxLen === 0 ? 1 : 1 - dist / maxLen;
            return { candidate, similarity };
        });
        return scored
            .filter(s => s.similarity >= this.SIMILARITY_THRESHOLD)
            .sort((a, b) => b.similarity - a.similarity)
            .slice(0, limit)
            .map(s => s.candidate);
    }
    /**
     * 获取本地化错误消息
     */
    static getLocalizedMessage(code, lang = 'zh', ...args) {
        const messages = ErrorMessages[lang] || ErrorMessages.zh;
        let message = messages[code] || messages[exports.ErrorCodes.UNKNOWN];
        // 替换参数
        args.forEach((arg, index) => {
            message = message.replace(`{${index}}`, arg);
        });
        return message;
    }
    /**
     * 获取本地化建议
     */
    static getLocalizedSuggestion(key, lang = 'zh') {
        const suggestions = Suggestions[lang] || Suggestions.zh;
        return suggestions[key] || key;
    }
    /**
     * 创建预定义错误 - Pack 不存在
     */
    static packNotFound(packName, availablePacks) {
        const lang = (0, config_js_1.getConfig)().get('language');
        return new MoltCareError({
            code: exports.ErrorCodes.PACK_NOT_FOUND,
            message: this.getLocalizedMessage(exports.ErrorCodes.PACK_NOT_FOUND, lang, packName),
            category: ErrorCategory.PACK,
            severity: ErrorSeverity.ERROR,
            suggestion: this.getLocalizedSuggestion('list_packs', lang),
            didYouMean: this.findSimilar(packName, availablePacks),
            context: { packName, availableCount: availablePacks.length },
        });
    }
    /**
     * 创建预定义错误 - Pack 已安装
     */
    static packAlreadyInstalled(packName) {
        const lang = (0, config_js_1.getConfig)().get('language');
        return new MoltCareError({
            code: exports.ErrorCodes.PACK_ALREADY_INSTALLED,
            message: this.getLocalizedMessage(exports.ErrorCodes.PACK_ALREADY_INSTALLED, lang, packName),
            category: ErrorCategory.PACK,
            severity: ErrorSeverity.WARN,
            suggestion: this.getLocalizedSuggestion('force_option', lang),
            recoverable: true,
            recoveryAction: `moltcare apply ${packName} --force`,
            context: { packName },
        });
    }
    /**
     * 创建预定义错误 - 配置不存在
     */
    static configNotFound() {
        const lang = (0, config_js_1.getConfig)().get('language');
        return new MoltCareError({
            code: exports.ErrorCodes.CONFIG_NOT_FOUND,
            message: this.getLocalizedMessage(exports.ErrorCodes.CONFIG_NOT_FOUND, lang),
            category: ErrorCategory.CONFIG,
            severity: ErrorSeverity.ERROR,
            suggestion: this.getLocalizedSuggestion('init', lang),
            recoverable: true,
            recoveryAction: 'moltcare init',
        });
    }
    /**
     * 创建预定义错误 - 命令不存在
     */
    static commandNotFound(command, availableCommands) {
        const lang = (0, config_js_1.getConfig)().get('language');
        return new MoltCareError({
            code: exports.ErrorCodes.COMMAND_NOT_FOUND,
            message: this.getLocalizedMessage(exports.ErrorCodes.COMMAND_NOT_FOUND, lang, command),
            category: ErrorCategory.CLI,
            severity: ErrorSeverity.ERROR,
            suggestion: '运行 "moltcare --help" 查看所有可用命令',
            didYouMean: this.findSimilar(command, availableCommands),
            context: { command },
        });
    }
    /**
     * 创建预定义错误 - 缺少参数
     */
    static missingArgument(argument) {
        const lang = (0, config_js_1.getConfig)().get('language');
        return new MoltCareError({
            code: exports.ErrorCodes.MISSING_ARGUMENT,
            message: this.getLocalizedMessage(exports.ErrorCodes.MISSING_ARGUMENT, lang, argument),
            category: ErrorCategory.CLI,
            severity: ErrorSeverity.ERROR,
            suggestion: '使用 --help 查看命令用法',
            context: { argument },
        });
    }
    /**
     * 创建预定义错误 - 模板渲染失败
     */
    static templateRenderFailed(file, reason) {
        const lang = (0, config_js_1.getConfig)().get('language');
        return new MoltCareError({
            code: exports.ErrorCodes.TEMPLATE_RENDER_FAILED,
            message: this.getLocalizedMessage(exports.ErrorCodes.TEMPLATE_RENDER_FAILED, lang, file),
            category: ErrorCategory.TEMPLATE,
            severity: ErrorSeverity.ERROR,
            suggestion: this.getLocalizedSuggestion('check_manifest', lang),
            details: [reason],
            context: { file },
        });
    }
    /**
     * 创建预定义错误 - 文件写入失败
     */
    static fileWriteFailed(file, reason) {
        const lang = (0, config_js_1.getConfig)().get('language');
        return new MoltCareError({
            code: exports.ErrorCodes.FILE_WRITE_ERROR,
            message: this.getLocalizedMessage(exports.ErrorCodes.FILE_WRITE_ERROR, lang, file),
            category: ErrorCategory.FILE_SYSTEM,
            severity: ErrorSeverity.ERROR,
            suggestion: this.getLocalizedSuggestion('check_permission', lang),
            details: [reason],
            context: { file },
        });
    }
    /**
     * 创建预定义错误 - 权限不足
     */
    static permissionDenied(resource) {
        const lang = (0, config_js_1.getConfig)().get('language');
        return new MoltCareError({
            code: exports.ErrorCodes.PERMISSION_DENIED,
            message: this.getLocalizedMessage(exports.ErrorCodes.PERMISSION_DENIED, lang, resource),
            category: ErrorCategory.PERMISSION,
            severity: ErrorSeverity.ERROR,
            suggestion: this.getLocalizedSuggestion('check_permission', lang),
            context: { resource },
        });
    }
    /**
     * 获取错误历史（用于调试）
     */
    static getErrorHistory() {
        return [...errorHistory];
    }
    /**
     * 清空错误历史
     */
    static clearErrorHistory() {
        errorHistory.length = 0;
    }
    /**
     * 包装异步函数，自动捕获错误
     */
    static wrapAsync(fn, errorHandler) {
        return async (...args) => {
            try {
                return await fn(...args);
            }
            catch (error) {
                if (errorHandler) {
                    errorHandler(error);
                }
                else {
                    this.exit(error);
                }
                throw error;
            }
        };
    }
}
exports.ErrorHandler = ErrorHandler;
exports.default = ErrorHandler;
//# sourceMappingURL=errors-enhanced.js.map