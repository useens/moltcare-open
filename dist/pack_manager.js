"use strict";
/**
 * Pack Manager (TypeScript)
 * Pack 扫描和管理功能
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.PackManager = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const handlebars_1 = __importDefault(require("handlebars"));
class PackManager {
    packsDir;
    indexPath;
    index;
    constructor(packsDir) {
        this.packsDir = packsDir;
        this.indexPath = path.join(packsDir, '.index.json');
        this.index = { updatedAt: new Date().toISOString(), packs: {} };
        this.loadIndex();
    }
    /**
     * 加载索引
     */
    loadIndex() {
        try {
            if (fs.existsSync(this.indexPath)) {
                const content = fs.readFileSync(this.indexPath, 'utf-8');
                this.index = JSON.parse(content);
            }
        }
        catch (error) {
            this.index = { updatedAt: new Date().toISOString(), packs: {} };
        }
    }
    /**
     * 保存索引
     */
    saveIndex() {
        try {
            this.index.updatedAt = new Date().toISOString();
            fs.writeFileSync(this.indexPath, JSON.stringify(this.index, null, 2), 'utf-8');
            return true;
        }
        catch (error) {
            return false;
        }
    }
    /**
     * 净化pack名称（安全检查）
     */
    sanitizePackName(name) {
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
    scanPacks() {
        const packs = [];
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
                const manifest = JSON.parse(content);
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
            }
            catch (error) {
                // 忽略损坏的 manifest
            }
        }
        // 按优先级排序（core packs 优先）
        return packs.sort((a, b) => {
            if (a.isCore && !b.isCore)
                return -1;
            if (!a.isCore && b.isCore)
                return 1;
            const priorityA = a.manifest.priority ?? 999;
            const priorityB = b.manifest.priority ?? 999;
            return priorityA - priorityB;
        });
    }
    /**
     * 获取指定 pack
     */
    getPack(name) {
        return this.scanPacks().find(p => p.name === name);
    }
    /**
     * 检查 pack 是否已安装
     */
    isInstalled(name) {
        return name in this.index.packs;
    }
    /**
     * 获取所有 pack 名称
     */
    getPackNames() {
        return this.scanPacks().map(p => p.name);
    }
    /**
     * 获取已分类的 packs
     */
    getPacksByCategory() {
        const packs = this.scanPacks();
        const categories = {};
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
    renderTemplate(templatePath, variables) {
        const content = fs.readFileSync(templatePath, 'utf-8');
        const template = handlebars_1.default.compile(content);
        return template(variables);
    }
    /**
     * 安装 pack（标记为已安装）
     */
    install(name) {
        const pack = this.getPack(name);
        if (!pack)
            return false;
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
    getInstalledNames() {
        return Object.keys(this.index.packs);
    }
    /**
     * 获取索引
     */
    getIndex() {
        return { ...this.index };
    }
}
exports.PackManager = PackManager;
//# sourceMappingURL=pack_manager.js.map