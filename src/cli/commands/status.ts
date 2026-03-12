import { promises as fs } from 'fs';
import path from 'path';
import chalk from 'chalk';
import yaml from 'js-yaml';
import { getEnhancedConfig } from '../../utils/config-enhanced.js';

interface StatusOptions {
  json?: boolean;
  verbose?: boolean;
}

interface SystemStatus {
  moltcare: {
    version: string;
    initialized: boolean;
    configPath: string;
    workspacePath: string;
  };
  environment: {
    nodeVersion: string;
    platform: string;
    cwd: string;
  };
  packs: {
    total: number;
    installed: number;
    available: number;
    list: string[];
  };
  config: {
    language: string;
    autoUpdate: boolean;
    logLevel: string;
    theme: string;
  };
}

export async function statusCommand(options: StatusOptions): Promise<void> {
  const config = getEnhancedConfig();
  const packageJsonPath = path.join(process.cwd(), 'package.json');
  
  // 收集状态信息
  const status: SystemStatus = {
    moltcare: {
      version: '1.1.0',
      initialized: false,
      configPath: '',
      workspacePath: '',
    },
    environment: {
      nodeVersion: process.version,
      platform: process.platform,
      cwd: process.cwd(),
    },
    packs: {
      total: 0,
      installed: 0,
      available: 0,
      list: [],
    },
    config: {
      language: config.get('language') || 'zh',
      autoUpdate: config.get('autoUpdate') ?? true,
      logLevel: config.get('logLevel') || 'info',
      theme: config.get('theme') || 'default',
    },
  };

  // 检查初始化状态
  try {
    const configPath = config.getConfigPath('user');
    status.moltcare.configPath = configPath;
    status.moltcare.workspacePath = config.get('workspacePath') || '';
    
    await fs.access(configPath);
    status.moltcare.initialized = true;
  } catch {
    status.moltcare.initialized = false;
  }

  // 扫描智能包
  const packsDir = path.join(process.cwd(), 'packs');
  try {
    const entries = await fs.readdir(packsDir, { withFileTypes: true });
    const packDirs = entries.filter(e => e.isDirectory() && !e.name.startsWith('.'));
    
    status.packs.total = packDirs.length;
    status.packs.list = packDirs.map(p => p.name);
    
    // 检查已安装（从索引）
    const indexPath = path.join(packsDir, '.index.json');
    try {
      const indexContent = await fs.readFile(indexPath, 'utf-8');
      const index = JSON.parse(indexContent);
      status.packs.installed = Object.keys(index.packs || {}).length;
    } catch {
      status.packs.installed = 0;
    }
    
    status.packs.available = status.packs.total;
  } catch {
    // packs 目录不存在
  }

  // 尝试读取 package.json 获取真实版本
  try {
    const content = await fs.readFile(packageJsonPath, 'utf-8');
    const pkg = JSON.parse(content);
    status.moltcare.version = pkg.version || status.moltcare.version;
  } catch {
    // 使用默认版本
  }

  // 输出格式
  if (options.json) {
    console.log(JSON.stringify(status, null, 2));
    return;
  }

  // 人类可读格式
  console.log(chalk.cyan('🦞 MoltCare 状态\n'));

  // MoltCare 信息
  console.log(chalk.white.bold('MoltCare'));
  console.log(`  版本:     ${chalk.green(status.moltcare.version)}`);
  console.log(`  初始化:   ${status.moltcare.initialized ? chalk.green('✓ 已完成') : chalk.yellow('✗ 未初始化')}`);
  if (status.moltcare.initialized) {
    console.log(`  配置文件: ${chalk.gray(status.moltcare.configPath)}`);
    console.log(`  工作区:   ${chalk.gray(status.moltcare.workspacePath)}`);
  }
  console.log();

  // 配置信息
  console.log(chalk.white.bold('配置'));
  console.log(`  语言:     ${status.config.language}`);
  console.log(`  主题:     ${status.config.theme}`);
  console.log(`  日志级别: ${status.config.logLevel}`);
  console.log(`  自动更新: ${status.config.autoUpdate ? '开启' : '关闭'}`);
  console.log();

  // 智能包信息
  console.log(chalk.white.bold('智能包'));
  console.log(`  总计:     ${status.packs.total}`);
  console.log(`  已安装:   ${chalk.green(status.packs.installed)}`);
  console.log(`  可用:     ${status.packs.available}`);
  if (options.verbose && status.packs.list.length > 0) {
    console.log(`  列表:`);
    status.packs.list.forEach(name => {
      const installed = status.packs.installed > 0 ? chalk.gray(' [待检查]') : '';
      console.log(`    • ${name}${installed}`);
    });
  }
  console.log();

  // 环境信息
  if (options.verbose) {
    console.log(chalk.white.bold('环境'));
    console.log(`  Node.js:  ${status.environment.nodeVersion}`);
    console.log(`  平台:     ${status.environment.platform}`);
    console.log(`  当前目录: ${status.environment.cwd}`);
    console.log();
  }

  // 下一步建议
  if (!status.moltcare.initialized) {
    console.log(chalk.yellow('💡 提示: 运行 "moltcare init" 进行初始化'));
  } else if (status.packs.installed === 0) {
    console.log(chalk.yellow('💡 提示: 运行 "moltcare apply foundation" 应用基础智能包'));
  }
}
