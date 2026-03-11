/**
 * CLI Commands Integration Tests
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { initCommand } from '../src/commands/init.js';
import { listCommand } from '../src/commands/list.js';
import { applyCommand } from '../src/commands/apply.js';
import { ConfigManager, resetConfig } from '../src/config.js';

// Mock console methods
const mockConsole = {
  log: vi.spyOn(console, 'log').mockImplementation(() => {}),
  error: vi.spyOn(console, 'error').mockImplementation(() => {}),
  warn: vi.spyOn(console, 'warn').mockImplementation(() => {}),
};

describe('Commands Integration', () => {
  let tempDir: string;
  let originalCwd: string;
  let configPath: string;

  beforeEach(() => {
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'moltcare-cmd-test-'));
    originalCwd = process.cwd();
    process.chdir(tempDir);
    configPath = path.join(tempDir, '.moltcare', 'config.yaml');
    resetConfig();
    
    // Reset mocks
    vi.clearAllMocks();
  });

  afterEach(() => {
    process.chdir(originalCwd);
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true });
    }
    vi.clearAllMocks();
  });

  describe('init command', () => {
    it('should initialize with --yes option', async () => {
      await initCommand({ yes: true, workspace: tempDir });
      
      const config = new ConfigManager(configPath);
      expect(config.isInitialized()).toBe(true);
      expect(config.get('workspacePath')).toBe(tempDir);
    });

    it('should create workspace structure', async () => {
      await initCommand({ yes: true, workspace: tempDir });
      
      expect(fs.existsSync(path.join(tempDir, 'memory'))).toBe(true);
      expect(fs.existsSync(path.join(tempDir, 'scripts'))).toBe(true);
      expect(fs.existsSync(path.join(tempDir, 'docs'))).toBe(true);
      expect(fs.existsSync(path.join(tempDir, 'docs', 'README.md'))).toBe(true);
    });

    it('should not reinitialize without --force', async () => {
      await initCommand({ yes: true, workspace: tempDir });
      
      // Reset mock to check for warning message
      mockConsole.log.mockClear();
      await initCommand({ yes: true, workspace: tempDir });
      
      // Should warn about already initialized
      const logs = mockConsole.log.mock.calls.map(c => c[0]).join(' ');
      expect(logs).toContain('已经初始化');
    });

    it('should reinitialize with --force', async () => {
      await initCommand({ yes: true, workspace: tempDir });
      
      mockConsole.log.mockClear();
      await initCommand({ yes: true, force: true, workspace: tempDir });
      
      // Should show force mode message
      const logs = mockConsole.log.mock.calls.map(c => c[0]).join(' ');
      expect(logs).toContain('强制');
    });
  });

  describe('list command', () => {
    it('should fail if not initialized', async () => {
      const exitSpy = vi.spyOn(process, 'exit').mockImplementation(() => {
        throw new Error('Process exit');
      });

      await expect(listCommand({})).rejects.toThrow();
      
      exitSpy.mockRestore();
    });

    it('should list packs after initialization', async () => {
      // Setup: init with custom packs dir
      const packsDir = path.join(tempDir, 'packs');
      fs.mkdirSync(packsDir, { recursive: true });
      
      // Create a test pack
      const packDir = path.join(packsDir, 'test-pack');
      fs.mkdirSync(packDir, { recursive: true });
      fs.writeFileSync(
        path.join(packDir, 'manifest.json'),
        JSON.stringify({
          name: 'test-pack',
          version: '1.0.0',
          description: 'Test pack',
        })
      );

      await initCommand({ yes: true, workspace: tempDir });
      
      // Update config to use our test packs dir
      const config = new ConfigManager(configPath);
      config.set('packsDir', packsDir);
      
      resetConfig();
      
      mockConsole.log.mockClear();
      await listCommand({});
      
      // Should show the test pack
      const logs = mockConsole.log.mock.calls.map(c => String(c[0])).join(' ');
      expect(logs).toContain('test-pack');
    });

    it('should filter by category', async () => {
      // Setup packs
      const packsDir = path.join(tempDir, 'packs');
      fs.mkdirSync(packsDir, { recursive: true });
      
      // Create packs in different categories
      const foundationDir = path.join(packsDir, 'foundation');
      fs.mkdirSync(foundationDir, { recursive: true });
      fs.writeFileSync(
        path.join(foundationDir, 'manifest.json'),
        JSON.stringify({
          name: 'foundation',
          version: '1.0.0',
          category: 'foundation',
        })
      );

      const otherDir = path.join(packsDir, 'other');
      fs.mkdirSync(otherDir, { recursive: true });
      fs.writeFileSync(
        path.join(otherDir, 'manifest.json'),
        JSON.stringify({
          name: 'other',
          version: '1.0.0',
          category: 'other',
        })
      );

      await initCommand({ yes: true, workspace: tempDir });
      
      const config = new ConfigManager(configPath);
      config.set('packsDir', packsDir);
      resetConfig();
      
      // Should work without error
      await expect(listCommand({ category: 'foundation' })).resolves.not.toThrow();
    });

    it('should output JSON when requested', async () => {
      const packsDir = path.join(tempDir, 'packs');
      fs.mkdirSync(packsDir, { recursive: true });

      await initCommand({ yes: true, workspace: tempDir });
      
      const config = new ConfigManager(configPath);
      config.set('packsDir', packsDir);
      resetConfig();
      
      mockConsole.log.mockClear();
      await listCommand({ json: true });
      
      // Should output valid JSON
      const output = mockConsole.log.mock.calls[0]?.[0];
      if (output) {
        expect(() => JSON.parse(output)).not.toThrow();
      }
    });
  });

  describe('apply command', () => {
    beforeEach(async () => {
      // Create packs directory with a test pack
      const packsDir = path.join(tempDir, 'packs');
      const testPackDir = path.join(packsDir, 'test-pack');
      const templatesDir = path.join(testPackDir, 'templates');
      
      fs.mkdirSync(templatesDir, { recursive: true });
      
      // Create manifest
      fs.writeFileSync(
        path.join(testPackDir, 'manifest.json'),
        JSON.stringify({
          name: 'test-pack',
          version: '1.0.0',
          description: 'Test pack for apply command',
          templates: [
            {
              file: 'templates/hello.md',
              target: 'hello.md',
              required: true,
            },
          ],
          config: {
            backupExisting: true,
          },
        })
      );
      
      // Create template file
      fs.writeFileSync(
        path.join(templatesDir, 'hello.md'),
        '# Hello {{pack.name}}!\n\nThis is version {{pack.version}}.'
      );
      
      // Initialize
      await initCommand({ yes: true, workspace: tempDir });
      
      const config = new ConfigManager(configPath);
      config.set('packsDir', packsDir);
      resetConfig();
    });

    it('should fail if not initialized', async () => {
      // Create new temp dir without init
      const newTemp = fs.mkdtempSync(path.join(os.tmpdir(), 'moltcare-new-'));
      const originalCwd = process.cwd();
      process.chdir(newTemp);
      
      const exitSpy = vi.spyOn(process, 'exit').mockImplementation(() => {
        throw new Error('Process exit');
      });

      await expect(applyCommand('test-pack', {})).rejects.toThrow();
      
      exitSpy.mockRestore();
      process.chdir(originalCwd);
      fs.rmSync(newTemp, { recursive: true });
    });

    it('should fail for invalid pack name', async () => {
      const exitSpy = vi.spyOn(process, 'exit').mockImplementation(() => {
        throw new Error('Process exit');
      });

      await expect(applyCommand('../etc/passwd', {})).rejects.toThrow();
      
      exitSpy.mockRestore();
    });

    it('should fail for non-existent pack', async () => {
      const exitSpy = vi.spyOn(process, 'exit').mockImplementation(() => {
        throw new Error('Process exit');
      });

      await expect(applyCommand('non-existent', {})).rejects.toThrow();
      
      exitSpy.mockRestore();
    });

    it('should apply pack in dry-run mode', async () => {
      await applyCommand('test-pack', { dryRun: true, yes: true });
      
      const outputFile = path.join(tempDir, 'hello.md');
      expect(fs.existsSync(outputFile)).toBe(false);
      
      // Should show preview mode message
      const logs = mockConsole.log.mock.calls.map(c => String(c[0])).join(' ');
      expect(logs).toContain('预览');
    });

    it('should apply pack and create files', async () => {
      await applyCommand('test-pack', { yes: true });
      
      const outputFile = path.join(tempDir, 'hello.md');
      expect(fs.existsSync(outputFile)).toBe(true);
      
      const content = fs.readFileSync(outputFile, 'utf-8');
      expect(content).toContain('Hello test-pack!');
      expect(content).toContain('This is version 1.0.0.');
    });

    it('should skip if already installed without --force', async () => {
      await applyCommand('test-pack', { yes: true });
      
      const exitSpy = vi.spyOn(process, 'exit').mockImplementation(() => {
        throw new Error('Process exit');
      });
      
      await expect(applyCommand('test-pack', { yes: true })).rejects.toThrow();
      
      exitSpy.mockRestore();
    });

    it('should overwrite with --force', async () => {
      await applyCommand('test-pack', { yes: true });
      
      // Modify the output file
      const outputFile = path.join(tempDir, 'hello.md');
      fs.writeFileSync(outputFile, 'Modified content');
      
      await applyCommand('test-pack', { force: true, yes: true });
      
      // Should have backup file
      const files = fs.readdirSync(tempDir);
      const backupFiles = files.filter(f => f.startsWith('hello.md.backup.'));
      expect(backupFiles.length).toBeGreaterThan(0);
      
      // Should be restored to template content
      const content = fs.readFileSync(outputFile, 'utf-8');
      expect(content).toContain('Hello test-pack!');
    });
  });
});
