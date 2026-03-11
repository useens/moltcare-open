/**
 * Pack Manager Tests
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { PackManager } from '../src/pack_manager.js';

describe('PackManager', () => {
  let tempDir: string;
  let packsDir: string;

  beforeEach(() => {
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'moltcare-test-'));
    packsDir = path.join(tempDir, 'packs');
    fs.mkdirSync(packsDir, { recursive: true });
  });

  afterEach(() => {
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true });
    }
  });

  // Helper to create a test pack
  function createTestPack(name: string, manifest: Record<string, unknown> = {}) {
    const packDir = path.join(packsDir, name);
    fs.mkdirSync(packDir, { recursive: true });
    
    const defaultManifest = {
      name,
      version: '1.0.0',
      description: `Test pack ${name}`,
      ...manifest,
    };
    
    fs.writeFileSync(
      path.join(packDir, 'manifest.json'),
      JSON.stringify(defaultManifest, null, 2)
    );
    
    return packDir;
  }

  describe('sanitizePackName', () => {
    it('should accept valid pack names', () => {
      const pm = new PackManager(packsDir);
      
      const validNames = [
        'foundation',
        'my-pack',
        'my_pack',
        'pack123',
        'a'.repeat(100),
      ];

      for (const name of validNames) {
        const result = pm.sanitizePackName(name);
        expect(result.valid).toBe(true);
        expect(result.name).toBe(name);
      }
    });

    it('should reject empty pack names', () => {
      const pm = new PackManager(packsDir);
      
      const result1 = pm.sanitizePackName('');
      expect(result1.valid).toBe(false);
      expect(result1.error).toContain('不能为空');
      
      const result2 = pm.sanitizePackName('   ');
      expect(result2.valid).toBe(false);
      expect(result2.error).toContain('不能为空');
    });

    it('should reject pack names with path separators', () => {
      const pm = new PackManager(packsDir);
      
      const result1 = pm.sanitizePackName('pack/name');
      expect(result1.valid).toBe(false);
      expect(result1.error).toContain('分隔符');
      
      const result2 = pm.sanitizePackName('pack\\\\name');
      expect(result2.valid).toBe(false);
      expect(result2.error).toContain('分隔符');
    });

    it('should reject pack names with parent directory reference', () => {
      const pm = new PackManager(packsDir);
      
      const result = pm.sanitizePackName('..');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('..');
    });

    it('should reject hidden pack names', () => {
      const pm = new PackManager(packsDir);
      
      const result = pm.sanitizePackName('.hidden');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('.');
    });

    it('should reject pack names exceeding length limit', () => {
      const pm = new PackManager(packsDir);
      
      const result = pm.sanitizePackName('a'.repeat(101));
      expect(result.valid).toBe(false);
      expect(result.error).toContain('不能超过');
    });

    it('should reject control characters', () => {
      const pm = new PackManager(packsDir);
      const result = pm.sanitizePackName('pack\x01name');
      expect(result.valid).toBe(false);
      expect(result.error).toContain('控制字符');
    });
  });

  describe('scanPacks', () => {
    it('should return empty array when no packs', () => {
      const pm = new PackManager(packsDir);
      const packs = pm.scanPacks();
      expect(packs).toEqual([]);
    });

    it('should scan available packs', () => {
      createTestPack('pack1');
      createTestPack('pack2');
      
      const pm = new PackManager(packsDir);
      const packs = pm.scanPacks();
      
      expect(packs).toHaveLength(2);
      expect(packs.map(p => p.name)).toContain('pack1');
      expect(packs.map(p => p.name)).toContain('pack2');
    });
  });
});
