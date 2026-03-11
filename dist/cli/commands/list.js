"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.listCommand = listCommand;
const fs_1 = require("fs");
const path_1 = __importDefault(require("path"));
const chalk_1 = __importDefault(require("chalk"));
async function listCommand(options) {
    const packsDir = path_1.default.join(process.cwd(), 'packs');
    try {
        await fs_1.promises.access(packsDir);
    }
    catch {
        console.error(chalk_1.default.red('✗ 未找到 packs 目录'));
        console.log(chalk_1.default.gray('  请在 MoltCare 项目目录中运行此命令'));
        process.exit(1);
    }
    const entries = await fs_1.promises.readdir(packsDir, { withFileTypes: true });
    const packs = [];
    for (const entry of entries) {
        if (!entry.isDirectory())
            continue;
        const packName = entry.name;
        if (packName.startsWith('.') || packName === 'test-pack')
            continue;
        try {
            const manifestPath = path_1.default.join(packsDir, packName, 'manifest.json');
            const manifestContent = await fs_1.promises.readFile(manifestPath, 'utf-8');
            const manifest = JSON.parse(manifestContent);
            // 检查是否已安装
            const installedMarker = path_1.default.join(packsDir, '.index.json');
            let installed = false;
            try {
                const indexContent = await fs_1.promises.readFile(installedMarker, 'utf-8');
                const index = JSON.parse(indexContent);
                installed = index.installed?.includes(packName) || false;
            }
            catch {
                // 索引文件不存在
            }
            packs.push({
                name: packName,
                category: manifest.category || 'unknown',
                version: manifest.version || '0.0.1',
                description: manifest.description || 'No description',
                installed
            });
        }
        catch {
            // 读取失败，跳过
        }
    }
    // 过滤
    let filteredPacks = packs;
    if (options.category) {
        filteredPacks = packs.filter(p => p.category === options.category);
    }
    if (options.installed) {
        filteredPacks = packs.filter(p => p.installed);
    }
    // 输出
    if (options.json) {
        console.log(JSON.stringify(filteredPacks, null, 2));
    }
    else {
        console.log(chalk_1.default.cyan('📦 可用智能包\n'));
        if (filteredPacks.length === 0) {
            console.log(chalk_1.default.gray('  未找到符合条件的智能包'));
            return;
        }
        for (const pack of filteredPacks) {
            const status = pack.installed
                ? chalk_1.default.green('✓ 已安装')
                : chalk_1.default.gray('  未安装');
            console.log(`${status}  ${chalk_1.default.bold(pack.name)}`);
            console.log(`     ${chalk_1.default.gray(pack.description)}`);
            console.log(`     ${chalk_1.default.gray(`类别: ${pack.category} | 版本: ${pack.version}`)}`);
            console.log();
        }
        console.log(chalk_1.default.gray(`共 ${filteredPacks.length} 个智能包`));
        console.log(chalk_1.default.cyan('\n使用示例:'));
        console.log('  $ moltcare apply foundation      # 应用基础包');
        console.log('  $ moltcare apply foundation --dry-run  # 预览更改');
    }
}
//# sourceMappingURL=list.js.map