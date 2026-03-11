#!/usr/bin/env node

import { Command } from 'commander';
import chalk from 'chalk';
import { initCommand } from './commands/init.js';

const program = new Command();

// 程序元数据
program
  .name('moltcare')
  .description('🚀 Moltcare - 一键智能提升你的 Agent 核心文件')
  .version('0.1.0', '-v, --version', '显示版本号')
  .usage('<command> [options]')
  .helpOption('-h, --help', '显示帮助信息')
  .configureOutput({
    outputError: (str, write) => write(chalk.red(str))
  });

// 全局选项
program.option('-d, --debug', '启用调试模式', false);

// 子命令注册
program.addCommand(initCommand);

// 默认行为：如果没有提供命令，显示帮助
program.action(() => {
  program.help();
});

// 错误处理
program.exitOverride();

// 解析命令行参数
try {
  program.parse(process.argv);
} catch (error: unknown) {
  if (error instanceof Error) {
    if (error.message === 'commander.help') {
      process.exit(0);
    }
    if (error.message === 'commander.version') {
      process.exit(0);
    }
    console.error(chalk.red(`❌ 错误: ${error.message}`));
    process.exit(1);
  }
  console.error(chalk.red('❌ 发生未知错误'));
  process.exit(1);
}

// 处理未捕获的异常
process.on('uncaughtException', (error: Error) => {
  console.error(chalk.red(`❌ 未捕获的异常: ${error.message}`));
  if (program.opts().debug) {
    console.error(error.stack);
  }
  process.exit(1);
});

process.on('unhandledRejection', (reason: unknown) => {
  console.error(chalk.red(`❌ 未处理的 Promise 拒绝: ${reason}`));
  process.exit(1);
});
