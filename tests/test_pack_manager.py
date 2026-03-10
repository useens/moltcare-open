"""
测试: Pack管理器
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from moltcare.src.pack_manager import PackManager, PackManifest, PackInfo, get_pack_manager
from tests.test_base import TestBase


class TestPackManifest(unittest.TestCase):
    """测试 PackManifest 数据类"""
    
    def test_default_values(self):
        """测试默认值"""
        manifest = PackManifest(name="test", version="1.0.0")
        self.assertEqual(manifest.name, "test")
        self.assertEqual(manifest.version, "1.0.0")
        self.assertEqual(manifest.description, "")
        self.assertEqual(manifest.author, "")
        self.assertEqual(manifest.dependencies, [])
        self.assertEqual(manifest.entry_point, "main.py")
    
    def test_post_init_dependencies(self):
        """测试依赖列表初始化"""
        manifest = PackManifest(name="test", version="1.0.0")
        self.assertEqual(manifest.dependencies, [])
    
    def test_to_dict(self):
        """测试转换为字典"""
        manifest = PackManifest(
            name="test",
            version="1.0.0",
            description="Test pack"
        )
        data = manifest.to_dict()
        self.assertEqual(data["name"], "test")
        self.assertEqual(data["description"], "Test pack")
    
    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "name": "test",
            "version": "2.0.0",
            "description": "Test",
            "author": "Author",
            "dependencies": ["dep1", "dep2"],
            "entry_point": "custom.py"
        }
        manifest = PackManifest.from_dict(data)
        self.assertEqual(manifest.name, "test")
        self.assertEqual(manifest.version, "2.0.0")
        self.assertEqual(manifest.dependencies, ["dep1", "dep2"])


class TestPackManager(TestBase):
    """测试 PackManager"""
    
    def setUp(self):
        super().setUp()
        self.pm = PackManager(str(self.packs_dir))
    
    def test_init_creates_directory(self):
        """测试初始化创建目录"""
        new_dir = self.temp_dir / "new_packs"
        self.assertFalse(new_dir.exists())
        pm = PackManager(str(new_dir))
        self.assertTrue(new_dir.exists())
    
    def test_install_success(self):
        """测试成功安装"""
        mock_pack = self.create_mock_pack("test-pack", "1.0.0")
        success, msg = self.pm.install(str(mock_pack))
        
        self.assertTrue(success)
        self.assertIn("安装成功", msg)
        self.assertTrue(self.pm.is_installed("test-pack"))
    
    def test_install_invalid_manifest(self):
        """测试无效manifest"""
        invalid_pack = self.temp_dir / "invalid_pack"
        invalid_pack.mkdir()
        # 不创建manifest.json
        
        success, msg = self.pm.install(str(invalid_pack))
        self.assertFalse(success)
        self.assertIn("manifest", msg)
    
    def test_install_already_installed(self):
        """测试重复安装"""
        mock_pack = self.create_mock_pack("test-pack", "1.0.0")
        self.pm.install(str(mock_pack))
        
        # 不强制重装
        success, msg = self.pm.install(str(mock_pack))
        self.assertFalse(success)
        self.assertIn("已安装", msg)
    
    def test_install_force_reinstall(self):
        """测试强制重装"""
        mock_pack = self.create_mock_pack("test-pack", "1.0.0")
        self.pm.install(str(mock_pack))
        
        # 更新版本
        mock_pack2 = self.create_mock_pack("test-pack", "2.0.0")
        success, msg = self.pm.install(str(mock_pack2), force=True)
        
        self.assertTrue(success)
        info = self.pm.get_pack("test-pack")
        self.assertEqual(info.version, "2.0.0")
    
    def test_uninstall_success(self):
        """测试成功卸载"""
        mock_pack = self.create_mock_pack("test-pack")
        self.pm.install(str(mock_pack))
        
        success, msg = self.pm.uninstall("test-pack")
        self.assertTrue(success)
        self.assertIn("已卸载", msg)
        self.assertFalse(self.pm.is_installed("test-pack"))
    
    def test_uninstall_not_installed(self):
        """测试卸载未安装的pack"""
        success, msg = self.pm.uninstall("nonexistent")
        self.assertFalse(success)
        self.assertIn("未安装", msg)
    
    def test_list_packs(self):
        """测试列出packs"""
        # 安装两个pack
        pack1 = self.create_mock_pack("pack-1", "1.0.0")
        pack2 = self.create_mock_pack("pack-2", "2.0.0")
        self.pm.install(str(pack1))
        self.pm.install(str(pack2))
        
        packs = self.pm.list_packs()
        self.assertEqual(len(packs), 2)
        self.assertEqual(packs[0].name, "pack-1")
        self.assertEqual(packs[1].name, "pack-2")
    
    def test_list_packs_sorted(self):
        """测试packs按名称排序"""
        pack_z = self.create_mock_pack("z-pack")
        pack_a = self.create_mock_pack("a-pack")
        pack_m = self.create_mock_pack("m-pack")
        
        self.pm.install(str(pack_z))
        self.pm.install(str(pack_a))
        self.pm.install(str(pack_m))
        
        packs = self.pm.list_packs()
        names = [p.name for p in packs]
        self.assertEqual(names, ["a-pack", "m-pack", "z-pack"])
    
    def test_enable_disable(self):
        """测试启用/禁用"""
        mock_pack = self.create_mock_pack("test-pack")
        self.pm.install(str(mock_pack))
        
        # 禁用
        success, msg = self.pm.disable("test-pack")
        self.assertTrue(success)
        info = self.pm.get_pack("test-pack")
        self.assertFalse(info.active)
        
        # 启用
        success, msg = self.pm.enable("test-pack")
        self.assertTrue(success)
        info = self.pm.get_pack("test-pack")
        self.assertTrue(info.active)
    
    def test_get_active_packs(self):
        """测试获取启用的packs"""
        pack1 = self.create_mock_pack("active-pack")
        pack2 = self.create_mock_pack("inactive-pack")
        self.pm.install(str(pack1))
        self.pm.install(str(pack2))
        
        self.pm.disable("inactive-pack")
        
        active = self.pm.get_active_packs()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].name, "active-pack")
    
    def test_index_persistence(self):
        """测试索引持久化"""
        mock_pack = self.create_mock_pack("persistent-pack", "1.0.0")
        self.pm.install(str(mock_pack))
        
        # 创建新的manager实例
        pm2 = PackManager(str(self.packs_dir))
        
        self.assertTrue(pm2.is_installed("persistent-pack"))
        info = pm2.get_pack("persistent-pack")
        self.assertEqual(info.version, "1.0.0")
    
    def test_list_show_inactive(self):
        """测试列出包含禁用的packs"""
        pack = self.create_mock_pack("test-pack")
        self.pm.install(str(pack))
        self.pm.disable("test-pack")
        
        # 默认不显示
        packs = self.pm.list_packs()
        self.assertEqual(len(packs), 0)
        
        # 显示所有
        packs = self.pm.list_packs(show_inactive=True)
        self.assertEqual(len(packs), 1)


import unittest
if __name__ == "__main__":
    unittest.main()
