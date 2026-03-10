"""
测试: 配置系统
"""

import json
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from moltcare.src.config import ConfigManager, MoltCareConfig, get_config
from tests.test_base import TestBase, isolated_config


class TestMoltCareConfig(unittest.TestCase):
    """测试 MoltCareConfig 数据类"""
    
    def test_default_values(self):
        """测试默认值"""
        config = MoltCareConfig()
        self.assertEqual(config.version, "0.1.0")
        self.assertEqual(config.packs_dir, "./packs")
        self.assertEqual(config.log_level, "info")
        self.assertTrue(config.auto_update)
        self.assertEqual(config.max_cache_size, 100)
    
    def test_to_dict(self):
        """测试转换为字典"""
        config = MoltCareConfig(version="2.0.0", log_level="debug")
        data = config.to_dict()
        self.assertEqual(data["version"], "2.0.0")
        self.assertEqual(data["log_level"], "debug")
    
    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "version": "2.0.0",
            "log_level": "debug",
            "packs_dir": "/custom/path",
            "auto_update": False,
            "max_cache_size": 200
        }
        config = MoltCareConfig.from_dict(data)
        self.assertEqual(config.version, "2.0.0")
        self.assertEqual(config.log_level, "debug")
        self.assertEqual(config.packs_dir, "/custom/path")
        self.assertFalse(config.auto_update)
        self.assertEqual(config.max_cache_size, 200)
    
    def test_from_dict_partial(self):
        """测试部分字典创建"""
        data = {"version": "2.0.0"}
        config = MoltCareConfig.from_dict(data)
        self.assertEqual(config.version, "2.0.0")
        # 其他字段使用默认值
        self.assertEqual(config.log_level, "info")


class TestConfigManager(TestBase):
    """测试 ConfigManager"""
    
    def setUp(self):
        super().setUp()
        # 重置单例
        ConfigManager._instance = None
    
    def tearDown(self):
        super().tearDown()
        # 重置单例
        ConfigManager._instance = None
    
    def test_singleton(self):
        """测试单例模式"""
        config1 = ConfigManager(str(self.config_path))
        config2 = ConfigManager(str(self.config_path))
        self.assertIs(config1, config2)
    
    def test_load_nonexistent(self):
        """测试加载不存在的配置"""
        config = ConfigManager(str(self.config_path))
        # 应该使用默认值，不报错
        self.assertEqual(config.get("version"), "0.1.0")
    
    def test_save_and_load(self):
        """测试保存和加载"""
        config = ConfigManager(str(self.config_path))
        config.set("log_level", "debug")
        
        # 重置单例，重新加载
        ConfigManager._instance = None
        config2 = ConfigManager(str(self.config_path))
        
        self.assertEqual(config2.get("log_level"), "debug")
    
    def test_get_set(self):
        """测试获取和设置"""
        config = ConfigManager(str(self.config_path))
        
        # 获取存在的值
        self.assertEqual(config.get("version"), "0.1.0")
        
        # 设置值
        self.assertTrue(config.set("log_level", "warning"))
        self.assertEqual(config.get("log_level"), "warning")
        
        # 获取不存在的值
        self.assertIsNone(config.get("nonexistent"))
        self.assertEqual(config.get("nonexistent", "default"), "default")
        
        # 设置不存在的键
        self.assertFalse(config.set("nonexistent", "value"))
    
    def test_reset(self):
        """测试重置"""
        config = ConfigManager(str(self.config_path))
        config.set("log_level", "error")
        config.set("auto_update", False)
        
        config.reset()
        
        self.assertEqual(config.get("log_level"), "info")
        self.assertTrue(config.get("auto_update"))
    
    def test_get_all(self):
        """测试获取所有配置"""
        config = ConfigManager(str(self.config_path))
        all_config = config.get_all()
        
        self.assertIn("version", all_config)
        self.assertIn("log_level", all_config)
        self.assertIn("packs_dir", all_config)
    
    def test_config_file_created(self):
        """测试配置文件被创建"""
        config = ConfigManager(str(self.config_path))
        config.save()
        
        self.assertTrue(self.config_path.exists())
        
        # 验证内容
        with open(self.config_path, "r") as f:
            data = json.load(f)
        
        self.assertIn("version", data)


class TestGetConfig(unittest.TestCase):
    """测试 get_config 辅助函数"""
    
    def setUp(self):
        ConfigManager._instance = None
    
    def tearDown(self):
        ConfigManager._instance = None
    
    def test_get_config_returns_manager(self):
        """测试 get_config 返回 ConfigManager"""
        config = get_config()
        self.assertIsInstance(config, ConfigManager)


if __name__ == "__main__":
    unittest.main()
