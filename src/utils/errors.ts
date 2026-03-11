/**
 * MoltCare Error Handling
 * 统一错误格式和模糊匹配建议
 */

import chalk from 'chalk';
import { distance } from 'fastest-levenshtein';

export interface MoltCareError {
  code: string;
  message: string;
  suggestion?: string;
  details?: string[];
  didYouMean?: string[];
}

export class ErrorHandler {
  private static readonly SIMILARITY_THRESHOLD = 0.6;

  /**
   * 格式化错误输出
   */
  static formatError(error: MoltCareError | Error | string): string {
    let err: MoltCareError;
    
    if (typeof error === 'string') {
      err = { code: 'UNKNOWN', message: error };
    } else if (error instanceof Error) {
      err = { code: 'ERROR', message: error.message };
    } else {
      err = error;
    }

    const lines: string[] = [];
    
    // 错误代码和消息
    lines.push(chalk.red(`✗ [${err.code}] ${err.message}`));
    
    // 详细信息
    if (err.details && err.details.length > 0) {
      lines.push('');
      err.details.forEach(detail => {
        lines.push(chalk.gray(`  ${detail}`));
      });
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
      lines.push(chalk.cyan('🔍 您是否想查找:'));
      err.didYouMean.forEach(item => {
        lines.push(chalk.cyan(`  • ${item}`));
      });
    }
    
    return lines.join('\n');
  }

  /**
   * 打印错误并退出
   */
  static exit(error: MoltCareError | Error | string, code: number = 1): never {
    console.error(this.formatError(error));
    process.exit(code);
  }

  /**
   * 查找相似的字符串
   */
  static findSimilar(target: string, candidates: string[], limit: number = 3): string[] {
    if (!target || candidates.length === 0) return [];
    
    const scored = candidates.map(candidate => {
      const dist = distance(target.toLowerCase(), candidate.toLowerCase());
      const maxLen = Math.max(target.length, candidate.length);
      const similarity = 1 - dist / maxLen;
      return { candidate, similarity };
    });

    return scored
      .filter(s => s.similarity >= this.SIMILARITY_THRESHOLD)
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, limit)
      .map(s => s.candidate);
  }

  /**
   * 创建常见错误
   */
  static packNotFound(packName: string, availablePacks: string[]): MoltCareError {
    return {
      code: 'PACK_NOT_FOUND',
      message: `Pack "${packName}" 不存在`,
      suggestion: '使用 "moltcare list" 查看所有可用的 packs',
      didYouMean: this.findSimilar(packName, availablePacks),
    };
  }

  static packAlreadyInstalled(packName: string): MoltCareError {
    return {
      code: 'PACK_ALREADY_INSTALLED',
      message: `Pack "${packName}" 已安装`,
      suggestion: '使用 --force 选项强制重新安装，或使用 "moltcare apply ' + packName + '" 应用该 pack',
    };
  }

  static invalidPackName(name: string, reason: string): MoltCareError {
    return {
      code: 'INVALID_PACK_NAME',
      message: `Pack 名称 "${name}" 无效`,
      suggestion: 'Pack 名称只能包含字母、数字、连字符(-)和下划线(_)，不能以点开头',
      details: [reason],
    };
  }

  static configNotFound(): MoltCareError {
    return {
      code: 'CONFIG_NOT_FOUND',
      message: 'MoltCare 尚未初始化',
      suggestion: '运行 "moltcare init" 初始化配置',
    };
  }

  static openClawNotFound(): MoltCareError {
    return {
      code: 'OPENCLAW_NOT_FOUND',
      message: '未检测到 OpenClaw 环境',
      suggestion: '请确保已安装 OpenClaw 并设置了 OPENCLAW_WORKSPACE 环境变量',
      details: [
        '1. 检查 OPENCLAW_WORKSPACE 环境变量',
        '2. 确保 OpenClaw Gateway 正在运行',
        '3. 参考 OpenClaw 文档进行安装',
      ],
    };
  }

  static templateRenderFailed(file: string, reason: string): MoltCareError {
    return {
      code: 'TEMPLATE_RENDER_FAILED',
      message: `模板渲染失败: ${file}`,
      suggestion: '检查模板文件是否损坏或变量是否正确',
      details: [reason],
    };
  }

  static fileWriteFailed(file: string, reason: string): MoltCareError {
    return {
      code: 'FILE_WRITE_FAILED',
      message: `文件写入失败: ${file}`,
      suggestion: '检查目标路径的写入权限和磁盘空间',
      details: [reason],
    };
  }
}

/**
 * 预设错误代码
 */
export const ErrorCodes = {
  PACK_NOT_FOUND: 'PACK_NOT_FOUND',
  PACK_ALREADY_INSTALLED: 'PACK_ALREADY_INSTALLED',
  INVALID_PACK_NAME: 'INVALID_PACK_NAME',
  CONFIG_NOT_FOUND: 'CONFIG_NOT_FOUND',
  CONFIG_INVALID: 'CONFIG_INVALID',
  OPENCLAW_NOT_FOUND: 'OPENCLAW_NOT_FOUND',
  TEMPLATE_RENDER_FAILED: 'TEMPLATE_RENDER_FAILED',
  FILE_WRITE_FAILED: 'FILE_WRITE_FAILED',
  PERMISSION_DENIED: 'PERMISSION_DENIED',
  NETWORK_ERROR: 'NETWORK_ERROR',
  UNKNOWN: 'UNKNOWN',
} as const;
