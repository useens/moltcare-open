#!/usr/bin/env python3
"""
Moltcare CLI - 智能升级命令行工具
"""

import argparse
import sys
from pathlib import Path

from .diagnostic import DiagnosticEngine
from .merger import SmartMerger
from .validator import ConfigValidator


def cmd_diagnose(args):
    """诊断当前配置质量"""
    workspace = Path(args.workspace).expanduser()
    engine = DiagnosticEngine(workspace)

    print("🔍 正在诊断 OpenClaw 配置文件...\n")

    report = engine.run_diagnostic()

    print(f"📊 诊断报告")
    print(f"=" * 50)
    print(f"总体评分: {report['overall_score']}/100")
    print(f"发现问题: {len(report['issues'])} 个")
    print(f"建议优化: {len(report['suggestions'])} 项\n")

    if report['issues']:
        print("⚠️ 发现的问题:")
        for issue in report['issues']:
            print(f"  - [{issue['file']}] {issue['message']}")
        print()

    if report['suggestions']:
        print("💡 优化建议:")
        for suggestion in report['suggestions']:
            print(f"  - {suggestion}")
        print()

    return 0 if report['overall_score'] >= 70 else 1


def cmd_upgrade(args):
    """升级配置文件"""
    workspace = Path(args.workspace).expanduser()
    dry_run = args.dry_run

    engine = DiagnosticEngine(workspace)
    report = engine.run_diagnostic()

    if report['overall_score'] >= 90 and not args.force:
        print("✅ 你的配置质量已经很优秀了！")
        print("   使用 --force 强制升级也不建议。")
        return 0

    print(f"🚀 开始升级配置文件...")
    if dry_run:
        print("   (dry-run 模式，仅预览变更)\n")

    merger = SmartMerger(workspace, dry_run=dry_run)
    result = merger.merge_templates(report)

    print(f"\n✅ 升级完成！")
    print(f"   处理文件: {len(result['processed_files'])}")
    print(f"   备份位置: {result['backup_path']}")

    if dry_run:
        print(f"\n💡 这是 dry run，实际修改预览：")
        for file_info in result['processed_files']:
            print(f"   - {file_info['file']}: {file_info['changes']} 处变更")

    return 0


def cmd_validate(args):
    """验证配置文件"""
    workspace = Path(args.workspace).expanduser()
    validator = ConfigValidator(workspace)

    print("🔐 验证配置文件...\n")

    results = validator.validate_all()

    if results['valid']:
        print("✅ 所有配置文件验证通过！")
        return 0
    else:
        print("❌ 发现问题:")
        for error in results['errors']:
            print(f"  - {error}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Moltcare - OpenClaw 智能升级工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-w', '--workspace',
        default="~/.openclaw/workspace",
        help="OpenClaw 工作目录 (默认: ~/.openclaw/workspace)"
    )

    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # diagnose 命令
    diag_parser = subparsers.add_parser('diagnose', help='诊断配置质量')
    diag_parser.set_defaults(func=cmd_diagnose)

    # upgrade 命令
    upgrade_parser = subparsers.add_parser('upgrade', help='升级配置文件')
    upgrade_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预览变更，不实际修改'
    )
    upgrade_parser.add_argument(
        '--force',
        action='store_true',
        help='强制升级，即使质量已较高'
    )
    upgrade_parser.set_defaults(func=cmd_upgrade)

    # validate 命令
    val_parser = subparsers.add_parser('validate', help='验证配置文件')
    val_parser.set_defaults(func=cmd_validate)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
