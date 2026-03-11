import chalk from 'chalk';
import fs from 'fs/promises';
import path from 'path';
import { analyzeCoreFiles } from '../../core/analyzer.js';

interface EnhanceOptions {
  dir?: string;
  dryRun?: boolean;
}

export async function enhanceCommand(options: EnhanceOptions): Promise<void> {
  console.log(chalk.cyan.bold('\n🦞 Moltcare - 智能优化\n'));
  
  const targetDir = path.resolve(options.dir || '.');
  
  try {
    await fs.access(targetDir);
  } catch {
    console.log(chalk.red(`❌ 目录不存在: ${targetDir}`));
    process.exit(1);
  }

  console.log(chalk.gray('📁 目标目录:'), targetDir);
  console.log(chalk.gray('\n🔍 正在分析现有核心文件...\n'));

  const analysis = await analyzeCoreFiles(targetDir);

  // 显示分析结果
  console.log(chalk.white.bold('分析结果:'));
  console.log(chalk.gray('─'.repeat(40)));
  
  if (analysis.files.length === 0) {
    console.log(chalk.yellow('⚠️ 未找到核心文件'));
    console.log(chalk.gray('建议运行: moltcare init'));
    return;
  }

  analysis.files.forEach(file => {
    const status = file.exists 
      ? chalk.green('✓') 
      : chalk.red('✗');
    const score = file.score !== undefined 
      ? chalk.yellow(`${file.score}/100`) 
      : chalk.gray('N/A');
    
    console.log(`${status} ${file.name.padEnd(15)} ${score}`);
    
    if (file.issues && file.issues.length > 0) {
      file.issues.forEach(issue => {
        console.log(chalk.gray(`   ${issue.severity}: ${issue.message}`));
      });
    }
  });

  console.log(chalk.gray('─'.repeat(40)));
  console.log(chalk.white.bold(`总分: ${chalk.yellow(analysis.totalScore)}/100`));

  if (options.dryRun) {
    console.log(chalk.gray('\n[试运行模式，未执行修改]'));
    return;
  }

  console.log(chalk.gray('\n优化功能正在开发中...'));
}
