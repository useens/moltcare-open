/**
 * Enhanced Configuration System - Phase 5 优化
 * 
 * 功能:
 * - 多配置文件支持
 * - 配置合并和继承
 * - 环境变量支持
 * - 配置验证
 * - 实时重载
 * - 用户配置和项目配置分离
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import yaml from 'js-yaml';
import { EventEmitter } from 'events';
import { ErrorHandler, ErrorCodes, MoltCareError } from './errors-enhanced.js';

// 配置源类型
export type ConfigSource = 'default' | 'user' | 'project' | 'environment' | 'cli';

// 配置项元数据
export interface ConfigItemMetadata {
  description: string;
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  default?: unknown;
  envVar?: string;
  validate?: (value: unknown) => boolean | string;
  deprecated?: boolean;
  deprecatedMessage?: string;
}

// 配置定义
export interface ConfigSchema {
  [key: string]: ConfigItemMetadata;
}

// 配置变更事件
export interface ConfigChangeEvent {
  key: string;
  oldValue: unknown;
  newValue: unknown;
  source: ConfigSource;
}

// 增强的配置接口
export interface EnhancedMoltCareConfig {
  version: string;
  language: 'zh' | 'en' | 'ja' | 'ko' | 'de' | 'fr' | 'es' | 'ru' | 'ar';
  workspacePath: string;
  packsDir: string;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  autoUpdate: boolean;
  maxCacheSize: number;
  initialized: boolean;
  lastUpdated: string;
  theme: 'default' | 'dark' | 'light';
  editor: string;
  git: {
    enabled: boolean;
    autoCommit: boolean;
    commitMessage: string;
  };
  packs: {
    registry: string;
    cacheDir: string;
    parallelInstall: boolean;
  };
  templates: {
    engine: 'handlebars' | 'ejs' | 'mustache';
    strictMode: boolean;
    cacheEnabled: boolean;
  };
  network: {
    timeout: number;
    retryCount: number;
    proxy?: string;
  };
  advanced: {
    experimentalFeatures: boolean;
    debugMode: boolean;
    traceMode: boolean;
  };
}

// 默认配置
export const DEFAULT_CONFIG: EnhancedMoltCareConfig = {
  version: '1.0.0',
  language: 'zh',
  workspacePath: path.join(os.homedir(), '.moltcare', 'workspace'),
  packsDir: path.join(os.homedir(), '.moltcare', 'packs'),
  logLevel: 'info',
  autoUpdate: true,
  maxCacheSize: 100,
  initialized: false,
  lastUpdated: new Date().toISOString(),
  theme: 'default',
  editor: process.env.EDITOR || 'nano',
  git: {
    enabled: true,
    autoCommit: false,
    commitMessage: 'chore: update moltcare configuration',
  },
  packs: {
    registry: 'https://registry.moltcare.dev',
    cacheDir: path.join(os.homedir(), '.moltcare', 'cache'),
    parallelInstall: true,
  },
  templates: {
    engine: 'handlebars',
    strictMode: false,
    cacheEnabled: true,
  },
  network: {
    timeout: 30000,
    retryCount: 3,
  },
  advanced: {
    experimentalFeatures: false,
    debugMode: false,
    traceMode: false,
  },
};

// 配置定义（用于验证和文档）
export const CONFIG_SCHEMA: ConfigSchema = {
  version: {
    description: '配置版本',
    type: 'string',
    default: '1.0.0',
  },
  language: {
    description: '界面语言',
    type: 'string',
    default: 'zh',
    envVar: 'MOLTCARE_LANGUAGE',
    validate: (v) => ['zh', 'en', 'ja', 'ko', 'de', 'fr', 'es', 'ru', 'ar'].includes(v as string) || '无效的语言',
  },
  workspacePath: {
    description: '工作区路径',
    type: 'string',
    default: path.join(os.homedir(), '.moltcare', 'workspace'),
    envVar: 'MOLTCARE_WORKSPACE',
  },
  packsDir: {
    description: '智能包目录',
    type: 'string',
    default: path.join(os.homedir(), '.moltcare', 'packs'),
    envVar: 'MOLTCARE_PACKS_DIR',
  },
  logLevel: {
    description: '日志级别',
    type: 'string',
    default: 'info',
    envVar: 'MOLTCARE_LOG_LEVEL',
    validate: (v) => ['debug', 'info', 'warn', 'error'].includes(v as string) || '无效的日志级别',
  },
  autoUpdate: {
    description: '自动检查更新',
    type: 'boolean',
    default: true,
  },
  maxCacheSize: {
    description: '最大缓存大小(MB)',
    type: 'number',
    default: 100,
    validate: (v) => (typeof v === 'number' && v > 0) || '缓存大小必须为正数',
  },
  theme: {
    description: '界面主题',
    type: 'string',
    default: 'default',
    validate: (v) => ['default', 'dark', 'light'].includes(v as string) || '无效的主题',
  },
  editor: {
    description: '默认编辑器',
    type: 'string',
    default: 'nano',
    envVar: 'EDITOR',
  },
};

export class EnhancedConfigManager extends EventEmitter {
  private config: EnhancedMoltCareConfig;
  private userConfigPath: string;
  private projectConfigPath: string;
  private sources: Map<string, ConfigSource>;
  private watchers: fs.FSWatcher[] = [];
  private autoReload: boolean;

  constructor(options?: { 
    userConfigPath?: string; 
    projectConfigPath?: string;
    autoReload?: boolean;
  }) {
    super();
    
    this.userConfigPath = options?.userConfigPath || this.getDefaultUserConfigPath();
    this.projectConfigPath = options?.projectConfigPath || '.moltcare.yaml';
    this.autoReload = options?.autoReload ?? false;
    
    this.config = { ...DEFAULT_CONFIG };
    this.sources = new Map();
    
    this.load();
    
    if (this.autoReload) {
      this.setupWatchers();
    }
  }

  private getDefaultUserConfigPath(): string {
    return path.join(os.homedir(), '.moltcare', 'config.yaml');
  }

  /**
   * 加载所有配置源
   */
  load(): void {
    // 1. 默认配置（已设置）
    this.markSource('default');

    // 2. 用户配置
    this.loadFromFile(this.userConfigPath, 'user');

    // 3. 项目配置
    this.loadFromFile(this.projectConfigPath, 'project');

    // 4. 环境变量
    this.loadFromEnvironment();

    // 验证配置
    this.validate();
  }

  /**
   * 从文件加载配置
   */
  private loadFromFile(filePath: string, source: ConfigSource): boolean {
    try {
      if (!fs.existsSync(filePath)) {
        return false;
      }

      const content = fs.readFileSync(filePath, 'utf-8');
      const loaded = yaml.load(content) as Partial<EnhancedMoltCareConfig>;
      
      this.merge(loaded, source);
      return true;
    } catch (error) {
      if (source === 'user') {
        console.warn(`[Config] 加载用户配置失败: ${error}`);
      }
      return false;
    }
  }

  /**
   * 从环境变量加载配置
   */
  private loadFromEnvironment(): void {
    Object.entries(CONFIG_SCHEMA).forEach(([key, meta]) => {
      if (meta.envVar && process.env[meta.envVar]) {
        const value = this.parseValue(process.env[meta.envVar]!, meta.type);
        (this.config as any)[key] = value;
        this.sources.set(key, 'environment');
      }
    });

    // 特殊处理嵌套配置
    if (process.env.MOLTCARE_GIT_ENABLED) {
      this.config.git.enabled = process.env.MOLTCARE_GIT_ENABLED === 'true';
    }
    if (process.env.MOLTCARE_NETWORK_TIMEOUT) {
      this.config.network.timeout = parseInt(process.env.MOLTCARE_NETWORK_TIMEOUT, 10);
    }
  }

  /**
   * 解析配置值
   */
  private parseValue(value: string, type: string): unknown {
    switch (type) {
      case 'boolean':
        return value === 'true' || value === '1';
      case 'number':
        return parseFloat(value);
      case 'array':
        return value.split(',').map(s => s.trim());
      default:
        return value;
    }
  }

  /**
   * 合并配置
   */
  private merge(updates: Partial<EnhancedMoltCareConfig>, source: ConfigSource): void {
    const mergeDeep = (target: any, source: any) => {
      for (const key in source) {
        if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
          target[key] = target[key] || {};
          mergeDeep(target[key], source[key]);
        } else {
          const oldValue = target[key];
          const newValue = source[key];
          if (oldValue !== newValue) {
            target[key] = newValue;
            this.sources.set(key, source);
            this.emit('change', { key, oldValue, newValue, source });
          }
        }
      }
    };

    mergeDeep(this.config, updates);
  }

  /**
   * 标记配置来源
   */
  private markSource(source: ConfigSource): void {
    Object.keys(this.config).forEach(key => {
      if (!this.sources.has(key)) {
        this.sources.set(key, source);
      }
    });
  }

  /**
   * 验证配置
   */
  validate(): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    Object.entries(CONFIG_SCHEMA).forEach(([key, meta]) => {
      const value = this.get(key as keyof EnhancedMoltCareConfig);
      
      // 类型验证
      if (value !== undefined && value !== null) {
        const actualType = Array.isArray(value) ? 'array' : typeof value;
        if (actualType !== meta.type) {
          errors.push(`配置项 "${key}" 类型错误，期望 ${meta.type}，实际 ${actualType}`);
        }
      }

      // 自定义验证
      if (meta.validate && value !== undefined) {
        const result = meta.validate(value);
        if (result !== true) {
          errors.push(`配置项 "${key}" 验证失败: ${result}`);
        }
      }

      // 弃用检查
      if (meta.deprecated) {
        console.warn(`[Config] 配置项 "${key}" 已弃用${meta.deprecatedMessage ? `: ${meta.deprecatedMessage}` : ''}`);
      }
    });

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * 设置配置项
   */
  set<K extends keyof EnhancedMoltCareConfig>(
    key: K, 
    value: EnhancedMoltCareConfig[K], 
    source: ConfigSource = 'cli'
  ): void {
    const oldValue = this.config[key];
    if (oldValue !== value) {
      this.config[key] = value;
      this.sources.set(key as string, source);
      this.config.lastUpdated = new Date().toISOString();
      this.emit('change', { key, oldValue, newValue: value, source });
    }
  }

  /**
   * 获取配置项
   */
  get<K extends keyof EnhancedMoltCareConfig>(key: K): EnhancedMoltCareConfig[K] {
    return this.config[key];
  }

  /**
   * 获取配置来源
   */
  getSource(key: string): ConfigSource | undefined {
    return this.sources.get(key);
  }

  /**
   * 获取所有配置
   */
  getAll(): EnhancedMoltCareConfig {
    return { ...this.config };
  }

  /**
   * 批量更新配置
   */
  update(updates: Partial<EnhancedMoltCareConfig>, source: ConfigSource = 'cli'): void {
    this.merge(updates, source);
  }

  /**
   * 保存用户配置
   */
  save(): boolean {
    try {
      const configDir = path.dirname(this.userConfigPath);
      if (!fs.existsSync(configDir)) {
        fs.mkdirSync(configDir, { recursive: true });
      }

      // 只保存非默认值的配置
      const toSave = this.getNonDefaultValues();

      const content = yaml.dump(toSave, {
        indent: 2,
        lineWidth: 120,
        noRefs: true,
        sortKeys: true,
      });

      fs.writeFileSync(this.userConfigPath, content, 'utf-8');
      return true;
    } catch (error) {
      console.error(`[Config] 保存配置失败: ${error}`);
      return false;
    }
  }

  /**
   * 获取与默认值不同的配置项
   */
  private getNonDefaultValues(): Partial<EnhancedMoltCareConfig> {
    const result: Partial<EnhancedMoltCareConfig> = {};
    
    const compareDeep = (current: any, default_: any, key: string) => {
      if (typeof current !== typeof default_) {
        return current;
      }
      
      if (typeof current === 'object' && current !== null && !Array.isArray(current)) {
        const nested: any = {};
        for (const k in current) {
          const diff = compareDeep(current[k], default_?.[k], k);
          if (diff !== undefined) {
            nested[k] = diff;
          }
        }
        return Object.keys(nested).length > 0 ? nested : undefined;
      }
      
      return current !== default_ ? current : undefined;
    };

    for (const key of Object.keys(this.config) as Array<keyof EnhancedMoltCareConfig>) {
      const diff = compareDeep(this.config[key], DEFAULT_CONFIG[key], key);
      if (diff !== undefined) {
        (result as any)[key] = diff;
      }
    }

    return result;
  }

  /**
   * 重置为默认配置
   */
  reset(): void {
    this.config = { ...DEFAULT_CONFIG };
    this.sources.clear();
    this.markSource('default');
  }

  /**
   * 检查是否已初始化
   */
  isInitialized(): boolean {
    return this.config.initialized;
  }

  /**
   * 标记为已初始化
   */
  markInitialized(): void {
    this.config.initialized = true;
    this.config.lastUpdated = new Date().toISOString();
    this.save();
  }

  /**
   * 获取配置文件路径
   */
  getConfigPath(type: 'user' | 'project' = 'user'): string {
    return type === 'user' ? this.userConfigPath : this.projectConfigPath;
  }

  /**
   * 设置配置文件路径
   */
  setConfigPath(type: 'user' | 'project', filePath: string): void {
    if (type === 'user') {
      this.userConfigPath = filePath;
    } else {
      this.projectConfigPath = filePath;
    }
  }

  /**
   * 启用配置热重载
   */
  setupWatchers(): void {
    this.cleanupWatchers();

    // 监听用户配置
    if (fs.existsSync(this.userConfigPath)) {
      const watcher = fs.watch(this.userConfigPath, () => {
        console.log('[Config] 用户配置已更改，重新加载...');
        this.loadFromFile(this.userConfigPath, 'user');
      });
      this.watchers.push(watcher);
    }

    // 监听项目配置
    if (fs.existsSync(this.projectConfigPath)) {
      const watcher = fs.watch(this.projectConfigPath, () => {
        console.log('[Config] 项目配置已更改，重新加载...');
        this.loadFromFile(this.projectConfigPath, 'project');
      });
      this.watchers.push(watcher);
    }
  }

  /**
   * 清理文件监听器
   */
  cleanupWatchers(): void {
    this.watchers.forEach(watcher => watcher.close());
    this.watchers = [];
  }

  /**
   * 获取配置文档
   */
  getDocumentation(): string {
    const lines: string[] = [];
    lines.push('# MoltCare 配置选项');
    lines.push('');

    Object.entries(CONFIG_SCHEMA).forEach(([key, meta]) => {
      lines.push(`## ${key}`);
      lines.push('');
      lines.push(`**类型**: ${meta.type}`);
      lines.push(`**描述**: ${meta.description}`);
      if (meta.default !== undefined) {
        lines.push(`**默认值**: ${JSON.stringify(meta.default)}`);
      }
      if (meta.envVar) {
        lines.push(`**环境变量**: ${meta.envVar}`);
      }
      lines.push('');
    });

    return lines.join('\n');
  }

  /**
   * 导出配置
   */
  export(format: 'yaml' | 'json' = 'yaml'): string {
    if (format === 'json') {
      return JSON.stringify(this.config, null, 2);
    }
    return yaml.dump(this.config, {
      indent: 2,
      lineWidth: 120,
      noRefs: true,
    });
  }
}

// 全局配置实例
let globalConfig: EnhancedConfigManager | null = null;

export function getEnhancedConfig(options?: {
  userConfigPath?: string;
  autoReload?: boolean;
}): EnhancedConfigManager {
  if (!globalConfig || options) {
    globalConfig = new EnhancedConfigManager(options);
  }
  return globalConfig;
}

export function resetEnhancedConfig(): void {
  globalConfig = null;
}

export default EnhancedConfigManager;
