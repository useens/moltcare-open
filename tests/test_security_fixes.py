"""
安全漏洞修复测试
验证 SEC-001 和 SEC-002 的修复是否有效
"""

import json
import os
import sys
import tempfile
import subprocess
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pack_manager import PackManager, PackManifest
from test_base import TestBase


class TestPathTraversalSecurity(TestBase):
    """测试路径遍历漏洞修复 (SEC-001)"""
    
    def setUp(self):
        super().setUp()
        self.pm = PackManager(str(self.packs_dir))
    
    def _create_malicious_pack(self, pack_dir, name):
        """创建带有恶意名称的pack"""
        pack_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "name": name,
            "version": "1.0.0",
            "description": "Test pack"
        }
        with open(pack_dir / "manifest.json", 'w') as f:
            json.dump(manifest, f)
        return pack_dir
    
    def test_sanitize_pack_name_empty(self):
        """测试空名称被拒绝"""
        is_valid, result = self.pm._sanitize_pack_name("")
        self.assertFalse(is_valid)
        self.assertIn("不能为空", result)
    
    def test_sanitize_pack_name_whitespace(self):
        """测试纯空白名称被拒绝"""
        is_valid, result = self.pm._sanitize_pack_name("   ")
        self.assertFalse(is_valid)
    
    def test_sanitize_pack_name_parent_directory(self):
        """测试包含 '..' 的名称被拒绝"""
        # 纯'..'名称
        is_valid, result = self.pm._sanitize_pack_name("..")
        self.assertFalse(is_valid)
        # 包含'..'但没有'/'的名称
        is_valid, result = self.pm._sanitize_pack_name("pack..name")
        self.assertFalse(is_valid)
    
    def test_sanitize_pack_name_forward_slash(self):
        """测试包含 '/' 的名称被拒绝"""
        is_valid, result = self.pm._sanitize_pack_name("path/to/pack")
        self.assertFalse(is_valid)
        self.assertIn("分隔符", result)
    
    def test_sanitize_pack_name_backslash(self):
        """测试包含 '\\' 的名称被拒绝"""
        is_valid, result = self.pm._sanitize_pack_name("path\\to\\pack")
        self.assertFalse(is_valid)
        self.assertIn("分隔符", result)
    
    def test_sanitize_pack_name_hidden_file(self):
        """测试以 '.' 开头的名称被拒绝"""
        is_valid, result = self.pm._sanitize_pack_name(".hidden")
        self.assertFalse(is_valid)
        self.assertIn(".", result)
    
    def test_sanitize_pack_name_control_chars(self):
        """测试包含控制字符的名称被拒绝"""
        is_valid, result = self.pm._sanitize_pack_name("pack\x00name")
        self.assertFalse(is_valid)
        self.assertIn("控制字符", result)
    
    def test_sanitize_pack_name_too_long(self):
        """测试超长名称被拒绝"""
        is_valid, result = self.pm._sanitize_pack_name("a" * 101)
        self.assertFalse(is_valid)
        self.assertIn("长度", result)
    
    def test_sanitize_pack_name_valid(self):
        """测试有效名称被接受"""
        is_valid, result = self.pm._sanitize_pack_name("valid-pack_name123")
        self.assertTrue(is_valid)
        self.assertEqual(result, "valid-pack_name123")
    
    def test_sanitize_pack_name_trimmed(self):
        """测试首尾空白被去除"""
        is_valid, result = self.pm._sanitize_pack_name("  valid-name  ")
        self.assertTrue(is_valid)
        self.assertEqual(result, "valid-name")
    
    def test_install_rejects_path_traversal_attack(self):
        """测试安装时拒绝路径遍历攻击"""
        malicious_names = [
            ("../../../etc/cron.d/backdoor", "slashes"),
            ("..\\..\\Windows\\System32\\malicious", "backslashes"),
            (".hidden", "hidden"),
            ("valid/../../../etc/passwd", "embedded_path"),
        ]
        
        for idx, (name, desc) in enumerate(malicious_names):
            with self.subTest(name=name, desc=desc):
                pack_dir = self.temp_dir / f"malicious_pack_{idx}"
                self._create_malicious_pack(pack_dir, name)
                success, msg = self.pm.install(str(pack_dir))
                self.assertFalse(success, f"恶意名称 '{name}' ({desc}) 应该被拒绝")
                
                # 确认没有文件被创建到不安全的位置
                etc_path = Path("/etc/cron.d/backdoor")
                if etc_path.exists():
                    self.fail(f"CRITICAL: 恶意文件被创建: {etc_path}")
    
    def test_install_accepts_valid_name(self):
        """测试正常名称可以被安装"""
        pack_dir = self.temp_dir / "valid_pack"
        self._create_malicious_pack(pack_dir, "valid-pack-name")
        success, msg = self.pm.install(str(pack_dir))
        self.assertTrue(success, f"有效pack应该被安装: {msg}")
        self.assertTrue(self.pm.is_installed("valid-pack-name"))


class TestApplyShSecurity(unittest.TestCase):
    """测试 apply.sh 路径遍历漏洞修复 (SEC-002)"""
    
    def setUp(self):
        self.apply_sh = Path("/root/.openclaw/workspace/moltcare/packs/foundation/scripts/apply.sh")
        self.assertTrue(self.apply_sh.exists(), "apply.sh 必须存在")
    
    def test_apply_sh_rejects_absolute_path(self):
        """测试 apply.sh 拒绝绝对路径"""
        result = subprocess.run(
            ["bash", str(self.apply_sh), "/etc"],
            capture_output=True,
            text=True,
            cwd="/root/.openclaw/workspace/moltcare"
        )
        # 应该返回错误 (非零退出码)
        self.assertNotEqual(result.returncode, 0, "绝对路径应该被拒绝")
        output = result.stderr + result.stdout
        self.assertTrue(
            "绝对路径" in output or "路径验证失败" in output or result.returncode != 0,
            f"应该显示绝对路径错误信息，输出: {output}"
        )
    
    def test_apply_sh_rejects_parent_directory(self):
        """测试 apply.sh 拒绝包含 '..' 的路径"""
        result = subprocess.run(
            ["bash", str(self.apply_sh), "../../etc"],
            capture_output=True,
            text=True,
            cwd="/root/.openclaw/workspace/moltcare"
        )
        # 应该返回错误
        self.assertNotEqual(result.returncode, 0, "包含'..'的路径应该被拒绝")
        output = result.stderr + result.stdout
        self.assertTrue(
            "'..'" in output or "路径验证失败" in output or result.returncode != 0,
            f"应该显示路径遍历错误信息，输出: {output}"
        )
    
    def test_apply_sh_rejects_tilde_path(self):
        """测试 apply.sh 拒绝以 '~' 开头的路径"""
        result = subprocess.run(
            ["bash", str(self.apply_sh), "~/etc"],
            capture_output=True,
            text=True,
            cwd="/root/.openclaw/workspace/moltcare"
        )
        # 应该返回错误
        self.assertNotEqual(result.returncode, 0, "以'~'开头的路径应该被拒绝")


if __name__ == "__main__":
    unittest.main()
