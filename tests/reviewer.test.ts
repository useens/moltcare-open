import { describe, it, expect } from 'vitest';
import { CodeReviewer, ReviewRule } from '../src/review/code-reviewer';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

describe('CodeReviewer', () => {
  let tempDir: string;

  const createTempFile = (content: string, filename = 'test.ts') => {
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'review-test-'));
    const filePath = path.join(tempDir, filename);
    fs.writeFileSync(filePath, content);
    return filePath;
  };

  const cleanup = () => {
    if (tempDir && fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true });
    }
  };

  describe('reviewFile', () => {
    it('should detect TODO comments', async () => {
      const filePath = createTempFile('// TODO: fix this\nconst x = 1;');
      const reviewer = new CodeReviewer();
      
      const result = await reviewer.reviewFile(filePath);
      
      expect(result.issues.some(i => i.message.includes('TODO'))).toBe(true);
      cleanup();
    });

    it('should detect console.log', async () => {
      const filePath = createTempFile('console.log("debug");\nconst x = 1;');
      const reviewer = new CodeReviewer();
      
      const result = await reviewer.reviewFile(filePath);
      
      expect(result.issues.some(i => i.message.includes('console.log'))).toBe(true);
      cleanup();
    });

    it('should detect long lines', async () => {
      const longLine = 'const x = "' + 'a'.repeat(120) + '";\n';
      const filePath = createTempFile(longLine);
      const reviewer = new CodeReviewer();
      
      const result = await reviewer.reviewFile(filePath);
      
      expect(result.issues.some(i => i.message.includes('行长度'))).toBe(true);
      cleanup();
    });

    it('should pass clean code', async () => {
      const cleanCode = `const x = 1;
// This is a normal comment
function add(a: number, b: number): number {
  return a + b;
}`;
      const filePath = createTempFile(cleanCode);
      const reviewer = new CodeReviewer();
      
      const result = await reviewer.reviewFile(filePath);
      
      expect(result.score).toBeGreaterThan(80);
      cleanup();
    });

    it('should handle missing JSDoc for functions', async () => {
      const code = `function complexFunction(a, b, c) {
  return a + b + c;
}`;
      const filePath = createTempFile(code);
      const reviewer = new CodeReviewer();
      
      const result = await reviewer.reviewFile(filePath);
      
      expect(result.issues.some(i => i.message.includes('JSDoc'))).toBe(true);
      cleanup();
    });
  });

  describe('reviewDirectory', () => {
    it('should review all TypeScript files in directory', async () => {
      tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'review-dir-test-'));
      fs.writeFileSync(path.join(tempDir, 'file1.ts'), '// TODO: fix');
      fs.writeFileSync(path.join(tempDir, 'file2.ts'), 'const x = 1;');
      
      const reviewer = new CodeReviewer();
      const results = await reviewer.reviewDirectory(tempDir);
      
      expect(results.length).toBe(2);
      cleanup();
    });

    it('should filter .d.ts files', async () => {
      tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'review-dts-test-'));
      fs.writeFileSync(path.join(tempDir, 'file.ts'), 'const x = 1;');
      fs.writeFileSync(path.join(tempDir, 'file.d.ts'), 'declare const x: number;');
      
      const reviewer = new CodeReviewer();
      const results = await reviewer.reviewDirectory(tempDir);
      
      expect(results.length).toBe(1);
      expect(results[0].file).not.toContain('.d.ts');
      cleanup();
    });
  });

  describe('calculateScore', () => {
    it('should calculate high score for clean code', () => {
      const reviewer = new CodeReviewer();
      const issues: any[] = [];
      const lines = 100;
      
      const score = (reviewer as any).calculateScore(issues, lines);
      
      expect(score).toBe(100);
    });

    it('should reduce score for issues', () => {
      const reviewer = new CodeReviewer();
      const issues = [
        { severity: 'error' },
        { severity: 'warning' },
        { severity: 'info' }
      ];
      const lines = 100;
      
      const score = (reviewer as any).calculateScore(issues, lines);
      
      expect(score).toBeLessThan(100);
      expect(score).toBeGreaterThan(0);
    });
  });

  describe('generateReport', () => {
    it('should generate markdown report', async () => {
      tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'review-report-test-'));
      fs.writeFileSync(path.join(tempDir, 'file.ts'), '// TODO: fix\nconst x = 1;');
      
      const reviewer = new CodeReviewer();
      const results = await reviewer.reviewDirectory(tempDir);
      const report = reviewer.generateReport(results, 'markdown');
      
      expect(report).toContain('# 代码评审报告');
      expect(report).toContain('TODO');
      cleanup();
    });

    it('should generate JSON report', async () => {
      tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'review-json-test-'));
      fs.writeFileSync(path.join(tempDir, 'file.ts'), 'const x = 1;');
      
      const reviewer = new CodeReviewer();
      const results = await reviewer.reviewDirectory(tempDir);
      const report = reviewer.generateReport(results, 'json');
      
      const parsed = JSON.parse(report);
      expect(parsed).toHaveProperty('summary');
      expect(parsed).toHaveProperty('files');
      cleanup();
    });
  });
});
