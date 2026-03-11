import chalk from 'chalk';
import fs from 'fs/promises';
import path from 'path';
import { analyzeCoreFiles } from '../../core/analyzer.js';

interface VerifyOptions {
  dir?: string;
  strict?: boolean;
}

export async function verifyCommand(options: VerifyOptions): Promise<void> {
  console.log(chalk.cyan.bold('\n🦞 Moltcare - 质量验证\n'));
  
  const targetDir = path.resolve(options.dir || '.');
  
  try {
    await fs.access(targetDir);
  } catch {
    console.log(chalk.red(`❌ 目录不存在: ${targetDir}`));
    process.exit(1);
  }

  console.log(chalk.gray('📁 目标目录:'), targetDir);
  console.log(chalk.gray(`🔍 验证模式: ${options.strict ? '严格' : '标准'}\n`));

  const analysis = await analyzeCoreFiles(targetDir);

  // 验证结果
  console.log(chalk.white.bold('验证结果:'));
  console.log(chalk.gray('─'.repeat(40)));

  let passed = 0;
  let failed = 0;

  analysis.files.forEach(file => {
    if (!file.exists) {
      console.log(chalk.red(`✗ ${file.name.padEnd(15)} 文件缺失`));
      failed++;
      return;
    }

    const score = file.score || 0;
    const threshold = options.strict ? 80 : 60;
    
    if (score >= threshold) {
      console.log(chalk.green(`✓ ${file.name.padEnd(15)} ${score}/100`));
      passed++;
    } else {
      console.log(chalk.yellow(`⚠ ${file.name.padEnd(15)} ${score}/100`));
      failed++;
    }

    if (file.issues && file.issues.length > 0) {
      file.issues.forEach(issue => {
        const color = issue.severity === 'error' ? chalk.red : chalk.yellow;
        console.log(color(`   [${issue.severity}] ${issue.message}`));
      });
    }
  });

  console.log(chalk.gray('─'.repeat(40)));
  
  const total = analysis.files.length;
  console.log(chalk.white(`总计: ${chalk.green(passed.toString())} 通过, ${chalk.red(failed.toString())} 待改进 / ${total}`));

  if (failed === 0) {
    console.log(chalk.green.bold('\n✅ 所有检查通过!'));
  } else if (failed <= 2) {
    console.log(chalk.yellow.bold('\n⚠️  部分检查未通过，建议优化'));
  } else {
    console.log(chalk.red.bold('\n❌ 多项检查未通过，建议运行: moltcare init'));
  }
}
