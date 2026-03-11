import { promises as fs } from 'fs';
import path from 'path';
import chalk from 'chalk';

interface ListOptions {
  category?: string;
  installed?: boolean;
  json?: boolean;
}

interface PackInfo {
  name: string;
  category: string;
  version: string;
  description: string;
  installed: boolean;
}

export async function listCommand(options: ListOptions): Promise<void> {
  const packsDir = path.join(process.cwd(), 'packs');
  
  try {
    await fs.access(packsDir);
  } catch {
    console.error(chalk.red('✗ 未找到 packs 目录'));
    console.log(chalk.gray('  请在 MoltCare 项目目录中运行此命令'));
    process.exit(1);
  }

  const entries = await fs.readdir(packsDir, { withFileTypes: true });
  const packs: PackInfo[] = [];

  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    
    const packName = entry.name;
    if (packName.startsWith('.') || packName === 'test-pack') continue;

    try {
      const manifestPath = path.join(packsDir, packName, 'manifest.json');
      const manifestContent = await fs.readFile(manifestPath, 'utf-8');
      const manifest = JSON.parse(manifestContent);

      // 检查是否已安装
      const installedMarker = path.join(packsDir, '.index.json');
      let installed = false;
      try {
        const indexContent = await fs.readFile(installedMarker, 'utf-8');
        const index = JSON.parse(indexContent);
        installed = index.installed?.includes(packName) || false;
      } catch {
        // 索引文件不存在
      }

      packs.push({
        name: packName,
        category: manifest.category || 'unknown',
        version: manifest.version || '0.0.1',
        description: manifest.description || 'No description',
        installed
      });
    } catch {
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
  } else {
    console.log(chalk.cyan('📦 可用智能包\n'));
    
    if (filteredPacks.length === 0) {
      console.log(chalk.gray('  未找到符合条件的智能包'));
      return;
    }

    for (const pack of filteredPacks) {
      const status = pack.installed 
        ? chalk.green('✓ 已安装') 
        : chalk.gray('  未安装');
      
      console.log(`${status}  ${chalk.bold(pack.name)}`);
      console.log(`     ${chalk.gray(pack.description)}`);
      console.log(`     ${chalk.gray(`类别: ${pack.category} | 版本: ${pack.version}`)}`);
      console.log();
    }

    console.log(chalk.gray(`共 ${filteredPacks.length} 个智能包`));
    console.log(chalk.cyan('\n使用示例:'));
    console.log('  $ moltcare apply foundation      # 应用基础包');
    console.log('  $ moltcare apply foundation --dry-run  # 预览更改');
  }
}
