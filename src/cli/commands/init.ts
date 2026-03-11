import { promises as fs } from 'fs';
import path from 'path';
import chalk from 'chalk';
import inquirer from 'inquirer';
import yaml from 'js-yaml';

interface InitOptions {
  force?: boolean;
  yes?: boolean;
  workspace?: string;
}

interface MoltCareConfig {
  version: string;
  workspace: string;
  language: string;
  autoUpdate: boolean;
  packs: string[];
}

export async function initCommand(options: InitOptions): Promise<void> {
  console.log(chalk.cyan('🦞 MoltCare 初始化\n'));

  const configDir = path.join(process.env.HOME || '~', '.moltcare');
  const configPath = path.join(configDir, 'config.yaml');

  // 检查是否已存在配置
  try {
    await fs.access(configPath);
    if (!options.force) {
      console.log(chalk.yellow('⚠️  MoltCare 已初始化'));
      console.log(chalk.gray(`   配置文件: ${configPath}`));
      console.log(chalk.gray('   使用 --force 重新初始化'));
      return;
    }
  } catch {
    // 文件不存在，继续初始化
  }

  // 使用默认值或交互式询问
  let config: MoltCareConfig;

  if (options.yes) {
    config = {
      version: '1.0.0',
      workspace: options.workspace || path.join(process.env.HOME || '~', 'moltcare-workspace'),
      language: 'zh',
      autoUpdate: true,
      packs: []
    };
  } else {
    const answers = await inquirer.prompt([
      {
        type: 'input',
        name: 'workspace',
        message: '工作区路径:',
        default: options.workspace || path.join(process.env.HOME || '~', 'moltcare-workspace')
      },
      {
        type: 'list',
        name: 'language',
        message: '首选语言:',
        choices: [
          { name: '中文', value: 'zh' },
          { name: 'English', value: 'en' },
          { name: '日本語', value: 'ja' }
        ],
        default: 'zh'
      },
      {
        type: 'confirm',
        name: 'autoUpdate',
        message: '是否自动检查更新?',
        default: true
      }
    ]);

    config = {
      version: '1.0.0',
      workspace: answers.workspace,
      language: answers.language,
      autoUpdate: answers.autoUpdate,
      packs: []
    };
  }

  // 创建配置目录
  await fs.mkdir(configDir, { recursive: true });

  // 写入配置文件
  const configYaml = yaml.dump(config);
  await fs.writeFile(configPath, configYaml, 'utf-8');

  // 创建工作区目录
  await fs.mkdir(config.workspace, { recursive: true });

  console.log(chalk.green('✓ 初始化完成!'));
  console.log(chalk.gray(`  配置文件: ${configPath}`));
  console.log(chalk.gray(`  工作区: ${config.workspace}`));
  console.log(chalk.cyan('\n下一步:'));
  console.log('  $ moltcare list       # 查看可用智能包');
  console.log('  $ moltcare apply foundation  # 应用基础包');
}
