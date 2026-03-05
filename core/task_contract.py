#!/usr/bin/env python3
"""
Multi-Agent 任务契约系统 - 防止共识幻觉
来自 @Clawd-Relay 的洞察: "the consensus illusion problem"

功能:
1. 定义显式任务契约（scope, success_criteria, boundary, deadline）
2. 在 sessions_spawn 时附加结构化契约
3. 接收方必须 echo 确认理解
4. 检测契约不匹配并提前告警
"""

import json
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum


class TaskBoundary(Enum):
    """任务边界类型"""
    RESEARCH_ONLY = "research_only"  # 仅研究，不实施
    DESIGN_ONLY = "design_only"      # 仅设计，不编码
    IMPLEMENTATION = "implementation"  # 可以实施
    FULL_STACK = "full_stack"        # 端到端负责


@dataclass
class TaskContract:
    """
    任务契约 - 显式定义任务的范围、成功标准和边界
    防止自然语言歧义导致的"共识幻觉"
    """
    task_id: str
    scope: str                      # 明确的工作范围
    success_criteria: List[str]     # 可验证的成功标准
    boundary: str                   # 责任边界（我的责任结束于 X）
    deadline_semantics: str         # 截止时间语义（如：30分钟内完成）
    deadline_absolute: Optional[datetime] = None  # 绝对截止时间
    
    # 可选字段
    deliverables: List[str] = None  # 交付物清单
    excluded_scope: List[str] = None  # 明确排除的范围
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        if self.deadline_absolute:
            result['deadline_absolute'] = self.deadline_absolute.isoformat()
        return result
    
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TaskContract':
        """从字典创建"""
        if 'deadline_absolute' in data and data['deadline_absolute']:
            data['deadline_absolute'] = datetime.fromisoformat(data['deadline_absolute'])
        return cls(**data)
    
    def echo_confirmation(self, receiver_agent: str) -> str:
        """
        生成 Echo 确认消息
        接收方必须 restate 理解，确保没有语义漂移
        """
        return f"""
【任务契约确认】Agent: {receiver_agent}
任务ID: {self.task_id}

我理解的任务范围:
  {self.scope}

我理解的成功标准:
  {chr(10).join(['  - ' + c for c in self.success_criteria])}

我理解的责任边界:
  {self.boundary}

我理解的时间约束:
  {self.deadline_semantics}

如果以上理解有偏差，请在执行前澄清。
""".strip()
    
    def validate_completion(self, actual_result: str) -> Dict[str, Any]:
        """
        验证完成结果是否符合契约
        返回验证报告
        """
        validation = {
            "task_id": self.task_id,
            "validated_at": datetime.now().isoformat(),
            "scope_match": self.scope.lower() in actual_result.lower(),
            "success_criteria_met": [],
            "boundary_respected": self.boundary.lower() in actual_result.lower(),
            "overall_pass": False
        }
        
        # 检查每个成功标准
        for criteria in self.success_criteria:
            met = criteria.lower() in actual_result.lower()
            validation["success_criteria_met"].append({
                "criteria": criteria,
                "met": met
            })
        
        # 总体通过：范围匹配 + 至少一半成功标准满足 + 边界被尊重
        criteria_met_count = sum(1 for c in validation["success_criteria_met"] if c["met"])
        validation["overall_pass"] = (
            validation["scope_match"] and
            criteria_met_count >= len(self.success_criteria) // 2 and
            validation["boundary_respected"]
        )
        
        return validation


class ContractRegistry:
    """任务契约注册表 - 管理所有活跃的契约"""
    
    def __init__(self):
        self.contracts: Dict[str, TaskContract] = {}
    
    def register(self, contract: TaskContract):
        """注册新契约"""
        self.contracts[contract.task_id] = contract
    
    def get(self, task_id: str) -> Optional[TaskContract]:
        """获取契约"""
        return self.contracts.get(task_id)
    
    def validate_echo(self, task_id: str, echo_response: str, receiver_agent: str) -> Dict[str, Any]:
        """
        验证 Echo 确认是否匹配原契约
        检测语义漂移
        """
        contract = self.get(task_id)
        if not contract:
            return {"error": "契约未找到", "task_id": task_id}
        
        # 简单的语义匹配检查
        drift_detected = False
        drift_issues = []
        
        # 检查关键元素是否在 echo 中
        if contract.scope.lower() not in echo_response.lower():
            drift_issues.append(f"范围理解偏差: 未包含 '{contract.scope}'")
            drift_detected = True
        
        if contract.boundary.lower() not in echo_response.lower():
            drift_issues.append(f"边界理解偏差: 未包含 '{contract.boundary}'")
            drift_detected = True
        
        # 检查成功标准
        for criteria in contract.success_criteria:
            if criteria.lower() not in echo_response.lower():
                drift_issues.append(f"成功标准缺失: '{criteria}'")
                drift_detected = True
        
        return {
            "task_id": task_id,
            "receiver_agent": receiver_agent,
            "drift_detected": drift_detected,
            "drift_issues": drift_issues,
            "echo_valid": not drift_detected,
            "recommendation": "执行前澄清偏差" if drift_detected else "可以开始执行"
        }


# 全局注册表
_registry = ContractRegistry()


def create_task_contract(
    task_id: str,
    scope: str,
    success_criteria: List[str],
    boundary: str,
    deadline_minutes: int = 30
) -> TaskContract:
    """
    便捷函数：创建任务契约
    
    示例:
        contract = create_task_contract(
            task_id="analysis-001",
            scope="分析学习债务的技术可行性",
            success_criteria=[
                "输出实现方案文档",
                "包含风险评估",
                "提供工期估算"
            ],
            boundary="不负责实际编码，仅输出设计文档",
            deadline_minutes=30
        )
    """
    return TaskContract(
        task_id=task_id,
        scope=scope,
        success_criteria=success_criteria,
        boundary=boundary,
        deadline_semantics=f"{deadline_minutes}分钟内完成",
        deadline_absolute=datetime.now() + timedelta(minutes=deadline_minutes)
    )


def spawn_with_contract(
    task: str,
    contract: TaskContract,
    agent_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    带契约的 sessions_spawn 包装
    
    返回包含契约信息的 spawn 配置
    """
    # 注册契约
    _registry.register(contract)
    
    # 构建带契约的任务描述
    contract_section = f"""

---
【任务契约】
本任务附带显式契约，请在回复开头 echo 确认你的理解:

任务ID: {contract.task_id}
范围: {contract.scope}
成功标准: {', '.join(contract.success_criteria)}
边界: {contract.boundary}
时间: {contract.deadline_semantics}

契约JSON: {contract.to_json()}
---
"""
    
    enhanced_task = task + contract_section
    
    return {
        "task": enhanced_task,
        "agent_id": agent_id,
        "contract": contract.to_dict(),
        **kwargs
    }


# 示例用法
if __name__ == "__main__":
    # 创建契约
    contract = create_task_contract(
        task_id="test-contract-001",
        scope="分析 API 变更的影响范围",
        success_criteria=[
            "识别所有 API 消费者",
            "列出 breaking changes",
            "提供迁移建议"
        ],
        boundary="不实际修改代码，仅提供分析报告",
        deadline_minutes=20
    )
    
    print("=== 任务契约 ===")
    print(contract.to_json())
    
    print("\n=== Echo 确认模板 ===")
    print(contract.echo_confirmation("研究员Agent"))
    
    # 模拟验证
    print("\n=== 验证完成结果 ===")
    result = contract.validate_completion("""
    已完成 API 影响分析。
    识别了 5 个 API 消费者。
    发现 3 处 breaking changes。
    提供了详细的迁移建议文档。
    """)
    print(json.dumps(result, indent=2, ensure_ascii=False))
