"""
MoltCare - 智能Pack管理平台

核心模块:
- config: 配置管理系统
- pack_manager: Pack管理器
- cli: 命令行接口
"""

__version__ = "0.1.0"
__author__ = "MoltCare Team"

from .config import ConfigManager, MoltCareConfig, get_config
from .pack_manager import PackManager, PackManifest, PackInfo, get_pack_manager

__all__ = [
    "ConfigManager",
    "MoltCareConfig", 
    "get_config",
    "PackManager",
    "PackManifest",
    "PackInfo",
    "get_pack_manager",
]
