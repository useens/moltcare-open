"use strict";
/**
 * MoltCare Configuration System (TypeScript)
 * 核心配置管理模块
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
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConfigManager = exports.DEFAULT_CONFIG = void 0;
exports.getConfig = getConfig;
exports.resetConfig = resetConfig;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const os = __importStar(require("os"));
const yaml = __importStar(require("js-yaml"));
exports.DEFAULT_CONFIG = {
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
class ConfigManager {
    configPath;
    config;
    constructor(configPath) {
        this.configPath = configPath || this.getDefaultConfigPath();
        this.config = { ...exports.DEFAULT_CONFIG };
        this.load();
    }
    getDefaultConfigPath() {
        return path.join(os.homedir(), '.moltcare', 'config.yaml');
    }
    /**
     * 获取配置目录路径
     */
    getConfigDir() {
        return path.dirname(this.configPath);
    }
    /**
     * 从文件加载配置
     */
    load() {
        try {
            if (fs.existsSync(this.configPath)) {
                const content = fs.readFileSync(this.configPath, 'utf-8');
                const loaded = yaml.load(content);
                this.config = { ...exports.DEFAULT_CONFIG, ...loaded };
                return true;
            }
        }
        catch (error) {
            // 加载失败时使用默认配置
            console.warn(`[Config] 加载配置失败: ${error}`);
        }
        return false;
    }
    /**
     * 保存配置到文件
     */
    save() {
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
        }
        catch (error) {
            console.error(`[Config] 保存配置失败: ${error}`);
            return false;
        }
    }
    /**
     * 获取配置项
     */
    get(key) {
        return this.config[key];
    }
    /**
     * 设置配置项
     */
    set(key, value) {
        this.config[key] = value;
        this.config.lastUpdated = new Date().toISOString();
    }
    /**
     * 获取所有配置
     */
    getAll() {
        return { ...this.config };
    }
    /**
     * 批量更新配置
     */
    update(updates) {
        this.config = { ...this.config, ...updates };
        this.config.lastUpdated = new Date().toISOString();
    }
    /**
     * 重置为默认配置
     */
    reset() {
        this.config = { ...exports.DEFAULT_CONFIG };
    }
    /**
     * 检查是否已初始化
     */
    isInitialized() {
        return this.config.initialized;
    }
    /**
     * 标记为已初始化
     */
    markInitialized() {
        this.config.initialized = true;
        this.config.lastUpdated = new Date().toISOString();
        this.save();
    }
    /**
     * 获取配置文件路径
     */
    getConfigPath() {
        return this.configPath;
    }
    /**
     * 检查OpenClaw环境
     */
    checkOpenClawEnv() {
        const details = [];
        // 检查 OPENCLAW_WORKSPACE 环境变量
        const workspaceEnv = process.env.OPENCLAW_WORKSPACE;
        if (workspaceEnv) {
            details.push(`OPENCLAW_WORKSPACE: ${workspaceEnv}`);
            if (fs.existsSync(workspaceEnv)) {
                details.push('✓ OpenClaw工作区已存在');
                return { exists: true, workspacePath: workspaceEnv, details };
            }
            else {
                details.push('✗ OPENCLAW_WORKSPACE 指向的路径不存在');
            }
        }
        else {
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
exports.ConfigManager = ConfigManager;
// 全局配置实例
let globalConfig = null;
function getConfig(configPath) {
    if (!globalConfig || configPath) {
        globalConfig = new ConfigManager(configPath);
    }
    return globalConfig;
}
function resetConfig() {
    globalConfig = null;
}
//# sourceMappingURL=config.js.map