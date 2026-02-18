"""
进化编排器 - 管理进化周期
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from core.dimension_assessor import DimensionAssessor, DimensionScore
from core import EvolutionState

# 尝试导入策略模块（支持不同运行路径）
try:
    from strategies import ALL_STRATEGIES
except ImportError:
    from evolution.strategies import ALL_STRATEGIES

try:
    from collectors import run_all_collectors
except ImportError:
    from evolution.collectors import run_all_collectors

class EvolutionOrchestrator:
    """进化编排器 - 管理完整的进化周期"""
    
    def __init__(self, data_dir: str = "evolution/data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.data_dir / "evolution.db"
        self.scores_path = self.data_dir / "dimension_scores.json"
        
        self.assessor = DimensionAssessor()
        self.state = EvolutionState()
        self.execution_history = []
        
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evolution_cycles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL,
                decisions TEXT,
                execution_results TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _save_scores(self, scores: Dict):
        """保存维度分数到JSON文件"""
        formatted = {}
        for dim_id, score in scores.items():
            formatted[dim_id] = {
                "name": score.name,
                "icon": score.icon,
                "score": score.score,
                "level": str(score.level),
                "triggers": score.triggers,
                "evidence": score.evidence,
                "last_updated": score.last_updated
            }
        
        with open(self.scores_path, 'w', encoding='utf-8') as f:
            json.dump(formatted, f, indent=2, ensure_ascii=False)
    
    def run_evolution_cycle(self, dry_run: bool = True) -> Dict:
        """运行完整的进化周期"""
        print("\n🚀 开始完整进化周期...\n")
        
        # 1. 收集所有维度数据
        print("1️⃣ 评估十维状态...")
        collector_data = run_all_collectors()
        
        # 2. 评估十维状态
        scores = self.assessor.assess_all(collector_data)
        self._save_scores(scores)
        self.assessor.print_status()
        
        # 3. 决策：哪些维度需要进化
        print("\n2️⃣ 决策进化方向...")
        decisions = []
        for dim_id, dim_data in collector_data.items():
            if dim_data.get("triggers"):
                decision = self._select_evolution_strategy(dim_id, dim_data)
                if decision:
                    decisions.append(decision)
        
        print(f"\n3️⃣ 检测到 {len(decisions)} 个需要进化的维度")
        
        # 4. 执行决策
        if not dry_run and decisions:
            print("\n4️⃣ 执行进化策略...")
            for i, decision in enumerate(decisions, 1):
                print(f"   [{i}/{len(decisions)}] {decision['dimension_name']}: {decision['strategy']}")
                result = self._execute_strategy(decision, dry_run)
                
                if result:
                    self.execution_history.append(result)
        
        # 5. 保存执行记录
        self._save_cycle_to_db(collector_data, decisions, dry_run)
        
        # 6. 重新评估（如果执行了策略）
        if not dry_run:
            print("\n4️⃣ 重新评估...")
            new_scores = self.assessor.assess_all(run_all_collectors())
            
            # 计算变化
            changes = []
            for dim_id in scores:
                old_score = scores[dim_id].score
                new_score = new_scores[dim_id].score
                if abs(new_score - old_score) > 0.1:
                    changes.append(f"{self.assessor.DIMENSIONS[dim_id]['name']}: {old_score:.1f}% → {new_score:.1f}%")
            
            if changes:
                print(f"   进化效果: ✨ 变化检测")
                for change in changes:
                    print(f"      {change}")
            else:
                print("   进化效果: ➡️  无变化")
        
        # 返回周期结果
        result = {
            "status": "completed",
            "decisions_count": len(decisions),
            "executed": not dry_run,
            "scores": {
                dim_id: score.score
                for dim_id, score in scores.items()
            }
        }
        
        return result
    
    def _save_cycle_to_db(self, collector_data: Dict, decisions: List, dry_run: bool):
        """保存进化周期到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO evolution_cycles (timestamp, status, decisions, execution_results)
            VALUES (?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            "dry_run" if dry_run else "completed",
            json.dumps(decisions, ensure_ascii=False),
            json.dumps(self.execution_history, ensure_ascii=False)
        ))
        
        conn.commit()
        conn.close()
    
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
        """执行进化策略 - 使用统一策略注册中心"""
        dimension = decision["dimension"]
        strategy_name = decision["strategy"]
        
        if dry_run:
            return {
                "dimension": dimension,
                "strategy": strategy_name,
                "success": None,
                "dry_run": True,
                "message": "Dry-run 模式",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # 从统一策略注册中心获取策略（已在顶部导入）
            if dimension not in ALL_STRATEGIES:
                return {
                    "dimension": dimension,
                    "strategy": strategy_name,
                    "success": False,
                    "message": f"未知维度: {dimension}",
                    "timestamp": datetime.now().isoformat()
                }
            
            dim_strategies = ALL_STRATEGIES[dimension]
            
            if strategy_name not in dim_strategies:
                return {
                    "dimension": dimension,
                    "strategy": strategy_name,
                    "success": False,
                    "message": f"未找到策略: {strategy_name}",
                    "timestamp": datetime.now().isoformat()
                }
            
            strategy = dim_strategies[strategy_name]
            
            # 执行策略
            evidence = decision.get("evidence", {})
            result = strategy.execute(evidence)
            
            return {
                "dimension": dimension,
                "strategy": strategy_name,
                "success": result.get("success", True),
                "dry_run": False,
                "actions": result.get("actions_taken", []),
                "message": result.get("message", "策略执行完成"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            import traceback
            return {
                "dimension": dimension,
                "strategy": strategy_name,
                "success": False,
                "dry_run": False,
                "message": f"执行失败: {str(e)}",
                "error": traceback.format_exc(),
                "timestamp": datetime.now().isoformat()
            }
    
    def _format_scores(self, scores: Dict) -> Dict:
        """格式化评分"""
        return {
            dim_id: {
                "name": score.name,
                "icon": score.icon,
                "score": score.score,
                "level": str(score.level),
                "triggers": score.triggers,
                "evidence": score.evidence
            }
            for dim_id, score in scores.items()
        }
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """获取进化历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, timestamp, status, decisions
            FROM evolution_cycles
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "status": row[2],
                "decisions": json.loads(row[3]) if row[3] else []
            }
            for row in results
        ]
