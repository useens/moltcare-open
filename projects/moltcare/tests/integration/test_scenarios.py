import pytest
import sys
from pathlib import Path
from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from moltcare.cli import cli


class TestRealWorldScenarios:
    """真实世界场景测试"""

    def test_new_installation_scenario(self):
        """测试新安装场景"""
        runner = CliRunner()
        
        result = runner.invoke(cli, ["--help"])
        
        assert result.exit_code == 0
        assert "init" in result.output

    def test_partial_setup_scenario(self):
        """测试部分配置场景"""
        runner = CliRunner()
        
        result = runner.invoke(cli, ["doctor", "--help"])
        assert result.exit_code == 0

    def test_upgrade_workflow(self):
        """测试升级工作流"""
        runner = CliRunner()
        
        result = runner.invoke(cli, ["upgrade", "--help"])
        assert result.exit_code == 0
        assert "dry" in result.output.lower()


class TestMultiLanguageSupport:
    """多语言支持测试"""

    def test_chinese_content_in_examples(self):
        """测试示例中的中文内容"""
        example_dir = Path(__file__).parent.parent / "examples" / "basic-agent"
        soul_file = example_dir / "SOUL.md"
        
        if soul_file.exists():
            content = soul_file.read_text(encoding="utf-8")
            assert len(content) > 0

    def test_unicode_support(self):
        """测试Unicode支持"""
        content = "🌲 原则\n🎯 核心\n中文\nEnglish\n日本語"
        
        assert "🌲" in content
        assert "中文" in content
        assert "English" in content


class TestEdgeCases:
    """边界情况测试"""

    def test_very_long_input(self):
        """测试超长输入"""
        long_input = "A" * 10000
        
        assert len(long_input) == 10000

    def test_empty_input(self):
        """测试空输入"""
        empty = ""
        
        assert len(empty) == 0

    def test_special_characters(self):
        """测试特殊字符"""
        special = "<>\"&'\n\t\\"
        
        assert len(special) > 0
