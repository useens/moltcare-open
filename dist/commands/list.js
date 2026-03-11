"use strict";
/**
 * List Command
 * 列出可用的 Packs
 */
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.listCommand = listCommand;
const chalk_1 = __importDefault(require("chalk"));
const pack_manager_js_1 = require("../pack_manager.js");
const config_js_1 = require("../config.js");
const errors_js_1 = require("../utils/errors.js");
/**
 * 格式化 pack 信息
 */
function formatPack(pack, isLast = false) {
    const indent = '  ';
    const connector = isLast ? '└── ' : '├── ';
    const subIndent = isLast ? '    ' : '│   ';
    const statusIcon = pack.installed
        ? chalk_1.default.green('●')
        : chalk_1.default.gray('○');
    const coreBadge = pack.isCore
        ? chalk_1.default.yellow('[核心] ')
        : '';
    const title = pack.title || pack.name;
    const version = chalk_1.default.gray(`v${pack.version}`);
    let lines = [];
    lines.push(`${indent}${connector}${statusIcon} ${coreBadge}${chalk_1.default.bold(title)} ${version}`);
    if (pack.description) {
        lines.push(`${indent}${subIndent}${chalk_1.default.gray(pack.description)}`);
    }
    if (pack.category) {
        lines.push(`${indent}${subIndent}${chalk_1.default.cyan(`类别: ${pack.category}`)}`);
    }
    if (pack.author) {
        lines.push(`${indent}${subIndent}${chalk_1.default.gray(`作者: ${pack.author}`)}`);
    }
    if (pack.installed && pack.installDate) {
        const date = new Date(pack.installDate).toLocaleDateString('zh-CN');
        lines.push(`${indent}${subIndent}${chalk_1.default.green(`已安装于 ${date}`)}`);
    }
    return lines.join('\n');
}
/**
 * 显示 pack 列表（表格格式）
 */
function displayTable(packs) {
    if (packs.length === 0) {
        console.log(chalk_1.default.yellow('  暂无可用的 Packs'));
        return;
    }
    // 计算列宽
    const nameWidth = Math.max(...packs.map(p => p.name.length), 10);
    const versionWidth = 10;
    const statusWidth = 8;
    // 表头
    const header = `${chalk_1.default.bold('名称').padEnd(nameWidth)}  ${chalk_1.default.bold('版本').padEnd(versionWidth)}  ${chalk_1.default.bold('状态')}`;
    const separator = '─'.repeat(nameWidth + versionWidth + statusWidth + 4);
    console.log(`  ${header}`);
    console.log(`  ${separator}`);
    // 数据行
    for (const pack of packs) {
        const status = pack.installed
            ? chalk_1.default.green('已安装')
            : chalk_1.default.gray('未安装');
        const coreBadge = pack.isCore ? chalk_1.default.yellow('★ ') : '  ';
        const name = `${coreBadge}${pack.name}`.padEnd(nameWidth);
        const version = `v${pack.version}`.padEnd(versionWidth);
        console.log(`  ${name}  ${version}  ${status}`);
    }
}
/**
 * 显示分类列表
 */
function displayByCategory(packs) {
    const categories = {};
    for (const pack of packs) {
        const category = pack.category || 'other';
        if (!categories[category]) {
            categories[category] = [];
        }
        categories[category].push(pack);
    }
    const categoryNames = {
        core: '🔧 核心包',
        foundation: '🏗️ 基础包',
        domain: '🎯 领域包',
        professional: '💼 专业包',
        other: '📦 其他包',
    };
    for (const [category, categoryPacks] of Object.entries(categories)) {
        const displayName = categoryNames[category] || `📦 ${category}`;
        console.log(`\n${chalk_1.default.bold(displayName)}`);
        console.log(chalk_1.default.gray('─'.repeat(40)));
        categoryPacks.forEach((pack, index) => {
            console.log(formatPack(pack, index === categoryPacks.length - 1));
        });
    }
}
/**
 * 执行 list 命令
 */
async function listCommand(options) {
    const configManager = new config_js_1.ConfigManager();
    // 检查是否已初始化
    if (!configManager.isInitialized()) {
        const error = errors_js_1.ErrorHandler.configNotFound();
        console.error(errors_js_1.ErrorHandler.formatError(error));
        process.exit(1);
    }
    // 获取 packs 目录
    const packsDir = configManager.get('packsDir');
    const packManager = new pack_manager_js_1.PackManager(packsDir);
    // 扫描 packs
    let packs = packManager.scanPacks();
    // 应用过滤
    if (options.category) {
        packs = packs.filter(p => (p.category || 'other').toLowerCase() === options.category.toLowerCase());
    }
    if (options.installed) {
        packs = packs.filter(p => p.installed);
    }
    // JSON 输出模式
    if (options.json) {
        console.log(JSON.stringify(packs, null, 2));
        return;
    }
    // 显示标题
    console.log(chalk_1.default.cyan('📦 可用的智能包\n'));
    // 显示统计
    const installedCount = packs.filter(p => p.installed).length;
    console.log(chalk_1.default.gray(`  总计: ${packs.length} | 已安装: ${installedCount} | 未安装: ${packs.length - installedCount}`));
    console.log('');
    // 显示列表
    if (options.category) {
        // 表格模式
        displayTable(packs);
    }
    else {
        // 分类模式
        displayByCategory(packs);
    }
    console.log('');
    console.log(chalk_1.default.gray('  ● 已安装  ○ 未安装  ★ 核心包'));
    console.log('');
    console.log(chalk_1.default.white('💡 提示:'));
    console.log(chalk_1.default.gray('  moltcare apply <pack>  安装指定 pack'));
    console.log(chalk_1.default.gray('  moltcare list --json    以 JSON 格式输出'));
    console.log(chalk_1.default.gray('  moltcare list --category foundation  按类别过滤'));
}
//# sourceMappingURL=list.js.map