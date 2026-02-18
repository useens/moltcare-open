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
        """收集各维度数据"""
        from collectors import run_all_collectors
        return run_all_collectors()
    
    def _select_evolution_strategy(self, dim_id: str, dim_data: Dict) -> Optional[Dict]:
        """为维度选择进化策略"""
        triggers = dim_data.get("triggers", [])
        
        if not triggers:
            return None
        
        # 完整的策略映射表
        strategy_map = {
            "cognitive": {
                "shallow_reasoning": "deep_reasoning_upgrade",
                "logical_errors_detected": "logical_consistency_checker",
                "contradictions_found": "counter_argument_framework",
                "deep_reasoning_not_enabled": "deep_reasoning_upgrade",
                "no_counter_argument_framework": "counter_argument_framework",
                "no_abstraction_ladder": "abstraction_ladder",
                "default": "abstraction_ladder"
            },
            "learning": {
                "learning_debt_high": "knowledge_gap_analysis",
                "high_signal_unprocessed": "urgent_signal_processor",
                "knowledge_graph_sparse": "graph_rebuilder",
                "knowledge_graph_missing": "graph_rebuilder",
                "no_domain_exploration": "active_curiosity_engine",
                "insufficient_domain_exploration": "active_curiosity_engine",
                "low_knowledge_application": "cross_reference_synthesizer",
                "no_knowledge_application": "cross_reference_synthesizer",
                "no_learning_debt_tracking": "knowledge_validation_gate",
                "no_active_curiosity": "active_curiosity_engine",
                "default": "active_curiosity_engine"
            },
            "autonomy": {
                "external_dependency_high": "self_ownership_framework",
                "frequent_human_intervention": "autonomous_decision_tree",
                "low_autonomous_task_count": "autonomous_decision_tree",
                "high_rollback_rate": "decision_caching_system",
                "no_decision_cache": "decision_caching_system",
                "default": "autonomous_decision_tree"
            },
            "goal": {
                "no_self_defined_goals": "self_goal_definition",
                "insufficient_self_goals": "self_goal_definition",
                "no_clear_priority": "priority_dynamic_adaptive",
                "low_goal_completion_rate": "milestone_tracking",
                "no_goals_tracked": "milestone_tracking",
                "low_milestone_progress": "milestone_tracking",
                "no_milestone_tracking": "milestone_tracking",
                "no_long_term_plan": "self_goal_definition",
                "no_goal_alignment_check": "goal_alignment_checker",
                "default": "priority_dynamic_adaptive"
            },
            "creativity": {
                "no_innovations": "inspiration_fusion_engine",
                "no_new_frameworks": "framework_generator",
                "no_inspiration_fusion": "inspiration_fusion_engine",
                "low_inspiration_fusion": "inspiration_fusion_engine",
                "no_lateral_thinking": "lateral_thinking_module",
                "no_concept_synthesis": "concept_synthesizer",
                "no_framework_generation": "framework_generator",
                "default": "inspiration_fusion_engine"
            },
            "adaptive": {
                "no_context_awareness_tracking": "context_awareness_upgrade",
                "insufficient_anomaly_handling": "anomaly_self_detection",
                "no_anomaly_detection": "anomaly_self_detection",
                "insufficient_pattern_adaptation": "pattern_evolution_engine",
                "no_pattern_adaptation": "pattern_evolution_engine",
                "no_recent_context_switches": "adaptive_mode_switching",
                "no_context_switch_tracking": "adaptive_mode_switching",
                "no_environment_responses": "adaptive_mode_switching",
                "default": "adaptive_mode_switching"
            },
            "collaboration": {
                "low_tool_diversity": "tool_matrix_fusion",
                "no_tools_usage_tracking": "tool_matrix_fusion",
                "insufficient_multi_agent_collab": "multi_agent_orchestrator",
                "no_multi_agent_tracking": "multi_agent_orchestrator",
                "no_resource_integration": "resource_allocation_optimizer",
                "low_concurrency_usage": "resource_allocation_optimizer",
                "no_concurrency_tracking": "resource_allocation_optimizer",
                "no_tool_matrix_fusion": "tool_matrix_fusion",
                "default": "multi_agent_orchestrator"
            },
            "protection": {
                "insufficient_risk_prediction": "risk_prediction_engine",
                "no_risk_prediction": "risk_prediction_engine",
                "insufficient_safety_boundaries": "safety_boundary_evolution",
                "no_safety_boundaries": "safety_boundary_evolution",
                "no_threat_detection": "threat_detection_system",
                "high_risk_commands_executed": "self_preservation_protocol",
                "no_high_risk_tracking": "self_preservation_protocol",
                "no_self_preservation": "self_preservation_protocol",
                "default": "safety_boundary_evolution"
            },
            "prediction": {
                "no_causal_reasoning": "causal_chain_reasoning_engine",
                "insufficient_impact_prediction": "impact_prediction_system",
                "no_impact_prediction": "impact_prediction_system",
                "no_scenario_simulation": "scenario_simulation",
                "no_preemptive_actions": "preemptive_action_generator",
                "no_forward_planning": "scenario_simulation",
                "default": "impact_prediction_system"
            },
            "self_awareness": {
                "no_capability_boundary_mapping": "capability_boundary_mapper",
                "low_self_awareness_calibration": "self_awareness_calibrator",
                "no_self_awareness_calibration": "self_awareness_calibrator",
                "insufficient_reflection": "reflective_journal_system",
                "no_reflective_journal": "reflective_journal_system",
                "insufficient_unknown_honesty": "honest_unknown_declaration",
                "no_unknown_tracking": "honest_unknown_declaration",
                "no_self_evaluation": "self_awareness_calibrator",
                "over_confident": "reflective_journal_system",
                "default": "reflective_journal_system"
            }
        }
        
        if dim_id in strategy_map:
            dim_strategies = strategy_map[dim_id]
            for trigger in triggers:
                if trigger in dim_strategies:
                    strategy_name = dim_strategies[trigger]
                    return {
                        "dimension": dim_id,
                        "dimension_name": self.assessor.DIMENSIONS[dim_id]["name"],
                        "strategy": strategy_name,
                        "confidence": 0.8,
                        "triggers": triggers,
                        "evidence": dim_data.get("evidence", {}),
                        "timestamp": datetime.now().isoformat()
                    }
            # 使用默认策略
            strategy_name = dim_strategies["default"]
            return {
                "dimension": dim_id,
                "dimension_name": self.assessor.DIMENSIONS[dim_id]["name"],
                "strategy": strategy_name,
                "confidence": 0.7,
                "triggers": triggers,
                "evidence": dim_data.get("evidence", {}),
                "timestamp": datetime.now().isoformat()
            }
        
        return None
    
    def _execute_strategy(self, decision: Dict, dry_run: bool) -> Dict:
        """执行进化策略"""
        strategy_name = decision["strategy"]
        
        # 尝试从认知策略库中获取
        try:
            from strategies.cognitive import STRATEGIES as COG_STRATEGIES
            if strategy_name in COG_STRATEGIES:
                strategy = COG_STRATEGIES[strategy_name]
        except:
            strategy = None
        
        if strategy is None:
            # 策略未实现
            return {
                "dimension": decision["dimension"],
                "strategy": strategy_name,
                "success": None,
                "dry_run": dry_run,
                "message": "策略未实现",
                "timestamp": datetime.now().isoformat()
            }
        
        if dry_run:
            return {
                "dimension": decision["dimension"],
                "strategy": strategy_name,
                "success": None,
                "dry_run": True,
                "message": "Dry-run 模式",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            result = strategy.execute(decision)
            return {
                "dimension": decision["dimension"],
                "strategy": strategy_name,
                "success": result.get("status") == "success",
                "dry_run": False,
                "actions": result.get("actions", []),
                "message": result.get("status"),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "dimension": decision["dimension"],
                "strategy": strategy_name,
                "success": False,
                "dry_run": False,
                "error": str(e),
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
