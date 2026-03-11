/**
 * Pack Manager (TypeScript)
 * Pack 扫描和管理功能
 */

import * as fs from 'fs';
import * as path from 'path';
import Handlebars from 'handlebars';

export interface PackManifest {
  name: string;
  version: string;
  title?: string;
  description?: string;
  author?: string;
  category?: string;
  priority?: number;
  isCore?: boolean;
  createdAt?: string;
  templates?: PackTemplate[];
  scripts?: {
    apply?: string;
    preApply?: string;
    postApply?: string;
  };
  dependencies?: string[];
  config?: {
    backupExisting?: boolean;
    allowOverwrite?: boolean;
    validateTarget?: boolean;
  };
}

export interface PackTemplate {
  file: string;
  target: string;
  required?: boolean;
  description?: string;
  variables?: Record<string, string>;
}

export interface PackInfo {
  name: string;
  version: string;
  title?: string;
  description?: string;
  author?: string;
  category?: string;
  isCore?: boolean;
  manifest: PackManifest;
  path: string;
  installed: boolean;
  installDate?: string;
}

export interface PackIndexEntry {
  version: string;
  installDate: string;
  manifest: PackManifest;
  path: string;
  active: boolean;
}

export interface PackIndex {
  updatedAt: string;
  packs: Record<string, PackIndexEntry>;
}

export class PackManager {
  private packsDir: string;
  private indexPath: string;
  private index: PackIndex;

  constructor(packsDir: string) {
    this.packsDir = packsDir;
    this.indexPath = path.join(packsDir, '.index.json');
    this.index = { updatedAt: new Date().toISOString(), packs: {} };
    this.loadIndex();
  }

  /**
   * 加载索引
   */
  private loadIndex(): void {
    try {
      if (fs.existsSync(this.indexPath)) {
        const content = fs.readFileSync(this.indexPath, 'utf-8');
        this.index = JSON.parse(content) as PackIndex;
      }
    } catch (error) {
      this.index = { updatedAt: new Date().toISOString(), packs: {} };
    }
  }

  /**
   * 保存索引
   */
  private saveIndex(): boolean {
    try {
      this.index.updatedAt = new Date().toISOString();
      fs.writeFileSync(this.indexPath, JSON.stringify(this.index, null, 2), 'utf-8');
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * 净化pack名称（安全检查）
   */
  sanitizePackName(name: string): { valid: boolean; name?: string; error?: string } {
    if (!name || !name.trim()) {
      return { valid: false, error: 'Pack 名称不能为空' };
    }

    // 检查路径分隔符
    if (name.includes('/') || name.includes('\\')) {
      return { valid: false, error: 'Pack 名称不能包含路径分隔符' };
    }

    // 检查父目录引用
    if (name.includes('..')) {
      return { valid: false, error: 'Pack 名称不能包含 ".."' };
    }

    // 检查隐藏文件
    if (name.startsWith('.')) {
      return { valid: false, error: 'Pack 名称不能以 "." 开头' };
    }

    // 检查控制字符
    for (const char of name) {
      if (char.charCodeAt(0) < 32 || char.charCodeAt(0) === 127) {
        return { valid: false, error: 'Pack 名称包含非法控制字符' };
      }
    }

    const sanitized = name.trim();

    if (sanitized.length > 100) {
      return { valid: false, error: 'Pack 名称长度不能超过 100 字符' };
    }

    return { valid: true, name: sanitized };
  }

  /**
   * 扫描可用的 packs
   */
  scanPacks(): PackInfo[] {
    const packs: PackInfo[] = [];

    if (!fs.existsSync(this.packsDir)) {
      return packs;
    }

    const entries = fs.readdirSync(this.packsDir, { withFileTypes: true });

    for (const entry of entries) {
      if (!entry.isDirectory() || entry.name.startsWith('.')) {
        continue;
      }

      const packPath = path.join(this.packsDir, entry.name);
      const manifestPath = path.join(packPath, 'manifest.json');

      if (!fs.existsSync(manifestPath)) {
        continue;
      }

      try {
        const content = fs.readFileSync(manifestPath, 'utf-8');
        const manifest = JSON.parse(content) as PackManifest;

        // 验证名称
        const validation = this.sanitizePackName(manifest.name || entry.name);
        if (!validation.valid) {
          continue;
        }

        const installedEntry = this.index.packs[manifest.name];

        packs.push({
          name: manifest.name || entry.name,
          version: manifest.version || '0.0.0',
          title: manifest.title,
          description: manifest.description,
          author: manifest.author,
          category: manifest.category,
          isCore: manifest.isCore,
          manifest,
          path: packPath,
          installed: !!installedEntry,
          installDate: installedEntry?.installDate,
        });
      } catch (error) {
        // 忽略损坏的 manifest
      }
    }

    // 按优先级排序（core packs 优先）
    return packs.sort((a, b) => {
      if (a.isCore && !b.isCore) return -1;
      if (!a.isCore && b.isCore) return 1;
      const priorityA = a.manifest.priority ?? 999;
      const priorityB = b.manifest.priority ?? 999;
      return priorityA - priorityB;
    });
  }

  /**
   * 获取指定 pack
   */
  getPack(name: string): PackInfo | undefined {
    return this.scanPacks().find(p => p.name === name);
  }

  /**
   * 检查 pack 是否已安装
   */
  isInstalled(name: string): boolean {
    return name in this.index.packs;
  }

  /**
   * 获取所有 pack 名称
   */
  getPackNames(): string[] {
    return this.scanPacks().map(p => p.name);
  }

  /**
   * 获取已分类的 packs
   */
  getPacksByCategory(): Record<string, PackInfo[]> {
    const packs = this.scanPacks();
    const categories: Record<string, PackInfo[]> = {};

    for (const pack of packs) {
      const category = pack.category || 'other';
      if (!categories[category]) {
        categories[category] = [];
      }
      categories[category].push(pack);
    }

    return categories;
  }

  /**
   * 渲染模板
   */
  renderTemplate(templatePath: string, variables: Record<string, unknown>): string {
    const content = fs.readFileSync(templatePath, 'utf-8');
    const template = Handlebars.compile(content);
    return template(variables);
  }

  /**
   * 安装 pack（标记为已安装）
   */
  install(name: string): boolean {
    const pack = this.getPack(name);
    if (!pack) return false;

    this.index.packs[name] = {
      version: pack.version,
      installDate: new Date().toISOString(),
      manifest: pack.manifest,
      path: pack.path,
      active: true,
    };

    return this.saveIndex();
  }

  /**
   * 获取所有已安装 pack 名称
   */
  getInstalledNames(): string[] {
    return Object.keys(this.index.packs);
  }

  /**
   * 获取索引
   */
  getIndex(): PackIndex {
    return { ...this.index };
  }
}
