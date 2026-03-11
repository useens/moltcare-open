"use strict";
/**
 * Init Command
 * 初始化 MoltCare 配置和环境
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
exports.initCommand = initCommand;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const chalk_1 = __importDefault(require("chalk"));
const inquirer_1 = __importDefault(require("inquirer"));
const config_js_1 = require("../config.js");
const WELCOME_BANNER = `
${chalk_1.default.cyan('╔════════════════════════════════════════════════════════╗')}
${chalk_1.default.cyan('║')}     🦞 ${chalk_1.default.bold('MoltCare')} - 智能 Agent 初始化向导              ${chalk_1.default.cyan('║')}
${chalk_1.default.cyan('║')}                                                        ${chalk_1.default.cyan('║')}
${chalk_1.default.cyan('║')}   让每一只刚安装的 OpenClaw Agent                    ${chalk_1.default.cyan('║')}
${chalk_1.default.cyan('║')}   都能一键获得专业级智能                              ${chalk_1.default.cyan('║')}
${chalk_1.default.cyan('╚════════════════════════════════════════════════════════╝')}
`;
/**
 * 检测 OpenClaw 环境
 */
function checkOpenClawEnv() {
    const details = [];
    // 检查环境变量
    const workspaceEnv = process.env.OPENCLAW_WORKSPACE;
    if (workspaceEnv) {
        details.push(`OPENCLAW_WORKSPACE: ${workspaceEnv}`);
        if (fs.existsSync(workspaceEnv)) {
            details.push(chalk_1.default.green('✓ 环境变量指向的路径存在'));
            return { exists: true, workspacePath: workspaceEnv, details };
        }
        else {
            details.push(chalk_1.default.yellow('⚠ 环境变量指向的路径不存在'));
        }
    }
    // 检查常见路径
    const commonPaths = [
        process.env.OPENCLAW_WORKSPACE,
        path.join(process.env.HOME || '/root', '.openclaw', 'workspace'),
        '/workspace',
        '/root/.openclaw/workspace',
        process.cwd(),
    ].filter(Boolean);
    for (const p of commonPaths) {
        if (fs.existsSync(p)) {
            details.push(chalk_1.default.green(`✓ 发现有效路径: ${p}`));
            return { exists: true, workspacePath: p, details };
        }
    }
    details.push(chalk_1.default.red('✗ 未发现 OpenClaw 工作区'));
    return { exists: false, details };
}
/**
 * 交互式询问配置
 */
async function promptConfig(existingConfig) {
    const config = existingConfig || config_js_1.DEFAULT_CONFIG;
    const answers = await inquirer_1.default.prompt([
        {
            type: 'list',
            name: 'language',
            message: '选择首选语言:',
            choices: [
                { name: '中文 (Chinese)', value: 'zh' },
                { name: 'English', value: 'en' },
            ],
            default: config.language,
        },
        {
            type: 'input',
            name: 'workspacePath',
            message: '设置工作区路径:',
            default: config.workspacePath,
            validate: (input) => {
                if (!input.trim())
                    return '路径不能为空';
                return true;
            },
        },
        {
            type: 'input',
            name: 'packsDir',
            message: '设置 Packs 目录:',
            default: config.packsDir,
            validate: (input) => {
                if (!input.trim())
                    return '路径不能为空';
                return true;
            },
        },
        {
            type: 'list',
            name: 'logLevel',
            message: '选择日志级别:',
            choices: [
                { name: 'debug - 详细调试信息', value: 'debug' },
                { name: 'info - 常规信息 (推荐)', value: 'info' },
                { name: 'warn - 仅警告', value: 'warn' },
                { name: 'error - 仅错误', value: 'error' },
            ],
            default: config.logLevel,
        },
        {
            type: 'confirm',
            name: 'autoUpdate',
            message: '是否启用自动更新检查?',
            default: config.autoUpdate,
        },
    ]);
    return answers;
}
/**
 * 创建示例工作区结构
 */
function createExampleWorkspace(workspacePath) {
    const dirs = [
        'memory',
        'scripts',
        'docs',
        'templates',
    ];
    for (const dir of dirs) {
        const fullPath = path.join(workspacePath, dir);
        if (!fs.existsSync(fullPath)) {
            fs.mkdirSync(fullPath, { recursive: true });
        }
    }
    // 创建示例文件
    const exampleFiles = {
        'memory/.gitkeep': '',
        'scripts/.gitkeep': '',
        'docs/README.md': `# MoltCare 工作区

这是您的 MoltCare 智能 Agent 工作区。

## 目录结构

- \`memory/\` - 记忆存储目录
- \`scripts/\` - 自定义脚本
- \`docs/\` - 文档
- \`templates/\` - 模板文件

## 开始使用

运行 \`moltcare list\` 查看可用的智能包。
`,
    };
    for (const [file, content] of Object.entries(exampleFiles)) {
        const fullPath = path.join(workspacePath, file);
        if (!fs.existsSync(fullPath)) {
            const dir = path.dirname(fullPath);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            fs.writeFileSync(fullPath, content, 'utf-8');
        }
    }
}
/**
 * 执行 init 命令
 */
async function initCommand(options) {
    console.log(WELCOME_BANNER);
    const configManager = new config_js_1.ConfigManager();
    const isInitialized = configManager.isInitialized();
    // 检查是否已初始化
    if (isInitialized && !options.force) {
        console.log(chalk_1.default.yellow('⚠️ MoltCare 已经初始化过'));
        console.log(chalk_1.default.gray(`  配置文件: ${configManager.getConfigPath()}`));
        console.log(chalk_1.default.gray('  使用 --force 强制重新初始化'));
        return;
    }
    if (isInitialized && options.force) {
        console.log(chalk_1.default.yellow('⚠️ 强制重新初始化模式'));
        console.log('');
    }
    // 检测 OpenClaw 环境
    console.log(chalk_1.default.cyan('🔍 检测 OpenClaw 环境...'));
    const envCheck = checkOpenClawEnv();
    for (const detail of envCheck.details) {
        console.log(`  ${detail}`);
    }
    console.log('');
    if (!envCheck.exists) {
        console.log(chalk_1.default.yellow('⚠️ 未检测到 OpenClaw 环境，但您可以继续初始化'));
        console.log(chalk_1.default.gray('  MoltCare 将使用独立配置'));
        console.log('');
    }
    // 获取配置
    let newConfig;
    if (options.yes) {
        // 使用默认值
        console.log(chalk_1.default.cyan('⚡ 使用默认配置'));
        newConfig = {
            workspacePath: options.workspace || envCheck.workspacePath || config_js_1.DEFAULT_CONFIG.workspacePath,
        };
    }
    else {
        newConfig = await promptConfig(configManager.getAll());
    }
    // 如果命令行指定了工作区，覆盖
    if (options.workspace) {
        newConfig.workspacePath = options.workspace;
    }
    // 更新配置
    configManager.update(newConfig);
    // 创建工作区
    const workspacePath = configManager.get('workspacePath');
    console.log(chalk_1.default.cyan('\n📁 创建工作区...'));
    try {
        createExampleWorkspace(workspacePath);
        console.log(chalk_1.default.green(`✓ 工作区创建成功: ${workspacePath}`));
    }
    catch (error) {
        console.error(chalk_1.default.red(`✗ 创建工作区失败: ${error}`));
        throw error;
    }
    // 创建 packs 目录
    const packsDir = configManager.get('packsDir');
    if (!fs.existsSync(packsDir)) {
        fs.mkdirSync(packsDir, { recursive: true });
        console.log(chalk_1.default.green(`✓ Packs 目录创建成功: ${packsDir}`));
    }
    // 标记为已初始化并保存
    configManager.markInitialized();
    console.log('');
    console.log(chalk_1.default.green('✅ MoltCare 初始化完成!'));
    console.log('');
    console.log(chalk_1.default.white('📋 配置摘要:'));
    console.log(chalk_1.default.gray(`  语言: ${configManager.get('language') === 'zh' ? '中文' : 'English'}`));
    console.log(chalk_1.default.gray(`  工作区: ${configManager.get('workspacePath')}`));
    console.log(chalk_1.default.gray(`  Packs: ${configManager.get('packsDir')}`));
    console.log(chalk_1.default.gray(`  日志级别: ${configManager.get('logLevel')}`));
    console.log('');
    console.log(chalk_1.default.white('🚀 下一步:'));
    console.log(chalk_1.default.cyan('  moltcare list          ') + chalk_1.default.gray('查看可用的智能包'));
    console.log(chalk_1.default.cyan('  moltcare apply foundation  ') + chalk_1.default.gray('安装基础智能包'));
    console.log(chalk_1.default.cyan('  moltcare --help        ') + chalk_1.default.gray('查看所有命令'));
    console.log('');
}
//# sourceMappingURL=init.js.map