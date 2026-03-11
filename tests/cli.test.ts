import { describe, it, expect } from 'vitest';
import { execSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const cliPath = path.join(__dirname, '../dist/cli/index.js');

describe('CLI Commands', () => {
  it('should show help', () => {
    try {
      const output = execSync(`node ${cliPath} --help`, { encoding: 'utf-8' });
      expect(output).toContain('moltcare');
      expect(output).toContain('init');
      expect(output).toContain('review');
    } catch (error: any) {
      // CLI 可能以非零状态码退出，但 help 内容仍在 stdout
      expect(error.stdout).toContain('moltcare');
      expect(error.stdout).toContain('init');
    }
  });

  it('should show version', () => {
    try {
      const output = execSync(`node ${cliPath} --version`, { encoding: 'utf-8' });
      expect(output).toContain('1.1.0');
    } catch (error: any) {
      expect(error.stdout).toContain('1.1.0');
    }
  });

  it('should show status', () => {
    try {
      const output = execSync(`node ${cliPath} status`, { encoding: 'utf-8' });
      expect(output).toContain('MoltCare');
    } catch (error: any) {
      expect(error.stdout || error.stderr || '').toContain('MoltCare');
    }
  });

  it('should show sync info', () => {
    try {
      const output = execSync(`node ${cliPath} sync`, { encoding: 'utf-8' });
      expect(output).toContain('KimiSensen');
    } catch (error: any) {
      expect(error.stdout || error.stderr || '').toContain('KimiSensen');
    }
  });
});
