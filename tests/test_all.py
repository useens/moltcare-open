#!/usr/bin/env python3
"""
MoltCare Test Suite - Standalone
不依赖包结构的独立测试
"""

import sys
import os
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from io import StringIO
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

# 将src目录添加到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# 直接导入要测试的模块
import config as config_module
import pack_manager as pm_module


# ==================== 配置系统测试 ====================

class TestMoltCareConfig(unittest.TestCase):
    """测试 MoltCareConfig 数据类"""
    
    def test_default_values(self):
        config = config_module.MoltCareConfig()
        self.assertEqual(config.version, "0.1.0")
        self.assertEqual(config.packs_dir, "./packs")
        self.assertEqual(config.log_level, "info")
        self.assertTrue(config.auto_update)
    
    def test_to_dict(self):
        config = config_module.MoltCareConfig(version="2.0.0")
        data = config.to_dict()
        self.assertEqual(data["version"], "2.0.0")
    
    def test_from_dict(self):
        data = {"version": "2.0.0", "log_level": "debug"}
        config = config_module.MoltCareConfig.from_dict(data)
        self.assertEqual(config.version, "2.0.0")


class TestConfigManager(unittest.TestCase):
    """测试 ConfigManager"""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_path = self.temp_dir / "config.json"
        config_module.ConfigManager._instance = None
    
    def tearDown(self):
        config_module.ConfigManager._instance = None
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_singleton(self):
        config1 = config_module.ConfigManager(str(self.config_path))
        config2 = config_module.ConfigManager(str(self.config_path))
        self.assertIs(config1, config2)
    
    def test_get_set(self):
        config = config_module.ConfigManager(str(self.config_path))
        config.set("log_level", "debug")
        self.assertEqual(config.get("log_level"), "debug")
    
    def test_save_and_load(self):
        config = config_module.ConfigManager(str(self.config_path))
        config.set("log_level", "error")
        
        config_module.ConfigManager._instance = None
        config2 = config_module.ConfigManager(str(self.config_path))
        self.assertEqual(config2.get("log_level"), "error")


# ==================== Pack管理器测试 ====================

class TestPackManifest(unittest.TestCase):
    """测试 PackManifest"""
    
    def test_default_values(self):
        manifest = pm_module.PackManifest(name="test", version="1.0.0")
        self.assertEqual(manifest.name, "test")
        self.assertEqual(manifest.entry_point, "main.py")
    
    def test_to_dict(self):
        manifest = pm_module.PackManifest(name="test", version="1.0.0", description="Desc")
        data = manifest.to_dict()
        self.assertEqual(data["description"], "Desc")


class TestPackManager(unittest.TestCase):
    """测试 PackManager"""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.packs_dir = self.temp_dir / "packs"
        self.pm = pm_module.PackManager(str(self.packs_dir))
    
    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_mock_pack(self, name: str, version: str = "1.0.0") -> Path:
        pack_dir = self.temp_dir / "mock" / name
        pack_dir.mkdir(parents=True)
        manifest = {
            "name": name,
            "version": version,
            "description": f"Test {name}",
            "author": "Test",
            "entry_point": "main.py",
            "dependencies": []
        }
        with open(pack_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)
        with open(pack_dir / "main.py", "w") as f:
            f.write(f"# {name}\n")
        return pack_dir
    
    def test_install_success(self):
        mock_pack = self.create_mock_pack("test-pack")
        success, msg = self.pm.install(str(mock_pack))
        self.assertTrue(success)
        self.assertTrue(self.pm.is_installed("test-pack"))
    
    def test_uninstall(self):
        mock_pack = self.create_mock_pack("test-pack")
        self.pm.install(str(mock_pack))
        success, msg = self.pm.uninstall("test-pack")
        self.assertTrue(success)
        self.assertFalse(self.pm.is_installed("test-pack"))
    
    def test_enable_disable(self):
        mock_pack = self.create_mock_pack("test-pack")
        self.pm.install(str(mock_pack))
        
        self.pm.disable("test-pack")
        self.assertFalse(self.pm.get_pack("test-pack").active)
        
        self.pm.enable("test-pack")
        self.assertTrue(self.pm.get_pack("test-pack").active)
    
    def test_list_packs(self):
        pack1 = self.create_mock_pack("pack-a")
        pack2 = self.create_mock_pack("pack-b")
        self.pm.install(str(pack1))
        self.pm.install(str(pack2))
        
        packs = self.pm.list_packs()
        self.assertEqual(len(packs), 2)


# ==================== 主运行器 ====================

def run_all_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestMoltCareConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigManager))
    suite.addTests(loader.loadTestsFromTestCase(TestPackManifest))
    suite.addTests(loader.loadTestsFromTestCase(TestPackManager))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("🧪 MoltCare 核心功能测试")
    print("=" * 40)
    success = run_all_tests()
    sys.exit(0 if success else 1)
