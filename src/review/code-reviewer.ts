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
          message: 'Found TODO/FIXME comment',
          suggestion: 'Resolve before committing'
        });
        score -= 5;
      }

      // Check for console.log
      if (line.includes('console.log') && !line.includes('//')) {
        comments.push({
          line: lineNum,
          severity: 'warning',
          message: 'Console.log statement found',
          suggestion: 'Use proper logging library'
        });
        score -= 3;
      }

      // Check line length
      if (line.length > 100) {
        comments.push({
          line: lineNum,
          severity: 'info',
          message: 'Line exceeds 100 characters',
          suggestion: 'Break into multiple lines'
        });
        score -= 1;
      }
    });

    // File-level checks
    if (!content.includes('/**') && content.length > 200) {
      comments.push({
        severity: 'warning',
        message: 'Missing JSDoc header',
        suggestion: 'Add file-level documentation'
      });
      score -= 5;
    }

    return {
      file: path.basename(filePath),
      score: Math.max(0, score),
      comments
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

  generateReport(reviews: FileReview[]): string {
    const lines: string[] = [];
    lines.push('# Code Review Report\n');
    
    const avgScore = reviews.length > 0 
      ? Math.round(reviews.reduce((sum, r) => sum + r.score, 0) / reviews.length)
      : 0;
    
    lines.push(`**Overall Score**: ${avgScore}/100\n`);
    lines.push(`**Files Reviewed**: ${reviews.length}\n`);
    lines.push('---\n');

    reviews.forEach(review => {
      const status = review.score >= 80 ? '✅' : review.score >= 60 ? '⚠️' : '❌';
      lines.push(`\n## ${status} ${review.file} (${review.score}/100)\n`);
      
      if (review.comments.length === 0) {
        lines.push('No issues found.\n');
      } else {
        review.comments.forEach(comment => {
          const icon = comment.severity === 'error' ? '🔴' : 
                      comment.severity === 'warning' ? '🟡' : '🔵';
          lines.push(`${icon} **Line ${comment.line || 'N/A'}**: ${comment.message}\n`);
          if (comment.suggestion) {
            lines.push(`   💡 ${comment.suggestion}\n`);
          }
        });
      }
    });

    return lines.join('');
  }
}
