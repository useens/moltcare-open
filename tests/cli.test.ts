import { describe, it, expect } from 'vitest';
import { execSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const cliPath = path.join(__dirname, '../dist/cli/index.js');

describe('CLI Commands', () => {
  it('should show help', () => {
    const output = execSync(`node ${cliPath} --help`, { encoding: 'utf-8' });
    expect(output).toContain('moltcare');
    expect(output).toContain('init');
    expect(output).toContain('review');
  });

  it('should show version', () => {
    const output = execSync(`node ${cliPath} --version`, { encoding: 'utf-8' });
    expect(output).toContain('1.0.0');
  });

  it('should show status', () => {
    const output = execSync(`node ${cliPath} status`, { encoding: 'utf-8' });
    expect(output).toContain('MoltCare');
  });

  it('should show sync info', () => {
    const output = execSync(`node ${cliPath} sync`, { encoding: 'utf-8' });
    expect(output).toContain('KimiSensen');
    expect(output).toContain('OracleSensen');
  });
});
