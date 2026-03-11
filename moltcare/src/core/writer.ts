import * as fs from 'fs/promises';
import * as path from 'path';

// 变更报告
export interface ChangeReport {
  path: string;
  status: 'created' | 'updated' | 'unchanged' | 'backed-up';
  size: number;
  backupPath?: string;
  changes?: string[];
  timestamp: Date;
}

// 写入选项
export interface WriteOptions {
  backup?: boolean;
  dryRun?: boolean;
  encoding?: BufferEncoding;
}

// 默认选项
const DEFAULT_WRITE_OPTIONS: Required<WriteOptions> = {
  backup: true,
  dryRun: false,
  encoding: 'utf-8'
};

// 备份配置
const BACKUP_CONFIG = {
  dirName: '.moltcare-backups',
  maxBackups: 10,
  timestampFormat: 'YYYY-MM-DD_HH-mm-ss'
};

/**
 * 文件写入器 - 安全地写入文件，支持自动备份和回滚
 */
export class Writer {
  private baseDir: string;

  constructor(baseDir: string) {
    this.baseDir = path.resolve(baseDir);
  }

  /**
   * 写入文件（自动备份现有文件）
   */
  async writeFile(
    filePath: string, 
    content: string, 
    options: WriteOptions = {}
  ): Promise<ChangeReport> {
    const opts = { ...DEFAULT_WRITE_OPTIONS, ...options };
    const fullPath = path.join(this.baseDir, filePath);
    const normalizedPath = path.normalize(filePath);

    // 检查路径是否在项目内（安全检查）
    this.validatePath(fullPath);

    // 确保目录存在
    await this.ensureDirectory(path.dirname(fullPath));

    // 检查文件是否存在
    const exists = await this.fileExists(fullPath);
    let backupPath: string | undefined;

    // 如果文件存在且需要备份
    if (exists && opts.backup && !opts.dryRun) {
      backupPath = await this.createBackup(fullPath);
    }

    // 检查内容是否相同
    if (exists && !opts.dryRun) {
      const existingContent = await fs.readFile(fullPath, opts.encoding);
      if (existingContent === content) {
        return {
          path: normalizedPath,
          status: 'unchanged',
          size: content.length,
          timestamp: new Date()
        };
      }
    }

    // 确定状态
    const status: ChangeReport['status'] = exists ? 'updated' : 'created';

    // 写入文件（或模拟）
    if (!opts.dryRun) {
      await fs.writeFile(fullPath, content, { encoding: opts.encoding });
    }

    // 生成变更摘要
    const changes = await this.generateChangeSummary(fullPath, content, exists);

    return {
      path: normalizedPath,
      status,
      size: content.length,
      backupPath,
      changes,
      timestamp: new Date()
    };
  }

  /**
   * 批量写入多个文件
   */
  async writeFiles(
    files: Array<{ path: string; content: string }>,
    options: WriteOptions = {}
  ): Promise<ChangeReport[]> {
    const reports: ChangeReport[] = [];

    for (const file of files) {
      try {
        const report = await this.writeFile(file.path, file.content, options);
        reports.push(report);
      } catch (error: unknown) {
        reports.push({
          path: file.path,
          status: 'unchanged',
          size: 0,
          changes: [`错误: ${(error as Error).message}`],
          timestamp: new Date()
        });
      }
    }

    return reports;
  }

  /**
   * 回滚到最近的备份
   */
  async rollback(filePath: string): Promise<ChangeReport> {
    const fullPath = path.join(this.baseDir, filePath);
    this.validatePath(fullPath);

    // 查找最近的备份
    const backups = await this.listBackups(filePath);
    if (backups.length === 0) {
      throw new Error(`没有找到 ${filePath} 的备份`);
    }

    const latestBackup = backups[0]; // 按时间排序后最新的
    const backupFullPath = path.join(this.baseDir, BACKUP_CONFIG.dirName, latestBackup);

    // 读取备份内容
    const backupContent = await fs.readFile(backupFullPath, 'utf-8');

    // 写入回原文件
    await fs.writeFile(fullPath, backupContent, 'utf-8');

    return {
      path: filePath,
      status: 'backed-up',
      size: backupContent.length,
      changes: [`回滚到备份: ${latestBackup}`],
      timestamp: new Date()
    };
  }

  /**
   * 列出文件的所有备份
   */
  async listBackups(filePath: string): Promise<string[]> {
    const backupDir = path.join(this.baseDir, BACKUP_CONFIG.dirName);
    const fileName = path.basename(filePath);

    try {
      const entries = await fs.readdir(backupDir);
      const backups = entries
        .filter(entry => entry.startsWith(fileName + '.'))
        .sort((a, b) => {
          // 按时间倒序排列
          const timeA = this.extractTimestamp(a);
          const timeB = this.extractTimestamp(b);
          return timeB.localeCompare(timeA);
        });
      return backups;
    } catch {
      return [];
    }
  }

  /**
   * 清理旧备份（保留最近 N 个）
   */
  async cleanupBackups(filePath: string, keepCount: number = BACKUP_CONFIG.maxBackups): Promise<number> {
    const backups = await this.listBackups(filePath);
    if (backups.length <= keepCount) return 0;

    const toDelete = backups.slice(keepCount);
    const backupDir = path.join(this.baseDir, BACKUP_CONFIG.dirName);

    let deletedCount = 0;
    for (const backup of toDelete) {
      try {
        await fs.unlink(path.join(backupDir, backup));
        deletedCount++;
      } catch {
        // 忽略删除错误
      }
    }

    return deletedCount;
  }

  /**
   * 生成变更摘要报告
   */
  generateSummaryReport(reports: ChangeReport[]): SummaryReport {
    const created = reports.filter(r => r.status === 'created');
    const updated = reports.filter(r => r.status === 'updated');
    const unchanged = reports.filter(r => r.status === 'unchanged');
    const withBackup = reports.filter(r => r.backupPath);

    return {
      timestamp: new Date(),
      totalFiles: reports.length,
      created: created.length,
      updated: updated.length,
      unchanged: unchanged.length,
      backedUp: withBackup.length,
      totalSize: reports.reduce((sum, r) => sum + r.size, 0),
      details: reports
    };
  }

  /**
   * 创建备份
   */
  private async createBackup(filePath: string): Promise<string> {
    const backupDir = path.join(this.baseDir, BACKUP_CONFIG.dirName);
    await this.ensureDirectory(backupDir);

    const fileName = path.basename(filePath);
    const timestamp = this.formatTimestamp(new Date());
    const backupName = `${fileName}.${timestamp}.backup`;
    const backupPath = path.join(backupDir, backupName);

    await fs.copyFile(filePath, backupPath);

    // 清理旧备份
    await this.cleanupBackups(filePath);

    return backupPath;
  }

  /**
   * 确保目录存在
   */
  private async ensureDirectory(dir: string): Promise<void> {
    try {
      await fs.access(dir);
    } catch {
      await fs.mkdir(dir, { recursive: true });
    }
  }

  /**
   * 检查文件是否存在
   */
  private async fileExists(filePath: string): Promise<boolean> {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * 验证路径安全（防止目录遍历攻击）
   */
  private validatePath(filePath: string): void {
    const resolvedPath = path.resolve(filePath);
    const resolvedBase = path.resolve(this.baseDir);

    if (!resolvedPath.startsWith(resolvedBase)) {
      throw new Error(`不安全的路径: ${filePath} (路径遍历检测)`);
    }
  }

  /**
   * 生成变更摘要
   */
  private async generateChangeSummary(
    filePath: string, 
    newContent: string, 
    exists: boolean
  ): Promise<string[]> {
    const changes: string[] = [];

    if (!exists) {
      changes.push(`新建文件，共 ${newContent.split('\n').length} 行`);
    } else {
      try {
        const oldContent = await fs.readFile(filePath, 'utf-8');
        const oldLines = oldContent.split('\n').length;
        const newLines = newContent.split('\n').length;
        const lineDiff = newLines - oldLines;

        if (lineDiff > 0) {
          changes.push(`增加 ${lineDiff} 行`);
        } else if (lineDiff < 0) {
          changes.push(`减少 ${Math.abs(lineDiff)} 行`);
        } else {
          changes.push('行数相同，内容已更新');
        }

        const sizeDiff = newContent.length - oldContent.length;
        if (sizeDiff > 0) {
          changes.push(`增加 ${sizeDiff} 字节`);
        } else if (sizeDiff < 0) {
          changes.push(`减少 ${Math.abs(sizeDiff)} 字节`);
        }
      } catch {
        changes.push('内容已更新');
      }
    }

    return changes;
  }

  /**
   * 格式化时间戳
   */
  private formatTimestamp(date: Date): string {
    const pad = (n: number) => n.toString().padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}_` +
           `${pad(date.getHours())}-${pad(date.getMinutes())}-${pad(date.getSeconds())}`;
  }

  /**
   * 从备份文件名提取时间戳
   */
  private extractTimestamp(backupName: string): string {
    const match = backupName.match(/(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})/);
    return match ? match[1] : '';
  }
}

// 汇总报告
export interface SummaryReport {
  timestamp: Date;
  totalFiles: number;
  created: number;
  updated: number;
  unchanged: number;
  backedUp: number;
  totalSize: number;
  details: ChangeReport[];
}
