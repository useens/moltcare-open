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
const js_yaml_1 = __importDefault(require("js-yaml"));
async function initCommand(options) {
    console.log(chalk_1.default.cyan('🦞 MoltCare 初始化\n'));
    const configDir = path_1.default.join(process.env.HOME || '~', '.moltcare');
    const configPath = path_1.default.join(configDir, 'config.yaml');
    // 检查是否已存在配置
    try {
        await fs_1.promises.access(configPath);
        if (!options.force) {
            console.log(chalk_1.default.yellow('⚠️  MoltCare 已初始化'));
            console.log(chalk_1.default.gray(`   配置文件: ${configPath}`));
            console.log(chalk_1.default.gray('   使用 --force 重新初始化'));
            return;
        }
    }
    catch {
        // 文件不存在，继续初始化
    }
    // 使用默认值或交互式询问
    let config;
    if (options.yes) {
        config = {
            version: '1.0.0',
            workspace: options.workspace || path_1.default.join(process.env.HOME || '~', 'moltcare-workspace'),
            language: 'zh',
            autoUpdate: true,
            packs: []
        };
    }
    else {
        const answers = await inquirer_1.default.prompt([
            {
                type: 'input',
                name: 'workspace',
                message: '工作区路径:',
                default: options.workspace || path_1.default.join(process.env.HOME || '~', 'moltcare-workspace')
            },
            {
                type: 'list',
                name: 'language',
                message: '首选语言:',
                choices: [
                    { name: '中文', value: 'zh' },
                    { name: 'English', value: 'en' },
                    { name: '日本語', value: 'ja' }
                ],
                default: 'zh'
            },
            {
                type: 'confirm',
                name: 'autoUpdate',
                message: '是否自动检查更新?',
                default: true
            }
        ]);
        config = {
            version: '1.0.0',
            workspace: answers.workspace,
            language: answers.language,
            autoUpdate: answers.autoUpdate,
            packs: []
        };
    }
    // 创建配置目录
    await fs_1.promises.mkdir(configDir, { recursive: true });
    // 写入配置文件
    const configYaml = js_yaml_1.default.dump(config);
    await fs_1.promises.writeFile(configPath, configYaml, 'utf-8');
    // 创建工作区目录
    await fs_1.promises.mkdir(config.workspace, { recursive: true });
    console.log(chalk_1.default.green('✓ 初始化完成!'));
    console.log(chalk_1.default.gray(`  配置文件: ${configPath}`));
    console.log(chalk_1.default.gray(`  工作区: ${config.workspace}`));
    console.log(chalk_1.default.cyan('\n下一步:'));
    console.log('  $ moltcare list       # 查看可用智能包');
    console.log('  $ moltcare apply foundation  # 应用基础包');
}
//# sourceMappingURL=init.js.map