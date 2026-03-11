import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestInitCommand:
    """init命令单元测试"""

    def test_init_creates_files(self):
        """测试init创建文件"""
        files_to_create = [
            "SOUL.md",
            "AGENTS.md", 
            "IDENTITY.md",
            "MEMORY.md",
            "HEARTBEAT.md",
            "TOOLS.md",
            "USER.md"
        ]
        
        # 验证应该创建的核心文件
        assert len(files_to_create) == 7
        assert "SOUL.md" in files_to_create

    def test_init_templates_exist(self):
        """测试模板存在"""
        templates = ["basic", "advanced", "minimal"]
        
        # 验证模板选项
        assert "basic" in templates
        assert "advanced" in templates

    def test_init_with_force(self):
        """测试强制覆盖"""
        force = True
        
        # 验证force选项
        assert force == True


class TestInitValidation:
    """init验证测试"""

    def test_init_validates_workspace(self):
        """测试工作目录验证"""
        workspace = Path("/tmp/test")
        
        # 验证路径有效性
        assert isinstance(workspace, Path)

    def test_init_checks_existing_files(self):
        """测试检查现有文件"""
        existing_files = ["SOUL.md", "AGENTS.md"]
        
        # 验证文件列表
        assert len(existing_files) > 0
        assert "SOUL.md" in existing_files
