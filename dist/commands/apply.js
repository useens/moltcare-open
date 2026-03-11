"use strict";
/**
 * Apply Command
 * 应用 Pack 模板到工作区
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
exports.applyCommand = applyCommand;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const chalk_1 = __importDefault(require("chalk"));
const handlebars_1 = __importDefault(require("handlebars"));
const pack_manager_js_1 = require("../pack_manager.js");
const config_js_1 = require("../config.js");
const errors_js_1 = require("../utils/errors.js");
/**
 * 备份现有文件
 */
function backupFile(filePath) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupPath = `${filePath}.backup.${timestamp}`;
    fs.copyFileSync(filePath, backupPath);
    return backupPath;
}
/**
 * 渲染模板文件
 */
function renderTemplate(templatePath, variables) {
    const content = fs.readFileSync(templatePath, 'utf-8');
    const template = handlebars_1.default.compile(content);
    return template(variables);
}
/**
 * 获取模板变量
 */
function getTemplateVariables(pack, config) {
    const now = new Date();
    return {
        pack: {
            name: pack.name,
            version: pack.version,
            title: pack.title,
            description: pack.description,
            author: pack.author,
        },
        config: {
            workspacePath: config.get('workspacePath'),
            language: config.get('language'),
            logLevel: config.get('logLevel'),
        },
        date: {
            year: now.getFullYear(),
            month: now.getMonth() + 1,
            day: now.getDate(),
            iso: now.toISOString(),
            locale: now.toLocaleDateString(config.get('language') === 'zh' ? 'zh-CN' : 'en-US'),
        },
        env: {
            home: process.env.HOME,
            user: process.env.USER,
            pwd: process.cwd(),
        },
    };
}
/**
 * 执行单个模板应用
 */
function applyTemplate(pack, template, variables, workspacePath, options) {
    const templatePath = path.join(pack.path, template.file);
    const targetPath = path.join(workspacePath, template.target);
    // 检查模板文件是否存在
    if (!fs.existsSync(templatePath)) {
        if (template.required) {
            return {
                success: false,
                action: 'failed',
                error: `模板文件不存在: ${template.file}`,
            };
        }
        return { success: true, action: 'skipped' };
    }
    // 检查目标文件是否已存在
    const targetExists = fs.existsSync(targetPath);
    if (targetExists && !options.force && !options.dryRun) {
        return {
            success: true,
            action: 'skipped',
            error: '目标文件已存在，使用 --force 覆盖',
        };
    }
    // Dry run 模式
    if (options.dryRun) {
        return { success: true, action: 'applied' };
    }
    try {
        // 备份现有文件
        let backupPath;
        if (targetExists && pack.manifest.config?.backupExisting !== false) {
            backupPath = backupFile(targetPath);
        }
        // 渲染并写入
        const rendered = renderTemplate(templatePath, variables);
        // 确保目标目录存在
        const targetDir = path.dirname(targetPath);
        if (!fs.existsSync(targetDir)) {
            fs.mkdirSync(targetDir, { recursive: true });
        }
        fs.writeFileSync(targetPath, rendered, 'utf-8');
        return {
            success: true,
            action: 'applied',
            backupPath,
        };
    }
    catch (error) {
        return {
            success: false,
            action: 'failed',
            error: error instanceof Error ? error.message : String(error),
        };
    }
}
/**
 * 执行 apply 命令
 */
async function applyCommand(packName, options) {
    const configManager = new config_js_1.ConfigManager();
    // 检查是否已初始化
    if (!configManager.isInitialized()) {
        const error = errors_js_1.ErrorHandler.configNotFound();
        console.error(errors_js_1.ErrorHandler.formatError(error));
        process.exit(1);
    }
    // 验证 pack 名称
    const packsDir = configManager.get('packsDir');
    const packManager = new pack_manager_js_1.PackManager(packsDir);
    const validation = packManager.sanitizePackName(packName);
    if (!validation.valid) {
        const error = errors_js_1.ErrorHandler.invalidPackName(packName, validation.error || '未知错误');
        console.error(errors_js_1.ErrorHandler.formatError(error));
        process.exit(1);
    }
    const sanitizedName = validation.name;
    // 获取 pack 信息
    const pack = packManager.getPack(sanitizedName);
    if (!pack) {
        const availablePacks = packManager.getPackNames();
        const error = errors_js_1.ErrorHandler.packNotFound(sanitizedName, availablePacks);
        console.error(errors_js_1.ErrorHandler.formatError(error));
        process.exit(1);
    }
    console.log(chalk_1.default.cyan(`📦 准备应用 Pack: ${chalk_1.default.bold(pack.title || pack.name)}`));
    console.log(chalk_1.default.gray(`   版本: v${pack.version}`));
    if (pack.description) {
        console.log(chalk_1.default.gray(`   描述: ${pack.description}`));
    }
    console.log('');
    // 检查是否已安装（非核心包）
    if (pack.installed && !options.force && !options.dryRun) {
        const error = errors_js_1.ErrorHandler.packAlreadyInstalled(sanitizedName);
        console.error(errors_js_1.ErrorHandler.formatError(error));
        process.exit(1);
    }
    // 显示模式信息
    if (options.dryRun) {
        console.log(chalk_1.default.yellow('🔍 预览模式 - 不会实际写入文件'));
        console.log('');
    }
    else if (options.force) {
        console.log(chalk_1.default.yellow('⚠️ 强制模式 - 将覆盖现有文件'));
        console.log('');
    }
    // 获取模板列表
    const templates = pack.manifest.templates || [];
    if (templates.length === 0) {
        console.log(chalk_1.default.yellow('⚠️ 该 Pack 没有模板文件'));
        return;
    }
    console.log(chalk_1.default.white(`📋 将应用 ${templates.length} 个模板文件:`));
    for (const template of templates) {
        const status = template.required
            ? chalk_1.default.red('[必需]')
            : chalk_1.default.gray('[可选]');
        console.log(chalk_1.default.gray(`  ${status} ${template.file} → ${template.target}`));
        if (template.description) {
            console.log(chalk_1.default.gray(`       ${template.description}`));
        }
    }
    console.log('');
    // 确认（非强制模式且非 dry-run）
    if (!options.yes && !options.dryRun) {
        const { confirm } = await import('inquirer');
        const answer = await confirm.prompt({
            type: 'confirm',
            name: 'proceed',
            message: '确认应用这些模板?',
            default: true,
        });
        if (!answer.proceed) {
            console.log(chalk_1.default.yellow('已取消'));
            return;
        }
        console.log('');
    }
    // 执行应用
    const workspacePath = configManager.get('workspacePath');
    const variables = getTemplateVariables(pack, configManager);
    const result = {
        success: true,
        packName: sanitizedName,
        applied: [],
        skipped: [],
        failed: [],
        backedUp: [],
    };
    console.log(chalk_1.default.cyan('🚀 开始应用...'));
    console.log('');
    for (const template of templates) {
        const outcome = applyTemplate(pack, template, variables, workspacePath, options);
        const displayName = `${template.file} → ${template.target}`;
        switch (outcome.action) {
            case 'applied':
                console.log(chalk_1.default.green(`  ✓ ${displayName}`));
                result.applied.push(template.target);
                if (outcome.backupPath) {
                    result.backedUp.push(outcome.backupPath);
                    console.log(chalk_1.default.gray(`    已备份: ${path.basename(outcome.backupPath)}`));
                }
                break;
            case 'skipped':
                console.log(chalk_1.default.yellow(`  ⏸ ${displayName}`));
                if (outcome.error) {
                    console.log(chalk_1.default.gray(`    ${outcome.error}`));
                }
                result.skipped.push(template.target);
                break;
            case 'failed':
                console.log(chalk_1.default.red(`  ✗ ${displayName}`));
                console.log(chalk_1.default.red(`    ${outcome.error}`));
                result.failed.push({ file: template.target, error: outcome.error || '未知错误' });
                result.success = false;
                break;
        }
    }
    console.log('');
    // 显示结果
    if (options.dryRun) {
        console.log(chalk_1.default.cyan('📋 预览结果:'));
    }
    else {
        console.log(chalk_1.default.cyan('📋 应用结果:'));
    }
    console.log(chalk_1.default.green(`  ✓ 成功: ${result.applied.length}`));
    console.log(chalk_1.default.yellow(`  ⏸ 跳过: ${result.skipped.length}`));
    console.log(chalk_1.default.red(`  ✗ 失败: ${result.failed.length}`));
    if (result.backedUp && result.backedUp.length > 0) {
        console.log(chalk_1.default.gray(`  📦 备份: ${result.backedUp.length}`));
    }
    console.log('');
    // 标记为已安装
    if (!options.dryRun && result.success && result.applied.length > 0) {
        packManager.install(sanitizedName);
        console.log(chalk_1.default.green(`✅ Pack "${sanitizedName}" 应用成功`));
    }
    if (!result.success) {
        console.log('');
        console.log(chalk_1.default.red('⚠️ 部分模板应用失败，请检查错误信息'));
        process.exit(1);
    }
}
//# sourceMappingURL=apply.js.map