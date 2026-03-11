import { describe, it, expect } from 'vitest';
import { CodeReviewer } from '../src/review/code-reviewer.js';
import fs from 'fs/promises';
import path from 'path';
import os from 'os';

describe('CodeReviewer', () => {
  const testDir = path.join(os.tmpdir(), 'moltcare-review-test-' + Date.now());

  it('should detect TODO comments', async () => {
    const reviewer = new CodeReviewer();
    const testFile = path.join(testDir, 'test.ts');
    
    await fs.mkdir(testDir, { recursive: true });
    await fs.writeFile(testFile, '// TODO: fix this\nconsole.log("test");');
    
    const result = await reviewer.reviewFile(testFile);
    
    expect(result.score).toBeLessThan(100);
    expect(result.comments.some(c => c.message.includes('TODO'))).toBe(true);
    
    await fs.rm(testDir, { recursive: true, force: true });
  });

  it('should detect console.log', async () => {
    const reviewer = new CodeReviewer();
    const testFile = path.join(testDir, 'test2.ts');
    
    await fs.mkdir(testDir, { recursive: true });
    await fs.writeFile(testFile, 'console.log("debug");');
    
    const result = await reviewer.reviewFile(testFile);
    
    expect(result.comments.some(c => c.message.toLowerCase().includes('console'))).toBe(true);
    
    await fs.rm(testDir, { recursive: true, force: true });
  });

  it('should generate report', async () => {
    const reviewer = new CodeReviewer();
    const reviews = [
      { file: 'test.ts', score: 90, comments: [] },
      { file: 'test2.ts', score: 80, comments: [{ line: 1, severity: 'warning' as const, message: 'Test' }] }
    ];
    
    const report = reviewer.generateReport(reviews);
    
    expect(report).toContain('代码评审报告');
    expect(report).toContain('85/100');  // Average score
  });
});
