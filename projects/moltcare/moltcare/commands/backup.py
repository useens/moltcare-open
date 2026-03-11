"""Moltcare backup/restore 命令 - 备份管理."""

import json
import shutil
from datetime import datetime
from pathlib import Path

import click

from moltcare.constants import CORE_FILES, BACKUP_DIR
from moltcare.utils import (
    load_config, save_config, get_workspace_dir,
    create_backup_id, format_timestamp,
    print_success, print_info, print_warning, print_error
)


@click.command(name="backup")
@click.option(
    "--workspace", "-w",
    type=click.Path(),
    help="指定工作目录"
)
@click.option(
    "--name", "-n",
    help="备份名称"
)
@click.option(
    "--description", "-d",
    help="备份描述"
)
@click.option(
    "--list", "-l", "list_backups",
    is_flag=True,
    help="列出所有备份"
)
@click.option(
    "--delete", "--rm",
    help="删除指定备份"
)
def backup(
    workspace: str | None,
    name: str | None,
    description: str | None,
    list_backups: bool,
    delete: str | None
) -> None:
    """创建配置备份.
    
    备份 Agent 的核心配置文件。
    
    示例:
        moltcare backup                    # 创建备份
        moltcare backup -n "v1.0"          # 指定名称
        moltcare backup -l                 # 列出备份
        moltcare backup --rm <backup-id>   # 删除备份
    """
    if list_backups:
        list_all_backups()
        return
    
    if delete:
        delete_backup(delete)
        return
    
    # 确定工作目录
    if workspace:
        workspace_path = Path(workspace).expanduser().resolve()
    else:
        workspace_path = get_workspace_dir()
    
    # 创建备份ID
    backup_id = create_backup_id()
    if name:
        backup_id = f"{backup_id}_{name}"
    
    backup_path = BACKUP_DIR / backup_id
    backup_path.mkdir(parents=True, exist_ok=True)
    
    click.secho(f"💾 创建备份: {backup_id}", fg="cyan")
    print_info(f"工作目录: {workspace_path}")
    
    # 备份元数据
    metadata = {
        "id": backup_id,
        "created_at": datetime.now().isoformat(),
        "workspace": str(workspace_path),
        "name": name,
        "description": description,
        "files": [],
    }
    
    # 备份核心文件
    backed_up = []
    skipped = []
    
    for filename in CORE_FILES:
        src_path = workspace_path / filename
        if src_path.exists():
            dest_path = backup_path / filename
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest_path)
            backed_up.append(filename)
        else:
            skipped.append(filename)
    
    # 保存元数据
    metadata["files"] = backed_up
    metadata_path = backup_path / "backup.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # 显示结果
    click.echo()
    click.secho(f"✅ 备份完成!", fg="green", bold=True)
    print_info(f"备份ID: {backup_id}")
    print_info(f"备份文件: {len(backed_up)}")
    
    if skipped:
        print_warning(f"跳过文件: {', '.join(skipped)}")
    
    click.echo()
    print_info(f"备份位置: {backup_path}")
    print_info("使用 'moltcare restore <backup-id>' 恢复此备份")


@click.command(name="restore")
@click.argument("backup_id", required=False)
@click.option(
    "--workspace", "-w",
    type=click.Path(),
    help="指定工作目录"
)
@click.option(
    "--list", "-l", "list_backups",
    is_flag=True,
    help="列出所有备份"
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="强制恢复，不提示确认"
)
def restore(
    backup_id: str | None,
    workspace: str | None,
    list_backups: bool,
    force: bool
) -> None:
    """从备份恢复配置.
    
    从备份恢复 Agent 的核心配置文件。
    
    示例:
        moltcare restore <backup-id>     # 恢复指定备份
        moltcare restore -l              # 列出备份
        moltcare restore <id> -f         # 强制恢复
    """
    if list_backups or not backup_id:
        list_all_backups()
        return
    
    # 确定工作目录
    if workspace:
        workspace_path = Path(workspace).expanduser().resolve()
    else:
        workspace_path = get_workspace_dir()
    
    # 查找备份
    backup_path = BACKUP_DIR / backup_id
    
    if not backup_path.exists():
        print_error(f"备份不存在: {backup_id}")
        
        # 尝试模糊匹配
        similar = find_similar_backups(backup_id)
        if similar:
            click.echo()
            print_info("你是否想找:")
            for b in similar:
                click.echo(f"  - {b}")
        
        return
    
    # 加载元数据
    metadata_path = backup_path / "backup.json"
    if metadata_path.exists():
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        click.secho(f"📦 备份信息", fg="cyan", bold=True)
        print_info(f"备份ID: {metadata['id']}")
        print_info(f"创建时间: {metadata['created_at']}")
        if metadata.get("name"):
            print_info(f"名称: {metadata['name']}")
        if metadata.get("description"):
            print_info(f"描述: {metadata['description']}")
        print_info(f"文件数: {len(metadata['files'])}")
    
    # 确认恢复
    if not force:
        click.echo()
        if not click.confirm(
            f"确定要恢复到备份 '{backup_id}'? 这将覆盖当前配置!",
            default=False
        ):
            click.echo("恢复取消")
            return
    
    # 执行恢复
    click.echo()
    click.secho("🔄 开始恢复...", fg="cyan")
    
    restored_count = 0
    
    for file_path in backup_path.iterdir():
        if file_path.name == "backup.json":
            continue
        
        dest_path = workspace_path / file_path.name
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, dest_path)
        print_success(f"恢复: {file_path.name}")
        restored_count += 1
    
    click.echo()
    click.secho(f"✅ 恢复完成! 恢复了 {restored_count} 个文件", fg="green", bold=True)
    print_info(f"工作目录: {workspace_path}")


def list_all_backups() -> None:
    """列出所有备份."""
    if not BACKUP_DIR.exists():
        print_info("暂无备份")
        return
    
    backups = []
    
    for backup_path in BACKUP_DIR.iterdir():
        if backup_path.is_dir():
            metadata_path = backup_path / "backup.json"
            
            if metadata_path.exists():
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                backups.append(metadata)
            else:
                # 没有元数据的备份
                backups.append({
                    "id": backup_path.name,
                    "created_at": "unknown",
                    "name": None,
                    "description": None,
                    "files": [],
                })
    
    if not backups:
        print_info("暂无备份")
        return
    
    # 按时间排序
    backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    click.secho("📦 备份列表", fg="cyan", bold=True)
    click.echo()
    
    for backup in backups:
        backup_id = backup["id"]
        created_at = backup.get("created_at", "unknown")
        name = backup.get("name", "")
        description = backup.get("description", "")
        file_count = len(backup.get("files", []))
        
        # 格式化显示
        display_name = f"{backup_id}"
        if name:
            display_name += f" ({name})"
        
        click.echo(f"  • {display_name}")
        click.echo(f"    时间: {created_at}")
        click.echo(f"    文件: {file_count}")
        if description:
            click.echo(f"    描述: {description}")
        click.echo()
    
    print_info(f"共 {len(backups)} 个备份")
    print_info("使用 'moltcare restore <backup-id>' 恢复备份")


def delete_backup(backup_id: str) -> None:
    """删除备份.
    
    Args:
        backup_id: 备份ID
    """
    backup_path = BACKUP_DIR / backup_id
    
    if not backup_path.exists():
        print_error(f"备份不存在: {backup_id}")
        return
    
    if not click.confirm(f"确定要删除备份 '{backup_id}'?", default=False):
        click.echo("删除取消")
        return
    
    shutil.rmtree(backup_path)
    print_success(f"已删除备份: {backup_id}")


def find_similar_backups(query: str) -> list[str]:
    """查找相似的备份.
    
    Args:
        query: 查询字符串
        
    Returns:
        相似备份ID列表
    """
    if not BACKUP_DIR.exists():
        return []
    
    similar = []
    query_lower = query.lower()
    
    for backup_path in BACKUP_DIR.iterdir():
        if backup_path.is_dir():
            backup_id = backup_path.name
            if query_lower in backup_id.lower():
                similar.append(backup_id)
    
    return similar[:5]  # 最多返回5个
