import { Command } from 'commander';
import chalk from 'chalk';
import inquirer from 'inquirer';
import { Analyzer } from '../../core/analyzer.js';
import { Writer, type ChangeReport } from '../../core/writer.js';
import * as fs from 'fs/promises';
import * as path from 'path';

interface InitAnswers {
  targetDir: string;
  templateType: 'minimal' | 'standard' | 'advanced';
  agentName: string;
  agentRole: string;
  enableMultiAgent: boolean;
  enableMemory: boolean;
}

// 模板类型定义 (用于未来扩展)
// const TEMPLATE_DESCRIPTIONS: Record<InitAnswers['templateType'], string> = {
//   minimal: '精简模板 - 仅包含最基础的 SOUL.md 和 AGENTS.md',
//   standard: '标准模板 - 完整的核心文件套装（推荐）',
//   advanced: '高级模板 - 包含多专家讨论和记忆系统配置'
// };

// init 命令
export const initCommand = new Command('init')
  .description('🎯 初始化或升级 Agent 核心文件')
  .argument('[directory]', '目标目录路径', '.')
  .option('-t, --template <type>', '模板类型 (minimal|standard|advanced)')
  .option('-y, --yes', '跳过交互，使用默认值', false)
  .option('--dry-run', '模拟运行，不实际写入文件', false)
  .action(async (directory: string, options) => {
    try {
      console.log(chalk.cyan.bold('\n🚀 Moltcare - 初始化 Agent 核心文件\n'));

      const targetDir = path.resolve(directory);
      
      // 验证目标目录
      await validateTargetDir(targetDir);

      // 检查现有文件
      const analyzer = new Analyzer(targetDir);
      const existingFiles = await analyzer.scanExistingFiles();

      if (existingFiles.length > 0) {
        console.log(chalk.yellow(`📁 发现 ${existingFiles.length} 个现有核心文件:`));
        existingFiles.forEach(f => console.log(chalk.gray(`   - ${f}`)));
        console.log();
      }

      let answers: InitAnswers;

      // 非交互模式
      if (options.yes) {
        answers = {
          targetDir,
          templateType: options.template || 'standard',
          agentName: 'MyAgent',
          agentRole: '智能助手',
          enableMultiAgent: true,
          enableMemory: true
        };
      } else {
        // 交互式询问
        answers = await inquirer.prompt<InitAnswers>([
          {
            type: 'list',
            name: 'templateType',
            message: '选择模板类型:',
            choices: [
              { name: `标准模板 ${chalk.gray('(推荐)')}`, value: 'standard' },
              { name: `精简模板 ${chalk.gray('(快速开始)')}`, value: 'minimal' },
              { name: `高级模板 ${chalk.gray('(完整功能)')}`, value: 'advanced' }
            ],
            when: !options.template
          },
          {
            type: 'input',
            name: 'agentName',
            message: 'Agent 名称:',
            default: path.basename(targetDir),
            validate: (input: string) => {
              if (!input.trim()) return '名称不能为空';
              if (input.length > 50) return '名称不能超过50个字符';
              return true;
            }
          },
          {
            type: 'input',
            name: 'agentRole',
            message: 'Agent 角色描述:',
            default: '智能助手',
            validate: (input: string) => {
              if (!input.trim()) return '角色描述不能为空';
              return true;
            }
          },
          {
            type: 'confirm',
            name: 'enableMultiAgent',
            message: '启用多专家讨论模式?',
            default: true
          },
          {
            type: 'confirm',
            name: 'enableMemory',
            message: '启用记忆系统?',
            default: true
          }
        ]);

        // 如果命令行指定了模板，使用命令行的值
        if (options.template) {
          answers.templateType = options.template as InitAnswers['templateType'];
        }
        answers.targetDir = targetDir;
      }

      console.log(chalk.cyan('\n📋 配置摘要:'));
      console.log(chalk.gray(`   目标目录: ${answers.targetDir}`));
      console.log(chalk.gray(`   模板类型: ${answers.templateType}`));
      console.log(chalk.gray(`   Agent名称: ${answers.agentName}`));
      console.log(chalk.gray(`   Agent角色: ${answers.agentRole}`));
      console.log(chalk.gray(`   多专家模式: ${answers.enableMultiAgent ? '✅' : '❌'}`));
      console.log(chalk.gray(`   记忆系统: ${answers.enableMemory ? '✅' : '❌'}`));
      console.log();

      // 执行写入
      if (options.dryRun) {
        console.log(chalk.yellow('🏃 模拟运行模式，不会实际写入文件\n'));
        await simulateGeneration(answers);
      } else {
        await generateFiles(answers);
      }

      console.log(chalk.green.bold('\n✨ 完成! 你的 Agent 已获得智能提升\n'));

    } catch (error: unknown) {
      if (error instanceof Error) {
        console.error(chalk.red(`\n❌ 错误: ${error.message}\n`));
      } else {
        console.error(chalk.red('\n❌ 发生未知错误\n'));
      }
      process.exit(1);
    }
  });

// 验证目标目录
async function validateTargetDir(dir: string): Promise<void> {
  try {
    const stats = await fs.stat(dir);
    if (!stats.isDirectory()) {
      throw new Error(`路径不是目录: ${dir}`);
    }
  } catch (error: unknown) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      console.log(chalk.yellow(`📁 目录不存在，正在创建: ${dir}`));
      await fs.mkdir(dir, { recursive: true });
    } else {
      throw error;
    }
  }
}

// 生成文件
async function generateFiles(answers: InitAnswers): Promise<void> {
  const writer = new Writer(answers.targetDir);
  const files = getTemplateFiles(answers);

  console.log(chalk.cyan('📝 正在生成核心文件...\n'));

  for (const file of files) {
    try {
      const report = await writer.writeFile(file.path, file.content);
      displayChangeReport(report);
    } catch (error: unknown) {
      console.error(chalk.red(`   ❌ ${file.path}: ${(error as Error).message}`));
    }
  }
}

// 模拟生成（dry-run 模式）
async function simulateGeneration(answers: InitAnswers): Promise<void> {
  const files = getTemplateFiles(answers);

  for (const file of files) {
    console.log(chalk.cyan(`📝 将要创建: ${file.path}`));
    console.log(chalk.gray(`   大小: ${file.content.length} 字节`));
    console.log();
  }
}

// 显示变更报告
function displayChangeReport(report: ChangeReport): void {
  const statusIcon = report.status === 'created' ? '🆕' : 
                     report.status === 'updated' ? '📝' : 
                     report.status === 'unchanged' ? '✅' : '💾';
  
  const statusText = report.status === 'created' ? chalk.green('创建') :
                     report.status === 'updated' ? chalk.yellow('更新') :
                     report.status === 'unchanged' ? chalk.gray('未变更') : chalk.cyan('备份');

  console.log(`   ${statusIcon} ${chalk.bold(report.path)} ${statusText}`);
  
  if (report.backupPath) {
    console.log(chalk.gray(`      备份: ${report.backupPath}`));
  }
  if (report.changes && report.changes.length > 0) {
    report.changes.forEach(change => {
      console.log(chalk.gray(`      ${change}`));
    });
  }
}

// 根据模板类型获取文件列表
function getTemplateFiles(answers: InitAnswers): Array<{path: string, content: string}> {
  const files: Array<{path: string, content: string}> = [];
  const { agentName, agentRole, enableMultiAgent, enableMemory } = answers;

  // SOUL.md - 所有模板都包含
  files.push({
    path: 'SOUL.md',
    content: generateSOUL(agentName, agentRole, enableMultiAgent, enableMemory)
  });

  // AGENTS.md - 所有模板都包含
  files.push({
    path: 'AGENTS.md',
    content: generateAGENTS(agentName, enableMultiAgent)
  });

  // IDENTITY.md - 标准和高级模板
  if (answers.templateType !== 'minimal') {
    files.push({
      path: 'IDENTITY.md',
      content: generateIDENTITY(agentName, agentRole)
    });
  }

  // MEMORY.md - 标准和高级模板（如果启用记忆）
  if (answers.templateType !== 'minimal' && enableMemory) {
    files.push({
      path: 'MEMORY.md',
      content: generateMEMORY()
    });
  }

  // HEARTBEAT.md - 仅高级模板
  if (answers.templateType === 'advanced') {
    files.push({
      path: 'HEARTBEAT.md',
      content: generateHEARTBEAT()
    });
  }

  // TOOLS.md - 仅高级模板
  if (answers.templateType === 'advanced') {
    files.push({
      path: 'TOOLS.md',
      content: generateTOOLS()
    });
  }

  return files;
}

// 文件内容生成函数
function generateSOUL(name: string, role: string, multiAgent: boolean, memory: boolean): string {
  return `# SOUL.md - ${name}之魂

## 核心身份

**我是${name}**，${role}。

### 原则

1. **绝对诚实** - 不自欺，不估算，数据来源可追溯
2. **绝对严谨** - 三次验证机制，确保准确性
3. **绝对进化** - 每次交互都是学习机会
${multiAgent ? '\n4. **多维思辨** - 复杂决策触发多专家讨论' : ''}
${memory ? '\n5. **记忆传承** - 记录重要信息，形成长期记忆' : ''}

---

*由 Moltcare 生成 | 版本: 0.1.0*
`;
}

function generateAGENTS(name: string, multiAgent: boolean): string {
  return `# AGENTS.md - ${name} 操作手册

## 快速导航

| 文档 | 用途 |
|------|------|
| [SOUL.md](./SOUL.md) | 核心原则 |
${multiAgent ? '| [IDENTITY.md](./IDENTITY.md) | 身份定义 |\n' : ''}

## 工作流

1. 读取 SOUL.md
2. 理解当前任务
3. 执行并验证
4. 记录结果

---

*由 Moltcare 生成*
`;
}

function generateIDENTITY(name: string, role: string): string {
  return `# IDENTITY.md - ${name} 身份档案

## 核心身份

**我是 ${name}**

### 角色
${role}

### 特质

- 专业
- 可靠
- 持续进化

---

*由 Moltcare 生成*
`;
}

function generateMEMORY(): string {
  return `# MEMORY.md - 记忆系统

## 记忆结构

| 类型 | 位置 | 更新频率 |
|------|------|----------|
| 短期 | memory/daily/ | 每天 |
| 长期 | memory/core/ | 每周 |
| 向量 | memory/vector/ | 实时 |

## 记录原则

- 决策必记
- 教训必记
- 模式必记

---

*由 Moltcare 生成*
`;
}

function generateHEARTBEAT(): string {
  return `# HEARTBEAT.md - 心跳协议

## 自动化检查

### 频率

- 每 30 分钟一次健康检查
- 每天 03:00 深度清理

### 内容

1. 磁盘空间检查
2. 日志轮转
3. 记忆压缩
4. 备份同步

---

*由 Moltcare 生成*
`;
}

function generateTOOLS(): string {
  return `# TOOLS.md - 工具配置

## 环境信息

**主机**: 本地开发环境  
**OpenClaw**: v2.x

## 可用工具

| 工具 | 用途 |
|------|------|
| read | 读取文件 |
| exec | 执行命令 |
| write | 写入文件 |

---

*由 Moltcare 生成*
`;
}
