"""Moltcare CLI 主入口."""

import click
from pathlib import Path

from moltcare import __version__
from moltcare.commands.init import init
from moltcare.commands.upgrade import upgrade
from moltcare.commands.doctor import doctor
from moltcare.commands.backup import backup, restore


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="显示版本信息")
@click.pass_context
def cli(ctx: click.Context, version: bool) -> None:
    """Moltcare - 一键提升 OpenClaw Agent 智能.
    
    让每个刚安装的 OpenClaw Agent 都能一键获得智能。
    
    主要命令:
        init      交互式初始化 Agent 配置
        upgrade   智能升级现有配置
        doctor    诊断并修复配置问题
        backup    创建配置备份
        restore   从备份恢复配置
    
    示例:
        moltcare init                    # 交互式初始化
        moltcare init --template=pro     # 使用高级模板
        moltcare upgrade                 # 检查并升级
        moltcare doctor                  # 诊断问题
        moltcare backup                  # 创建备份
        moltcare restore <backup-id>     # 恢复备份
    """
    if version:
        click.echo(f"Moltcare v{__version__}")
        ctx.exit(0)
    
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


cli.add_command(init)
cli.add_command(upgrade)
cli.add_command(doctor)
cli.add_command(backup)
cli.add_command(restore)


if __name__ == "__main__":
    cli()
