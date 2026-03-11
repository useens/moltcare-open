import { promises as fs } from 'fs';
import path from 'path';
import chalk from 'chalk';

interface ApplyOptions {
  force?: boolean;
  dryRun?: boolean;
  yes?: boolean;
}

export async function applyCommand(packName: string, options: ApplyOptions): Promise<void> {
  // 验证 pack 名称
  if (!packName || packName.trim() === '') {
    console.error(chalk.red('✗ 请指定要应用的智能包名称'));
    console.log(chalk.gray('  示例: moltcare apply foundation'));
    console.log(chalk.gray('  运行 \'moltcare list\' 查看可用包'));
    process.exit(1);
  }

  // 清理名称
  const sanitizedName = packName.trim().toLowerCase();

  // 检查是否包含非法字符
  if (/[\/\\<>:"|?*]/.test(sanitizedName) || sanitizedName.includes('..')) {
    console.error(chalk.red(`✗ 非法的 pack 名称: "${packName}"`));
    console.log(chalk.gray('  名称不能包含路径分隔符或特殊字符'));
    process.exit(1);
  }

  const packsDir = path.join(process.cwd(), 'packs');
  const packPath = path.join(packsDir, sanitizedName);

  // 检查 pack 是否存在
  try {
    await fs.access(packPath);
  } catch {
    console.error(chalk.red(`✗ 智能包 "${sanitizedName}" 不存在`));
    
    // 尝试提供建议
    try {
      const entries = await fs.readdir(packsDir, { withFileTypes: true });
      const availablePacks = entries
        .filter(e => e.isDirectory() && !e.name.startsWith('.'))
        .map(e => e.name);
      
      const similar = availablePacks.filter(p => 
        p.includes(sanitizedName) || sanitizedName.includes(p)
      );
      
      if (similar.length > 0) {
        console.log(chalk.yellow('\n您是否想输入:'));
        similar.forEach(p => console.log(`  • ${p}`));
      }
      
      console.log(chalk.gray(`\n运行 'moltcare list' 查看所有可用包`));
    } catch {
      // 忽略错误
    }
    
    process.exit(1);
  }

  // 读取 manifest
  let manifest;
  try {
    const manifestPath = path.join(packPath, 'manifest.json');
    const content = await fs.readFile(manifestPath, 'utf-8');
    manifest = JSON.parse(content);
  } catch {
    console.error(chalk.red(`✗ 无法读取 "${sanitizedName}" 的 manifest`));
    process.exit(1);
  }

  console.log(chalk.cyan(`📦 应用智能包: ${chalk.bold(manifest.name || sanitizedName)}`));
  console.log(chalk.gray(`   ${manifest.description || '无描述'}`));
  console.log();

  // 如果是 dry-run，仅预览
  if (options.dryRun) {
    console.log(chalk.yellow('🔍 预览模式 (dry-run)，不会实际应用更改'));
    console.log();
    
    // 列出将要应用的文件
    const templatesDir = path.join(packPath, 'templates');
    try {
      await fs.access(templatesDir);
      console.log(chalk.gray('将要应用的模板文件:'));
      
      const listFiles = async (dir: string, prefix = '') => {
        const entries = await fs.readdir(dir, { withFileTypes: true });
        for (const entry of entries) {
          const fullPath = path.join(dir, entry.name);
          if (entry.isDirectory()) {
            console.log(chalk.gray(`${prefix}📁 ${entry.name}/`));
            await listFiles(fullPath, prefix + '  ');
          } else {
            console.log(chalk.gray(`${prefix}📄 ${entry.name}`));
          }
        }
      };
      
      await listFiles(templatesDir);
    } catch {
      console.log(chalk.gray('  无模板文件'));
    }
    
    console.log();
    console.log(chalk.cyan('使用 --force 实际应用这些更改'));
    return;
  }

  // 确认提示
  if (!options.yes) {
    console.log(chalk.yellow('⚠️  提示: 使用 --yes 跳过确认提示'));
    console.log(chalk.gray('   或使用 --dry-run 预览更改'));
    console.log();
  }

  // 实际应用
  console.log(chalk.gray('正在应用...'));
  
  // 读取配置获取目标工作区
  const configPath = path.join(process.env.HOME || '~', '.moltcare', 'config.yaml');
  let targetWorkspace = process.cwd();
  
  try {
    const yaml = await import('js-yaml');
    const configContent = await fs.readFile(configPath, 'utf-8');
    const config = yaml.load(configContent) as any;
    targetWorkspace = config.workspace || targetWorkspace;
  } catch {
    // 使用当前目录
  }

  // 复制模板文件
  const templatesDir = path.join(packPath, 'templates');
  const scriptsDir = path.join(packPath, 'scripts');
  
  try {
    await fs.access(templatesDir);
    await copyDir(templatesDir, targetWorkspace, !!options.force);
  } catch {
    // 无模板目录
  }

  try {
    await fs.access(scriptsDir);
    await copyDir(scriptsDir, path.join(targetWorkspace, 'scripts'), !!options.force);
  } catch {
    // 无脚本目录
  }

  console.log(chalk.green(`✓ 智能包 "${sanitizedName}" 应用成功!`));
  console.log(chalk.gray(`  目标目录: ${targetWorkspace}`));
}

async function copyDir(src: string, dest: string, force: boolean): Promise<void> {
  await fs.mkdir(dest, { recursive: true });
  
  const entries = await fs.readdir(src, { withFileTypes: true });
  
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    
    if (entry.isDirectory()) {
      await copyDir(srcPath, destPath, force);
    } else {
      // 检查目标文件是否存在
      if (!force) {
        try {
          await fs.access(destPath);
          console.log(chalk.yellow(`  ⚠️  跳过已存在文件: ${entry.name}`));
          continue;
        } catch {
          // 文件不存在，继续
        }
      }
      
      await fs.copyFile(srcPath, destPath);
      console.log(chalk.gray(`  📄 ${entry.name}`));
    }
  }
}
