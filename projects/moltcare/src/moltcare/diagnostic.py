"""
诊断引擎 - 评估配置文件质量
"""

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

# 质量评分规则
QUALITY_RULES = {
    'SOUL.md': {
        'min_lines': 50,
        'required_sections': [
            '原则',
            '核心',
            '身份',
            'SOUL'
        ],
        'weight': 0.2  # 权重 20%
    },
    'AGENTS.md': {
        'min_lines': 30,
        'required_sections': [
            '操作手册',
            '触发词',
            '工作流'
        ],
        'weight': 0.15
    },
    'IDENTITY.md': {
        'min_lines': 30,
        'required_sections': [
            '身份',
            '定位',
            '角色'
        ],
        'weight': 0.15
    },
    'MEMORY.md': {
        'min_lines': 20,
        'required_sections': [
            '仪表盘',
            '系统',
            '状态'
        ],
        'weight': 0.1
    },
    'HEARTBEAT.md': {
        'min_lines': 15,
        'required_sections': [
            '心跳',
            '检查'
        ],
        'weight': 0.1
    },
    'TOOLS.md': {
        'min_lines': 10,
        'required_sections': [
            '工具',
            '环境'
        ],
        'weight': 0.1
    },
    'USER.md': {
        'min_lines': 15,
        'required_sections': [
            '用户',
            '档案',
            '偏好'
        ],
        'weight': 0.2
    }
}

# 常见问题模式
COMMON_ISSUES = [
    {
        'pattern': ['TODO', '待补充', 'TBD', '[', 'placeholder'],
        'message': '包含待补充内容占位符',
        'level': 'warning'
    },
    {
        'pattern': ['test', 'example', 'demo'],
        'message': '包含示例/测试内容（未实际配置）',
        'level': 'warning'
    },
    {
        'pattern': ['default', '模板', 'template'],
        'message': '可能使用默认模板（未个性化）',
        'level': 'info'
    }
]


class DiagnosticEngine:
    """诊断引擎"""

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.results = {}

    def run_diagnostic(self) -> Dict[str, Any]:
        """运行完整诊断"""
        overall_score = 0
        issues = []
        suggestions = []

        for filename in CORE_FILES:
            filepath = self.workspace / filename

            if not filepath.exists():
                issues.append({
                    'file': filename,
                    'message': '文件不存在',
                    'level': 'error'
                })
                overall_score += 0
                continue

            # 评估单个文件
            file_score, file_issues, file_suggestions = self._evaluate_file(filepath, filename)

            overall_score += file_score * QUALITY_RULES[filename]['weight']
            issues.extend(file_issues)
            suggestions.extend(file_suggestions)

            self.results[filename] = {
                'score': file_score,
                'issues': file_issues
            }

        # 四舍五入到整数
        overall_score = round(overall_score)

        # 生成建议
        if overall_score < 60:
            suggestions.append("建议运行 `moltcare upgrade` 提升配置质量")
        elif overall_score < 80:
            suggestions.append("配置质量良好，可运行 `moltcare upgrade` 进一步优化")

        return {
            'overall_score': overall_score,
            'issues': issues,
            'suggestions': list(set(suggestions)),  # 去重
            'file_scores': self.results
        }

    def _evaluate_file(self, filepath: Path, filename: str) -> tuple:
        """评估单个文件"""
        rules = QUALITY_RULES.get(filename, {})
        issues = []
        suggestions = []

        # 读取文件
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            return (0, [{'file': filename, 'message': f'读取失败: {e}', 'level': 'error'}], [])

        # 检查文件行数
        if len(lines) < rules.get('min_lines', 10):
            issues.append({
                'file': filename,
                'message': f"内容过少 ({len(lines)}/{rules.get('min_lines', 10)} 行)",
                'level': 'warning'
            })

        # 检查必需章节
        required_sections = rules.get('required_sections', [])
        missing_sections = []
        for section in required_sections:
            if section.lower() not in content.lower():
                missing_sections.append(section)

        if missing_sections:
            issues.append({
                'file': filename,
                'message': f"缺少关键章节: {', '.join(missing_sections)}",
                'level': 'warning'
            })

        # 检查常见问题
        for issue_pattern in COMMON_ISSUES:
            for pattern in issue_pattern['pattern']:
                if pattern in content:
                    issues.append({
                        'file': filename,
                        'message': issue_pattern['message'],
                        'level': issue_pattern['level']
                    })
                    break

        # 计算分数
        score = 100
        score -= len(issues) * 10  # 每个问题扣10分
        score -= len(missing_sections) * 15  # 缺失章节更重要
        score = max(0, min(100, score))  # 限制在 0-100 之间

        # 基本完成度分数
        if len(lines) >= rules.get('min_lines', 10):
            score += 5  # 达到最低行数奖励

        return (score, issues, suggestions)
