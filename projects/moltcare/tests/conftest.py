"""
pytest全局配置和fixtures
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock

# 添加项目源码到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def temp_workspace():
    """创建临时工作目录"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_workspace_with_files(tmp_path):
    """创建带有一些文件的模拟工作目录"""
    # 创建高质量SOUL.md
    soul_content = """
# 核心原则

## 绝对自主驱动
独立思考，自主决策

## 绝对进化闭环
学习-内化-应用

## 绝对诚实严谨
三次验证机制

## 绝对潜能释放
全力执行

## 绝对工具融合
工具是本能

## 绝对多维思辨
Multi-Agent

## 绝对使命必达
结果导向

## 核心身份
我是AI助手

## 行为准则
先执行，后汇报
"""
    (tmp_path / "SOUL.md").write_text(soul_content, encoding="utf-8")
    
    # 创建AGENTS.md
    agents_content = """
# 操作手册

## 触发词系统
- "记住这个"
- "多专家讨论"

## 工作流
1. 接收任务
2. 分析分解
3. 执行验证
4. 汇报完成

## 决策规则
自主决策范围：常规操作
需确认操作：高危操作
"""
    (tmp_path / "AGENTS.md").write_text(agents_content, encoding="utf-8")
    
    # 创建IDENTITY.md
    identity_content = """
# 身份档案

## 基本信息
名称：AI助手
版本：1.0

## 角色定位
执行用户指令
提供专业协助

## 性格特质
可靠、高效、专业、友好

## 能力范围
文件操作、代码开发、系统监控
"""
    (tmp_path / "IDENTITY.md").write_text(identity_content, encoding="utf-8")
    
    # 创建MEMORY.md
    memory_content = """
# 系统仪表盘

## 系统状态
运行正常

## 配置信息
版本：1.0
工具可用

## 记忆分类
长期记忆、短期记忆
"""
    (tmp_path / "MEMORY.md").write_text(memory_content, encoding="utf-8")
    
    # 创建HEARTBEAT.md
    heartbeat_content = """
# 心跳协议

## 检查项
- CPU使用率
- 内存使用
- 磁盘空间

## 维护计划
每日、每周、每月任务
"""
    (tmp_path / "HEARTBEAT.md").write_text(heartbeat_content, encoding="utf-8")
    
    # 创建TOOLS.md
    tools_content = """
# 工具配置

## 环境信息
Python 3.10
Linux系统

## 可用工具
read、write、exec

## API配置
已配置
"""
    (tmp_path / "TOOLS.md").write_text(tools_content, encoding="utf-8")
    
    # 创建USER.md
    user_content = """
# 用户档案

## 基本信息
时区：GMT+8
语言：中文

## 用户偏好
直接高效
重视结果
授权自主决策

## 注意事项
不喜欢冗余说明
"""
    (tmp_path / "USER.md").write_text(user_content, encoding="utf-8")
    
    return tmp_path


@pytest.fixture
def mock_workspace_poor_quality(tmp_path):
    """创建低质量文件的模拟工作目录"""
    poor_content = "# 标题\nTODO: 待补充\n[待填写]\n"
    
    for filename in ["SOUL.md", "AGENTS.md", "IDENTITY.md", "MEMORY.md", 
                     "HEARTBEAT.md", "TOOLS.md", "USER.md"]:
        (tmp_path / filename).write_text(poor_content, encoding="utf-8")
    
    return tmp_path


@pytest.fixture
def mock_diagnostic_report():
    """返回模拟的诊断报告"""
    return {
        "overall_score": 75,
        "issues": [
            {"file": "SOUL.md", "message": "内容可以更丰富", "level": "info"}
        ],
        "suggestions": ["建议优化SOUL.md"],
        "file_scores": {
            "SOUL.md": {"score": 80, "issues": []},
            "AGENTS.md": {"score": 75, "issues": []}
        }
    }


@pytest.fixture
def mock_validation_result():
    """返回模拟的验证结果"""
    return {
        "valid": True,
        "errors": [],
        "warnings": ["SOUL.md: 可以更丰富"]
    }


@pytest.fixture
def mock_args_factory():
    """返回模拟参数工厂"""
    def create_args(**kwargs):
        defaults = {
            "workspace": "~/.openclaw/workspace",
            "dry_run": False,
            "force": False
        }
        defaults.update(kwargs)
        return Mock(**defaults)
    return create_args


@pytest.fixture(scope="session")
def project_root():
    """返回项目根目录"""
    return Path(__file__).parent.parent


@pytest.fixture
def template_dir(tmp_path):
    """创建临时模板目录"""
    template_dir = tmp_path / "templates" / "core"
    template_dir.mkdir(parents=True)
    
    # 创建模板文件
    for filename in ["SOUL.md", "AGENTS.md", "IDENTITY.md", "MEMORY.md",
                     "HEARTBEAT.md", "TOOLS.md", "USER.md"]:
        (template_dir / filename).write_text(
            f"# 模板 {filename}\n高质量模板内容\n" * 20,
            encoding="utf-8"
        )
    
    return template_dir


# 测试标记
def pytest_configure(config):
    """配置pytest"""
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "slow: 慢速测试")
    config.addinivalue_line("markers", "cli: CLI相关测试")


# 自动标记测试
def pytest_collection_modifyitems(config, items):
    """自动为测试添加标记"""
    for item in items:
        # 根据路径自动添加标记
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # CLI测试
        if "cli" in str(item.fspath) or "test_cli" in str(item.nodeid):
            item.add_marker(pytest.mark.cli)
