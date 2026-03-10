"""
MoltCare Test Utilities
测试工具类
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Generator
from contextlib import contextmanager


class TestBase(unittest.TestCase):
    """测试基类 - 提供临时目录和清理功能"""
    
    def setUp(self):
        """每个测试前创建临时目录"""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="moltcare_test_"))
        self.config_path = self.temp_dir / "test_config.json"
        self.packs_dir = self.temp_dir / "packs"
        self.packs_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """每个测试后清理临时目录"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_mock_pack(self, pack_name: str, version: str = "1.0.0", 
                         description: str = "", author: str = "") -> Path:
        """创建模拟Pack目录"""
        pack_dir = self.temp_dir / "mock_packs" / pack_name
        pack_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建manifest.json
        manifest = {
            "name": pack_name,
            "version": version,
            "description": description or f"Test pack {pack_name}",
            "author": author or "Test Author",
            "entry_point": "main.py",
            "dependencies": []
        }
        
        import json
        with open(pack_dir / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        
        # 创建main.py
        with open(pack_dir / "main.py", "w", encoding="utf-8") as f:
            f.write(f"# Pack {pack_name} v{version}\n")
        
        return pack_dir


@contextmanager
def isolated_config() -> Generator[Path, None, None]:
    """
    隔离配置上下文管理器
    用于确保测试不相互影响配置状态
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="moltcare_cfg_"))
    config_path = temp_dir / "config.json"
    
    # 重置单例
    from moltcare.src.config import ConfigManager
    ConfigManager._instance = None
    
    try:
        yield config_path
    finally:
        # 清理
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        ConfigManager._instance = None


@contextmanager
def isolated_pack_manager(packs_dir: Path = None) -> Generator[Path, None, None]:
    """
    隔离Pack管理器上下文管理器
    """
    temp_dir = packs_dir or Path(tempfile.mkdtemp(prefix="moltcare_pm_"))
    
    try:
        yield temp_dir
    finally:
        if packs_dir is None and temp_dir.exists():
            shutil.rmtree(temp_dir)
