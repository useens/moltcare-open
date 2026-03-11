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

import chalk from 'chalk';
import { distance } from 'fastest-levenshtein';
import { getConfig } from '../config.js';

// 错误严重级别
export enum ErrorSeverity {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error',
  FATAL = 'fatal',
}

// 错误分类
export enum ErrorCategory {
  CLI = 'CLI',
  CONFIG = 'CONFIG',
  PACK = 'PACK',
  TEMPLATE = 'TEMPLATE',
  FILE_SYSTEM = 'FILE_SYSTEM',
  NETWORK = 'NETWORK',
  VALIDATION = 'VALIDATION',
  PERMISSION = 'PERMISSION',
  RUNTIME = 'RUNTIME',
  UNKNOWN = 'UNKNOWN',
}

// 错误代码常量
export const ErrorCodes = {
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
} as const;

export type ErrorCode = typeof ErrorCodes[keyof typeof ErrorCodes];

// 错误详情接口
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

// 错误消息多语言支持
const ErrorMessages: Record<string, Record<string, string>> = {
  zh: {
    [ErrorCodes.COMMAND_NOT_FOUND]: '未知命令: {0}',
    [ErrorCodes.MISSING_ARGUMENT]: '缺少必要参数: {0}',
    [ErrorCodes.INVALID_ARGUMENT]: '参数无效: {0}',
    [ErrorCodes.CONFIG_NOT_FOUND]: 'MoltCare 尚未初始化，请先运行 "moltcare init"',
    [ErrorCodes.CONFIG_INVALID]: '配置文件格式无效',
    [ErrorCodes.PACK_NOT_FOUND]: '智能包 "{0}" 不存在',
    [ErrorCodes.PACK_ALREADY_INSTALLED]: '智能包 "{0}" 已安装',
    [ErrorCodes.PACK_INVALID_MANIFEST]: '智能包 "{0}" 的 manifest 文件无效',
    [ErrorCodes.TEMPLATE_NOT_FOUND]: '模板文件不存在: {0}',
    [ErrorCodes.TEMPLATE_RENDER_FAILED]: '模板渲染失败: {0}',
    [ErrorCodes.FILE_NOT_FOUND]: '文件不存在: {0}',
    [ErrorCodes.DIRECTORY_NOT_FOUND]: '目录不存在: {0}',
    [ErrorCodes.PERMISSION_DENIED]: '权限不足: {0}',
    [ErrorCodes.VALIDATION_FAILED]: '验证失败: {0}',
    [ErrorCodes.UNKNOWN]: '发生未知错误',
  },
  en: {
    [ErrorCodes.COMMAND_NOT_FOUND]: 'Unknown command: {0}',
    [ErrorCodes.MISSING_ARGUMENT]: 'Missing required argument: {0}',
    [ErrorCodes.INVALID_ARGUMENT]: 'Invalid argument: {0}',
    [ErrorCodes.CONFIG_NOT_FOUND]: 'MoltCare not initialized, please run "moltcare init" first',
    [ErrorCodes.CONFIG_INVALID]: 'Invalid configuration format',
    [ErrorCodes.PACK_NOT_FOUND]: 'Pack "{0}" not found',
    [ErrorCodes.PACK_ALREADY_INSTALLED]: 'Pack "{0}" already installed',
    [ErrorCodes.PACK_INVALID_MANIFEST]: 'Invalid manifest for pack "{0}"',
    [ErrorCodes.TEMPLATE_NOT_FOUND]: 'Template file not found: {0}',
    [ErrorCodes.TEMPLATE_RENDER_FAILED]: 'Template render failed: {0}',
    [ErrorCodes.FILE_NOT_FOUND]: 'File not found: {0}',
    [ErrorCodes.DIRECTORY_NOT_FOUND]: 'Directory not found: {0}',
    [ErrorCodes.PERMISSION_DENIED]: 'Permission denied: {0}',
    [ErrorCodes.VALIDATION_FAILED]: 'Validation failed: {0}',
    [ErrorCodes.UNKNOWN]: 'An unknown error occurred',
  },
};

// 解决建议多语言支持
const Suggestions: Record<string, Record<string, string>> = {
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
const errorHistory: MoltCareErrorDetails[] = [];
const MAX_ERROR_HISTORY = 50;

export class MoltCareError extends Error {
  public readonly details: MoltCareErrorDetails;

  constructor(details: Partial<MoltCareErrorDetails>) {
    const fullDetails: MoltCareErrorDetails = {
      code: details.code || ErrorCodes.UNKNOWN,
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

export class ErrorHandler {
  private static readonly SIMILARITY_THRESHOLD = 0.6;
  private static readonly MAX_SUGGESTIONS = 3;

  /**
   * 格式化错误输出（带颜色）
   */
  static formatError(error: MoltCareError | Error | string): string {
    let err: MoltCareErrorDetails;

    if (typeof error === 'string') {
      err = {
        code: ErrorCodes.UNKNOWN,
        message: error,
        category: ErrorCategory.UNKNOWN,
        severity: ErrorSeverity.ERROR,
        timestamp: new Date().toISOString(),
      };
    } else if (error instanceof MoltCareError) {
      err = error.details;
    } else if (error instanceof Error) {
      err = {
        code: ErrorCodes.UNKNOWN,
        message: error.message,
        category: ErrorCategory.RUNTIME,
        severity: ErrorSeverity.ERROR,
        timestamp: new Date().toISOString(),
        originalError: error,
      };
    } else {
      err = error as MoltCareErrorDetails;
    }

    const lines: string[] = [];
    const isFatal = err.severity === ErrorSeverity.FATAL;
    const icon = isFatal ? '💥' : '✗';
    const color = isFatal ? chalk.red.bold : chalk.red;

    // 错误头部
    lines.push('');
    lines.push(color(`${icon} [${err.code}] ${err.message}`));
    lines.push(chalk.gray('─'.repeat(Math.min(60, err.message.length + err.code.length + 10))));

    // 详细信息
    if (err.details && err.details.length > 0) {
      lines.push('');
      lines.push(chalk.white('详情:'));
      err.details.forEach(detail => {
        lines.push(chalk.gray(`  • ${detail}`));
      });
    }

    // 上下文信息（DEBUG 模式）
    if (err.context && Object.keys(err.context).length > 0) {
      const config = getConfig();
      if (config.get('logLevel') === 'debug') {
        lines.push('');
        lines.push(chalk.gray('上下文:'));
        Object.entries(err.context).forEach(([key, value]) => {
          lines.push(chalk.gray(`  ${key}: ${JSON.stringify(value)}`));
        });
      }
    }

    // 解决建议
    if (err.suggestion) {
      lines.push('');
      lines.push(chalk.yellow('💡 建议:'));
      lines.push(chalk.yellow(`  ${err.suggestion}`));
    }

    // 模糊匹配建议
    if (err.didYouMean && err.didYouMean.length > 0) {
      lines.push('');
      lines.push(chalk.cyan('🔍 您是否想找:'));
      err.didYouMean.forEach(item => {
        lines.push(chalk.cyan(`  • ${item}`));
      });
    }

    // 恢复操作
    if (err.recoverable && err.recoveryAction) {
      lines.push('');
      lines.push(chalk.green('🔄 恢复操作:'));
      lines.push(chalk.green(`  ${err.recoveryAction}`));
    }

    // 时间戳（DEBUG 模式）
    if (err.timestamp) {
      const config = getConfig();
      if (config.get('logLevel') === 'debug') {
        lines.push('');
        lines.push(chalk.gray(`时间戳: ${err.timestamp}`));
      }
    }

    lines.push('');
    return lines.join('\n');
  }

  /**
   * 打印错误并退出
   */
  static exit(error: MoltCareError | Error | string, exitCode: number = 1): never {
    console.error(this.formatError(error));
    process.exit(exitCode);
  }

  /**
   * 打印警告（不退出）
   */
  static warn(message: string, details?: string[]): void {
    console.warn(chalk.yellow(`⚠️  ${message}`));
    if (details) {
      details.forEach(d => console.warn(chalk.gray(`   ${d}`)));
    }
  }

  /**
   * 打印信息
   */
  static info(message: string): void {
    console.log(chalk.blue(`ℹ️  ${message}`));
  }

  /**
   * 查找相似的字符串
   */
  static findSimilar(target: string, candidates: string[], limit: number = 3): string[] {
    if (!target || candidates.length === 0) return [];

    const scored = candidates.map(candidate => {
      const dist = distance(target.toLowerCase(), candidate.toLowerCase());
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
  static getLocalizedMessage(code: ErrorCode, lang: string = 'zh', ...args: string[]): string {
    const messages = ErrorMessages[lang] || ErrorMessages.zh;
    let message = messages[code] || messages[ErrorCodes.UNKNOWN];
    
    // 替换参数
    args.forEach((arg, index) => {
      message = message.replace(`{${index}}`, arg);
    });
    
    return message;
  }

  /**
   * 获取本地化建议
   */
  static getLocalizedSuggestion(key: string, lang: string = 'zh'): string {
    const suggestions = Suggestions[lang] || Suggestions.zh;
    return suggestions[key] || key;
  }

  /**
   * 创建预定义错误 - Pack 不存在
   */
  static packNotFound(packName: string, availablePacks: string[]): MoltCareError {
    const lang = getConfig().get('language');
    return new MoltCareError({
      code: ErrorCodes.PACK_NOT_FOUND,
      message: this.getLocalizedMessage(ErrorCodes.PACK_NOT_FOUND, lang, packName),
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
  static packAlreadyInstalled(packName: string): MoltCareError {
    const lang = getConfig().get('language');
    return new MoltCareError({
      code: ErrorCodes.PACK_ALREADY_INSTALLED,
      message: this.getLocalizedMessage(ErrorCodes.PACK_ALREADY_INSTALLED, lang, packName),
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
  static configNotFound(): MoltCareError {
    const lang = getConfig().get('language');
    return new MoltCareError({
      code: ErrorCodes.CONFIG_NOT_FOUND,
      message: this.getLocalizedMessage(ErrorCodes.CONFIG_NOT_FOUND, lang),
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
  static commandNotFound(command: string, availableCommands: string[]): MoltCareError {
    const lang = getConfig().get('language');
    return new MoltCareError({
      code: ErrorCodes.COMMAND_NOT_FOUND,
      message: this.getLocalizedMessage(ErrorCodes.COMMAND_NOT_FOUND, lang, command),
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
  static missingArgument(argument: string): MoltCareError {
    const lang = getConfig().get('language');
    return new MoltCareError({
      code: ErrorCodes.MISSING_ARGUMENT,
      message: this.getLocalizedMessage(ErrorCodes.MISSING_ARGUMENT, lang, argument),
      category: ErrorCategory.CLI,
      severity: ErrorSeverity.ERROR,
      suggestion: '使用 --help 查看命令用法',
      context: { argument },
    });
  }

  /**
   * 创建预定义错误 - 模板渲染失败
   */
  static templateRenderFailed(file: string, reason: string): MoltCareError {
    const lang = getConfig().get('language');
    return new MoltCareError({
      code: ErrorCodes.TEMPLATE_RENDER_FAILED,
      message: this.getLocalizedMessage(ErrorCodes.TEMPLATE_RENDER_FAILED, lang, file),
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
  static fileWriteFailed(file: string, reason: string): MoltCareError {
    const lang = getConfig().get('language');
    return new MoltCareError({
      code: ErrorCodes.FILE_WRITE_ERROR,
      message: this.getLocalizedMessage(ErrorCodes.FILE_WRITE_ERROR, lang, file),
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
  static permissionDenied(resource: string): MoltCareError {
    const lang = getConfig().get('language');
    return new MoltCareError({
      code: ErrorCodes.PERMISSION_DENIED,
      message: this.getLocalizedMessage(ErrorCodes.PERMISSION_DENIED, lang, resource),
      category: ErrorCategory.PERMISSION,
      severity: ErrorSeverity.ERROR,
      suggestion: this.getLocalizedSuggestion('check_permission', lang),
      context: { resource },
    });
  }

  /**
   * 获取错误历史（用于调试）
   */
  static getErrorHistory(): MoltCareErrorDetails[] {
    return [...errorHistory];
  }

  /**
   * 清空错误历史
   */
  static clearErrorHistory(): void {
    errorHistory.length = 0;
  }

  /**
   * 包装异步函数，自动捕获错误
   */
  static wrapAsync<T extends (...args: any[]) => Promise<any>>(
    fn: T,
    errorHandler?: (error: Error) => void
  ): (...args: Parameters<T>) => Promise<ReturnType<T>> {
    return async (...args: Parameters<T>): Promise<ReturnType<T>> => {
      try {
        return await fn(...args);
      } catch (error) {
        if (errorHandler) {
          errorHandler(error as Error);
        } else {
          this.exit(error as Error);
        }
        throw error;
      }
    };
  }
}

export default ErrorHandler;
