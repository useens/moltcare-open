"""
测试: CLI命令行接口
"""

import sys
from pathlib import Path
from io import StringIO
import unittest

sys.path.insert(0, str(Path(__file__).parent.parent))

from moltcare.src.cli import main, create_parser, cmd_status
from moltcare.src.config import ConfigManager
from tests.test_base import TestBase


class TestCLIParser(unittest.TestCase):
    """测试命令行解析"""
    
    def setUp(self):
        self.parser = create_parser()
    
    def test_parser_creation(self):
        """测试解析器创建"""
        self.assertIsNotNone(self.parser)
    
    def test_status_command(self):
        """测试status命令解析"""
        args = self.parser.parse_args(["status"])
        self.assertEqual(args.command, "status")
    
    def test_config_get(self):
        """测试config get命令"""
        args = self.parser.parse_args(["config", "get"])
        self.assertEqual(args.command, "config")
        self.assertEqual(args.action, "get")
    
    def test_config_set(self):
        """测试config set命令"""
        args = self.parser.parse_args(["config", "set", "log_level", "debug"])
        self.assertEqual(args.action, "set")
        self.assertEqual(args.key, "log_level")
        self.assertEqual(args.value, "debug")
    
    def test_pack_list(self):
        """测试pack list命令"""
        args = self.parser.parse_args(["pack", "list"])
        self.assertEqual(args.command, "pack")
        self.assertEqual(args.action, "list")
    
    def test_pack_install(self):
        """测试pack install命令"""
        args = self.parser.parse_args(["pack", "install", "./my-pack"])
        self.assertEqual(args.action, "install")
        self.assertEqual(args.source, "./my-pack")
    
    def test_pack_install_with_force(self):
        """测试pack install --force"""
        args = self.parser.parse_args(["pack", "install", "./pack", "--force"])
        self.assertTrue(args.force)


class TestCLICommands(TestBase):
    """测试CLI命令执行"""
    
    def setUp(self):
        super().setUp()
        ConfigManager._instance = None
        self.config_path = self.temp_dir / ".moltcare" / "config.json"
    
    def tearDown(self):
        super().tearDown()
        ConfigManager._instance = None
    
    def test_main_no_args(self):
        """测试无参数显示帮助"""
        # 应该返回0
        result = main([])
        self.assertEqual(result, 0)
    
    def test_status_command(self):
        """测试status命令"""
        # 捕获输出
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            result = main(["status"])
            self.assertEqual(result, 0)
            output = sys.stdout.getvalue()
            self.assertIn("MoltCare", output)
        finally:
            sys.stdout = old_stdout
    
    def test_config_path_command(self):
        """测试config path命令"""
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            result = main(["config", "path"])
            self.assertEqual(result, 0)
            output = sys.stdout.getvalue()
            self.assertIn("config.json", output)
        finally:
            sys.stdout = old_stdout
    
    def test_config_get_all(self):
        """测试config get (无key)"""
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            result = main(["config", "get"])
            self.assertEqual(result, 0)
            output = sys.stdout.getvalue()
            self.assertIn("version", output)
            self.assertIn("log_level", output)
        finally:
            sys.stdout = old_stdout


if __name__ == "__main__":
    unittest.main()
