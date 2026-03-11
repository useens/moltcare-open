import { promises as fs } from 'fs';
import path from 'path';
import chalk from 'chalk';
import inquirer from 'inquirer';
import yaml from 'js-yaml';
import { ErrorHandler } from '../../utils/errors-enhanced.js';
import { getEnhancedConfig, EnhancedMoltCareConfig } from '../../utils/config-enhanced.js';

interface InitOptions {
  force?: boolean;
  yes?: boolean;
  workspace?: string;
  verbose?: boolean;
}

export async function initCommand(options: InitOptions): Promise<void> {
  const config = getEnhancedConfig();
  
  if (options.verbose) {
    console.log(chalk.gray('[debug] 开始初始化...'));
    console.log(chalk.gray(`[debug] 用户配置路径: ${config.getConfigPath('user')}`));
  }

  console.log(chalk.cyan('🦞 MoltCare 初始化\n'));

  const configDir = path.dirname(config.getConfigPath('user'));
  const configPath = config.getConfigPath('user');

  // 检查是否已存在配置
  try {
    await fs.access(configPath);
    if (!options.force) {
      console.log(chalk.yellow('⚠️  MoltCare 已初始化'));
      console.log(chalk.gray(`   配置文件: ${configPath}`));
      console.log(chalk.gray('   使用 --force 重新初始化'));
      
      // 显示当前配置概览
      console.log('');
      console.log(chalk.white('当前配置:'));
      console.log(chalk.gray(`  语言: ${config.get('language')}`));
      console.log(chalk.gray(`  工作区: ${config.get('workspacePath')}`));
      console.log(chalk.gray(`  日志级别: ${config.get('logLevel')}`));
      return;
    }
    
    console.log(chalk.yellow('⚠️  强制重新初始化将覆盖现有配置'));
    console.log('');
  } catch {
    // 文件不存在，继续初始化
    if (options.verbose) {
      console.log(chalk.gray('[debug] 配置文件不存在，创建新配置'));
    }
  }

  // 使用默认值或交互式询问
  let newConfig: Partial<EnhancedMoltCareConfig>;

  if (options.yes) {
    // 使用默认配置
    newConfig = {
      version: '1.0.0',
      workspacePath: options.workspace || path.join(process.env.HOME || '~', '.moltcare', 'workspace'),
      language: 'zh',
      autoUpdate: true,
      logLevel: 'info',
      theme: 'default',
      git: {
        enabled: true,
        autoCommit: false,
        commitMessage: 'chore: update moltcare configuration',
      },
    };
    console.log(chalk.gray('使用默认配置...'));
  } else {
    // 交互式配置
    console.log(chalk.white('请回答以下问题来配置 MoltCare:\n'));
    
    const answers = await inquirer.prompt([
      {
        type: 'input',
        name: 'workspacePath',
        message: '工作区路径:',
        default: options.workspace || config.get('workspacePath'),
      },
      {
        type: 'list',
        name: 'language',
        message: '首选语言:',
        choices: [
          { name: '中文 (zh)', value: 'zh' },
          { name: 'English (en)', value: 'en' },
          { name: '日本語 (ja)', value: 'ja' },
          { name: '한국어 (ko)', value: 'ko' },
        ],
        default: config.get('language'),
      },
      {
        type: 'list',
        name: 'logLevel',
        message: '日志级别:',
        choices: [
          { name: 'debug - 调试信息', value: 'debug' },
          { name: 'info - 一般信息', value: 'info' },
          { name: 'warn - 仅警告', value: 'warn' },
          { name: 'error - 仅错误', value: 'error' },
        ],
        default: config.get('logLevel'),
      },
      {
        type: 'list',
        name: 'theme',
        message: '界面主题:',
        choices: [
          { name: '默认', value: 'default' },
          { name: '暗色', value: 'dark' },
          { name: '亮色', value: 'light' },
        ],
        default: config.get('theme'),
      },
      {
        type: 'confirm',
        name: 'autoUpdate',
        message: '是否自动检查更新?',
        default: config.get('autoUpdate'),
      },
      {
        type: 'confirm',
        name: 'gitEnabled',
        message: '启用 Git 集成?',
        default: true,
      },
    ]);

    newConfig = {
      version: '1.0.0',
      workspacePath: answers.workspacePath,
      language: answers.language,
      logLevel: answers.logLevel,
      theme: answers.theme,
      autoUpdate: answers.autoUpdate,
      initialized: true,
      git: {
        enabled: answers.gitEnabled,
        autoCommit: false,
        commitMessage: 'chore: update moltcare configuration',
      },
    };
  }

  // 创建配置目录
  try {
    await fs.mkdir(configDir, { recursive: true });
    if (options.verbose) {
      console.log(chalk.gray(`[debug] 创建配置目录: ${configDir}`));
    }
  } catch (error) {
    throw new Error(`无法创建配置目录: ${error}`);
  }

  // 创建工作区目录
  try {
    await fs.mkdir(newConfig.workspacePath!, { recursive: true });
    if (options.verbose) {
      console.log(chalk.gray(`[debug] 创建工作区目录: ${newConfig.workspacePath}`));
    }
  } catch (error) {
    throw new Error(`无法创建工作区目录: ${error}`);
  }

  // 更新配置并保存
  config.update(newConfig);
  config.markInitialized();
  
  if (options.verbose) {
    console.log(chalk.gray('[debug] 配置已保存'));
  }

  // 创建项目配置文件模板
  const projectConfigPath = path.join(newConfig.workspacePath!, '.moltcare.yaml');
  try {
    await fs.access(projectConfigPath);
  } catch {
    // 项目配置文件不存在，创建一个模板
    const projectConfigTemplate = `# MoltCare 项目配置
# 此文件应该提交到版本控制

# 项目基本信息
project:
  name: my-project
  description: ''
  
# 智能包配置
packs:
  # 自动安装的包
  autoInstall: []
  
# 模板变量
template:
  variables:
    author: ''
    email: ''
    
# 忽略的文件（不应用模板）
ignore:
  - node_modules/
  - .git/
  - dist/
`;
    await fs.writeFile(projectConfigPath, projectConfigTemplate, 'utf-8');
    if (options.verbose) {
      console.log(chalk.gray(`[debug] 创建项目配置文件: ${projectConfigPath}`));
    }
  }

  // 显示成功信息
  console.log(chalk.green('✓ 初始化完成!'));
  console.log('');
  console.log(chalk.white('配置信息:'));
  console.log(chalk.gray(`  用户配置: ${configPath}`));
  console.log(chalk.gray(`  项目配置: ${projectConfigPath}`));
  console.log(chalk.gray(`  工作区: ${newConfig.workspacePath}`));
  console.log(chalk.gray(`  语言: ${newConfig.language}`));
  console.log('');
  
  // 显示后续步骤
  console.log(chalk.cyan('下一步:'));
  console.log('  $ moltcare list              # 查看可用智能包');
  console.log('  $ moltcare apply foundation  # 应用基础包');
  console.log('');
  console.log(chalk.gray('使用 "moltcare help" 查看所有命令'));
}
