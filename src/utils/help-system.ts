/**
 * Enhanced Help System - Phase 5 优化
 * 
 * 功能:
 * - 交互式帮助文档
 * - 命令补全建议
 * - 使用示例库
 * - 多语言帮助支持
 * - 上下文相关帮助
 */

import chalk from 'chalk';
import { Command } from 'commander';
import { getConfig } from '../config.js';

// 命令定义
export interface CommandDefinition {
  name: string;
  aliases?: string[];
  description: string;
  usage: string;
  examples: CommandExample[];
  options: CommandOption[];
  arguments?: CommandArgument[];
  subcommands?: CommandDefinition[];
  category: CommandCategory;
  related?: string[];
  seeAlso?: string[];
}

// 命令示例
export interface CommandExample {
  description: string;
  command: string;
  output?: string;
}

// 命令选项
export interface CommandOption {
  flags: string;
  description: string;
  defaultValue?: string | boolean;
  required?: boolean;
}

// 命令参数
export interface CommandArgument {
  name: string;
  description: string;
  required?: boolean;
  variadic?: boolean;
}

// 命令分类
export enum CommandCategory {
  CORE = '核心命令',
  PACK = '智能包管理',
  DEVELOPMENT = '开发工具',
  CONFIG = '配置管理',
  UTILITY = '实用工具',
}

// 命令库
export const COMMAND_LIBRARY: CommandDefinition[] = [
  {
    name: 'init',
    aliases: ['initialize', 'setup'],
    description: '初始化 MoltCare 配置',
    usage: 'moltcare init [options]',
    category: CommandCategory.CORE,
    arguments: [],
    options: [
      { flags: '-f, --force', description: '强制重新初始化，覆盖现有配置', defaultValue: false },
      { flags: '-y, --yes', description: '使用默认配置，不提示交互', defaultValue: false },
      { flags: '-w, --workspace <path>', description: '指定工作区路径' },
    ],
    examples: [
      { description: '交互式初始化', command: 'moltcare init' },
      { description: '使用默认配置快速初始化', command: 'moltcare init --yes' },
      { description: '强制重新初始化', command: 'moltcare init --force' },
      { description: '指定工作区路径', command: 'moltcare init --workspace /custom/path' },
    ],
    related: ['config', 'status'],
  },
  {
    name: 'list',
    aliases: ['ls', 'packages'],
    description: '列出所有可用的智能包',
    usage: 'moltcare list [options]',
    category: CommandCategory.PACK,
    options: [
      { flags: '-c, --category <category>', description: '按类别过滤' },
      { flags: '-i, --installed', description: '仅显示已安装的智能包', defaultValue: false },
      { flags: '--json', description: '以 JSON 格式输出', defaultValue: false },
    ],
    examples: [
      { description: '列出所有智能包', command: 'moltcare list' },
      { description: '仅显示已安装的智能包', command: 'moltcare list --installed' },
      { description: '按类别过滤', command: 'moltcare list --category foundation' },
      { description: 'JSON 格式输出', command: 'moltcare list --json' },
    ],
    related: ['apply', 'info'],
  },
  {
    name: 'apply',
    aliases: ['install', 'use'],
    description: '应用指定的智能包',
    usage: 'moltcare apply <pack> [options]',
    category: CommandCategory.PACK,
    arguments: [
      { name: 'pack', description: '智能包名称', required: true },
    ],
    options: [
      { flags: '-f, --force', description: '强制重新应用，覆盖现有文件', defaultValue: false },
      { flags: '-d, --dry-run', description: '预览更改，不实际应用', defaultValue: false },
      { flags: '-y, --yes', description: '跳过确认提示', defaultValue: false },
    ],
    examples: [
      { description: '应用基础智能包', command: 'moltcare apply foundation' },
      { description: '预览更改', command: 'moltcare apply foundation --dry-run' },
      { description: '强制重新应用', command: 'moltcare apply foundation --force' },
      { description: '跳过确认', command: 'moltcare apply foundation --yes' },
    ],
    related: ['list', 'remove'],
  },
  {
    name: 'review',
    aliases: ['check', 'audit'],
    description: '对代码进行审查',
    usage: 'moltcare review [path] [options]',
    category: CommandCategory.DEVELOPMENT,
    arguments: [
      { name: 'path', description: '要审查的路径', required: false },
    ],
    options: [
      { flags: '--format <type>', description: '输出格式: text|json', defaultValue: 'text' },
      { flags: '-s, --strict', description: '严格模式', defaultValue: false },
    ],
    examples: [
      { description: '审查当前目录', command: 'moltcare review' },
      { description: '审查指定目录', command: 'moltcare review ./src' },
      { description: 'JSON 格式输出', command: 'moltcare review --format json' },
    ],
    related: ['test'],
  },
  {
    name: 'test',
    description: '运行测试',
    usage: 'moltcare test [pattern] [options]',
    category: CommandCategory.DEVELOPMENT,
    arguments: [
      { name: 'pattern', description: '测试匹配模式', required: false },
    ],
    options: [
      { flags: '-w, --watch', description: '监视模式', defaultValue: false },
      { flags: '-c, --coverage', description: '生成覆盖率报告', defaultValue: false },
    ],
    examples: [
      { description: '运行所有测试', command: 'moltcare test' },
      { description: '运行匹配模式的测试', command: 'moltcare test cli' },
      { description: '监视模式', command: 'moltcare test --watch' },
      { description: '生成覆盖率报告', command: 'moltcare test --coverage' },
    ],
    related: ['review'],
  },
  {
    name: 'status',
    aliases: ['info'],
    description: '显示 MoltCare 状态信息',
    usage: 'moltcare status [options]',
    category: CommandCategory.UTILITY,
    options: [
      { flags: '--json', description: '以 JSON 格式输出', defaultValue: false },
    ],
    examples: [
      { description: '查看状态', command: 'moltcare status' },
      { description: 'JSON 格式输出', command: 'moltcare status --json' },
    ],
    related: ['init', 'config'],
  },
  {
    name: 'sync',
    description: '显示协作状态',
    usage: 'moltcare sync',
    category: CommandCategory.UTILITY,
    options: [],
    examples: [
      { description: '查看协作状态', command: 'moltcare sync' },
    ],
  },
  {
    name: 'config',
    aliases: ['cfg', 'settings'],
    description: '管理 MoltCare 配置',
    usage: 'moltcare config <command> [options]',
    category: CommandCategory.CONFIG,
    options: [],
    subcommands: [
      {
        name: 'get',
        description: '获取配置项',
        usage: 'moltcare config get <key>',
        category: CommandCategory.CONFIG,
        options: [],
        arguments: [{ name: 'key', description: '配置项键名', required: true }],
        examples: [{ description: '获取语言配置', command: 'moltcare config get language' }],
      },
      {
        name: 'set',
        description: '设置配置项',
        usage: 'moltcare config set <key> <value>',
        category: CommandCategory.CONFIG,
        options: [],
        arguments: [
          { name: 'key', description: '配置项键名', required: true },
          { name: 'value', description: '配置项值', required: true },
        ],
        examples: [{ description: '设置语言为英文', command: 'moltcare config set language en' }],
      },
      {
        name: 'list',
        description: '列出所有配置',
        usage: 'moltcare config list [options]',
        category: CommandCategory.CONFIG,
        options: [{ flags: '--json', description: 'JSON 格式输出', defaultValue: false }],
        examples: [{ description: '列出所有配置', command: 'moltcare config list' }],
      },
    ],
    examples: [
      { description: '获取配置', command: 'moltcare config get language' },
      { description: '设置配置', command: 'moltcare config set language en' },
      { description: '列出配置', command: 'moltcare config list' },
    ],
    related: ['init', 'status'],
  },
  {
    name: 'help',
    description: '显示帮助信息',
    usage: 'moltcare help [command]',
    category: CommandCategory.UTILITY,
    options: [],
    arguments: [{ name: 'command', description: '要查看帮助的命令', required: false }],
    examples: [
      { description: '显示全局帮助', command: 'moltcare help' },
      { description: '显示命令帮助', command: 'moltcare help apply' },
    ],
  },
];

export class HelpSystem {
  /**
   * 显示全局帮助
   */
  static showGlobalHelp(program: Command): void {
    console.log('');
    console.log(chalk.cyan.bold('🦞 MoltCare - 让每一只刚安装的 OpenClaw Agent 都能一键获得专业级智能'));
    console.log('');
    console.log(chalk.gray('版本: 1.0.0 | https://moltcare.dev'));
    console.log('');

    // 显示命令分类
    const categories = Object.values(CommandCategory);
    for (const category of categories) {
      const commands = COMMAND_LIBRARY.filter(cmd => cmd.category === category);
      if (commands.length === 0) continue;

      console.log(chalk.white.bold(category));
      console.log('');

      for (const cmd of commands) {
        const aliases = cmd.aliases ? chalk.gray(`(${cmd.aliases.join(', ')})`) : '';
        console.log(`  ${chalk.green(cmd.name.padEnd(12))} ${cmd.description} ${aliases}`);
      }
      console.log('');
    }

    // 显示快捷提示
    console.log(chalk.white.bold('快速开始:'));
    console.log(chalk.gray('  moltcare init           初始化 MoltCare'));
    console.log(chalk.gray('  moltcare list           查看可用智能包'));
    console.log(chalk.gray('  moltcare apply <pack>   应用智能包'));
    console.log('');

    // 显示帮助提示
    console.log(chalk.gray('使用 "moltcare help <command>" 查看具体命令的帮助'));
    console.log('');
  }

  /**
   * 显示命令帮助
   */
  static showCommandHelp(commandName: string): void {
    const cmd = this.findCommand(commandName);
    
    if (!cmd) {
      console.log(chalk.red(`未知命令: ${commandName}`));
      console.log(chalk.gray('使用 "moltcare --help" 查看所有命令'));
      return;
    }

    console.log('');
    console.log(chalk.cyan.bold(`📖 ${cmd.name}`));
    console.log('');
    console.log(chalk.white(cmd.description));
    console.log('');

    // 用法
    console.log(chalk.white.bold('用法:'));
    console.log(`  ${chalk.gray(cmd.usage)}`);
    console.log('');

    // 别名
    if (cmd.aliases && cmd.aliases.length > 0) {
      console.log(chalk.white.bold('别名:'));
      console.log(`  ${cmd.aliases.join(', ')}`);
      console.log('');
    }

    // 参数
    if (cmd.arguments && cmd.arguments.length > 0) {
      console.log(chalk.white.bold('参数:'));
      for (const arg of cmd.arguments) {
        const required = arg.required ? chalk.red('*') : chalk.gray('?');
        console.log(`  ${required} ${chalk.green(arg.name.padEnd(12))} ${arg.description}`);
      }
      console.log('');
    }

    // 选项
    if (cmd.options && cmd.options.length > 0) {
      console.log(chalk.white.bold('选项:'));
      for (const opt of cmd.options) {
        const defaultVal = opt.defaultValue !== undefined 
          ? chalk.gray(`(默认: ${opt.defaultValue})`) 
          : '';
        console.log(`  ${chalk.green(opt.flags.padEnd(20))} ${opt.description} ${defaultVal}`);
      }
      console.log('');
    }

    // 子命令
    if (cmd.subcommands && cmd.subcommands.length > 0) {
      console.log(chalk.white.bold('子命令:'));
      for (const sub of cmd.subcommands) {
        console.log(`  ${chalk.green(sub.name.padEnd(12))} ${sub.description}`);
      }
      console.log('');
    }

    // 示例
    if (cmd.examples && cmd.examples.length > 0) {
      console.log(chalk.white.bold('示例:'));
      for (const example of cmd.examples) {
        console.log(`  ${chalk.gray('# ' + example.description)}`);
        console.log(`  ${chalk.cyan(example.command)}`);
        if (example.output) {
          console.log(chalk.gray(example.output.split('\n').map(l => '  ' + l).join('\n')));
        }
        console.log('');
      }
    }

    // 相关命令
    if (cmd.related && cmd.related.length > 0) {
      console.log(chalk.white.bold('相关命令:'));
      console.log(`  ${cmd.related.map(r => chalk.cyan(r)).join(', ')}`);
      console.log('');
    }
  }

  /**
   * 查找命令
   */
  static findCommand(name: string): CommandDefinition | undefined {
    return COMMAND_LIBRARY.find(
      cmd => cmd.name === name || (cmd.aliases?.includes(name) ?? false)
    );
  }

  /**
   * 获取所有命令名称
   */
  static getAllCommandNames(): string[] {
    const names: string[] = [];
    for (const cmd of COMMAND_LIBRARY) {
      names.push(cmd.name);
      if (cmd.aliases) {
        names.push(...cmd.aliases);
      }
    }
    return names;
  }

  /**
   * 显示快速提示
   */
  static showQuickTips(): void {
    console.log('');
    console.log(chalk.cyan('💡 提示:'));
    const tips = [
      '使用 Tab 键自动补全命令',
      '使用 --help 查看命令详细用法',
      '使用 --dry-run 预览更改而不实际应用',
      '使用 --yes 跳过确认提示',
    ];
    tips.forEach(tip => console.log(`  ${chalk.gray('•')} ${tip}`));
    console.log('');
  }

  /**
   * 显示命令建议（模糊匹配）
   */
  static showCommandSuggestions(input: string): void {
    const { findSimilar } = require('./errors-enhanced.js');
    const allCommands = this.getAllCommandNames();
    const suggestions = findSimilar(input, allCommands, 3);

    if (suggestions.length > 0) {
      console.log(chalk.yellow(`\n您是否想输入:`));
      suggestions.forEach((cmd: string) => {
        const def = this.findCommand(cmd);
        console.log(`  ${chalk.cyan(cmd.padEnd(12))} ${chalk.gray(def?.description || '')}`);
      });
    }
  }

  /**
   * 生成 Markdown 文档
   */
  static generateMarkdownDocs(): string {
    const lines: string[] = [];
    lines.push('# MoltCare CLI 文档');
    lines.push('');
    lines.push('> 自动生成于 ' + new Date().toLocaleString());
    lines.push('');
    lines.push('## 命令列表');
    lines.push('');

    const categories = Object.values(CommandCategory);
    for (const category of categories) {
      const commands = COMMAND_LIBRARY.filter(cmd => cmd.category === category);
      if (commands.length === 0) continue;

      lines.push(`### ${category}`);
      lines.push('');

      for (const cmd of commands) {
        lines.push(`#### ${cmd.name}`);
        lines.push('');
        lines.push(cmd.description);
        lines.push('');
        lines.push(`**用法**: \`\`\`${cmd.usage}\`\`\``);
        lines.push('');

        if (cmd.aliases?.length) {
          lines.push(`**别名**: ${cmd.aliases.join(', ')}`);
          lines.push('');
        }

        if (cmd.options?.length) {
          lines.push('**选项**:');
          lines.push('');
          lines.push('| 选项 | 描述 | 默认值 |');
          lines.push('|------|------|--------|');
          for (const opt of cmd.options) {
            const defaultVal = opt.defaultValue !== undefined ? String(opt.defaultValue) : '-';
            lines.push(`| ${opt.flags} | ${opt.description} | ${defaultVal} |`);
          }
          lines.push('');
        }

        if (cmd.examples?.length) {
          lines.push('**示例**:');
          lines.push('');
          for (const ex of cmd.examples) {
            lines.push(`- ${ex.description}`);
            lines.push(`  \`\`\`bash\n  ${ex.command}\n  \`\`\``);
            lines.push('');
          }
        }
      }
    }

    return lines.join('\n');
  }

  /**
   * 交互式帮助向导
   */
  static async interactiveHelp(): Promise<void> {
    const inquirer = await import('inquirer');

    const { action } = await inquirer.default.prompt([
      {
        type: 'list',
        name: 'action',
        message: '您需要什么帮助?',
        choices: [
          { name: '📚 查看命令帮助', value: 'command' },
          { name: '🚀 快速开始向导', value: 'quickstart' },
          { name: '💡 查看使用技巧', value: 'tips' },
          { name: '📖 生成完整文档', value: 'docs' },
          { name: '❌ 退出', value: 'exit' },
        ],
      },
    ]);

    switch (action) {
      case 'command':
        const { command } = await inquirer.default.prompt([
          {
            type: 'list',
            name: 'command',
            message: '选择要查看帮助的命令:',
            choices: COMMAND_LIBRARY.map(cmd => ({
              name: `${cmd.name} - ${cmd.description}`,
              value: cmd.name,
            })),
          },
        ]);
        this.showCommandHelp(command);
        break;

      case 'quickstart':
        this.showQuickstartGuide();
        break;

      case 'tips':
        this.showQuickTips();
        break;

      case 'docs':
        console.log(this.generateMarkdownDocs());
        break;
    }
  }

  /**
   * 显示快速开始向导
   */
  static showQuickstartGuide(): void {
    console.log('');
    console.log(chalk.cyan.bold('🚀 MoltCare 快速开始'));
    console.log('');
    console.log(chalk.white('第 1 步: 初始化'));
    console.log(chalk.gray('  $ moltcare init'));
    console.log('');
    console.log(chalk.white('第 2 步: 查看可用智能包'));
    console.log(chalk.gray('  $ moltcare list'));
    console.log('');
    console.log(chalk.white('第 3 步: 应用智能包'));
    console.log(chalk.gray('  $ moltcare apply foundation'));
    console.log('');
    console.log(chalk.white('第 4 步: 查看状态'));
    console.log(chalk.gray('  $ moltcare status'));
    console.log('');
    console.log(chalk.green('✨ 完成！您现在拥有了一个专业级的 AI Agent'));
    console.log('');
  }
}

export default HelpSystem;
