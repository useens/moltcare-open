import * as fs from 'fs/promises';
import * as path from 'path';

// 核心文件列表
export const CORE_FILES = [
  'SOUL.md',
  'AGENTS.md',
  'IDENTITY.md',
  'MEMORY.md',
  'HEARTBEAT.md',
  'TOOLS.md',
  'USER.md'
] as const;

export type CoreFile = typeof CORE_FILES[number];

// 文件分析结果
export interface FileAnalysis {
  path: string;
  exists: boolean;
  size: number;
  lastModified?: Date;
  quality: QualityScore;
  missingSections: string[];
  suggestions: string[];
}

// 质量评分
export interface QualityScore {
  total: number;        // 0-100
  completeness: number; // 完整性 0-30
  structure: number;    // 结构 0-30
  content: number;      // 内容 0-40
}

// 分析器配置
export interface AnalyzerOptions {
  strictMode?: boolean;
  checkSections?: boolean;
}

// 默认配置
const DEFAULT_OPTIONS: Required<AnalyzerOptions> = {
  strictMode: true,
  checkSections: true
};

/**
 * 文件分析器 - 分析现有核心文件的质量和完整性
 */
export class Analyzer {
  private baseDir: string;
  private options: Required<AnalyzerOptions>;

  constructor(baseDir: string, options: AnalyzerOptions = {}) {
    this.baseDir = path.resolve(baseDir);
    this.options = { ...DEFAULT_OPTIONS, ...options };
  }

  /**
   * 扫描现有核心文件
   */
  async scanExistingFiles(): Promise<string[]> {
    const existing: string[] = [];

    for (const file of CORE_FILES) {
      const filePath = path.join(this.baseDir, file);
      try {
        await fs.access(filePath);
        existing.push(file);
      } catch {
        // 文件不存在，跳过
      }
    }

    return existing;
  }

  /**
   * 扫描缺失的核心文件
   */
  async scanMissingFiles(): Promise<string[]> {
    const existing = await this.scanExistingFiles();
    return CORE_FILES.filter(f => !existing.includes(f));
  }

  /**
   * 分析单个文件
   */
  async analyzeFile(filename: CoreFile): Promise<FileAnalysis> {
    const filePath = path.join(this.baseDir, filename);

    try {
      const stats = await fs.stat(filePath);
      const content = await fs.readFile(filePath, 'utf-8');

      const quality = this.calculateQuality(filename, content);
      const missingSections = this.options.checkSections 
        ? this.identifyMissingSections(filename, content)
        : [];
      const suggestions = this.generateSuggestions(filename, content, quality);

      return {
        path: filename,
        exists: true,
        size: stats.size,
        lastModified: stats.mtime,
        quality,
        missingSections,
        suggestions
      };
    } catch (error: unknown) {
      // 文件不存在或无法读取
      return {
        path: filename,
        exists: false,
        size: 0,
        quality: { total: 0, completeness: 0, structure: 0, content: 0 },
        missingSections: this.getExpectedSections(filename),
        suggestions: [`文件不存在，建议创建 ${filename}`]
      };
    }
  }

  /**
   * 分析所有核心文件
   */
  async analyzeAll(): Promise<FileAnalysis[]> {
    const results: FileAnalysis[] = [];

    for (const file of CORE_FILES) {
      const analysis = await this.analyzeFile(file);
      results.push(analysis);
    }

    return results;
  }

  /**
   * 生成项目健康报告
   */
  async generateHealthReport(): Promise<HealthReport> {
    const analyses = await this.analyzeAll();
    const existingFiles = analyses.filter(a => a.exists);
    const missingFiles = analyses.filter(a => !a.exists);

    const overallScore = existingFiles.length > 0
      ? Math.round(existingFiles.reduce((sum, a) => sum + a.quality.total, 0) / existingFiles.length)
      : 0;

    return {
      timestamp: new Date(),
      baseDir: this.baseDir,
      summary: {
        totalFiles: CORE_FILES.length,
        existingFiles: existingFiles.length,
        missingFiles: missingFiles.length,
        overallScore,
        status: this.determineStatus(overallScore, existingFiles.length)
      },
      analyses,
      recommendations: this.generateRecommendations(analyses)
    };
  }

  /**
   * 计算文件质量评分
   */
  private calculateQuality(_filename: string, content: string): QualityScore {
    const completeness = this.scoreCompleteness(_filename, content);
    const structure = this.scoreStructure(content);
    const contentScore = this.scoreContent(content);

    return {
      completeness,
      structure,
      content: contentScore,
      total: Math.round(completeness + structure + contentScore)
    };
  }

  /**
   * 评分：完整性 (0-30)
   */
  private scoreCompleteness(filename: string, content: string): number {
    const expectedSections = this.getExpectedSections(filename);
    if (expectedSections.length === 0) return 30;

    const foundSections = expectedSections.filter(section => 
      content.toLowerCase().includes(section.toLowerCase())
    );

    return Math.round((foundSections.length / expectedSections.length) * 30);
  }

  /**
   * 评分：结构 (0-30)
   */
  private scoreStructure(content: string): number {
    let score = 0;

    // 有标题 (h1-h6)
    if (/^#{1,6}\s/m.test(content)) score += 10;

    // 有表格
    if (/\|.*\|.*\|/.test(content)) score += 5;

    // 有列表
    if (/^[-*+]\s/m.test(content)) score += 5;

    // 有代码块
    if (/```[\s\S]*?```/.test(content)) score += 5;

    // 有链接
    if (/\[.*\]\(.*\)/.test(content)) score += 5;

    return score;
  }

  /**
   * 评分：内容 (0-40)
   */
  private scoreContent(content: string): number {
    let score = 0;

    // 内容长度
    const lines = content.split('\n').length;
    if (lines >= 50) score += 15;
    else if (lines >= 20) score += 10;
    else if (lines >= 10) score += 5;

    // 字数
    const chars = content.length;
    if (chars >= 1000) score += 15;
    else if (chars >= 500) score += 10;
    else if (chars >= 200) score += 5;

    // 有实际内容（非模板占位符）
    if (!/TODO|FIXME|待补充|placeholder/i.test(content)) score += 10;

    return score;
  }

  /**
   * 识别缺失的章节
   */
  private identifyMissingSections(filename: string, content: string): string[] {
    const expected = this.getExpectedSections(filename);
    return expected.filter(section => 
      !content.toLowerCase().includes(section.toLowerCase())
    );
  }

  /**
   * 获取文件预期的章节
   */
  private getExpectedSections(_filename: string): string[] {
    const sections: Record<string, string[]> = {
      'SOUL.md': ['核心身份', '原则', '使命'],
      'AGENTS.md': ['工作流', '快速导航'],
      'IDENTITY.md': ['核心身份', '角色', '特质'],
      'MEMORY.md': ['记忆结构', '记录原则'],
      'HEARTBEAT.md': ['自动化检查', '频率'],
      'TOOLS.md': ['环境信息', '可用工具'],
      'USER.md': ['基本信息', '偏好']
    };

    return sections[_filename] || [];
  }

  /**
   * 生成建议
   */
  private generateSuggestions(_filename: string, content: string, quality: QualityScore): string[] {
    const suggestions: string[] = [];

    if (quality.completeness < 20) {
      suggestions.push(`补充缺失的核心章节`);
    }

    if (quality.structure < 15) {
      suggestions.push(`优化文档结构，添加表格或列表`);
    }

    if (quality.content < 20) {
      suggestions.push(`扩充内容，提供更多详细信息`);
    }

    if (/TODO|FIXME|待补充/i.test(content)) {
      suggestions.push(`替换模板占位符为实际内容`);
    }

    if (suggestions.length === 0) {
      suggestions.push('文件质量良好');
    }

    return suggestions;
  }

  /**
   * 生成整体建议
   */
  private generateRecommendations(analyses: FileAnalysis[]): string[] {
    const recommendations: string[] = [];
    const existingFiles = analyses.filter(a => a.exists);
    const missingFiles = analyses.filter(a => !a.exists);
    const lowQualityFiles = existingFiles.filter(a => a.quality.total < 50);

    // 缺失文件建议
    if (missingFiles.length > 0) {
      const criticalFiles = missingFiles.filter(f => 
        ['SOUL.md', 'AGENTS.md'].includes(f.path)
      );
      if (criticalFiles.length > 0) {
        recommendations.push(`优先创建核心文件: ${criticalFiles.map(f => f.path).join(', ')}`);
      }
    }

    // 低质量文件建议
    if (lowQualityFiles.length > 0) {
      recommendations.push(`需要改进的文件: ${lowQualityFiles.map(f => f.path).join(', ')}`);
    }

    // 整体建议
    const avgScore = existingFiles.length > 0
      ? existingFiles.reduce((sum, a) => sum + a.quality.total, 0) / existingFiles.length
      : 0;

    if (avgScore < 60) {
      recommendations.push('整体文件质量有待提升，建议参考最佳实践模板');
    } else if (avgScore >= 80) {
      recommendations.push('文件质量优秀，保持维护');
    }

    return recommendations;
  }

  /**
   * 确定项目健康状态
   */
  private determineStatus(score: number, existingCount: number): HealthStatus {
    if (existingCount < 2) return 'critical';
    if (score < 40) return 'poor';
    if (score < 60) return 'fair';
    if (score < 80) return 'good';
    return 'excellent';
  }
}

// 健康报告
export interface HealthReport {
  timestamp: Date;
  baseDir: string;
  summary: {
    totalFiles: number;
    existingFiles: number;
    missingFiles: number;
    overallScore: number;
    status: HealthStatus;
  };
  analyses: FileAnalysis[];
  recommendations: string[];
}

// 健康状态
export type HealthStatus = 'excellent' | 'good' | 'fair' | 'poor' | 'critical';
