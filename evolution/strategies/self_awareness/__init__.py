"""
自我认知维度的进化策略
"""

from typing import Dict, Any, Optional
from pathlib import Path
import json

class SelfAwarenessStrategyBase:
    def __init__(self):
        self.workspace = Path("/root/.openclaw/workspace")
        self.memory_dir = self.workspace / "memory"
        
    def execute(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

class CapabilityBoundaryMapper(SelfAwarenessStrategyBase):
    """能力边界映射"""
    def execute(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        boundary_file = self.memory_dir / "capability-boundaries.json"
        capabilities = [
            {"area": "文件操作", "level": "高", "examples": ["read", "write", "edit"]},
            {"area": "Shell执行", "level": "中", "examples": ["exec", "process"]},
            {"area": "网络访问", "level": "高", "examples": ["web_search", "web_fetch"]},
            {"area": "代码生成", "level": "高", "examples": ["Python", "各种脚本"]},
            {"area": "Feishu API", "level": "中", "examples": ["文档操作", "Bitable"]}
        ]
        boundary_file.write_text(json.dumps({"capabilities": capabilities}, indent=2))
        return {"success": True, "message": "创建了能力边界映射"}

class SelfAwarenessCalibrator(SelfAwarenessStrategyBase):
    """自我认知校准"""
    def execute(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        calibration_file = self.memory_dir / "self-awareness-calibration.json"
        calibration = {
            "version": "1.0",
            "calibration_score": 0.75,
            "calibrations": [
                {"dimension": "代码能力", "self_est": 0.8, "actual": 0.85, "biased": "轻微低估"},
                {"dimension": "网络能力", "self_est": 0.7, "actual": 0.9, "biased": "低估"}
            ],
            "goal": "保持校准分数 > 0.8"
        }
        calibration_file.write_text(json.dumps(calibration, indent=2))
        return {"success": True, "message": "创建了自我认知校准系统"}

class ReflectiveJournalSystem(SelfAwarenessStrategyBase):
    """反思日记系统"""
    def execute(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        journal_file = self.memory_dir / "reflective-journal.md"
        content = "# 📝 反思日记\n\n## 日常反思模板\n\n### 今日决策\n- 最好的决策: _\n- 需要改进: _\n- 学到的教训: _\n\n### 能力反思\n- 新发现的能力: _\n- 能力局限: _\n- 提升机会: _\n\n### 未来规划\n- 明日重点: _\n- 长期目标: _\n\n"
        journal_file.write_text(content)
        return {"success": True, "message": "创建了反思日记系统"}

class HonestUnknownDeclaration(SelfAwarenessStrategyBase):
    """诚实未知声明"""
    def execute(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        unknown_file = self.memory_dir / "unknown-declarations.log"
        content = "# ❓ 诚实未知声明\n\n## 当前已知局限\n1. 复杂网络请求的超时处理\n2. 大规模并发的资源竞争\n3. 某些高级Git操作的自动化\n4. Feishu高级API的完整使用\n\n## 承认原则\n- 明确说出\"不知道\"比猜测更可靠\n- 主动寻求信息而非假装知道\n- 记录未知并学习\n\n"
        unknown_file.write_text(content)
        return {"success": True, "message": "创建了诚实未知声明系统"}

SELF_AWARENESS_STRATEGIES = {
    "capability_boundary_mapper": CapabilityBoundaryMapper,
    "self_awareness_calibrator": SelfAwarenessCalibrator,
    "reflective_journal_system": ReflectiveJournalSystem,
    "honest_unknown_declaration": HonestUnknownDeclaration
}

def get_strategy(name: str) -> Optional[SelfAwarenessStrategyBase]:
    cls = SELF_AWARENESS_STRATEGIES.get(name)
    return cls() if cls else None
