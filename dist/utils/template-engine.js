"use strict";
/**
 * Enhanced Template System - Phase 5 优化
 *
 * 功能:
 * - Handlebars 模板引擎集成
 * - 内置 helpers 和 partials
 * - 变量验证和类型检查
 * - 条件渲染支持
 * - 模板缓存
 * - 多语言模板支持
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
exports.templateEngine = exports.TemplateEngine = void 0;
const handlebars_1 = __importDefault(require("handlebars"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const errors_enhanced_js_1 = require("./errors-enhanced.js");
// 模板缓存
const templateCache = new Map();
class TemplateEngine {
    static instance;
    handlebars;
    registeredHelpers;
    registeredPartials;
    constructor() {
        this.handlebars = handlebars_1.default.create();
        this.registeredHelpers = new Set();
        this.registeredPartials = new Set();
        this.registerBuiltInHelpers();
        this.registerBuiltInPartials();
    }
    static getInstance() {
        if (!TemplateEngine.instance) {
            TemplateEngine.instance = new TemplateEngine();
        }
        return TemplateEngine.instance;
    }
    /**
     * 注册内置 helpers
     */
    registerBuiltInHelpers() {
        // 条件判断 helpers
        this.registerHelper('eq', (a, b) => a === b);
        this.registerHelper('ne', (a, b) => a !== b);
        this.registerHelper('gt', (a, b) => a > b);
        this.registerHelper('gte', (a, b) => a >= b);
        this.registerHelper('lt', (a, b) => a < b);
        this.registerHelper('lte', (a, b) => a <= b);
        this.registerHelper('and', (...args) => args.slice(0, -1).every(Boolean));
        this.registerHelper('or', (...args) => args.slice(0, -1).some(Boolean));
        this.registerHelper('not', (a) => !a);
        // 字符串处理 helpers
        this.registerHelper('uppercase', (str) => String(str).toUpperCase());
        this.registerHelper('lowercase', (str) => String(str).toLowerCase());
        this.registerHelper('capitalize', (str) => {
            const s = String(str);
            return s.charAt(0).toUpperCase() + s.slice(1);
        });
        this.registerHelper('camelCase', (str) => {
            return String(str)
                .replace(/[-_](.)/g, (_, char) => char.toUpperCase())
                .replace(/^(.)/, (_, char) => char.toLowerCase());
        });
        this.registerHelper('kebabCase', (str) => {
            return String(str)
                .replace(/([A-Z])/g, '-$1')
                .toLowerCase()
                .replace(/^-/, '');
        });
        this.registerHelper('snakeCase', (str) => {
            return String(str)
                .replace(/([A-Z])/g, '_$1')
                .toLowerCase()
                .replace(/^_/, '');
        });
        // 数组处理 helpers
        this.registerHelper('join', (arr, separator = ', ') => {
            if (!Array.isArray(arr))
                return String(arr);
            return arr.join(separator);
        });
        this.registerHelper('length', (arr) => {
            if (Array.isArray(arr))
                return arr.length;
            if (typeof arr === 'string')
                return arr.length;
            return 0;
        });
        this.registerHelper('includes', (arr, item) => {
            if (!Array.isArray(arr))
                return false;
            return arr.includes(item);
        });
        this.registerHelper('first', (arr) => {
            if (!Array.isArray(arr) || arr.length === 0)
                return undefined;
            return arr[0];
        });
        this.registerHelper('last', (arr) => {
            if (!Array.isArray(arr) || arr.length === 0)
                return undefined;
            return arr[arr.length - 1];
        });
        // 日期处理 helpers
        this.registerHelper('now', (format = 'ISO') => {
            const date = new Date();
            switch (format) {
                case 'ISO':
                    return date.toISOString();
                case 'date':
                    return date.toDateString();
                case 'time':
                    return date.toTimeString();
                case 'locale':
                    return date.toLocaleString();
                default:
                    return date.toISOString();
            }
        });
        this.registerHelper('formatDate', (date, format) => {
            const d = new Date(date);
            if (isNaN(d.getTime()))
                return String(date);
            switch (format) {
                case 'YYYY-MM-DD':
                    return d.toISOString().split('T')[0];
                case 'YYYY/MM/DD':
                    return d.toISOString().split('T')[0].replace(/-/g, '/');
                default:
                    return d.toISOString();
            }
        });
        // JSON 处理 helpers
        this.registerHelper('json', (obj, indent = 2) => {
            try {
                return JSON.stringify(obj, null, indent);
            }
            catch {
                return String(obj);
            }
        });
        this.registerHelper('prettyJson', (obj) => {
            try {
                return JSON.stringify(obj, null, 2);
            }
            catch {
                return String(obj);
            }
        });
        // 默认值 helper
        this.registerHelper('default', (value, defaultValue) => {
            return value != null ? value : defaultValue;
        });
        // 调试 helper
        this.registerHelper('log', (value) => {
            console.log('[Template Debug]:', value);
            return '';
        });
    }
    /**
     * 注册内置 partials
     */
    registerBuiltInPartials() {
        // 基础文档头部
        this.registerPartial('doc-header', `---
{{#if title}}title: {{title}}{{/if}}
{{#if description}}description: {{description}}{{/if}}
{{#if author}}author: {{author}}{{/if}}
{{#if version}}version: {{version}}{{/if}}
{{#if date}}created: {{date}}{{/if}}
---
`);
        // 警告框
        this.registerPartial('warning', `> ⚠️ **Warning**: {{message}}
`);
        // 提示框
        this.registerPartial('tip', `> 💡 **Tip**: {{message}}
`);
    }
    /**
     * 注册 helper
     */
    registerHelper(name, fn) {
        this.handlebars.registerHelper(name, fn);
        this.registeredHelpers.add(name);
    }
    /**
     * 注册 partial
     */
    registerPartial(name, content) {
        this.handlebars.registerPartial(name, content);
        this.registeredPartials.add(name);
    }
    /**
     * 从文件注册 partial
     */
    registerPartialFromFile(name, filePath) {
        const content = fs.readFileSync(filePath, 'utf-8');
        this.registerPartial(name, content);
    }
    /**
     * 获取已注册的 helpers
     */
    getRegisteredHelpers() {
        return Array.from(this.registeredHelpers);
    }
    /**
     * 获取已注册的 partials
     */
    getRegisteredPartials() {
        return Array.from(this.registeredPartials);
    }
    /**
     * 编译模板
     */
    compile(source, cacheKey) {
        if (cacheKey && templateCache.has(cacheKey)) {
            return templateCache.get(cacheKey);
        }
        const template = this.handlebars.compile(source, {
            strict: false,
            noEscape: false,
            preventIndent: false,
        });
        if (cacheKey) {
            templateCache.set(cacheKey, template);
        }
        return template;
    }
    /**
     * 从文件编译模板
     */
    compileFromFile(filePath, useCache = true) {
        const cacheKey = useCache ? filePath : undefined;
        if (cacheKey && templateCache.has(cacheKey)) {
            return templateCache.get(cacheKey);
        }
        if (!fs.existsSync(filePath)) {
            throw errors_enhanced_js_1.ErrorHandler.templateRenderFailed(filePath, '文件不存在');
        }
        const source = fs.readFileSync(filePath, 'utf-8');
        return this.compile(source, cacheKey);
    }
    /**
     * 渲染模板
     */
    render(source, options) {
        const errors = [];
        const warnings = [];
        const missingVariables = [];
        try {
            // 注册自定义 helpers
            if (options.helpers) {
                Object.entries(options.helpers).forEach(([name, fn]) => {
                    this.registerHelper(name, fn);
                });
            }
            // 注册自定义 partials
            if (options.partials) {
                Object.entries(options.partials).forEach(([name, content]) => {
                    this.registerPartial(name, content);
                });
            }
            // 编译模板
            const template = this.compile(source);
            // 检查缺失的变量
            if (options.strict) {
                const requiredVars = this.extractVariables(source);
                const providedVars = Object.keys(options.variables);
                const missing = requiredVars.filter(v => !providedVars.includes(v));
                if (missing.length > 0) {
                    missingVariables.push(...missing);
                    warnings.push(`缺失变量: ${missing.join(', ')}`);
                }
            }
            // 渲染
            const content = template(options.variables);
            return {
                content,
                success: true,
                warnings: warnings.length > 0 ? warnings : undefined,
                missingVariables: missingVariables.length > 0 ? missingVariables : undefined,
            };
        }
        catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            errors.push(message);
            return {
                content: '',
                success: false,
                errors,
                warnings: warnings.length > 0 ? warnings : undefined,
            };
        }
    }
    /**
     * 从文件渲染模板
     */
    renderFile(filePath, options) {
        try {
            if (!fs.existsSync(filePath)) {
                return {
                    content: '',
                    success: false,
                    errors: [`文件不存在: ${filePath}`],
                };
            }
            const source = fs.readFileSync(filePath, 'utf-8');
            return this.render(source, options);
        }
        catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            return {
                content: '',
                success: false,
                errors: [message],
            };
        }
    }
    /**
     * 提取模板中的变量
     */
    extractVariables(source) {
        const variables = new Set();
        const regex = /\{\{([^#\/\s][^\}]*)\}\}/g;
        let match;
        while ((match = regex.exec(source)) !== null) {
            const varName = match[1].trim().split(/\s+/)[0];
            // 排除 helpers 和内置变量
            if (!this.isHelper(varName) && !varName.startsWith('@')) {
                variables.add(varName);
            }
        }
        return Array.from(variables);
    }
    /**
     * 检查是否是 helper 调用
     */
    isHelper(name) {
        const helpers = ['if', 'unless', 'each', 'with', 'lookup', 'log'];
        return helpers.includes(name);
    }
    /**
     * 验证变量
     */
    validateVariables(variables, definitions) {
        const errors = [];
        for (const def of definitions) {
            const value = variables[def.name];
            // 检查必填项
            if (def.required && (value === undefined || value === null)) {
                errors.push(`变量 "${def.name}" 是必填项`);
                continue;
            }
            // 如果未提供且有默认值，跳过验证
            if (value === undefined || value === null) {
                continue;
            }
            // 类型验证
            if (def.type) {
                const actualType = Array.isArray(value) ? 'array' : typeof value;
                if (actualType !== def.type) {
                    errors.push(`变量 "${def.name}" 类型错误，期望 ${def.type}，实际 ${actualType}`);
                    continue;
                }
            }
            // 字符串验证
            if (def.type === 'string' && typeof value === 'string') {
                // 模式验证
                if (def.validation?.pattern) {
                    const regex = new RegExp(def.validation.pattern);
                    if (!regex.test(value)) {
                        errors.push(`变量 "${def.name}" 格式无效`);
                    }
                }
                // 长度验证
                if (def.validation?.min !== undefined && value.length < def.validation.min) {
                    errors.push(`变量 "${def.name}" 长度不能小于 ${def.validation.min}`);
                }
                if (def.validation?.max !== undefined && value.length > def.validation.max) {
                    errors.push(`变量 "${def.name}" 长度不能大于 ${def.validation.max}`);
                }
            }
            // 数值验证
            if (def.type === 'number' && typeof value === 'number') {
                if (def.validation?.min !== undefined && value < def.validation.min) {
                    errors.push(`变量 "${def.name}" 不能小于 ${def.validation.min}`);
                }
                if (def.validation?.max !== undefined && value > def.validation.max) {
                    errors.push(`变量 "${def.name}" 不能大于 ${def.validation.max}`);
                }
            }
            // 枚举验证
            if (def.validation?.enum && !def.validation.enum.includes(String(value))) {
                errors.push(`变量 "${def.name}" 必须是以下之一: ${def.validation.enum.join(', ')}`);
            }
        }
        return {
            valid: errors.length === 0,
            errors,
        };
    }
    /**
     * 加载模板配置
     */
    loadTemplateConfig(filePath) {
        const content = fs.readFileSync(filePath, 'utf-8');
        return JSON.parse(content);
    }
    /**
     * 批量渲染模板
     */
    renderBatch(templates, variables, options) {
        const results = [];
        for (const template of templates) {
            let result;
            if ('source' in template) {
                result = this.render(template.source, { variables });
            }
            else {
                result = this.renderFile(template.file, { variables });
            }
            if (!result.success) {
                results.push({
                    output: template.output,
                    success: false,
                    error: result.errors?.join(', '),
                });
                continue;
            }
            // 非 dry-run 模式下写入文件
            if (!options?.dryRun) {
                try {
                    const dir = path.dirname(template.output);
                    if (!fs.existsSync(dir)) {
                        fs.mkdirSync(dir, { recursive: true });
                    }
                    if (fs.existsSync(template.output) && !options?.overwrite) {
                        results.push({
                            output: template.output,
                            success: false,
                            error: '文件已存在，使用 overwrite 选项覆盖',
                        });
                        continue;
                    }
                    fs.writeFileSync(template.output, result.content, 'utf-8');
                }
                catch (error) {
                    results.push({
                        output: template.output,
                        success: false,
                        error: error instanceof Error ? error.message : String(error),
                    });
                    continue;
                }
            }
            results.push({
                output: template.output,
                success: true,
            });
        }
        return results;
    }
    /**
     * 清空模板缓存
     */
    clearCache() {
        templateCache.clear();
    }
    /**
     * 获取缓存统计
     */
    getCacheStats() {
        return {
            size: templateCache.size,
            keys: Array.from(templateCache.keys()),
        };
    }
}
exports.TemplateEngine = TemplateEngine;
// 便捷导出
exports.templateEngine = TemplateEngine.getInstance();
exports.default = exports.templateEngine;
//# sourceMappingURL=template-engine.js.map