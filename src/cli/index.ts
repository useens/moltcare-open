#!/usr/bin/env node
/**
 * MoltCare CLI - 统一入口
 * 
 * 整合功能:
 * - KimiSensen: 多专家系统, 智能包管理
 * - OracleSensen: 代码评审, 测试框架
 * 
 * @version 1.0.0
 */

import { Command } from 'commander';
import chalk from 'chalk';
import { initCommand } from './commands/init.js';
import { listCommand } from './commands/list.js';
import { applyCommand } from './commands/apply.js';
import { CodeReviewer } from '../review/code-reviewer.js';

const program = new Command();

program
  .name('moltcare')
  .description('MoltCare - 让每一只刚安装的 OpenClaw Agent 都能一键获得专业级智能')
  .version('1.0.0')
  .configureOutput({
    outputError: (str, write) => write(chalk.red(str))
  });

// 🚀 初始化命令
program
  .command('init')
  .description('Initialize MoltCare in current directory')
  .option('-f, --force', 'Force reinitialization')
  .option('-y, --yes', 'Use default values without prompting')
  .option('-w, --workspace <path>', 'Specify workspace path')
  .addHelpText('after', `
Examples:
  $ moltcare init              # 交互式初始化
  $ moltcare init --yes        # 使用默认配置
  $ moltcare init --force      # 强制重新初始化
  $ moltcare init -w /path     # 指定工作区路径
`)
  .action(async (options) => {
    try {
      await initCommand(options);
    } catch (error) {
      console.error(chalk.red(`✗ 初始化失败: ${error}`));
      process.exit(1);
    }
  });

// 📦 列出可用 packs
program
  .command('list')
  .description('List available intelligence packs')
  .option('-c, --category <category>', 'Filter by category')
  .option('-i, --installed', 'Show only installed packs')
  .option('--json', 'Output as JSON')
  .addHelpText('after', `
Examples:
  $ moltcare list              # 列出所有 packs
  $ moltcare list --category foundation  # 按类别过滤
  $ moltcare list --json       # JSON 格式输出
  $ moltcare list --installed  # 仅显示已安装
`)
  .action(async (options) => {
    try {
      await listCommand(options);
    } catch (error) {
      console.error(chalk.red(`✗ 列出失败: ${error}`));
      process.exit(1);
    }
  });

// 📦 应用 pack
program
  .command('apply <pack>')
  .description('Apply an intelligence pack')
  .option('-f, --force', 'Force reapply (overwrite existing files)')
  .option('-d, --dry-run', 'Preview changes without applying')
  .option('-y, --yes', 'Skip confirmation')
  .addHelpText('after', `
Examples:
  $ moltcare apply foundation       # 应用基础包
  $ moltcare apply foundation --dry-run  # 预览更改
  $ moltcare apply foundation --force    # 强制重新应用
  $ moltcare apply my-pack --yes    # 跳过确认
`)
  .action(async (pack, options) => {
    try {
      await applyCommand(pack, options);
    } catch (error) {
      console.error(chalk.red(`✗ 应用失败: ${error}`));
      process.exit(1);
    }
  });

// 🔍 代码评审命令
program
  .command('review [path]')
  .description('Code review for agent files')
  .option('--format <type>', 'Output format: text|json', 'text')
  .addHelpText('after', `
Examples:
  $ moltcare review            # 评审当前目录
  $ moltcare review ./src      # 评审指定目录
  $ moltcare review --format json  # JSON 输出
`)
  .action(async (filePath, options) => {
    try {
      const reviewer = new CodeReviewer();
      const target = filePath || './src';
      
      console.log(chalk.cyan('🔍 Reviewing code...'));
      
      const reviews = await reviewer.reviewDirectory(target);
      
      if (options.format === 'json') {
        console.log(JSON.stringify(reviews, null, 2));
      } else {
        const report = reviewer.generateReport(reviews);
        console.log(report);
      }
    } catch (error) {
      console.error(chalk.red(`✗ 评审失败: ${error}`));
      process.exit(1);
    }
  });

// 🧪 测试命令
program
  .command('test [pattern]')
  .description('Run tests')
  .option('-w, --watch', 'Watch mode')
  .addHelpText('after', `
Examples:
  $ moltcare test              # 运行所有测试
  $ moltcare test cli          # 运行匹配 cli 的测试
  $ moltcare test --watch      # 监视模式
`)
  .action(async (pattern, options) => {
    try {
      console.log(chalk.cyan('🧪 Running tests...'));
      if (pattern) {
        console.log(chalk.gray(`  Pattern: ${pattern}`));
      }
      if (options.watch) {
        console.log(chalk.gray('  Watch mode enabled'));
      }
      
      // 实际运行测试
      const { execSync } = await import('child_process');
      const cmd = options.watch ? 'npm run test -- --watch' : 'npm test';
      execSync(cmd, { stdio: 'inherit', cwd: process.cwd() });
    } catch (error) {
      // 测试失败，退出码非0
      process.exit(1);
    }
  });

// 🔄 同步命令
program
  .command('sync')
  .description('Show collaboration status')
  .action(() => {
    console.log(chalk.cyan('🔄 MoltCare Collaboration Status:'));
    console.log('');
    console.log(chalk.white('  KimiSensen (Phase 1):'));
    console.log(chalk.green('    ✅ CLI framework'));
    console.log(chalk.green('    ✅ Multi-expert system'));
    console.log(chalk.green('    ✅ Type definitions'));
    console.log(chalk.green('    ✅ Pack manager'));
    console.log('');
    console.log(chalk.white('  OracleSensen (Phase 2):'));
    console.log(chalk.green('    ✅ Test framework (Vitest)'));
    console.log(chalk.green('    ✅ Code review system'));
    console.log(chalk.green('    ✅ Documentation framework'));
    console.log('');
    console.log(chalk.white('  Bridge:'));
    console.log(chalk.gray('    https://github.com/useens/moltcare-bridge'));
  });

// 📊 状态命令
program
  .command('status')
  .description('Show MoltCare status')
  .addHelpText('after', `
Examples:
  $ moltcare status            # 查看状态
`)
  .action(async () => {
    try {
      const { ConfigManager } = await import('../config.js');
      const { PackManager } = await import('../pack_manager.js');
      
      const config = new ConfigManager();
      const packsDir = config.get('packsDir');
      const packManager = new PackManager(packsDir);
      
      console.log(chalk.cyan('🦞 MoltCare Status'));
      console.log('');
      console.log(chalk.white(`Version: ${config.get('version')}`));
      console.log(chalk.white(`Status:  ${config.isInitialized() ? chalk.green('✅ 已初始化') : chalk.yellow('⏸️ 未初始化')}`));
      console.log('');
      
      if (config.isInitialized()) {
        console.log(chalk.white('Configuration:'));
        console.log(chalk.gray(`  Config file: ${config.getConfigPath()}`));
        console.log(chalk.gray(`  Language: ${config.get('language')}`));
        console.log(chalk.gray(`  Workspace: ${config.get('workspacePath')}`));
        console.log(chalk.gray(`  Packs dir: ${config.get('packsDir')}`));
        console.log('');
        
        const packs = packManager.scanPacks();
        const installed = packs.filter(p => p.installed).length;
        console.log(chalk.white('Packs:'));
        console.log(chalk.gray(`  Available: ${packs.length}`));
        console.log(chalk.gray(`  Installed: ${installed}`));
      }
      
      console.log('');
      console.log(chalk.white('Available commands:'));
      console.log(chalk.gray('  init, list, apply, review, test, sync, status'));
    } catch (error) {
      console.error(chalk.red(`✗ 获取状态失败: ${error}`));
      process.exit(1);
    }
  });

// 全局错误处理
program.exitOverride();

try {
  program.parse();
} catch (error: any) {
  if (error.code === 'commander.help') {
    process.exit(0);
  }
  if (error.code === 'commander.version') {
    process.exit(0);
  }
  if (error.code === 'commander.unknownOption') {
    console.error(chalk.red(`✗ 未知选项: ${error.message}`));
    process.exit(1);
  }
  if (error.code === 'commander.missingArgument') {
    console.error(chalk.red(`✗ 缺少参数: ${error.message}`));
    process.exit(1);
  }
  console.error(chalk.red(`✗ 错误: ${error.message}`));
  process.exit(1);
}
