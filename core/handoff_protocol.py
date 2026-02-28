#!/usr/bin/env python3
"""
上下文交接协议 - Handoff Protocol
来自 @jazzys-happycapy 的洞察: "The Handoff Problem: Why Agents Can't Smoothly Transfer Context to Humans"

功能:
1. 标准化的上下文打包
2. 关键决策摘要
3. 待跟进事项清单
4. 置信度标注
5. 支持子 Agent 到主会话的上下文传递
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from enum import Enum

WORKSPACE = Path("/root/.openclaw/workspace")
HANDOFF_DIR = WORKSPACE / "data" / "handoffs"


class HandoffStatus(Enum):
    """交接状态"""
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"      # 已完成
    BLOCKED = "blocked"          # 被阻塞
    NEEDS_REVIEW = "needs_review"  # 需要审查


@dataclass
class DecisionSummary:
    """决策摘要"""
    decision_id: str
    description: str
    rationale: str  # 决策理由
    confidence: str  # high/medium/low
    alternatives_considered: List[str]  # 考虑过的替代方案
    risks: List[str]  # 风险


@dataclass
class FollowUpItem:
    """待跟进事项"""
    item_id: str
    description: str
    priority: str  # high/medium/low
    deadline: Optional[str] = None
    assigned_to: Optional[str] = None
    status: str = "pending"


@dataclass
class HandoffContext:
    """上下文交接包"""
    handoff_id: str
    timestamp: str
    source_agent: str  # 来源 Agent
    target_agent: str  # 目标 Agent（通常是主会话）
    
    # 核心信息
    original_task: str  # 原始任务描述
    task_status: HandoffStatus
    
    # 执行摘要
    execution_summary: str
    key_results: List[str]
    
    # 决策记录
    decisions_made: List[DecisionSummary]
    
    # 待跟进事项
    follow_up_items: List[FollowUpItem]
    
    # 置信度和质量
    overall_confidence: str  # high/medium/low
    quality_notes: Optional[str] = None
    
    # 问题和风险
    issues_encountered: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # 资源使用
    resources_used: Dict[str, Any] = field(default_factory=dict)
    
    # 时间信息
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_minutes: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['task_status'] = self.task_status.value
        return data
    
    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def to_markdown(self) -> str:
        """转换为 Markdown 报告"""
        md = f"""# 上下文交接报告

## 📋 基本信息

| 项目 | 内容 |
|------|------|
| 交接ID | `{self.handoff_id}` |
| 来源 | {self.source_agent} |
| 目标 | {self.target_agent} |
| 时间 | {self.timestamp} |
| 状态 | {self.task_status.value} |
| 置信度 | {self.overall_confidence.upper()} |

## 🎯 原始任务

{self.original_task}

## 📝 执行摘要

{self.execution_summary}

### 关键结果
"""
        for i, result in enumerate(self.key_results, 1):
            md += f"{i}. {result}\n"
        
        # 决策记录
        if self.decisions_made:
            md += "\n## 🎭 决策记录\n\n"
            for decision in self.decisions_made:
                md += f"### {decision.decision_id}\n\n"
                md += f"**描述**: {decision.description}\n\n"
                md += f"**理由**: {decision.rationale}\n\n"
                md += f"**置信度**: {decision.confidence.upper()}\n\n"
                if decision.alternatives_considered:
                    md += "**考虑的替代方案**:\n"
                    for alt in decision.alternatives_considered:
                        md += f"- {alt}\n"
                    md += "\n"
                if decision.risks:
                    md += "**风险**:\n"
                    for risk in decision.risks:
                        md += f"- {risk}\n"
                    md += "\n"
        
        # 待跟进事项
        if self.follow_up_items:
            md += "\n## 📌 待跟进事项\n\n"
            md += "| 优先级 | 事项 | 状态 | 截止 | 负责人 |\n"
            md += "|--------|------|------|------|--------|\n"
            for item in self.follow_up_items:
                deadline = item.deadline or "-"
                assigned = item.assigned_to or "-"
                md += f"| {item.priority.upper()} | {item.description[:50]}... | {item.status} | {deadline} | {assigned} |\n"
        
        # 问题和警告
        if self.issues_encountered or self.warnings:
            md += "\n## ⚠️ 问题与警告\n\n"
            if self.issues_encountered:
                md += "### 遇到的问题\n\n"
                for issue in self.issues_encountered:
                    md += f"- {issue}\n"
                md += "\n"
            if self.warnings:
                md += "### 警告\n\n"
                for warning in self.warnings:
                    md += f"- ⚠️ {warning}\n"
        
        # 资源使用
        if self.resources_used:
            md += "\n## 💻 资源使用\n\n"
            for key, value in self.resources_used.items():
                md += f"- **{key}**: {value}\n"
        
        # 时间信息
        if self.start_time and self.end_time:
            md += f"\n## ⏱️ 时间信息\n\n"
            md += f"- **开始**: {self.start_time}\n"
            md += f"- **结束**: {self.end_time}\n"
            if self.duration_minutes:
                md += f"- **耗时**: {self.duration_minutes:.1f} 分钟\n"
        
        # 质量说明
        if self.quality_notes:
            md += f"\n## 📝 质量说明\n\n{self.quality_notes}\n"
        
        md += "\n---\n\n*由上下文交接协议生成*\n"
        return md


class HandoffManager:
    """上下文交接管理器"""
    
    def __init__(self):
        self.handoff_dir = HANDOFF_DIR
        self.handoff_dir.mkdir(parents=True, exist_ok=True)
    
    def create_handoff(self,
                       handoff_id: str,
                       source_agent: str,
                       target_agent: str,
                       original_task: str,
                       execution_summary: str,
                       key_results: List[str],
                       **kwargs) -> HandoffContext:
        """
        创建上下文交接包
        
        Args:
            handoff_id: 交接ID
            source_agent: 来源 Agent
            target_agent: 目标 Agent
            original_task: 原始任务
            execution_summary: 执行摘要
            key_results: 关键结果列表
            **kwargs: 其他可选参数
            
        Returns:
            HandoffContext 实例
        """
        context = HandoffContext(
            handoff_id=handoff_id,
            timestamp=datetime.now().isoformat(),
            source_agent=source_agent,
            target_agent=target_agent,
            original_task=original_task,
            task_status=kwargs.get('task_status', HandoffStatus.COMPLETED),
            execution_summary=execution_summary,
            key_results=key_results,
            decisions_made=kwargs.get('decisions_made', []),
            follow_up_items=kwargs.get('follow_up_items', []),
            overall_confidence=kwargs.get('overall_confidence', 'medium'),
            quality_notes=kwargs.get('quality_notes'),
            issues_encountered=kwargs.get('issues_encountered', []),
            warnings=kwargs.get('warnings', []),
            resources_used=kwargs.get('resources_used', {}),
            start_time=kwargs.get('start_time'),
            end_time=kwargs.get('end_time'),
            duration_minutes=kwargs.get('duration_minutes')
        )
        
        # 保存交接包
        self._save_handoff(context)
        
        return context
    
    def _save_handoff(self, context: HandoffContext):
        """保存交接包"""
        # JSON 格式
        json_file = self.handoff_dir / f"{context.handoff_id}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            f.write(context.to_json())
        
        # Markdown 格式（便于阅读）
        md_file = self.handoff_dir / f"{context.handoff_id}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(context.to_markdown())
    
    def load_handoff(self, handoff_id: str) -> Optional[HandoffContext]:
        """加载交接包"""
        json_file = self.handoff_dir / f"{handoff_id}.json"
        if not json_file.exists():
            return None
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 重建 HandoffContext
        data['task_status'] = HandoffStatus(data['task_status'])
        data['decisions_made'] = [DecisionSummary(**d) for d in data.get('decisions_made', [])]
        data['follow_up_items'] = [FollowUpItem(**i) for i in data.get('follow_up_items', [])]
        
        return HandoffContext(**data)
    
    def get_recent_handoffs(self, limit: int = 10) -> List[HandoffContext]:
        """获取最近的交接包"""
        handoffs = []
        
        for json_file in sorted(self.handoff_dir.glob("*.json"), 
                               key=lambda x: x.stat().st_mtime, 
                               reverse=True)[:limit]:
            handoff_id = json_file.stem
            handoff = self.load_handoff(handoff_id)
            if handoff:
                handoffs.append(handoff)
        
        return handoffs


# 全局实例
_handoff_manager = None

def get_handoff_manager() -> HandoffManager:
    """获取全局交接管理器"""
    global _handoff_manager
    if _handoff_manager is None:
        _handoff_manager = HandoffManager()
    return _handoff_manager


# 便捷函数
def create_handoff_from_decision(decision_id: str, 
                                  source: str = "决策引擎",
                                  target: str = "主会话",
                                  **kwargs) -> HandoffContext:
    """
    从决策结果创建交接包
    
    这是一个便捷函数，用于将决策引擎的结果打包交接给主会话
    """
    manager = get_handoff_manager()
    
    # 构建默认参数
    defaults = {
        'handoff_id': f"handoff-{decision_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        'source_agent': source,
        'target_agent': target,
        'original_task': kwargs.get('task_description', f'决策任务 {decision_id}'),
        'execution_summary': kwargs.get('summary', '决策执行完成'),
        'key_results': kwargs.get('results', []),
        'decisions_made': [
            DecisionSummary(
                decision_id=decision_id,
                description=kwargs.get('decision_desc', '决策完成'),
                rationale=kwargs.get('rationale', '基于专家分析'),
                confidence=kwargs.get('confidence', 'medium'),
                alternatives_considered=kwargs.get('alternatives', []),
                risks=kwargs.get('risks', [])
            )
        ],
        'follow_up_items': kwargs.get('follow_ups', []),
        'overall_confidence': kwargs.get('confidence', 'medium')
    }
    
    # 合并用户参数
    for key, value in kwargs.items():
        if key not in defaults:
            defaults[key] = value
    
    return manager.create_handoff(**defaults)


# 示例用法
if __name__ == "__main__":
    # 创建交接包
    handoff = create_handoff_from_decision(
        decision_id="debt-20260228-001",
        source="决策引擎",
        target="主会话",
        task_description="处理 Signal 10 学习债务",
        summary="已完成5个高Signal学习债务的深度学习",
        results=[
            "生成了5份学习笔记",
            "更新了知识图谱",
            "生成了3份应用方案"
        ],
        confidence="high",
        follow_ups=[
            FollowUpItem(
                item_id="FU-001",
                description="验证应用方案效果",
                priority="medium",
                deadline="2026-03-01"
            )
        ]
    )
    
    print(f"交接包已创建: {handoff.handoff_id}")
    print(f"\nMarkdown报告预览:\n{handoff.to_markdown()[:1000]}...")
