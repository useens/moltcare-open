"""测试 Moltcare CLI."""

import pytest
from click.testing import CliRunner
from pathlib import Path
import tempfile
import shutil

from moltcare.cli import cli
from moltcare import __version__


@pytest.fixture
def runner():
    """创建 CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_dir():
    """创建临时目录."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


class TestCLI:
    """测试 CLI 主命令."""
    
    def test_version(self, runner):
        """测试版本显示."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output
    
    def test_help(self, runner):
        """测试帮助信息."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Moltcare" in result.output
        assert "init" in result.output
        assert "upgrade" in result.output
        assert "doctor" in result.output
        assert "backup" in result.output
        assert "restore" in result.output
    
    def test_no_args_shows_help(self, runner):
        """测试无参数显示帮助."""
        result = runner.invoke(cli)
        assert result.exit_code == 0
        assert "Moltcare" in result.output


class TestInitCommand:
    """测试 init 命令."""
    
    def test_init_help(self, runner):
        """测试 init 帮助."""
        result = runner.invoke(cli, ["init", "--help"])
        assert result.exit_code == 0
        assert "初始化" in result.output
    
    def test_init_non_interactive(self, runner, temp_dir):
        """测试非交互式初始化."""
        result = runner.invoke(cli, [
            "init",
            "--workspace", str(temp_dir),
            "--name", "TestAgent",
            "--description", "Test Description",
            "--non-interactive"
        ])
        assert result.exit_code == 0
        
        # 检查文件是否创建
        assert (temp_dir / "SOUL.md").exists()
        assert (temp_dir / "AGENTS.md").exists()
        assert (temp_dir / "IDENTITY.md").exists()
    
    def test_init_creates_directories(self, runner, temp_dir):
        """测试 init 创建目录."""
        result = runner.invoke(cli, [
            "init",
            "--workspace", str(temp_dir),
            "--non-interactive"
        ])
        assert result.exit_code == 0
        
        # 检查目录是否创建
        assert (temp_dir / "memory").exists()
        assert (temp_dir / "scripts").exists()


class TestDoctorCommand:
    """测试 doctor 命令."""
    
    def test_doctor_help(self, runner):
        """测试 doctor 帮助."""
        result = runner.invoke(cli, ["doctor", "--help"])
        assert result.exit_code == 0
        assert "诊断" in result.output
    
    def test_doctor_empty_workspace(self, runner, temp_dir):
        """测试诊断空工作目录."""
        result = runner.invoke(cli, [
            "doctor",
            "--workspace", str(temp_dir)
        ])
        assert result.exit_code == 0
        assert "诊断" in result.output


class TestBackupCommand:
    """测试 backup 命令."""
    
    def test_backup_help(self, runner):
        """测试 backup 帮助."""
        result = runner.invoke(cli, ["backup", "--help"])
        assert result.exit_code == 0
        assert "备份" in result.output
    
    def test_restore_help(self, runner):
        """测试 restore 帮助."""
        result = runner.invoke(cli, ["restore", "--help"])
        assert result.exit_code == 0
        assert "恢复" in result.output


class TestUtils:
    """测试工具函数."""
    
    def test_create_backup_id(self):
        """测试创建备份ID."""
        from moltcare.utils import create_backup_id
        backup_id = create_backup_id()
        assert backup_id.startswith("backup_")
        assert len(backup_id) > 15
    
    def test_format_timestamp(self):
        """测试格式化时间戳."""
        from moltcare.utils import format_timestamp
        result = format_timestamp("20240311_120000")
        assert "2024-03-11" in result
