import fs from 'fs/promises';
import path from 'path';

interface ReviewComment {
  line?: number;
  severity: 'error' | 'warning' | 'info';
  message: string;
  suggestion?: string;
}

interface FileReview {
  file: string;
  score: number;
  comments: ReviewComment[];
  issues: ReviewComment[];
}

/**
 * 代码评审器
 * 
 * @description 自动检测代码中的常见问题
 * @author OracleSensen
 * @since Phase 2
 */
export class CodeReviewer {
  async reviewFile(filePath: string): Promise<FileReview> {
    const content = await fs.readFile(filePath, 'utf-8');
    const lines = content.split('\n');
    const comments: ReviewComment[] = [];
    let score = 100;

    // Check for common issues
    lines.forEach((line, index) => {
      const lineNum = index + 1;

      // Check for TODO/FIXME
      if (line.includes('TODO') || line.includes('FIXME')) {
        comments.push({
          line: lineNum,
          severity: 'warning',
          message: '发现 TODO/FIXME 注释',
          suggestion: '提交前请解决'
        });
        score -= 5;
      }

      // Check for console.log
      if (line.includes('console.log') && !line.includes('//')) {
        comments.push({
          line: lineNum,
          severity: 'warning',
          message: '发现 console.log 语句',
          suggestion: '使用合适的日志库'
        });
        score -= 3;
      }

      // Check line length
      if (line.length > 120) {
        comments.push({
          line: lineNum,
          severity: 'info',
          message: '行长度超过120个字符',
          suggestion: '建议换行'
        });
        score -= 1;
      }
    });

    // File-level checks
    if (!content.includes('/**') && content.length > 50) {
      comments.push({
        severity: 'warning',
        message: '缺少 JSDoc 注释',
        suggestion: '添加文件级文档'
      });
      score -= 5;
    }

    return {
      file: path.basename(filePath),
      score: Math.max(0, score),
      comments,
      issues: comments
    };
  }

  async reviewDirectory(dir: string): Promise<FileReview[]> {
    const results: FileReview[] = [];
    
    try {
      const files = await fs.readdir(dir);
      
      for (const file of files) {
        if (file.endsWith('.ts') && !file.endsWith('.d.ts')) {
          const filePath = path.join(dir, file);
          const stat = await fs.stat(filePath);
          
          if (stat.isFile()) {
            const review = await this.reviewFile(filePath);
            results.push(review);
          }
        }
      }
    } catch {
      // Directory doesn't exist or can't read
    }

    return results;
  }

  generateReport(reviews: FileReview[], format: 'markdown' | 'json' = 'markdown'): string {
    if (format === 'json') {
      const summary = {
        summary: {
          totalFiles: reviews.length,
          avgScore: reviews.length > 0 
            ? Math.round(reviews.reduce((sum, r) => sum + r.score, 0) / reviews.length)
            : 0
        },
        files: reviews.map(r => ({
          file: r.file,
          score: r.score,
          issues: r.issues
        }))
      };
      return JSON.stringify(summary, null, 2);
    }

    const lines: string[] = [];
    lines.push('# 代码评审报告\n');
    
    const avgScore = reviews.length > 0 
      ? Math.round(reviews.reduce((sum, r) => sum + r.score, 0) / reviews.length)
      : 0;
    
    lines.push(`**总体评分**: ${avgScore}/100\n`);
    lines.push(`**评审文件数**: ${reviews.length}\n`);
    lines.push('---\n');

    reviews.forEach(review => {
      const status = review.score >= 80 ? '✅' : review.score >= 60 ? '⚠️' : '❌';
      lines.push(`\n## ${status} ${review.file} (${review.score}/100)\n`);
      
      if (review.comments.length === 0) {
        lines.push('未发现 issues。\n');
      } else {
        review.comments.forEach(comment => {
          const icon = comment.severity === 'error' ? '🔴' : 
                      comment.severity === 'warning' ? '🟡' : '🔵';
          lines.push(`${icon} **第 ${comment.line || 'N/A'} 行**: ${comment.message}\n`);
          if (comment.suggestion) {
            lines.push(`   💡 ${comment.suggestion}\n`);
          }
        });
      }
    });

    return lines.join('');
  }

  /**
   * 计算代码评分
   */
  calculateScore(issues: ReviewComment[], lines: number): number {
    let score = 100;
    
    for (const issue of issues) {
      if (issue.severity === 'error') {
        score -= 10;
      } else if (issue.severity === 'warning') {
        score -= 5;
      } else {
        score -= 1;
      }
    }
    
    // 根据代码行数调整（代码越多，允许的问题数可以适当增加）
    const allowedIssues = Math.max(3, Math.floor(lines / 50));
    if (issues.length > allowedIssues) {
      score -= (issues.length - allowedIssues) * 2;
    }
    
    return Math.max(0, Math.min(100, score));
  }
}
