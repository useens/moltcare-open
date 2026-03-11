"""Moltcare 常量定义."""

from pathlib import Path

# 版本信息
VERSION = "0.1.0"

# 核心文件列表
CORE_FILES = [
    "SOUL.md",
    "AGENTS.md", 
    "IDENTITY.md",
    "USER.md",
    "MEMORY.md",
    "HEARTBEAT.md",
    "TOOLS.md",
]

# 可选文件列表
OPTIONAL_FILES = [
    ".env",
    ".gitignore",
]

# 目录结构
DIRS = [
    "memory",
    "memory/modules",
    "scripts",
    "skills",
]

# 模板类型
TEMPLATES = {
    "basic": "基础版 - 适合新手",
    "pro": "专业版 - 适合进阶用户", 
    "enterprise": "企业版 - 适合团队协作",
    "minimal": "极简版 - 仅核心文件",
}

# 配置文件路径
CONFIG_DIR = Path.home() / ".config" / "moltcare"
CONFIG_FILE = CONFIG_DIR / "config.json"

# 备份目录
BACKUP_DIR = CONFIG_DIR / "backups"

# 模板目录
TEMPLATE_DIR = Path(__file__).parent / "templates"

# 远程仓库
GITHUB_REPO = "https://github.com/useens/moltcare"
RAW_TEMPLATE_URL = f"{GITHUB_REPO}/raw/main/templates"

# 检查间隔
CHECK_INTERVAL_DAYS = 7

# 颜色主题
COLORS = {
    "primary": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "info": "blue",
}
