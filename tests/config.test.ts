/**
 * Config Manager Tests
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { ConfigManager, DEFAULT_CONFIG, getConfig, resetConfig } from '../src/config.js';

describe('ConfigManager', () => {
  let tempDir: string;
  let configPath: string;

  beforeEach(() => {
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'moltcare-test-'));
    configPath = path.join(tempDir, 'config.yaml');
    resetConfig();
  });

  afterEach(() => {
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true });
    }
  });

  describe('initialization', () => {
    it('should use default config path when not specified', () => {
      const config = new ConfigManager();
      expect(config.getConfigPath()).toBe(path.join(os.homedir(), '.moltcare', 'config.yaml'));
    });

    it('should use custom config path when specified', () => {
      const config = new ConfigManager(configPath);
      expect(config.getConfigPath()).toBe(configPath);
    });

    it('should load default values initially', () => {
      const config = new ConfigManager(configPath);
      expect(config.get('version')).toBe(DEFAULT_CONFIG.version);
      expect(config.get('language')).toBe(DEFAULT_CONFIG.language);
      expect(config.get('logLevel')).toBe(DEFAULT_CONFIG.logLevel);
    });
  });

  describe('persistence', () => {
    it('should save and load config', () => {
      const config = new ConfigManager(configPath);
      config.set('language', 'en');
      config.set('logLevel', 'debug');
      config.save(); // 显式保存
      
      // Create new instance to test loading
      const config2 = new ConfigManager(configPath);
      expect(config2.get('language')).toBe('en');
      expect(config2.get('logLevel')).toBe('debug');
    });

    it('should create config directory if not exists', () => {
      const deepPath = path.join(tempDir, 'deep', 'nested', 'config.yaml');
      const config = new ConfigManager(deepPath);
      config.save();
      
      expect(fs.existsSync(deepPath)).toBe(true);
    });
  });

  describe('config operations', () => {
    it('should get config values', () => {
      const config = new ConfigManager(configPath);
      expect(config.get('version')).toBe('1.0.0');
      expect(config.get('language')).toBe('zh');
    });

    it('should set config values', () => {
      const config = new ConfigManager(configPath);
      config.set('language', 'en');
      expect(config.get('language')).toBe('en');
    });

    it('should update multiple config values', () => {
      const config = new ConfigManager(configPath);
      config.update({
        language: 'en',
        logLevel: 'debug',
        autoUpdate: false,
      });
      
      expect(config.get('language')).toBe('en');
      expect(config.get('logLevel')).toBe('debug');
      expect(config.get('autoUpdate')).toBe(false);
    });

    it('should get all config values', () => {
      const config = new ConfigManager(configPath);
      const all = config.getAll();
      
      expect(all.version).toBe('1.0.0');
      expect(all.language).toBe('zh');
      expect(all.initialized).toBe(false);
    });

    it('should reset to defaults', () => {
      const config = new ConfigManager(configPath);
      config.set('language', 'en');
      config.reset();
      
      expect(config.get('language')).toBe('zh');
    });
  });

  describe('initialization state', () => {
    it('should not be initialized by default', () => {
      const config = new ConfigManager(configPath);
      expect(config.isInitialized()).toBe(false);
    });

    it('should mark as initialized', () => {
      const config = new ConfigManager(configPath);
      config.markInitialized();
      expect(config.isInitialized()).toBe(true);
    });
  });

  describe('OpenClaw environment check', () => {
    it('should return correct env info structure', () => {
      const config = new ConfigManager(configPath);
      const result = config.checkOpenClawEnv();
      
      expect(result).toHaveProperty('exists');
      expect(result).toHaveProperty('details');
      expect(Array.isArray(result.details)).toBe(true);
    });
  });
});

describe('getConfig singleton', () => {
  let tempDir: string;

  beforeEach(() => {
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'moltcare-test-'));
    resetConfig();
  });

  afterEach(() => {
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true });
    }
  });

  it('should return same instance', () => {
    const config1 = getConfig();
    const config2 = getConfig();
    expect(config1).toBe(config2);
  });

  it('should return new instance after reset', () => {
    const config1 = getConfig();
    resetConfig();
    const config2 = getConfig();
    expect(config1).not.toBe(config2);
  });
});
