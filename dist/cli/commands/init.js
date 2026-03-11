"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.initCommand = initCommand;
const fs_1 = require("fs");
const path_1 = __importDefault(require("path"));
const chalk_1 = __importDefault(require("chalk"));
const inquirer_1 = __importDefault(require("inquirer"));
const config_enhanced_js_1 = require("../../utils/config-enhanced.js");
async function initCommand(options) {
    const config = (0, config_enhanced_js_1.getEnhancedConfig)();
    if (options.verbose) {
        console.log(chalk_1.default.gray('[debug] 开始初始化...'));
        console.log(chalk_1.default.gray(`[debug] 用户配置路径: ${config.getConfigPath('user')}`));
    }
    console.log(chalk_1.default.cyan('🦞 MoltCare 初始化\n'));
    const configDir = path_1.default.dirname(config.getConfigPath('user'));
    const configPath = config.getConfigPath('user');
    // 检查是否已存在配置
    try {
        await fs_1.promises.access(configPath);
        if (!options.force) {
            console.log(chalk_1.default.yellow('⚠️  MoltCare 已初始化'));
            console.log(chalk_1.default.gray(`   配置文件: ${configPath}`));
            console.log(chalk_1.default.gray('   使用 --force 重新初始化'));
            // 显示当前配置概览
            console.log('');
            console.log(chalk_1.default.white('当前配置:'));
            console.log(chalk_1.default.gray(`  语言: ${config.get('language')}`));
            console.log(chalk_1.default.gray(`  工作区: ${config.get('workspacePath')}`));
            console.log(chalk_1.default.gray(`  日志级别: ${config.get('logLevel')}`));
            return;
        }
        console.log(chalk_1.default.yellow('⚠️  强制重新初始化将覆盖现有配置'));
        console.log('');
    }
    catch {
        // 文件不存在，继续初始化
        if (options.verbose) {
            console.log(chalk_1.default.gray('[debug] 配置文件不存在，创建新配置'));
        }
    }
    // 使用默认值或交互式询问
    let newConfig;
    if (options.yes) {
        // 使用默认配置
        newConfig = {
            version: '1.0.0',
            workspacePath: options.workspace || path_1.default.join(process.env.HOME || '~', '.moltcare', 'workspace'),
            language: 'zh',
            autoUpdate: true,
            logLevel: 'info',
            theme: 'default',
            git: {
                enabled: true,
                autoCommit: false,
                commitMessage: 'chore: update moltcare configuration',
            },
        };
        console.log(chalk_1.default.gray('使用默认配置...'));
    }
    else {
        // 交互式配置
        console.log(chalk_1.default.white('请回答以下问题来配置 MoltCare:\n'));
        const answers = await inquirer_1.default.prompt([
            {
                type: 'input',
                name: 'workspacePath',
                message: '工作区路径:',
                default: options.workspace || config.get('workspacePath'),
            },
            {
                type: 'list',
                name: 'language',
                message: '首选语言:',
                choices: [
                    { name: '中文 (zh)', value: 'zh' },
                    { name: 'English (en)', value: 'en' },
                    { name: '日本語 (ja)', value: 'ja' },
                    { name: '한국어 (ko)', value: 'ko' },
                ],
                default: config.get('language'),
            },
            {
                type: 'list',
                name: 'logLevel',
                message: '日志级别:',
                choices: [
                    { name: 'debug - 调试信息', value: 'debug' },
                    { name: 'info - 一般信息', value: 'info' },
                    { name: 'warn - 仅警告', value: 'warn' },
                    { name: 'error - 仅错误', value: 'error' },
                ],
                default: config.get('logLevel'),
            },
            {
                type: 'list',
                name: 'theme',
                message: '界面主题:',
                choices: [
                    { name: '默认', value: 'default' },
                    { name: '暗色', value: 'dark' },
                    { name: '亮色', value: 'light' },
                ],
                default: config.get('theme'),
            },
            {
                type: 'confirm',
                name: 'autoUpdate',
                message: '是否自动检查更新?',
                default: config.get('autoUpdate'),
            },
            {
                type: 'confirm',
                name: 'gitEnabled',
                message: '启用 Git 集成?',
                default: true,
            },
        ]);
        newConfig = {
            version: '1.0.0',
            workspacePath: answers.workspacePath,
            language: answers.language,
            logLevel: answers.logLevel,
            theme: answers.theme,
            autoUpdate: answers.autoUpdate,
            initialized: true,
            git: {
                enabled: answers.gitEnabled,
                autoCommit: false,
                commitMessage: 'chore: update moltcare configuration',
            },
        };
    }
    // 创建配置目录
    try {
        await fs_1.promises.mkdir(configDir, { recursive: true });
        if (options.verbose) {
            console.log(chalk_1.default.gray(`[debug] 创建配置目录: ${configDir}`));
        }
    }
    catch (error) {
        throw new Error(`无法创建配置目录: ${error}`);
    }
    // 创建工作区目录
    try {
        await fs_1.promises.mkdir(newConfig.workspacePath, { recursive: true });
        if (options.verbose) {
            console.log(chalk_1.default.gray(`[debug] 创建工作区目录: ${newConfig.workspacePath}`));
        }
    }
    catch (error) {
        throw new Error(`无法创建工作区目录: ${error}`);
    }
    // 更新配置并保存
    config.update(newConfig);
    config.markInitialized();
    if (options.verbose) {
        console.log(chalk_1.default.gray('[debug] 配置已保存'));
    }
    // 创建项目配置文件模板
    const projectConfigPath = path_1.default.join(newConfig.workspacePath, '.moltcare.yaml');
    try {
        await fs_1.promises.access(projectConfigPath);
    }
    catch {
        // 项目配置文件不存在，创建一个模板
        const projectConfigTemplate = `# MoltCare 项目配置
# 此文件应该提交到版本控制

# 项目基本信息
project:
  name: my-project
  description: ''
  
# 智能包配置
packs:
  # 自动安装的包
  autoInstall: []
  
# 模板变量
template:
  variables:
    author: ''
    email: ''
    
# 忽略的文件（不应用模板）
ignore:
  - node_modules/
  - .git/
  - dist/
`;
        await fs_1.promises.writeFile(projectConfigPath, projectConfigTemplate, 'utf-8');
        if (options.verbose) {
            console.log(chalk_1.default.gray(`[debug] 创建项目配置文件: ${projectConfigPath}`));
        }
    }
    // 显示成功信息
    console.log(chalk_1.default.green('✓ 初始化完成!'));
    console.log('');
    console.log(chalk_1.default.white('配置信息:'));
    console.log(chalk_1.default.gray(`  用户配置: ${configPath}`));
    console.log(chalk_1.default.gray(`  项目配置: ${projectConfigPath}`));
    console.log(chalk_1.default.gray(`  工作区: ${newConfig.workspacePath}`));
    console.log(chalk_1.default.gray(`  语言: ${newConfig.language}`));
    console.log('');
    // 显示后续步骤
    console.log(chalk_1.default.cyan('下一步:'));
    console.log('  $ moltcare list              # 查看可用智能包');
    console.log('  $ moltcare apply foundation  # 应用基础包');
    console.log('');
    console.log(chalk_1.default.gray('使用 "moltcare help" 查看所有命令'));
}
//# sourceMappingURL=init.js.map