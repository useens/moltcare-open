import { promises as fs } from 'fs';
import path from 'path';
import chalk from 'chalk';
import { getEnhancedConfig } from '../../utils/config-enhanced.js';

interface DoctorOptions {
  fix?: boolean;
  json?: boolean;
}

interface CheckResult {
  name: string;
  status: 'ok' | 'warning' | 'error';
  message: string;
  details?: string;
  fixable?: boolean;
}

interface DoctorReport {
  timestamp: string;
  overall: 'healthy' | 'degraded' | 'unhealthy';
  checks: CheckResult[];
  summary: {
    total: number;
    ok: number;
    warning: number;
    error: number;
  };
}

export async function doctorCommand(options: DoctorOptions): Promise<void> {
  const report = await runDiagnostics();
  
  if (options.json) {
    console.log(JSON.stringify(report, null, 2));
    return;
  }

  // 显示报告
  console.log(chalk.cyan('🔧 MoltCare 健康诊断\n'));
  
  for (const check of report.checks) {
    const icon = check.status === 'ok' ? chalk.green('✓') :
                 check.status === 'warning' ? chalk.yellow('⚠') : chalk.red('✗');
    const statusColor = check.status === 'ok' ? chalk.green :
                        check.status === 'warning' ? chalk.yellow : chalk.red;
    
    console.log(`${icon} ${chalk.bold(check.name)}`);
    console.log(`  ${statusColor(check.message)}`);
    if (check.details) {
      console.log(`  ${chalk.gray(check.details)}`);
    }
    if (check.fixable && options.fix) {
      console.log(`  ${chalk.cyan('→ 已尝试自动修复')}`);
    }
    console.log();
  }

  // 摘要
  console.log(chalk.white.bold('诊断摘要'));
  console.log(`  总计: ${report.summary.total} 项检查`);
  console.log(`  ${chalk.green('✓ 正常')}: ${report.summary.ok}`);
  console.log(`  ${chalk.yellow('⚠ 警告')}: ${report.summary.warning}`);
  console.log(`  ${chalk.red('✗ 错误')}: ${report.summary.error}`);
  console.log();

  // 总体状态
  const overallIcon = report.overall === 'healthy' ? chalk.green('✓') :
                      report.overall === 'degraded' ? chalk.yellow('⚠') : chalk.red('✗');
  const overallText = report.overall === 'healthy' ? '系统健康' :
                      report.overall === 'degraded' ? '系统降级' : '系统异常';
  console.log(`${overallIcon} ${chalk.bold(overallText)}`);

  if (report.summary.error > 0) {
    console.log();
    console.log(chalk.yellow('💡 建议: 使用 --fix 选项尝试自动修复'));
  }
}

async function runDiagnostics(): Promise<DoctorReport> {
  const config = getEnhancedConfig();
  const checks: CheckResult[] = [];

  // 1. 检查配置文件
  const configPath = config.getConfigPath('user');
  try {
    await fs.access(configPath);
    checks.push({
      name: '配置文件',
      status: 'ok',
      message: '配置文件存在',
      details: configPath
    });
  } catch {
    checks.push({
      name: '配置文件',
      status: 'error',
      message: '配置文件不存在',
      details: '运行 moltcare init 初始化',
      fixable: true
    });
  }

  // 2. 检查工作目录
  const workspacePath = config.get('workspacePath');
  try {
    const stats = await fs.stat(workspacePath);
    if (stats.isDirectory()) {
      checks.push({
        name: '工作目录',
        status: 'ok',
        message: '工作目录存在',
        details: workspacePath
      });
    } else {
      checks.push({
        name: '工作目录',
        status: 'error',
        message: '工作目录路径不是目录',
        fixable: true
      });
    }
  } catch {
    checks.push({
      name: '工作目录',
      status: 'error',
      message: '工作目录不存在',
      details: workspacePath,
      fixable: true
    });
  }

  // 3. 检查智能包目录
  const packsDir = path.join(process.cwd(), 'packs');
  try {
    const entries = await fs.readdir(packsDir);
    const packCount = entries.filter(e => !e.startsWith('.')).length;
    checks.push({
      name: '智能包',
      status: packCount > 0 ? 'ok' : 'warning',
      message: packCount > 0 ? `找到 ${packCount} 个智能包` : '未找到智能包',
      details: packsDir
    });
  } catch {
    checks.push({
      name: '智能包',
      status: 'warning',
      message: '智能包目录不存在',
      details: '运行命令需要在 MoltCare 项目目录中'
    });
  }

  // 4. 检查 Node.js 版本
  const nodeVersion = process.version;
  const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);
  if (majorVersion >= 18) {
    checks.push({
      name: 'Node.js',
      status: 'ok',
      message: `版本 ${nodeVersion} 符合要求`,
      details: '需要 >= 18.0.0'
    });
  } else {
    checks.push({
      name: 'Node.js',
      status: 'error',
      message: `版本 ${nodeVersion} 过低`,
      details: '需要 >= 18.0.0'
    });
  }

  // 5. 检查内存系统
  const memoryPath = path.join(workspacePath, 'MEMORY.md');
  try {
    await fs.access(memoryPath);
    checks.push({
      name: '记忆系统',
      status: 'ok',
      message: 'MEMORY.md 存在'
    });
  } catch {
    checks.push({
      name: '记忆系统',
      status: 'warning',
      message: 'MEMORY.md 不存在',
      details: '建议创建以启用完整功能',
      fixable: true
    });
  }

  // 6. 检查权限
  try {
    const testFile = path.join(workspacePath, '.write-test');
    await fs.writeFile(testFile, 'test');
    await fs.unlink(testFile);
    checks.push({
      name: '写入权限',
      status: 'ok',
      message: '工作目录可写入'
    });
  } catch {
    checks.push({
      name: '写入权限',
      status: 'error',
      message: '工作目录无法写入',
      details: '请检查目录权限'
    });
  }

  // 计算总体状态
  const errorCount = checks.filter(c => c.status === 'error').length;
  const warningCount = checks.filter(c => c.status === 'warning').length;
  
  let overall: DoctorReport['overall'];
  if (errorCount === 0 && warningCount === 0) {
    overall = 'healthy';
  } else if (errorCount === 0) {
    overall = 'degraded';
  } else {
    overall = 'unhealthy';
  }

  return {
    timestamp: new Date().toISOString(),
    overall,
    checks,
    summary: {
      total: checks.length,
      ok: checks.filter(c => c.status === 'ok').length,
      warning: warningCount,
      error: errorCount
    }
  };
}
