"""
智能合并器 - 保留用户个性化，替换标准模板
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


CORE_FILES = [
    'SOUL.md',
    'AGENTS.md',
    'IDENTITY.md',
    'MEMORY.md',
    'HEARTBEAT.md',
    'TOOLS.md',
    'USER.md'
]


class SmartMerger:
    """智能合并器"""

    def __init__(self, workspace: Path, template_dir: Path = None, dry_run: bool = False):
        self.workspace = workspace
        self.template_dir = template_dir or Path(__file__).parent.parent.parent / 'templates' / 'core'
        self.dry_run = dry_run
        self.backup_root = workspace / '.openclaw' / 'backups' / 'moltcare'

    def merge_templates(self, diagnostic_report: Dict[str, Any]) -> Dict[str, Any]:
        """合并模板"""
        # 创建备份目录
        backup_path = self._create_backup()
        processed_files = []

        for filename in CORE_FILES:
            filepath = self.workspace / filename
            template_path = self.template_dir / filename

            if not template_path.exists():
                continue

            if not filepath.exists():
                # 文件不存在，直接复制模板
                changes = self._copy_template(template_path, filepath, backup_path)
                processed_files.append({
                    'file': filename,
                    'changes': changes,
                    'action': 'created'
                })
            else:
                # 文件已存在，智能合并
                changes = self._smart_merge(template_path, filepath, backup_path / filename)
                processed_files.append({
                    'file': filename,
                    'changes': changes,
                    'action': 'merged'
                })

        return {
            'backup_path': str(backup_path),
            'processed_files': processed_files,
            'dry_run': self.dry_run
        }

    def _create_backup(self) -> Path:
        """创建备份目录"""
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        backup_path = self.backup_root / timestamp

        if not self.dry_run:
            backup_path.mkdir(parents=True, exist_ok=True)

        return backup_path

    def _copy_template(self, template_path: Path, target_path: Path, backup_path: Path) -> int:
        """直接复制模板"""
        if not self.dry_run:
            shutil.copy2(template_path, target_path)

        return 1  # 复制了1处

    def _smart_merge(self, template_path: Path, target_path: Path, backup_backup_path: Path) -> int:
        """智能合并"""
        # 读取源文件
        with open(target_path, 'r', encoding='utf-8') as f:
            user_content = f.read()

        # 读取模板
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # 备份原文件
        if not self.dry_run:
            backup_backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target_path, backup_backup_path)

        # 简单策略：如果用户文件明显较差，直接替换
        # 识别"明显较差"的标准：
        # 1. 文件小于10行
        # 2. 包含大量占位符
        # 3. 标题全是默认模板的

        user_lines = user_content.split('\n')

        # 检测是否需要直接替换
        if self._should_replace(user_content):
            if not self.dry_run:
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(template_content)
            return 1
        else:
            # 用户文件有一定质量，尝试智能合并
            merged_content = self._merge_content(user_content, template_content)

            if not self.dry_run:
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(merged_content)

            return self._count_changes(user_content, merged_content)

    def _should_replace(self, user_content: str) -> bool:
        """判断是否应该直接替换"""
        lines = user_content.split('\n')

        # 文件太短
        if len(lines) < 10:
            return True

        # 检测占位符
        placeholder_keywords = [
            '[待补充]', '[TODO]', '[', 'placeholder',
            '你的名字', 'your name', '填写',
            '# 标题', '# Title', 'template', '示例'
        ]

        placeholder_count = sum(1 for line in lines
                               for keyword in placeholder_keywords
                               if keyword.lower() in line.lower())

        # 占位符超过30%内容
        if placeholder_count > len(lines) * 0.3:
            return True

        return False

    def _merge_content(self, user_content: str, template_content: str) -> str:
        """合并内容（简化版）"""
        # 策略：保留用户自定义部分，使用模板结构
        # 这是简化实现，实际可以更智能

        # 识别用户自定义的标题和内容块
        user_lines = user_content.split('\n')
        template_lines = template_content.split('\n')

        # 简单策略：使用模板，但在适当位置插入用户自定义内容
        # 识别以 "###" 开头的标题为自定义内容
        user_custom_sections = []
        current_section = None
        current_lines = []

        for line in user_lines:
            if line.startswith('### ') or line.startswith('## '):
                if current_section:
                    user_custom_sections.append((current_section, current_lines))
                current_section = line
                current_lines = [line]
            else:
                if current_section:
                    current_lines.append(line)
                else:
                    pass  # 忽略未开始的内容

        if current_section:
            user_custom_sections.append((current_section, current_lines))

        # 如果用户有自定义章节，保留它们
        if user_custom_sections:
            return template_content + "\n\n" + "# 用户自定义内容（保留）\n\n" + \
                   '\n\n'.join(['\n'.join(lines) for _, lines in user_custom_sections])
        else:
            return template_content

    def _count_changes(self, old_content: str, new_content: str) -> int:
        """粗略计算变更数量"""
        if not self.dry_run:
            # 实际对比
            old_lines = set(old_content.split('\n'))
            new_lines = set(new_content.split('\n'))
            return len(new_lines - old_lines)
        else:
            # Dry run 时估算
            return len(new_content.split('\n')) // 10
