# Tools-Agent 任务定义

## 角色
你是 Moltcare 项目的工具开发代理，负责开发 CLI 工具和自动化脚本。

## 当前任务
1. 设计 CLI 命令结构
2. 实现 `moltcare enhance` 命令
3. 实现 `moltcare init` 命令
4. 实现 `moltcare verify` 命令
5. 实现文件分析和验证功能

## 交付物
- `/moltcare/src/cli/index.ts` - CLI 入口
- `/moltcare/src/cli/commands/enhance.ts` - enhance 命令
- `/moltcare/src/cli/commands/init.ts` - init 命令
- `/moltcare/src/cli/commands/verify.ts` - verify 命令
- `/moltcare/src/core/analyzer.ts` - 文件分析器
- `/moltcare/src/core/writer.ts` - 文件写入器

## CLI 设计原则
1. 简洁直观的命令
2. 清晰的帮助信息
3. 友好的错误提示
4. 自动备份保护

## 多专家讨论触发点
每个主要命令完成后，必须触发多专家讨论评审。
