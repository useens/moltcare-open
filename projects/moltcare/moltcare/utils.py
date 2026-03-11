"""Moltcare 工具函数."""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import click

from moltcare.constants import CONFIG_DIR, CONFIG_FILE, BACKUP_DIR


def ensure_dirs() -> None:
    """确保必要的目录存在."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, Any]:
    """加载配置文件."""
    ensure_dirs()
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(config: dict[str, Any]) -> None:
    """保存配置文件."""
    ensure_dirs()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_workspace_dir() -> Path:
    """获取工作目录."""
    workspace = os.environ.get("OPENCLAW_WORKSPACE")
    if workspace:
        return Path(workspace)
    
    # 默认工作目录
    default = Path.home() / ".openclaw" / "workspace"
    if default.exists():
        return default
    
    # 当前目录
    return Path.cwd()


def check_core_files(workspace: Path | None = None) -> dict[str, bool]:
    """检查核心文件是否存在.
    
    Args:
        workspace: 工作目录，默认自动检测
        
    Returns:
        文件名到存在状态的映射
    """
    from moltcare.constants import CORE_FILES
    
    if workspace is None:
        workspace = get_workspace_dir()
    
    result = {}
    for file in CORE_FILES:
        result[file] = (workspace / file).exists()
    
    return result


def create_backup_id() -> str:
    """创建备份ID."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"backup_{timestamp}"


def format_timestamp(timestamp: str) -> str:
    """格式化时间戳."""
    try:
        dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return timestamp


def copy_template(src: Path, dest: Path, context: dict[str, Any] | None = None) -> None:
    """复制模板文件，支持变量替换.
    
    Args:
        src: 源文件路径
        dest: 目标文件路径
        context: 模板变量上下文
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    if context:
        # 使用 Jinja2 渲染模板
        try:
            from jinja2 import Template
            with open(src, "r", encoding="utf-8") as f:
                template = Template(f.read())
            content = template.render(**context)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(content)
        except ImportError:
            # 如果没有 Jinja2，直接复制
            shutil.copy2(src, dest)
    else:
        shutil.copy2(src, dest)


def print_success(message: str) -> None:
    """打印成功消息."""
    click.secho(f"✓ {message}", fg="green")


def print_error(message: str) -> None:
    """打印错误消息."""
    click.secho(f"✗ {message}", fg="red")


def print_warning(message: str) -> None:
    """打印警告消息."""
    click.secho(f"⚠ {message}", fg="yellow")


def print_info(message: str) -> None:
    """打印信息消息."""
    click.secho(f"ℹ {message}", fg="blue")


def confirm_overwrite(path: Path) -> bool:
    """确认是否覆盖文件.
    
    Args:
        path: 文件路径
        
    Returns:
        是否确认覆盖
    """
    if not path.exists():
        return True
    
    return click.confirm(
        f"文件 {path.name} 已存在，是否覆盖?",
        default=False
    )


def get_file_hash(path: Path) -> str:
    """获取文件哈希值.
    
    Args:
        path: 文件路径
        
    Returns:
        MD5哈希值
    """
    import hashlib
    
    if not path.exists():
        return ""
    
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()[:8]


def is_git_repo(path: Path) -> bool:
    """检查路径是否是 Git 仓库.
    
    Args:
        path: 目录路径
        
    Returns:
        是否是Git仓库
    """
    return (path / ".git").exists()
