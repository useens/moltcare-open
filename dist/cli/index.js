#!/usr/bin/env node
"use strict";
/**
 * MoltCare CLI - Phase 5 优化版
 *
 * 改进功能:
 * - 增强的错误处理机制
 * - 优化的模板系统
 * - 增强的配置文件支持
 * - 完善的帮助文档和命令提示
 * - 命令自动补全建议
 *
 * @version 1.1.0
 */
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const commander_1 = require("commander");
const chalk_1 = __importDefault(require("chalk"));
const init_js_1 = require("./commands/init.js");
const list_js_1 = require("./commands/list.js");
const apply_js_1 = require("./commands/apply.js");
const status_js_1 = require("./commands/status.js");
const doctor_js_1 = require("./commands/doctor.js");
const code_reviewer_js_1 = require("../review/code-reviewer.js");
const errors_enhanced_js_1 = require("../utils/errors-enhanced.js");
const help_system_js_1 = require("../utils/help-system.js");
const config_enhanced_js_1 = require("../utils/config-enhanced.js");
const program = new commander_1.Command();
const pkg = { version: '1.1.0', name: 'moltcare' };
// 设置 CLI 基础配置
program
    .name('moltcare')
    .description('MoltCare - 让每一只刚安装的 OpenClaw Agent 都能一键获得专业级智能')
    .version(pkg.version, '-v, --version', '显示版本号')
    .helpOption('-h, --help', '显示帮助信息')
    .configureOutput({
    outputError: (str, write) => write(chalk_1.default.red(str)),
})
    .exitOverride();
// ============ 核心命令 ============
// 🚀 初始化命令
program
    .command('init')
    .description('初始化 MoltCare 配置')
    .alias('initialize')
    .option('-f, --force', '强制重新初始化', false)
    .option('-y, --yes', '使用默认配置，不提示交互', false)
    .option('-w, --workspace <path>', '指定工作区路径')
    .option('-v, --verbose', '显示详细输出', false)
    .addHelpText('after', help_system_js_1.HelpSystem.findCommand('init')?.examples?.map(e => `
  $ ${e.command}  # ${e.description}`).join('\n') || '')
    .action(async (options) => {
    try {
        if (options.verbose) {
            console.log(chalk_1.default.gray('[debug] 初始化选项:'), options);
        }
        await (0, init_js_1.initCommand)(options);
        // 显示快速开始提示
        console.log('');
        console.log(chalk_1.default.cyan('💡 下一步建议:'));
        console.log(chalk_1.default.gray('  $ moltcare list       # 查看可用智能包'));
        console.log(chalk_1.default.gray('  $ moltcare apply foundation  # 应用基础包'));
    }
    catch (error) {
        errors_enhanced_js_1.ErrorHandler.exit(error instanceof Error ? error : String(error));
    }
});
// 📦 列出可用 packs
program
    .command('list')
    .description('列出所有可用的智能包')
    .alias('ls')
    .option('-c, --category <category>', '按类别过滤')
    .option('-i, --installed', '仅显示已安装的智能包', false)
    .option('--json', '以 JSON 格式输出', false)
    .option('-v, --verbose', '显示详细信息', false)
    .action(async (options) => {
    try {
        await (0, list_js_1.listCommand)(options);
    }
    catch (error) {
        errors_enhanced_js_1.ErrorHandler.exit(error instanceof Error ? error : String(error));
    }
});
// 📦 应用 pack
program
    .command('apply <pack>')
    .description('应用指定的智能包')
    .alias('install')
    .option('-f, --force', '强制重新应用，覆盖现有文件', false)
    .option('-d, --dry-run', '预览更改，不实际应用', false)
    .option('-y, --yes', '跳过确认提示', false)
    .option('-v, --verbose', '显示详细输出', false)
    .action(async (pack, options) => {
    try {
        if (options.verbose) {
            console.log(chalk_1.default.gray(`[debug] 应用 pack: ${pack}`));
            console.log(chalk_1.default.gray(`[debug] 选项: ${JSON.stringify(options)}`));
        }
        await (0, apply_js_1.applyCommand)(pack, options);
    }
    catch (error) {
        // 使用增强的错误处理
        if (error instanceof Error) {
            console.error(errors_enhanced_js_1.ErrorHandler.formatError(error));
        }
        else {
            console.error(chalk_1.default.red('✗ 应用智能包时发生错误'));
        }
        process.exit(1);
    }
});
// 🔍 代码评审命令
program
    .command('review [path]')
    .description('对代码进行审查')
    .alias('check')
    .option('--format <type>', '输出格式: text|json', 'text')
    .option('-s, --strict', '严格模式', false)
    .action(async (filePath, options) => {
    try {
        const config = (0, config_enhanced_js_1.getEnhancedConfig)();
        const reviewer = new code_reviewer_js_1.CodeReviewer();
        const target = filePath || './src';
        console.log(chalk_1.default.cyan('🔍 正在审查代码...'));
        console.log(chalk_1.default.gray(`  目标: ${target}`));
        console.log(chalk_1.default.gray(`  严格模式: ${options.strict ? '是' : '否'}`));
        console.log('');
        const reviews = await reviewer.reviewDirectory(target);
        if (options.format === 'json') {
            console.log(JSON.stringify(reviews, null, 2));
        }
        else {
            const report = reviewer.generateReport(reviews);
            console.log(report);
        }
    }
    catch (error) {
        errors_enhanced_js_1.ErrorHandler.exit(error instanceof Error ? error : String(error));
    }
});
// 🧪 测试命令
program
    .command('test [pattern]')
    .description('运行测试')
    .option('-w, --watch', '监视模式', false)
    .option('-c, --coverage', '生成覆盖率报告', false)
    .action(async (pattern, options) => {
    try {
        console.log(chalk_1.default.cyan('🧪 运行测试...'));
        if (pattern) {
            console.log(chalk_1.default.gray(`  匹配模式: ${pattern}`));
        }
        if (options.watch) {
            console.log(chalk_1.default.gray('  监视模式已启用'));
        }
        if (options.coverage) {
            console.log(chalk_1.default.gray('  覆盖率报告'));
        }
        const { execSync } = await import('child_process');
        let cmd = 'npm test';
        if (options.watch) {
            cmd += ' -- --watch';
        }
        if (options.coverage) {
            cmd = 'npm run test:coverage';
        }
        if (pattern) {
            cmd += ` -- ${pattern}`;
        }
        execSync(cmd, { stdio: 'inherit', cwd: process.cwd() });
    }
    catch {
        process.exit(1);
    }
});
// 🔄 同步命令
program
    .command('sync')
    .description('显示协作状态')
    .action(() => {
    console.log(chalk_1.default.cyan('🔄 MoltCare 协作状态'));
    console.log('');
    console.log(chalk_1.default.white('  KimiSensen:'));
    console.log(chalk_1.default.green('    ✅ CLI 框架 (Phase 5 已优化)'));
    console.log(chalk_1.default.green('    ✅ 多专家决策系统'));
    console.log(chalk_1.default.green('    ✅ 增强的错误处理'));
    console.log(chalk_1.default.green('    ✅ 优化的模板系统'));
    console.log('');
    console.log(chalk_1.default.white('  OracleSensen:'));
    console.log(chalk_1.default.green('    ✅ 测试框架 (Vitest)'));
    console.log(chalk_1.default.green('    ✅ 代码审查系统'));
    console.log(chalk_1.default.green('    ✅ 文档框架'));
    console.log('');
    console.log(chalk_1.default.white('  Bridge:'));
    console.log(chalk_1.default.gray('    https://github.com/useens/moltcare-bridge'));
});
// 📊 状态命令
program
    .command('status')
    .description('显示 MoltCare 状态信息')
    .alias('info')
    .option('--json', '以 JSON 格式输出', false)
    .option('-v, --verbose', '显示详细信息', false)
    .action(async (options) => {
    try {
        await (0, status_js_1.statusCommand)(options);
    }
    catch (error) {
        errors_enhanced_js_1.ErrorHandler.exit(error instanceof Error ? error : String(error));
    }
});
// 🔧 诊断命令
program
    .command('doctor')
    .description('运行系统健康诊断')
    .alias('diagnose')
    .option('--fix', '尝试自动修复问题', false)
    .option('--json', '以 JSON 格式输出', false)
    .action(async (options) => {
    try {
        await (0, doctor_js_1.doctorCommand)(options);
    }
    catch (error) {
        errors_enhanced_js_1.ErrorHandler.exit(error instanceof Error ? error : String(error));
    }
});
// ⚙️ 配置命令
const configCmd = program
    .command('config')
    .description('管理 MoltCare 配置');
configCmd
    .command('get <key>')
    .description('获取配置项值')
    .action((key) => {
    try {
        const config = (0, config_enhanced_js_1.getEnhancedConfig)();
        const value = config.get(key);
        console.log(value !== undefined ? String(value) : chalk_1.default.gray('(未设置)'));
    }
    catch (error) {
        errors_enhanced_js_1.ErrorHandler.exit(error instanceof Error ? error : String(error));
    }
});
configCmd
    .command('set <key> <value>')
    .description('设置配置项值')
    .action((key, value) => {
    try {
        const config = (0, config_enhanced_js_1.getEnhancedConfig)();
        // 尝试解析布尔值和数字
        let parsedValue = value;
        if (value === 'true')
            parsedValue = true;
        else if (value === 'false')
            parsedValue = false;
        else if (!isNaN(Number(value)))
            parsedValue = Number(value);
        config.set(key, parsedValue);
        config.save();
        console.log(chalk_1.default.green(`✓ 已设置 ${key} = ${value}`));
    }
    catch (error) {
        errors_enhanced_js_1.ErrorHandler.exit(error instanceof Error ? error : String(error));
    }
});
configCmd
    .command('list')
    .description('列出所有配置')
    .option('--json', 'JSON 格式输出')
    .action((options) => {
    try {
        const config = (0, config_enhanced_js_1.getEnhancedConfig)();
        const all = config.getAll();
        if (options.json) {
            console.log(JSON.stringify(all, null, 2));
            return;
        }
        console.log(chalk_1.default.cyan('⚙️  MoltCare 配置'));
        console.log('');
        Object.entries(all).forEach(([key, value]) => {
            const source = config.getSource(key);
            const sourceIcon = source === 'default' ? chalk_1.default.gray('(默认)') : chalk_1.default.cyan(`(${source})`);
            console.log(`  ${chalk_1.default.green(key.padEnd(16))} ${String(value).padEnd(20)} ${sourceIcon}`);
        });
    }
    catch (error) {
        errors_enhanced_js_1.ErrorHandler.exit(error instanceof Error ? error : String(error));
    }
});
// 🆘 帮助命令
program
    .command('help [command]')
    .description('显示帮助信息')
    .action((commandName) => {
    if (commandName) {
        help_system_js_1.HelpSystem.showCommandHelp(commandName);
    }
    else {
        help_system_js_1.HelpSystem.showGlobalHelp(program);
    }
});
// ============ 全局错误处理 ============
process.on('unhandledRejection', (reason) => {
    console.error(chalk_1.default.red('未处理的 Promise 拒绝:'));
    console.error(reason);
    process.exit(1);
});
process.on('uncaughtException', (error) => {
    console.error(chalk_1.default.red('未捕获的异常:'));
    console.error(error);
    process.exit(1);
});
// ============ 启动 CLI ============
try {
    program.parse();
}
catch (error) {
    if (error.code === 'commander.help') {
        help_system_js_1.HelpSystem.showGlobalHelp(program);
        process.exit(0);
    }
    if (error.code === 'commander.version') {
        console.log(chalk_1.default.cyan(`🦞 ${pkg.name} v${pkg.version}`));
        process.exit(0);
    }
    if (error.code === 'commander.unknownCommand') {
        console.error(chalk_1.default.red(`✗ 未知命令: ${error.message}`));
        console.log(chalk_1.default.yellow(`\n您是否想输入:`));
        const suggestions = ['init', 'list', 'apply', 'review', 'test', 'sync', 'status', 'config', 'help'];
        const similar = suggestions.filter(c => c.includes(error.message.toLowerCase()) ||
            error.message.toLowerCase().includes(c));
        similar.forEach(cmd => console.log(`  • ${chalk_1.default.cyan(cmd)}`));
        process.exit(1);
    }
    if (error.code === 'commander.unknownOption') {
        console.error(chalk_1.default.red(`✗ 未知选项: ${error.message}`));
        process.exit(1);
    }
    if (error.code === 'commander.missingArgument') {
        console.error(chalk_1.default.red(`✗ 缺少参数: ${error.message}`));
        process.exit(1);
    }
    console.error(chalk_1.default.red(`✗ 错误: ${error.message}`));
    process.exit(1);
}
//# sourceMappingURL=index.js.map