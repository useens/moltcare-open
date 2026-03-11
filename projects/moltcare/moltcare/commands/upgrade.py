"""Moltcare upgrade 命令 - 智能升级."""

from pathlib import Path

import click
import requests

from moltcare.constants import VERSION, GITHUB_REPO, CORE_FILES
from moltcare.utils import (
    load_config, save_config, get_workspace_dir,
    print_success, print_info, print_warning, print_error,
    confirm_overwrite, copy_template
)


@click.command()
@click.option(
    "--check-only", "-c",
    is_flag=True,
    help="仅检查更新，不执行升级"
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="强制升级所有文件"
)
@click.option(
    "--template", "-t",
    help="指定要升级到的模板版本"
)
@click.option(
    "--dry-run", "-n",
    is_flag=True,
    help="模拟运行，显示将要执行的操作"
)
@click.option(
    "--workspace", "-w",
    type=click.Path(),
    help="指定工作目录"
)
def upgrade(
    check_only: bool,
    force: bool,
    template: str | None,
    dry_run: bool,
    workspace: str | None
) -> None:
    """智能升级现有配置.
    
    检查并升级 Moltcare 和相关配置到最新版本。
    
    示例:
        moltcare upgrade           # 执行升级
        moltcare upgrade -c        # 仅检查更新
        moltcare upgrade -n        # 模拟运行
        moltcare upgrade -f        # 强制升级所有文件
    """
    if workspace:
        workspace_path = Path(workspace).expanduser().resolve()
    else:
        workspace_path = get_workspace_dir()
    
    config = load_config()
    
    click.secho("🔍 检查更新...", fg="cyan")
    print_info(f"当前版本: {VERSION}")
    print_info(f"工作目录: {workspace_path}")
    
    # 检查最新版本
    latest_version = check_latest_version()
    if latest_version:
        print_info(f"最新版本: {latest_version}")
        
        if latest_version == VERSION:
            print_success("你已经使用的是最新版本!")
        else:
            print_warning(f"发现新版本: {latest_version}")
    
    # 检查配置文件状态
    click.echo()
    click.secho("📋 检查配置文件...", fg="cyan")
    
    status = check_files_status(workspace_path)
    
    outdated = []
    missing = []
    modified = []
    
    for filename, info in status.items():
        if info["status"] == "missing":
            missing.append(filename)
        elif info["status"] == "outdated":
            outdated.append(filename)
        elif info["status"] == "modified":
            modified.append(filename)
    
    # 显示检查结果
    if missing:
        print_warning(f"缺失文件: {', '.join(missing)}")
    if outdated:
        print_warning(f"需要更新: {', '.join(outdated)}")
    if modified:
        print_info(f"已自定义: {', '.join(modified)} (不会被覆盖)")
    
    if not missing and not outdated:
        print_success("所有文件都是最新的!")
        return
    
    if check_only:
        click.echo()
        print_info("使用 'moltcare upgrade' 执行升级")
        return
    
    # 确认升级
    click.echo()
    files_to_update = missing + outdated
    
    if dry_run:
        click.secho("📋 模拟运行 - 将要执行的操作:", fg="cyan")
        for filename in files_to_update:
            action = "创建" if filename in missing else "更新"
            click.echo(f"  {action}: {filename}")
        return
    
    if not force:
        if not click.confirm(f"\n确定要升级 {len(files_to_update)} 个文件?", default=True):
            click.echo("升级取消")
            return
    
    # 执行升级
    click.echo()
    click.secho("🚀 开始升级...", fg="cyan")
    
    template_name = template or config.get("template", "basic")
    template_dir = Path(__file__).parent.parent / "templates" / template_name
    
    context = {
        "agent_name": config.get("agent_name", "Agent"),
        "template_type": template_name,
        "workspace": str(workspace_path),
    }
    
    updated_count = 0
    
    for filename in files_to_update:
        dest_path = workspace_path / filename
        
        # 如果是用户修改过的文件，且不是强制升级，则跳过
        if filename in modified and not force:
            print_warning(f"跳过 (已自定义): {filename}")
            continue
        
        # 查找模板文件
        src_path = template_dir / filename
        if src_path.exists():
            copy_template(src_path, dest_path, context)
        else:
            from moltcare.commands.init import create_default_file
            create_default_file(dest_path, filename, context)
        
        action = "创建" if filename in missing else "更新"
        print_success(f"{action}: {filename}")
        updated_count += 1
    
    # 更新配置
    config["last_upgrade"] = str(Path.home() / ".moltcare" / "last_upgrade")
    save_config(config)
    
    click.echo()
    click.secho(f"✨ 升级完成! 更新了 {updated_count} 个文件", fg="green", bold=True)
    
    if modified and not force:
        click.echo()
        print_info("提示: 使用 --force 选项可以覆盖已自定义的文件")


def check_latest_version() -> str | None:
    """检查最新版本.
    
    Returns:
        最新版本号，或 None 如果检查失败
    """
    try:
        # 尝试从 GitHub API 获取最新版本
        url = f"https://api.github.com/repos/useens/moltcare/releases/latest"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("tag_name", VERSION).lstrip("v")
    except Exception:
        pass
    
    return None


def check_files_status(workspace: Path) -> dict:
    """检查文件状态.
    
    Args:
        workspace: 工作目录
        
    Returns:
        文件状态字典
    """
    from moltcare.utils import get_file_hash
    
    status = {}
    
    for filename in CORE_FILES:
        file_path = workspace / filename
        
        if not file_path.exists():
            status[filename] = {"status": "missing"}
        else:
            # 简单检查：如果文件存在，认为是最新的
            # 更复杂的检查可以比较文件哈希
            status[filename] = {"status": "ok"}
    
    return status
