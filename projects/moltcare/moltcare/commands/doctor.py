"""Moltcare doctor 命令 - 诊断检查."""

from pathlib import Path

import click

from moltcare.constants import CORE_FILES, DIRS
from moltcare.utils import (
    load_config, get_workspace_dir, get_file_hash, is_git_repo,
    print_success, print_info, print_warning, print_error
)


@click.command()
@click.option(
    "--fix", "-f",
    is_flag=True,
    help="自动修复发现的问题"
)
@click.option(
    "--workspace", "-w",
    type=click.Path(),
    help="指定工作目录"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="显示详细输出"
)
def doctor(fix: bool, workspace: str | None, verbose: bool) -> None:
    """诊断并修复配置问题.
    
    全面检查 Agent 配置，发现问题并提供修复建议。
    
    示例:
        moltcare doctor           # 诊断检查
        moltcare doctor -f        # 自动修复问题
        moltcare doctor -v        # 显示详细信息
    """
    # 确定工作目录
    if workspace:
        workspace_path = Path(workspace).expanduser().resolve()
    else:
        workspace_path = get_workspace_dir()
    
    click.secho("🔍 Moltcare 诊断检查", fg="cyan", bold=True)
    print_info(f"工作目录: {workspace_path}")
    
    issues = []
    warnings = []
    
    # 1. 检查工作目录
    click.echo()
    click.secho("📁 检查目录结构...", fg="cyan")
    
    if not workspace_path.exists():
        issues.append({
            "type": "error",
            "message": f"工作目录不存在: {workspace_path}",
            "fix": lambda: workspace_path.mkdir(parents=True, exist_ok=True)
        })
        print_error(f"工作目录不存在: {workspace_path}")
    else:
        print_success("工作目录存在")
        
        # 检查子目录
        for dir_name in DIRS:
            dir_path = workspace_path / dir_name
            if dir_path.exists():
                print_success(f"目录存在: {dir_name}/")
            else:
                warnings.append({
                    "type": "warning",
                    "message": f"目录不存在: {dir_name}/",
                    "fix": lambda d=dir_path: d.mkdir(parents=True, exist_ok=True)
                })
                print_warning(f"目录缺失: {dir_name}/")
    
    # 2. 检查核心文件
    click.echo()
    click.secho("📄 检查核心文件...", fg="cyan")
    
    for filename in CORE_FILES:
        file_path = workspace_path / filename
        
        if file_path.exists():
            size = file_path.stat().st_size
            if size == 0:
                issues.append({
                    "type": "error",
                    "message": f"文件为空: {filename}",
                    "fix": None
                })
                print_error(f"文件为空: {filename}")
            else:
                print_success(f"文件存在: {filename} ({size} bytes)")
                
                if verbose:
                    # 显示文件前5行预览
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            lines = f.readlines()[:5]
                            for i, line in enumerate(lines, 1):
                                preview = line.strip()[:50]
                                click.echo(f"    {i}: {preview}...")
                    except Exception as e:
                        click.echo(f"    无法读取: {e}")
        else:
            issues.append({
                "type": "error",
                "message": f"文件缺失: {filename}",
                "fix": None
            })
            print_error(f"文件缺失: {filename}")
    
    # 3. 检查 Git 仓库
    click.echo()
    click.secho("🔀 检查版本控制...", fg="cyan")
    
    if is_git_repo(workspace_path):
        print_success("Git 仓库已初始化")
        
        # 检查 .gitignore
        gitignore_path = workspace_path / ".gitignore"
        if gitignore_path.exists():
            print_success(".gitignore 存在")
        else:
            warnings.append({
                "type": "warning",
                "message": "缺少 .gitignore 文件",
                "fix": lambda: create_gitignore(workspace_path)
            })
            print_warning("缺少 .gitignore 文件")
    else:
        warnings.append({
            "type": "warning",
            "message": "未初始化 Git 仓库",
            "fix": None
        })
        print_warning("未初始化 Git 仓库 (建议: git init)")
    
    # 4. 检查配置文件
    click.echo()
    click.secho("⚙️  检查配置...", fg="cyan")
    
    config = load_config()
    if config.get("initialized"):
        print_success("Moltcare 已初始化")
        if verbose:
            print_info(f"模板类型: {config.get('template', 'unknown')}")
            print_info(f"Agent 名称: {config.get('agent_name', 'unknown')}")
    else:
        warnings.append({
            "type": "warning",
            "message": "Moltcare 未初始化",
            "fix": None
        })
        print_warning("Moltcare 未初始化 (建议: moltcare init)")
    
    # 5. 检查环境
    click.echo()
    click.secho("🌍 检查环境...", fg="cyan")
    
    # 检查 .env 文件
    env_path = workspace_path / ".env"
    if env_path.exists():
        print_success(".env 文件存在")
        
        # 检查关键变量
        with open(env_path, "r") as f:
            content = f.read()
            if "GITHUB_TOKEN" in content:
                print_success("GITHUB_TOKEN 已配置")
            else:
                warnings.append({
                    "type": "warning",
                    "message": "未配置 GITHUB_TOKEN",
                    "fix": None
                })
                print_warning("未配置 GITHUB_TOKEN")
    else:
        warnings.append({
            "type": "warning",
            "message": "缺少 .env 文件",
            "fix": lambda: create_env_file(workspace_path)
        })
        print_warning("缺少 .env 文件")
    
    # 显示总结
    click.echo()
    click.secho("📊 诊断结果", fg="cyan", bold=True)
    
    error_count = len([i for i in issues if i["type"] == "error"])
    warning_count = len(warnings)
    
    if error_count == 0 and warning_count == 0:
        click.secho("✅ 所有检查通过! 你的 Agent 配置很健康。", fg="green", bold=True)
    else:
        if error_count > 0:
            print_error(f"发现 {error_count} 个错误")
        if warning_count > 0:
            print_warning(f"发现 {warning_count} 个警告")
        
        # 自动修复
        if fix:
            click.echo()
            click.secho("🔧 自动修复...", fg="cyan")
            
            fixed_count = 0
            
            for issue in issues + warnings:
                if issue.get("fix"):
                    try:
                        issue["fix"]()
                        print_success(f"已修复: {issue['message']}")
                        fixed_count += 1
                    except Exception as e:
                        print_error(f"修复失败: {issue['message']} - {e}")
            
            click.echo()
            if fixed_count > 0:
                click.secho(f"✅ 已自动修复 {fixed_count} 个问题", fg="green")
            else:
                print_info("没有可以自动修复的问题")
            
            print_info("其他问题需要手动修复，请查看上面的诊断信息")
        else:
            click.echo()
            print_info("使用 'moltcare doctor -f' 自动修复可修复的问题")


def create_gitignore(workspace: Path) -> None:
    """创建 .gitignore 文件.
    
    Args:
        workspace: 工作目录
    """
    content = """# Environment variables
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Backups
backups/
*.backup
"""
    
    gitignore_path = workspace / ".gitignore"
    with open(gitignore_path, "w") as f:
        f.write(content)


def create_env_file(workspace: Path) -> None:
    """创建 .env 文件模板.
    
    Args:
        workspace: 工作目录
    """
    content = """# GitHub Token (用于 GitHub API 访问)
GITHUB_TOKEN=your_github_token_here

# 其他 API Keys
# OPENAI_API_KEY=
# ANTHROPIC_API_KEY=

# OpenClaw 配置
# OPENCLAW_WORKSPACE=
"""
    
    env_path = workspace / ".env"
    with open(env_path, "w") as f:
        f.write(content)
