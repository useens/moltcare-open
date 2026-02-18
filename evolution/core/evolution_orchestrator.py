#!/usr/bin/env python3
"""
进化编排器 - 协调评估、决策、执行流程
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from .dimension_assessor import DimensionAssessor
from . import state, event_bus, Event

class EvolutionOrchestrator:
    """进化编排器"""
    
    def __init__(self):
        self.assessor = DimensionAssessor()
        self.state = state
        
    def run_full_cycle(self, dry_run: bool = False) -> Dict:
        """运行完整进化周期
        
        Returns:
            {
                "success": bool,
                "dimension_scores": {...},
                "evolution_decisions": [...],
                "executed_strategies": [...]
            }
        """
        print("🚀 开始完整进化周期...")
        
        # 1. 评估所有维度
        print("\n1️⃣ 评估十维状态...")
        dimension_data = self._collect_dimension_data()
        scores = self.assessor.assess_all(dimension_data)
        
        # 2. 打印当前状态
        self.assessor.print_status()
        
        # 3. 检测需要进化的维度
        critical_dimensions = self.assessor.get_critical_dimensions(40.0)
        
        if not critical_dimensions:
            print("\n✅ 所有维度状态良好，无需进化")
            return {
                "success": True,
                "dimension_scores": self._format_scores(scores),
                "evolution_decisions": [],
                "executed_strategies": [],
                "message": "所有维度健康"
            }
        
        print(f"\n2️⃣ 检测到 {len(critical_dimensions)} 个需要进化的维度")
        
        # 4. 为每个临界维度选择策略
        evolution_decisions = []
        for dim_id in critical_dimensions:
            decision = self._select_evolution_strategy(dim_id, dimension_data[dim_id])
            if decision:
                evolution_decisions.append(decision)
        
        # 5. 执行策略（如果非 dry_run）
        executed_strategies = []
        if not dry_run and evolution_decisions:
            print(f"\n3️⃣ 执行 {len(evolution_decisions)} 个进化策略...")
            for decision in evolution_decisions:
                result = self._execute_strategy(decision, dry_run=dry_run)
                executed_strategies.append(result)
        else:
            print(f"\n3️⃣ Dry-run 模式，跳过执行")
        
        # 6. 重新评估
        if not dry_run and executed_strategies:
            print("\n4️⃣ 重新评估...")
            new_scores = self.assessor.assess_all(self._collect_dimension_data())
            
            # 检查是否有改进
            improvement = self._check_improvement(scores, new_scores)
            print(f"   进化效果: {improvement}")
        
        # 发布事件
        event_bus.publish(Event(
            type="evolution.cycle_completed",
            source="EvolutionOrchestrator",
            timestamp=datetime.now(),
            data={
                "decisions_made": len(evolution_decisions),
                "strategies_executed": len(executed_strategies),
                "critical_dimensions": critical_dimensions
            }
        ))
        
        return {
            "success": True,
            "dimension_scores": self._format_scores(scores),
            "evolution_decisions": evolution_decisions,
            "executed_strategies": executed_strategies,
            "message": f"完成 {len(evolution_decisions)} 个进化决策"
        }
    
    def _collect_dimension_data(self) -> Dict[str, Dict]:
        """收集各维度数据
        
        这里应该调用对应的收集器
        现在返回简化数据
        """
        # TODO: 调用真正的维度收集器
        return {
            "cognitive": {
                "triggers": [],
                "evidence": {"positive_milestones": 0}
            },
            "learning": {
                "triggers": ["learning_debt_accumulating"],
                "evidence": {"positive_milestones": 0}
            },
            "autonomy": {
                "triggers": [],
                "evidence": {"positive_milestones": 2}
            },
            "goal": {
                "triggers": ["no_self_defined_goals"],
                "evidence": {"positive_milestones": 0}
            },
            "creativity": {
                "triggers": [],
                "evidence": {"positive_milestones": 1}
            },
            "adaptive": {
                "triggers": [],
                "evidence": {"positive_milestones": 1}
            },
            "collaboration": {
                "triggers": ["low_tool_usage"],
                "evidence": {"positive_milestones": 0}
            },
            "protection": {
                "triggers": [],
                "evidence": {"positive_milestones": 2}
            },
            "prediction": {
                "triggers": ["no_prediction_mechanism"],
                "evidence": {"positive_milestones": 0}
            },
            "self_awareness": {
                "triggers": [],
                "evidence": {"positive_milestones": 1}
            }
        }
    
    def _select_evolution_strategy(self, dim_id: str, dim_data: Dict) -> Optional[Dict]:
        """为维度选择进化策略
        
        这里应该根据触发条件选择对应策略
        现在是简化版
        """
        # TODO: 实现真正的策略选择逻辑
        return {
            "dimension": dim_id,
            "dimension_name": self.assessor.DIMENSIONS[dim_id]["name"],
            "strategy": f"{dim_id}_upgrade",
            "confidence": 0.8,
            "triggers": dim_data.get("triggers", []),
            "timestamp": datetime.now().isoformat()
        }
    
    def _execute_strategy(self, decision: Dict, dry_run: bool) -> Dict:
        """执行进化策略
        
        这里应该调用对应策略的 execute 方法
        现在是简化版
        """
        # TODO: 实现真正的策略执行
        return {
            "dimension": decision["dimension"],
            "strategy": decision["strategy"],
            "success": True if not dry_run else None,
            "dry_run": dry_run,
            "timestamp": datetime.now().isoformat()
        }
    
    def _format_scores(self, scores: Dict) -> Dict:
        """格式化评分"""
        return {
            dim_id: {
                "name": score.name,
                "icon": score.icon,
                "score": score.score,
                "level": score.level
            }
            for dim_id, score in scores.items()
        }
    
    def _check_improvement(self, old_scores: Dict, new_scores: Dict) -> str:
        """检查进化效果"""
        old_avg = sum(s.score for s in old_scores.values()) / len(old_scores)
        new_avg = sum(s.score for s in new_scores.values()) / len(new_scores)
        diff = new_avg - old_avg
        
        if diff > 0:
            return f"✅ 提升 +{diff:.1f} 分 ({old_avg:.1f} → {new_avg:.1f})"
        elif diff < 0:
            return f"⚠️  下降 {diff:.1f} 分 ({old_avg:.1f} → {new_avg:.1f})"
        else:
            return f"➡️  无变化 ({old_avg:.1f} 分)"

if __name__ == "__main__":
    orchestrator = EvolutionOrchestrator()
    result = orchestrator.run_full_cycle(dry_run=True)
    print(json.dumps(result, indent=2, ensure_ascii=False))
