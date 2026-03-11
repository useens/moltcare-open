"""Moltcare init 命令 - 交互式初始化."""

from pathlib import Path

import click

from moltcare.constants import TEMPLATES, CORE_FILES, DIRS
from moltcare.utils import (
    load_config, save_config, get_workspace_dir,
    print_success, print_info, print_warning, confirm_overwrite,
    copy_template
)


@click.command()
@click.option(
    "--template", "-t",
    type=click.Choice(list(TEMPLATES.keys())),
    default="basic",
    help="选择模板类型"
)
@click.option(
    "--workspace", "-w",
    type=click.Path(),
    help="工作目录路径"
)
@click.option(
    "--name", "-n",
    help="Agent 名称"
)
@click.option(
    "--description", "-d",
    help="Agent 描述"
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="强制覆盖现有文件"
)
@click.option(
    "--non-interactive", "--yes", "-y",
    is_flag=True,
    help="非交互模式，使用默认值"
)
def init(
    template: str,
    workspace: str | None,
    name: str | None,
    description: str | None,
    force: bool,
    non_interactive: bool
) -> None:
    """交互式初始化 Agent 配置.
    
    根据选择的模板，生成完整的 Agent 核心文件。
    
    示例:
        moltcare init                    # 交互式初始化
        moltcare init -t pro             # 使用专业版模板
        moltcare init -y                 # 非交互模式
        moltcare init -n "MyAgent"       # 指定 Agent 名称
    """
    # 确定工作目录
    if workspace:
        workspace_path = Path(workspace).expanduser().resolve()
    else:
        workspace_path = get_workspace_dir()
    
    print_info(f"工作目录: {workspace_path}")
    
    # 检查工作目录是否存在
    if not workspace_path.exists():
        if non_interactive or click.confirm(
            f"目录 {workspace_path} 不存在，是否创建?",
            default=True
        ):
            workspace_path.mkdir(parents=True, exist_ok=True)
            print_success(f"创建工作目录: {workspace_path}")
        else:
            click.echo("初始化取消")
            return
    
    # 交互式收集信息
    if not non_interactive:
        click.echo()
        click.secho("🚀 欢迎使用 Moltcare 初始化向导", fg="cyan", bold=True)
        click.echo()
        
        # 显示模板选项
        if template == "basic":
            click.echo("可用模板:")
            for key, desc in TEMPLATES.items():
                marker = "✓" if key == template else " "
                click.echo(f"  [{marker}] {key}: {desc}")
            
            new_template = click.prompt(
                "\n选择模板",
                type=click.Choice(list(TEMPLATES.keys())),
                default=template
            )
            template = new_template
        
        # Agent 名称
        if not name:
            default_name = workspace_path.name.replace("-", " ").replace("_", " ").title()
            name = click.prompt("Agent 名称", default=default_name)
        
        # Agent 描述
        if not description:
            description = click.prompt(
                "Agent 描述",
                default=f"{name} - 智能 Agent"
            )
        
        click.echo()
    else:
        # 非交互模式使用默认值
        name = name or workspace_path.name.replace("-", " ").replace("_", " ").title()
        description = description or f"{name} - 智能 Agent"
    
    # 准备模板上下文
    context = {
        "agent_name": name,
        "agent_description": description,
        "template_type": template,
        "workspace": str(workspace_path),
    }
    
    print_info(f"使用模板: {template} - {TEMPLATES[template]}")
    print_info(f"Agent 名称: {name}")
    
    # 创建目录结构
    click.echo()
    click.secho("📁 创建目录结构...", fg="cyan")
    for dir_name in DIRS:
        dir_path = workspace_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print_success(f"创建目录: {dir_name}/")
    
    # 生成核心文件
    click.echo()
    click.secho("📝 生成核心文件...", fg="cyan")
    
    template_dir = Path(__file__).parent.parent / "templates" / template
    
    # 如果本地模板不存在，使用内嵌模板
    if not template_dir.exists():
        template_dir = Path(__file__).parent.parent / "templates" / "basic"
    
    created_count = 0
    skipped_count = 0
    
    for filename in CORE_FILES:
        dest_path = workspace_path / filename
        
        # 检查是否需要覆盖
        if dest_path.exists() and not force:
            if not confirm_overwrite(dest_path):
                print_warning(f"跳过: {filename}")
                skipped_count += 1
                continue
        
        # 查找模板文件
        src_path = template_dir / filename
        if src_path.exists():
            copy_template(src_path, dest_path, context)
        else:
            # 使用默认模板
            create_default_file(dest_path, filename, context)
        
        print_success(f"创建: {filename}")
        created_count += 1
    
    # 保存配置
    config = load_config()
    config["initialized"] = True
    config["template"] = template
    config["agent_name"] = name
    config["workspace"] = str(workspace_path)
    config["core_files"] = CORE_FILES
    save_config(config)
    
    # 显示完成信息
    click.echo()
    click.secho("✨ 初始化完成!", fg="green", bold=True)
    click.echo()
    click.echo(f"工作目录: {workspace_path}")
    click.echo(f"模板类型: {template}")
    click.echo(f"创建文件: {created_count}")
    if skipped_count > 0:
        click.echo(f"跳过文件: {skipped_count}")
    
    click.echo()
    click.secho("🎉 你的 Agent 已经准备好了!", fg="green")
    click.echo()
    click.echo("下一步:")
    click.echo("  1. 编辑 SOUL.md 定义 Agent 的核心身份")
    click.echo("  2. 编辑 AGENTS.md 配置操作手册")
    click.echo("  3. 运行 'moltcare doctor' 检查配置")
    click.echo()


def create_default_file(dest_path: Path, filename: str, context: dict) -> None:
    """创建默认文件.
    
    Args:
        dest_path: 目标路径
        filename: 文件名
        context: 模板上下文
    """
    from moltcare.templates.default import get_default_template
    
    content = get_default_template(filename, context)
    
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(content)
