/**
 * CLI Commands Integration Tests
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { initCommand } from '../src/cli/commands/init';
import { listCommand } from '../src/cli/commands/list';
import { applyCommand } from '../src/cli/commands/apply';
import { ConfigManager, resetConfig } from '../src/config';

// Mock console methods
const mockConsole = {
  log: vi.spyOn(console, 'log').mockImplementation(() => {}),
  error: vi.spyOn(console, 'error').mockImplementation(() => {}),
  warn: vi.spyOn(console, 'warn').mockImplementation(() => {}),
};

describe('CLI Commands', () => {
  let tempDir: string;
  let originalCwd: string;
  let originalExit: typeof process.exit;

  beforeEach(() => {
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'moltcare-cli-test-'));
    originalCwd = process.cwd();
    originalExit = process.exit;
    process.exit = vi.fn() as any;
    process.chdir(tempDir);
    resetConfig();
    mockConsole.log.mockClear();
    mockConsole.error.mockClear();
    mockConsole.warn.mockClear();
  });

  afterEach(() => {
    process.exit = originalExit;
    process.chdir(originalCwd);
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true });
    }
  });

  describe('init command', () => {
    it('should initialize with default options', async () => {
      await initCommand({ yes: true, force: true });
      
      // 检查输出包含关键信息（可能带 ANSI 颜色代码）
      const logs = mockConsole.log.mock.calls.flat().join('');
      expect(logs).toContain('初始化完成');
    });

    it('should force reinitialization', async () => {
      await initCommand({ yes: true, force: true });
      
      const logs = mockConsole.log.mock.calls.flat().join('');
      expect(logs).toContain('初始化完成');
    });
  });

  describe('list command', () => {
    it.skip('should list packs', async () => {
      await listCommand({});
      
      expect(mockConsole.log).toHaveBeenCalled();
    });

    it.skip('should list packs with JSON output', async () => {
      await listCommand({ json: true });
      
      expect(mockConsole.log).toHaveBeenCalled();
    });
  });

  describe('apply command', () => {
    it('should show error for invalid pack name', async () => {
      try {
        await applyCommand('', {});
      } catch (error) {
        // Expected to throw
      }
      
      expect(mockConsole.error).toHaveBeenCalled();
    });
  });
});
