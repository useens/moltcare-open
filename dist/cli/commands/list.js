"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.listCommand = listCommand;
const fs_1 = require("fs");
const path_1 = __importDefault(require("path"));
const chalk_1 = __importDefault(require("chalk"));
const errors_enhanced_js_1 = require("../../utils/errors-enhanced.js");
async function listCommand(options) {
    const packsDir = path_1.default.join(process.cwd(), 'packs');
    // 检查 packs 目录是否存在
    try {
        await fs_1.promises.access(packsDir);
    }
    catch {
        const error = new (await import('../../utils/errors-enhanced.js')).MoltCareError({
            code: 'DIRECTORY_NOT_FOUND',
            message: '未找到 packs 目录',
            category: 'FILE_SYSTEM',
            severity: 'error',
            suggestion: '请在 MoltCare 项目目录中运行此命令',
        });
        console.error(errors_enhanced_js_1.ErrorHandler.formatError(error));
        process.exit(1);
    }
    const entries = await fs_1.promises.readdir(packsDir, { withFileTypes: true });
    const packs = [];
    // 读取索引文件
    let installedPacks = [];
    try {
        const indexPath = path_1.default.join(packsDir, '.index.json');
        const indexContent = await fs_1.promises.readFile(indexPath, 'utf-8');
        const index = JSON.parse(indexContent);
        installedPacks = Object.keys(index.packs || {});
    }
    catch {
        // 索引文件不存在或无效
        if (options.verbose) {
            console.log(chalk_1.default.gray('[debug] 索引文件不存在或无效'));
        }
    }
    // 扫描所有 packs
    for (const entry of entries) {
        if (!entry.isDirectory())
            continue;
        const packName = entry.name;
        if (packName.startsWith('.') || packName === 'test-pack')
            continue;
        try {
            const packPath = path_1.default.join(packsDir, packName);
            // 尝试读取 manifest.json
            let manifest = {};
            try {
                const manifestPath = path_1.default.join(packPath, 'manifest.json');
                const manifestContent = await fs_1.promises.readFile(manifestPath, 'utf-8');
                manifest = JSON.parse(manifestContent);
            }
            catch {
                // 尝试读取 pack.yaml
                try {
                    const packYamlPath = path_1.default.join(packPath, 'pack.yaml');
                    const packYamlContent = await fs_1.promises.readFile(packYamlPath, 'utf-8');
                    const yaml = await import('js-yaml');
                    manifest = yaml.load(packYamlContent);
                }
                catch {
                    // 无法读取 manifest
                    if (options.verbose) {
                        console.log(chalk_1.default.gray(`[debug] 无法读取 ${packName} 的 manifest`));
                    }
                }
            }
            // 判断是否已安装
            const installed = installedPacks.includes(packName);
            packs.push({
                name: packName,
                category: manifest.category || 'unknown',
                version: manifest.version || '0.0.1',
                description: manifest.description || manifest.title || '暂无描述',
                installed,
                author: manifest.author,
                priority: manifest.priority,
            });
        }
        catch (error) {
            if (options.verbose) {
                console.log(chalk_1.default.gray(`[debug] 读取 ${packName} 失败: ${error}`));
            }
        }
    }
    // 排序: 核心包优先，然后按优先级
    packs.sort((a, b) => {
        if (a.category === 'core' && b.category !== 'core')
            return -1;
        if (a.category !== 'core' && b.category === 'core')
            return 1;
        return (a.priority || 0) - (b.priority || 0);
    });
    // 过滤
    let filteredPacks = packs;
    if (options.category) {
        filteredPacks = packs.filter(p => p.category.toLowerCase() === options.category.toLowerCase());
    }
    if (options.installed) {
        filteredPacks = packs.filter(p => p.installed);
    }
    // 输出
    if (options.json) {
        console.log(JSON.stringify(filteredPacks, null, 2));
        return;
    }
    console.log(chalk_1.default.cyan('📦 可用智能包\n'));
    if (filteredPacks.length === 0) {
        console.log(chalk_1.default.gray('  未找到符合条件的智能包'));
        if (options.category) {
            console.log(chalk_1.default.gray(`  类别过滤: ${options.category}`));
        }
        return;
    }
    // 按类别分组显示
    const byCategory = new Map();
    for (const pack of filteredPacks) {
        const cat = pack.category;
        if (!byCategory.has(cat)) {
            byCategory.set(cat, []);
        }
        byCategory.get(cat).push(pack);
    }
    for (const [category, catPacks] of byCategory) {
        console.log(chalk_1.default.white.bold(category.charAt(0).toUpperCase() + category.slice(1)));
        console.log('');
        for (const pack of catPacks) {
            const status = pack.installed
                ? chalk_1.default.green('✓ 已安装')
                : chalk_1.default.gray('  未安装');
            console.log(`  ${status}  ${chalk_1.default.bold(pack.name)} ${chalk_1.default.gray(`v${pack.version}`)}`);
            console.log(`       ${chalk_1.default.gray(pack.description)}`);
            if (options.verbose) {
                if (pack.author) {
                    console.log(`       ${chalk_1.default.gray(`作者: ${pack.author}`)}`);
                }
                if (pack.priority !== undefined) {
                    console.log(`       ${chalk_1.default.gray(`优先级: ${pack.priority}`)}`);
                }
            }
            console.log();
        }
    }
    // 统计
    const installedCount = filteredPacks.filter(p => p.installed).length;
    console.log(chalk_1.default.gray(`共 ${filteredPacks.length} 个智能包`));
    console.log(chalk_1.default.gray(`已安装: ${installedCount} | 未安装: ${filteredPacks.length - installedCount}`));
    console.log('');
    // 使用提示
    console.log(chalk_1.default.cyan('使用示例:'));
    console.log('  $ moltcare apply foundation      # 应用基础包');
    console.log('  $ moltcare apply foundation --dry-run  # 预览更改');
    console.log('');
}
//# sourceMappingURL=list.js.map