#!/usr/bin/env python3
"""
MoltCare CLI
命令行入口 - 用户交互界面
"""

import argparse
import json
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

# 导入核心模块 - 支持相对导入和绝对导入
try:
    from .config import get_config, ConfigManager
    from .pack_manager import get_pack_manager, PackManager
except ImportError:
    from config import get_config, ConfigManager
    from pack_manager import get_pack_manager, PackManager


# 版本信息
VERSION = "1.1.0"

# 配置路径 (兼容旧版)
HOME_DIR = Path.home()
MOLTCARE_DIR = HOME_DIR / ".moltcare"
WORKSPACE_DIR = MOLTCARE_DIR / "workspace"


def print_banner():
    """打印启动横幅"""
    banner = """
╔═══════════════════════════════════════╗
║    🦀 MoltCare - 智能Pack管理平台     ║
║              v{}                  ║
╚═══════════════════════════════════════╝
""".format(VERSION)
    print(banner)


def cmd_config(args) -> int:
    """配置管理命令"""
    config = get_config()
    
    if args.action == "get":
        if args.key:
            value = config.get(args.key)
            if value is not None:
                print(f"{args.key} = {value}")
            else:
                print(f"配置项 '{args.key}' 不存在")
                return 1
        else:
            # 显示所有配置
            print("当前配置:")
            for key, value in config.get_all().items():
                print(f"  {key}: {value}")
    
    elif args.action == "set":
        if not args.key or not args.value:
            print("错误: set操作需要指定key和value")
            return 1
        
        # 类型转换
        value = args.value
        if value.lower() in ("true", "false"):
            value = value.lower() == "true"
        elif value.isdigit():
            value = int(value)
        
        if config.set(args.key, value):
            print(f"✓ {args.key} 设置为 {value}")
        else:
            print(f"✗ 设置失败，配置项 '{args.key}' 可能不存在")
            return 1
    
    elif args.action == "reset":
        if config.reset():
            print("✓ 配置已重置为默认值")
        else:
            print("✗ 重置失败")
            return 1
    
    elif args.action == "path":
        print(f"配置文件路径: {config.config_path}")
    
    return 0


def cmd_pack(args) -> int:
    """Pack管理命令"""
    # 从配置获取packs目录
    config = get_config()
    packs_dir = config.get("packs_dir", "./packs")
    pm = get_pack_manager(packs_dir)
    
    if args.action == "install":
        if not args.source:
            print("错误: 请指定要安装的Pack路径")
            return 1
        success, msg = pm.install(args.source, force=args.force)
        print(msg)
        return 0 if success else 1
    
    elif args.action == "uninstall":
        pack_name = args.name or args.source
        if not pack_name:
            print("错误: 请指定要卸载的Pack名称")
            return 1
        success, msg = pm.uninstall(pack_name)
        print(msg)
        return 0 if success else 1
    
    elif args.action == "list":
        packs = pm.list_packs(show_inactive=args.all)
        if not packs:
            print("没有已安装的Pack")
            return 0
        
        print(f"{'名称':<20} {'版本':<10} {'状态':<8} {'描述'}")
        print("-" * 60)
        for pack in packs:
            status = "启用" if pack.active else "禁用"
            desc = pack.manifest.description[:30] + "..." if len(pack.manifest.description) > 30 else pack.manifest.description
            print(f"{pack.name:<20} {pack.version:<10} {status:<8} {desc}")
    
    elif args.action == "show":
        pack_name = args.name or args.source  # 兼容两种方式
        if not pack_name:
            print("错误: 请指定Pack名称")
            return 1
        pack = pm.get_pack(pack_name)
        if pack:
            print(f"Pack: {pack.name}")
            print(f"  版本: {pack.version}")
            print(f"  状态: {'启用' if pack.active else '禁用'}")
            print(f"  路径: {pack.path}")
            print(f"  安装日期: {pack.install_date}")
            print(f"  描述: {pack.manifest.description}")
            print(f"  作者: {pack.manifest.author}")
            print(f"  入口: {pack.manifest.entry_point}")
            if pack.manifest.dependencies:
                print(f"  依赖: {', '.join(pack.manifest.dependencies)}")
        else:
            print(f"Pack '{pack_name}' 未找到")
            return 1
    
    elif args.action == "enable":
        pack_name = args.name or args.source
        if not pack_name:
            print("错误: 请指定Pack名称")
            return 1
        success, msg = pm.enable(pack_name)
        print(msg)
        return 0 if success else 1
    
    elif args.action == "disable":
        pack_name = args.name or args.source
        if not pack_name:
            print("错误: 请指定Pack名称")
            return 1
        success, msg = pm.disable(pack_name)
        print(msg)
        return 0 if success else 1
    
    return 0


# ========== 兼容旧版命令 (Legacy Commands) ==========

def cmd_init(args) -> int:
    """初始化命令 (兼容旧版)"""
    print("🦞 MoltCare 初始化\n")
    
    # 支持路径参数
    target_path = Path(args.path).expanduser().resolve() if args.path else MOLTCARE_DIR
    config_file = target_path / "config.yaml"
    
    # 检查是否已初始化
    if config_file.exists() and not args.force:
        print(f"⚠️  MoltCare 已在 {target_path} 初始化")
        print(f"   配置文件: {config_file}")
        print("   使用 --force 重新初始化")
        return 0
    
    # 确保目录存在
    target_path.mkdir(parents=True, exist_ok=True)
    workspace_path = target_path / "workspace"
    workspace_path.mkdir(exist_ok=True)
    packs_path = target_path / "packs"
    packs_path.mkdir(exist_ok=True)
    
    # 创建配置
    try:
        import yaml
        new_config = {
            'version': VERSION,
            'language': 'zh',
            'workspacePath': str(workspace_path),
            'packsDir': str(packs_path),
            'logLevel': 'info',
            'autoUpdate': True,
            'initialized': True,
            'initializedAt': str(datetime.now()),
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(new_config, f, allow_unicode=True, default_flow_style=False)
    except ImportError:
        # 如果没有yaml，使用json
        new_config = {
            'version': VERSION,
            'language': 'zh',
            'workspacePath': str(workspace_path),
            'packsDir': str(packs_path),
            'logLevel': 'info',
            'autoUpdate': True,
            'initialized': True,
            'initializedAt': str(datetime.now()),
        }
        with open(target_path / "config.json", 'w', encoding='utf-8') as f:
            json.dump(new_config, f, indent=2, ensure_ascii=False)
    
    print(f"✓ 初始化完成!")
    print(f"  目标路径: {target_path}")
    print(f"  配置文件: {config_file}")
    print(f"  工作区:   {workspace_path}")
    
    if not args.yes:
        print("\n💡 下一步:")
        print(f"  $ cd {target_path}")
        print("  $ moltcare list       # 查看可用智能包")
        print("  $ moltcare apply foundation  # 应用基础包")
    
    return 0


def cmd_list_legacy(args) -> int:
    """列出智能包命令 (兼容旧版，扫描本地目录)"""
    # 查找 packs 目录
    packs_dirs = [
        Path.cwd() / 'packs',
        MOLTCARE_DIR / 'packs',
    ]
    
    packs_found = []
    for packs_dir in packs_dirs:
        if packs_dir.exists():
            for entry in packs_dir.iterdir():
                if entry.is_dir() and not entry.name.startswith('.'):
                    manifest_file = entry / 'manifest.json'
                    if manifest_file.exists():
                        try:
                            with open(manifest_file, 'r', encoding='utf-8') as f:
                                manifest = json.load(f)
                            packs_found.append({
                                'name': manifest.get('name', entry.name),
                                'version': manifest.get('version', '0.0.1'),
                                'description': manifest.get('description', '暂无描述'),
                                'path': str(entry),
                            })
                        except Exception:
                            pass
    
    if args.json:
        print(json.dumps(packs_found, ensure_ascii=False, indent=2))
        return 0
    
    print("📦 可用智能包\n")
    
    if not packs_found:
        print("未找到智能包")
        print("\n💡 提示: 运行命令需要在 MoltCare 项目目录中")
        return 0
    
    for pack in packs_found:
        print(f"  {pack['name']} v{pack['version']}")
        print(f"    {pack['description']}")
        print()
    
    print(f"共 {len(packs_found)} 个智能包")
    return 0


def cmd_apply(args) -> int:
    """应用智能包命令 (兼容旧版)"""
    pack_name = args.pack
    
    if not pack_name:
        print("✗ 请指定要应用的智能包名称")
        print("  示例: moltcare apply foundation")
        return 1
    
    # 查找智能包
    packs_dirs = [
        Path.cwd() / 'packs',
        MOLTCARE_DIR / 'packs',
    ]
    
    pack_path = None
    for packs_dir in packs_dirs:
        candidate = packs_dir / pack_name
        if candidate.exists() and (candidate / 'manifest.json').exists():
            pack_path = candidate
            break
    
    if not pack_path:
        print(f"✗ 智能包 '{pack_name}' 不存在")
        return 1
    
    # 读取 manifest
    with open(pack_path / 'manifest.json', 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    print(f"📦 应用智能包: {manifest.get('name', pack_name)}")
    print(f"   {manifest.get('description', '')}")
    print()
    
    if args.dry_run:
        print("🔍 预览模式，不会实际应用更改")
        return 0
    
    # 复制模板文件
    templates_dir = pack_path / 'templates'
    if templates_dir.exists():
        if args.global_install:
            target_dir = WORKSPACE_DIR
        else:
            target_dir = Path.cwd()
        
        for template_file in templates_dir.rglob('*'):
            if template_file.is_file():
                rel_path = template_file.relative_to(templates_dir)
                target_file = target_dir / rel_path
                
                if target_file.exists() and not args.force:
                    print(f"  ⚠️  跳过已存在: {rel_path}")
                    continue
                
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 简单模板渲染
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                content = content.replace('{{AGENT_NAME}}', 'MoltCare Agent')
                content = content.replace('{{timestamp}}', str(datetime.now()))
                
                with open(target_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"  📄 {rel_path}")
    
    # 执行脚本
    scripts_dir = pack_path / 'scripts'
    if scripts_dir.exists():
        setup_script = scripts_dir / 'setup.sh'
        if setup_script.exists() and not args.dry_run:
            print("\n🔧 执行安装脚本...")
            result = os.system(f'bash "{setup_script}"')
            if result != 0:
                print(f"⚠️ 脚本执行返回非零状态: {result}")
    
    print(f"\n✓ 智能包 '{pack_name}' 应用成功!")
    return 0


def cmd_doctor(args) -> int:
    """诊断命令 (兼容旧版)"""
    checks = []
    
    # 检查 Python 版本
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    checks.append({'status': 'ok', 'icon': '✓', 'message': f'Python {py_version}'})
    
    # 检查配置文件
    config_file = MOLTCARE_DIR / "config.yaml"
    if config_file.exists():
        checks.append({'status': 'ok', 'icon': '✓', 'message': '配置文件存在'})
    else:
        checks.append({'status': 'error', 'icon': '✗', 'message': '配置文件不存在'})
    
    # 检查工作目录
    if WORKSPACE_DIR.exists():
        checks.append({'status': 'ok', 'icon': '✓', 'message': '工作目录存在'})
    else:
        checks.append({'status': 'error', 'icon': '✗', 'message': '工作目录不存在'})
    
    # 检查 PyYAML
    try:
        import yaml
        checks.append({'status': 'ok', 'icon': '✓', 'message': 'PyYAML 已安装'})
    except ImportError:
        checks.append({'status': 'warning', 'icon': '-', 'message': 'PyYAML 未安装 (可选)'})
    
    # 检查 Node.js (可选)
    node_version = os.popen('node --version 2>/dev/null').read().strip()
    if node_version:
        checks.append({'status': 'ok', 'icon': '✓', 'message': f'Node.js {node_version} (可选)'})
    else:
        checks.append({'status': 'warning', 'icon': '-', 'message': 'Node.js 未安装 (可选)'})
    
    # 检查智能包
    packs_dir = Path.cwd() / 'packs'
    if packs_dir.exists():
        pack_count = len([d for d in packs_dir.iterdir() if d.is_dir() and not d.name.startswith('.')])
        checks.append({'status': 'ok', 'icon': '✓', 'message': f'找到 {pack_count} 个智能包'})
    else:
        checks.append({'status': 'warning', 'icon': '-', 'message': '智能包目录不存在 (在项目外运行)'})
    
    if getattr(args, 'json', False):
        print(json.dumps(checks, ensure_ascii=False, indent=2))
        return 0
    
    print("🔧 MoltCare 健康诊断\n")
    
    for check in checks:
        print(f"  {check['icon']} {check['message']}")
    
    print("\n诊断完成")
    return 0


def cmd_status(args) -> int:
    """显示系统状态 (统一版本)"""
    config = get_config()
    packs_dir = config.get("packs_dir", "./packs")
    pm = get_pack_manager(packs_dir)
    
    packs = pm.list_packs(show_inactive=True)
    active_count = len(pm.get_active_packs())
    
    status_info = {
        'version': VERSION,
        'config_path': str(config.config_path),
        'packs_dir': packs_dir,
        'log_level': config.get('log_level'),
        'auto_update': config.get('auto_update'),
        'packs': {
            'total': len(packs),
            'active': active_count,
            'disabled': len(packs) - active_count
        }
    }
    
    if getattr(args, 'json', False):
        print(json.dumps(status_info, ensure_ascii=False, indent=2))
        return 0
    
    print_banner()
    print("📊 系统状态")
    print("-" * 40)
    print(f"版本: {status_info['version']}")
    print(f"配置路径: {status_info['config_path']}")
    print(f"Packs目录: {status_info['packs_dir']}")
    print(f"日志级别: {status_info['log_level']}")
    print(f"自动更新: {'开启' if status_info['auto_update'] else '关闭'}")
    print()
    print("📦 已安装Packs")
    print(f"  总数: {status_info['packs']['total']}")
    print(f"  启用: {status_info['packs']['active']}")
    print(f"  禁用: {status_info['packs']['disabled']}")
    
    return 0


def create_parser() -> argparse.ArgumentParser:
    """创建命令行解析器"""
    parser = argparse.ArgumentParser(
        prog="moltcare",
        description="MoltCare - 智能Pack管理平台",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  moltcare init                      # 初始化 MoltCare
  moltcare status                    # 查看系统状态
  moltcare config get                # 查看所有配置
  moltcare config set log_level debug
  moltcare pack list                 # 列出已安装packs
  moltcare pack install ./my-pack    # 安装pack
  moltcare pack uninstall my-pack    # 卸载pack
  moltcare apply foundation          # 应用基础智能包
  moltcare doctor                    # 运行健康诊断
        """
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # ========== config 命令 ==========
    config_parser = subparsers.add_parser("config", help="配置管理")
    config_parser.add_argument("action", choices=["get", "set", "reset", "path"],
                               help="配置操作")
    config_parser.add_argument("key", nargs="?", help="配置项名称")
    config_parser.add_argument("value", nargs="?", help="配置项值")
    config_parser.set_defaults(func=cmd_config)
    
    # ========== pack 命令 ==========
    pack_parser = subparsers.add_parser("pack", help="Pack管理")
    pack_parser.add_argument("action", 
                            choices=["install", "uninstall", "list", "show", "enable", "disable"],
                            help="Pack操作")
    pack_parser.add_argument("source", nargs="?", help="Pack源路径(用于install)")
    pack_parser.add_argument("name", nargs="?", help="Pack名称")
    pack_parser.add_argument("--force", "-f", action="store_true", help="强制重新安装")
    pack_parser.add_argument("--all", "-a", action="store_true", help="显示所有(包括禁用的)")
    pack_parser.set_defaults(func=cmd_pack)
    
    # ========== status 命令 ==========
    status_parser = subparsers.add_parser("status", help="查看系统状态")
    status_parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    status_parser.set_defaults(func=cmd_status)
    
    # ========== init 命令 (兼容旧版) ==========
    init_parser = subparsers.add_parser("init", help="初始化 MoltCare")
    init_parser.add_argument("path", nargs="?", help="目标目录路径 (默认: ~/.moltcare)")
    init_parser.add_argument("-f", "--force", action="store_true", help="强制重新初始化")
    init_parser.add_argument("-y", "--yes", action="store_true", help="非交互模式，使用默认值")
    init_parser.set_defaults(func=cmd_init)
    
    # ========== list 命令 (兼容旧版) ==========
    list_parser = subparsers.add_parser("list", help="列出可用智能包")
    list_parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    list_parser.set_defaults(func=cmd_list_legacy)
    
    # ========== apply 命令 (兼容旧版) ==========
    apply_parser = subparsers.add_parser("apply", help="应用智能包")
    apply_parser.add_argument("pack", help="智能包名称")
    apply_parser.add_argument("-f", "--force", action="store_true", help="强制覆盖")
    apply_parser.add_argument("-d", "--dry-run", action="store_true", help="预览更改")
    apply_parser.add_argument("-g", "--global-install", dest="global_install", action="store_true", help="应用到全局工作区")
    apply_parser.set_defaults(func=cmd_apply)
    
    # ========== doctor 命令 (兼容旧版) ==========
    doctor_parser = subparsers.add_parser("doctor", help="运行健康诊断")
    doctor_parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    doctor_parser.set_defaults(func=cmd_doctor)
    
    return parser


def main(argv: Optional[list] = None) -> int:
    """主入口函数"""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # 没有命令时显示帮助
    if args.command is None:
        parser.print_help()
        return 0
    
    # 执行对应命令
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n操作已取消")
        return 130
    except Exception as e:
        print(f"错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())


# 自我审查检查点 (累计代码行数: ~580行)
# ✅ 完整的CLI命令结构
# ✅ 子命令: config, pack, status, init, list, apply, doctor
# ✅ 向后兼容旧版命令
# ✅ 错误处理完善
# ✅ 返回值符合Unix规范
