"""
配置文件验证器 - 验证配置文件的正确性
"""

from pathlib import Path
from typing import Dict, List, Any


class ConfigValidator:
    """配置文件验证器"""

    def __init__(self, workspace: Path):
        self.workspace = workspace

        # 验证规则
        self.validation_rules = {
            'SOUL.md': self._validate_soul,
            'AGENTS.md': self._validate_agents,
            'IDENTITY.md': self._validate_identity,
            'MEMORY.md': self._validate_memory,
            'HEARTBEAT.md': self._validate_heartbeat,
            'TOOLS.md': self._validate_tools,
            'USER.md': self._validate_user
        }

    def validate_all(self) -> Dict[str, Any]:
        """验证所有配置文件"""
        errors = []
        warnings = []

        for filename, validator in self.validation_rules.items():
            filepath = self.workspace / filename

            if not filepath.exists():
                errors.append(f"❌ {filename}: 文件不存在")
                continue

            file_errors, file_warnings = validator(filepath)
            errors.extend([f"{filename}: {e}" for e in file_errors])
            warnings.extend([f"{filename}: {w}" for w in file_warnings])

        if warnings:
            print("⚠️ 警告:")
            for warning in warnings:
                print(f"  {warning}")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def _validate_file_basic(self, filepath: Path) -> tuple:
        """基础文件验证"""
        errors = []
        warnings = []

        if not filepath.exists():
            errors.append("文件不存在")
            return (errors, warnings)

        if filepath.stat().st_size == 0:
            errors.append("文件为空")

        if filepath.stat().st_size > 1024 * 1024:  # 1MB
            warnings.append("文件过大 (>1MB)")

        return (errors, warnings)

    def _validate_soul(self, filepath: Path) -> tuple:
        """验证 SOUL.md"""
        errors, warnings = self._validate_file_basic(filepath)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().lower()

            # 检查必需章节
            required_sections = ['原则', '核心', 'soul']
            for section in required_sections:
                if section not in content:
                    warnings.append(f"缺少 '{section}' 章节")

            # 检查原则数量
            if '原则' not in content:
                pass  # 已在上面检测
            elif 'absolute' in content or '绝对' in content:
                pass  # 有原则内容
            else:
                warnings.append("原则章节可能不完整")

        except Exception as e:
            errors.append(f"读取失败: {e}")

        return (errors, warnings)

    def _validate_agents(self, filepath: Path) -> tuple:
        """验证 AGENTS.md"""
        errors, warnings = self._validate_file_basic(filepath)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().lower()

            # 检查必需内容
            required_keywords = ['触发词', '工作流', 'agent']
            for keyword in required_keywords:
                if keyword not in content:
                    warnings.append(f"缺少 '{keyword}' 相关内容")

        except Exception as e:
            errors.append(f"读取失败: {e}")

        return (errors, warnings)

    def _validate_identity(self, filepath: Path) -> tuple:
        """验证 IDENTITY.md"""
        errors, warnings = self._validate_file_basic(filepath)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查是否为纯模板（默认值）
            template_indicators = [
                'Name:', '你的名字', 'your name',
                '待补充', 'TBD', 'placeholder',
                '默认', 'default'
            ]

            line_count = 0
            template_line_count = 0

            for line in content.split('\n'):
                line_count += 1
                if any(indicator in line.lower() for indicator in template_indicators):
                    template_line_count += 1

            if line_count > 0 and template_line_count / line_count > 0.3:
                warnings.append("可能使用默认模板（未个性化）")

            if line_count < 20:
                warnings.append("内容过少")

        except Exception as e:
            errors.append(f"读取失败: {e}")

        return (errors, warnings)

    def _validate_memory(self, filepath: Path) -> tuple:
        """验证 MEMORY.md"""
        errors, warnings = self._validate_file_basic(filepath)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().lower()

            # 检查基本结构
            if '状态' not in content and 'status' not in content:
                warnings.append("缺少状态信息")

        except Exception as e:
            errors.append(f"读取失败: {e}")

        return (errors, warnings)

    def _validate_heartbeat(self, filepath: Path) -> tuple:
        """验证 HEARTBEAT.md"""
        errors, warnings = self._validate_file_basic(filepath)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().lower()

            # 检查基本结构
            if '检查' not in content and 'check' not in content:
                warnings.append("缺少检查项")

        except Exception as e:
            errors.append(f"读取失败: {e}")

        return (errors, warnings)

    def _validate_tools(self, filepath: Path) -> tuple:
        """验证 TOOLS.md"""
        errors, warnings = self._validate_file_basic(filepath)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().lower()

            # 检查是否有API配置占位符
            if '待配置' in content or 'tbd' in content:
                warnings.append("存在未配置的工具")

        except Exception as e:
            errors.append(f"读取失败: {e}")

        return (errors, warnings)

    def _validate_user(self, filepath: Path) -> tuple:
        """验证 USER.md"""
        errors, warnings = self._validate_file_basic(filepath)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查是否为纯模板
            template_keywords = ['待补充', 'TBD', 'placeholder', '默认']

            line_count = 0
            template_line_count = 0

            for line in content.split('\n'):
                line_count += 1
                for keyword in template_keywords:
                    if keyword in line:
                        template_line_count += 1
                        break

            if line_count > 0 and template_line_count / line_count > 0.3:
                warnings.append("可能使用默认模板（未个性化）")

        except Exception as e:
            errors.append(f"读取失败: {e}")

        return (errors, warnings)
