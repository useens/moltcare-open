/**
 * MoltCare Configuration System (TypeScript)
 * 核心配置管理模块
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import * as yaml from 'js-yaml';

export interface MoltCareConfig {
  version: string;
  language: 'zh' | 'en';
  workspacePath: string;
  packsDir: string;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  autoUpdate: boolean;
  maxCacheSize: number; // MB
  initialized: boolean;
  lastUpdated: string;
}

export const DEFAULT_CONFIG: MoltCareConfig = {
  version: '1.0.0',
  language: 'zh',
  workspacePath: path.join(os.homedir(), '.moltcare', 'workspace'),
  packsDir: path.join(os.homedir(), '.moltcare', 'packs'),
  logLevel: 'info',
  autoUpdate: true,
  maxCacheSize: 100,
  initialized: false,
  lastUpdated: new Date().toISOString(),
};

export class ConfigManager {
  private configPath: string;
  private config: MoltCareConfig;

  constructor(configPath?: string) {
    this.configPath = configPath || this.getDefaultConfigPath();
    this.config = { ...DEFAULT_CONFIG };
    this.load();
  }

  private getDefaultConfigPath(): string {
    return path.join(os.homedir(), '.moltcare', 'config.yaml');
  }

  /**
   * 获取配置目录路径
   */
  getConfigDir(): string {
    return path.dirname(this.configPath);
  }

  /**
   * 从文件加载配置
   */
  load(): boolean {
    try {
      if (fs.existsSync(this.configPath)) {
        const content = fs.readFileSync(this.configPath, 'utf-8');
        const loaded = yaml.load(content) as Partial<MoltCareConfig>;
        this.config = { ...DEFAULT_CONFIG, ...loaded };
        return true;
      }
    } catch (error) {
      // 加载失败时使用默认配置
      console.warn(`[Config] 加载配置失败: ${error}`);
    }
    return false;
  }

  /**
   * 保存配置到文件
   */
  save(): boolean {
    try {
      const configDir = path.dirname(this.configPath);
      if (!fs.existsSync(configDir)) {
        fs.mkdirSync(configDir, { recursive: true });
      }
      
      const content = yaml.dump(this.config, {
        indent: 2,
        lineWidth: 120,
        noRefs: true,
      });
      
      fs.writeFileSync(this.configPath, content, 'utf-8');
      return true;
    } catch (error) {
      console.error(`[Config] 保存配置失败: ${error}`);
      return false;
    }
  }

  /**
   * 获取配置项
   */
  get<K extends keyof MoltCareConfig>(key: K): MoltCareConfig[K] {
    return this.config[key];
  }

  /**
   * 设置配置项
   */
  set<K extends keyof MoltCareConfig>(key: K, value: MoltCareConfig[K]): void {
    this.config[key] = value;
    this.config.lastUpdated = new Date().toISOString();
  }

  /**
   * 获取所有配置
   */
  getAll(): MoltCareConfig {
    return { ...this.config };
  }

  /**
   * 批量更新配置
   */
  update(updates: Partial<MoltCareConfig>): void {
    this.config = { ...this.config, ...updates };
    this.config.lastUpdated = new Date().toISOString();
  }

  /**
   * 重置为默认配置
   */
  reset(): void {
    this.config = { ...DEFAULT_CONFIG };
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
  getConfigPath(): string {
    return this.configPath;
  }

  /**
   * 检查OpenClaw环境
   */
  checkOpenClawEnv(): { exists: boolean; workspacePath?: string; details: string[] } {
    const details: string[] = [];
    
    // 检查 OPENCLAW_WORKSPACE 环境变量
    const workspaceEnv = process.env.OPENCLAW_WORKSPACE;
    if (workspaceEnv) {
      details.push(`OPENCLAW_WORKSPACE: ${workspaceEnv}`);
      if (fs.existsSync(workspaceEnv)) {
        details.push('✓ OpenClaw工作区已存在');
        return { exists: true, workspacePath: workspaceEnv, details };
      } else {
        details.push('✗ OPENCLAW_WORKSPACE 指向的路径不存在');
      }
    } else {
      details.push('✗ 未设置 OPENCLAW_WORKSPACE 环境变量');
    }

    // 检查常见的OpenClaw工作区路径
    const commonPaths = [
      path.join(os.homedir(), '.openclaw', 'workspace'),
      '/workspace',
      '/root/.openclaw/workspace',
    ];

    for (const p of commonPaths) {
      if (fs.existsSync(p)) {
        details.push(`✓ 发现OpenClaw工作区: ${p}`);
        return { exists: true, workspacePath: p, details };
      }
    }

    details.push('✗ 未发现OpenClaw工作区');
    return { exists: false, details };
  }
}

// 全局配置实例
let globalConfig: ConfigManager | null = null;

export function getConfig(configPath?: string): ConfigManager {
  if (!globalConfig || configPath) {
    globalConfig = new ConfigManager(configPath);
  }
  return globalConfig;
}

export function resetConfig(): void {
  globalConfig = null;
}
