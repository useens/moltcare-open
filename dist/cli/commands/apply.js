"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.applyCommand = applyCommand;
const fs_1 = require("fs");
const path_1 = __importDefault(require("path"));
const chalk_1 = __importDefault(require("chalk"));
async function applyCommand(packName, options) {
    // 验证 pack 名称
    if (!packName || packName.trim() === '') {
        console.error(chalk_1.default.red('✗ 请指定要应用的智能包名称'));
        console.log(chalk_1.default.gray('  示例: moltcare apply foundation'));
        console.log(chalk_1.default.gray('  运行 \'moltcare list\' 查看可用包'));
        process.exit(1);
    }
    // 清理名称
    const sanitizedName = packName.trim().toLowerCase();
    // 检查是否包含非法字符
    if (/[\/\\<>:"|?*]/.test(sanitizedName) || sanitizedName.includes('..')) {
        console.error(chalk_1.default.red(`✗ 非法的 pack 名称: "${packName}"`));
        console.log(chalk_1.default.gray('  名称不能包含路径分隔符或特殊字符'));
        process.exit(1);
    }
    const packsDir = path_1.default.join(process.cwd(), 'packs');
    const packPath = path_1.default.join(packsDir, sanitizedName);
    // 检查 pack 是否存在
    try {
        await fs_1.promises.access(packPath);
    }
    catch {
        console.error(chalk_1.default.red(`✗ 智能包 "${sanitizedName}" 不存在`));
        // 尝试提供建议
        try {
            const entries = await fs_1.promises.readdir(packsDir, { withFileTypes: true });
            const availablePacks = entries
                .filter(e => e.isDirectory() && !e.name.startsWith('.'))
                .map(e => e.name);
            const similar = availablePacks.filter(p => p.includes(sanitizedName) || sanitizedName.includes(p));
            if (similar.length > 0) {
                console.log(chalk_1.default.yellow('\n您是否想输入:'));
                similar.forEach(p => console.log(`  • ${p}`));
            }
            console.log(chalk_1.default.gray(`\n运行 'moltcare list' 查看所有可用包`));
        }
        catch {
            // 忽略错误
        }
        process.exit(1);
    }
    // 读取 manifest
    let manifest;
    try {
        const manifestPath = path_1.default.join(packPath, 'manifest.json');
        const content = await fs_1.promises.readFile(manifestPath, 'utf-8');
        manifest = JSON.parse(content);
    }
    catch {
        console.error(chalk_1.default.red(`✗ 无法读取 "${sanitizedName}" 的 manifest`));
        process.exit(1);
    }
    console.log(chalk_1.default.cyan(`📦 应用智能包: ${chalk_1.default.bold(manifest.name || sanitizedName)}`));
    console.log(chalk_1.default.gray(`   ${manifest.description || '无描述'}`));
    console.log();
    // 如果是 dry-run，仅预览
    if (options.dryRun) {
        console.log(chalk_1.default.yellow('🔍 预览模式 (dry-run)，不会实际应用更改'));
        console.log();
        // 列出将要应用的文件
        const templatesDir = path_1.default.join(packPath, 'templates');
        try {
            await fs_1.promises.access(templatesDir);
            console.log(chalk_1.default.gray('将要应用的模板文件:'));
            const listFiles = async (dir, prefix = '') => {
                const entries = await fs_1.promises.readdir(dir, { withFileTypes: true });
                for (const entry of entries) {
                    const fullPath = path_1.default.join(dir, entry.name);
                    if (entry.isDirectory()) {
                        console.log(chalk_1.default.gray(`${prefix}📁 ${entry.name}/`));
                        await listFiles(fullPath, prefix + '  ');
                    }
                    else {
                        console.log(chalk_1.default.gray(`${prefix}📄 ${entry.name}`));
                    }
                }
            };
            await listFiles(templatesDir);
        }
        catch {
            console.log(chalk_1.default.gray('  无模板文件'));
        }
        console.log();
        console.log(chalk_1.default.cyan('使用 --force 实际应用这些更改'));
        return;
    }
    // 确认提示
    if (!options.yes) {
        console.log(chalk_1.default.yellow('⚠️  提示: 使用 --yes 跳过确认提示'));
        console.log(chalk_1.default.gray('   或使用 --dry-run 预览更改'));
        console.log();
    }
    // 实际应用
    console.log(chalk_1.default.gray('正在应用...'));
    // 读取配置获取目标工作区
    const configPath = path_1.default.join(process.env.HOME || '~', '.moltcare', 'config.yaml');
    let targetWorkspace = process.cwd();
    try {
        const yaml = await import('js-yaml');
        const configContent = await fs_1.promises.readFile(configPath, 'utf-8');
        const config = yaml.load(configContent);
        targetWorkspace = config.workspace || targetWorkspace;
    }
    catch {
        // 使用当前目录
    }
    // 复制模板文件
    const templatesDir = path_1.default.join(packPath, 'templates');
    const scriptsDir = path_1.default.join(packPath, 'scripts');
    try {
        await fs_1.promises.access(templatesDir);
        await copyDir(templatesDir, targetWorkspace, !!options.force);
    }
    catch {
        // 无模板目录
    }
    try {
        await fs_1.promises.access(scriptsDir);
        await copyDir(scriptsDir, path_1.default.join(targetWorkspace, 'scripts'), !!options.force);
    }
    catch {
        // 无脚本目录
    }
    console.log(chalk_1.default.green(`✓ 智能包 "${sanitizedName}" 应用成功!`));
    console.log(chalk_1.default.gray(`  目标目录: ${targetWorkspace}`));
}
async function copyDir(src, dest, force) {
    await fs_1.promises.mkdir(dest, { recursive: true });
    const entries = await fs_1.promises.readdir(src, { withFileTypes: true });
    for (const entry of entries) {
        const srcPath = path_1.default.join(src, entry.name);
        const destPath = path_1.default.join(dest, entry.name);
        if (entry.isDirectory()) {
            await copyDir(srcPath, destPath, force);
        }
        else {
            // 检查目标文件是否存在
            if (!force) {
                try {
                    await fs_1.promises.access(destPath);
                    console.log(chalk_1.default.yellow(`  ⚠️  跳过已存在文件: ${entry.name}`));
                    continue;
                }
                catch {
                    // 文件不存在，继续
                }
            }
            await fs_1.promises.copyFile(srcPath, destPath);
            console.log(chalk_1.default.gray(`  📄 ${entry.name}`));
        }
    }
}
//# sourceMappingURL=apply.js.map