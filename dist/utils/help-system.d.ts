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
import { Command } from 'commander';
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
export interface CommandExample {
    description: string;
    command: string;
    output?: string;
}
export interface CommandOption {
    flags: string;
    description: string;
    defaultValue?: string | boolean;
    required?: boolean;
}
export interface CommandArgument {
    name: string;
    description: string;
    required?: boolean;
    variadic?: boolean;
}
export declare enum CommandCategory {
    CORE = "\u6838\u5FC3\u547D\u4EE4",
    PACK = "\u667A\u80FD\u5305\u7BA1\u7406",
    DEVELOPMENT = "\u5F00\u53D1\u5DE5\u5177",
    CONFIG = "\u914D\u7F6E\u7BA1\u7406",
    UTILITY = "\u5B9E\u7528\u5DE5\u5177"
}
export declare const COMMAND_LIBRARY: CommandDefinition[];
export declare class HelpSystem {
    /**
     * 显示全局帮助
     */
    static showGlobalHelp(program: Command): void;
    /**
     * 显示命令帮助
     */
    static showCommandHelp(commandName: string): void;
    /**
     * 查找命令
     */
    static findCommand(name: string): CommandDefinition | undefined;
    /**
     * 获取所有命令名称
     */
    static getAllCommandNames(): string[];
    /**
     * 显示快速提示
     */
    static showQuickTips(): void;
    /**
     * 显示命令建议（模糊匹配）
     */
    static showCommandSuggestions(input: string): void;
    /**
     * 生成 Markdown 文档
     */
    static generateMarkdownDocs(): string;
    /**
     * 交互式帮助向导
     */
    static interactiveHelp(): Promise<void>;
    /**
     * 显示快速开始向导
     */
    static showQuickstartGuide(): void;
}
export default HelpSystem;
//# sourceMappingURL=help-system.d.ts.map