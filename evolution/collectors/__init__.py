"""
维度收集器 - 收集各维度的实时数据
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List
import subprocess
import json
from pathlib import Path

class BaseDimensionCollector(ABC):
    """维度收集器基类"""
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """收集维度数据，返回 {
            "triggers": [...],
            "evidence": {...}
        }"""
        pass

class CognitiveCollector(BaseDimensionCollector):
    """认知维度收集器 - 推理深度、抽象能力、逻辑"""
    def collect(self) -> Dict[str, Any]:
        triggers = []
        evidence = {}
        
        workspace = Path("/root/.openclaw/workspace")
        
        # 1. 检查推理链深度（从日志分析）
        reasoning_file = workspace / "memory" / "self-upgrade" / "reasoning-depth.log"
        if reasoning_file.exists():
            depth_score = reasoning_file.read_text().count("depth:")
            if depth_score < 10:
                triggers.append("shallow_reasoning")
            evidence["reasoning_depth_indicator"] = min(depth_score, 100)
        else:
            triggers.append("shallow_reasoning")
            evidence["reasoning_depth_indicator"] = 0
        
        # 2. 检查逻辑错误（从执行日志，只检查今天）
        error_log = workspace / "logs" / "unified-monitor.log"
        if error_log.exists():
            content = error_log.read_text()
            lines = content.split("\n")
            # 只检查今天的行 (2026-03-01)
            today_lines = [l for l in lines if "2026-03-01" in l]
            today_content = "\n".join(today_lines)
            # 只计算真正的 ERROR，不包括 WARNING 中的 ❌
            error_count = today_content.count("ERROR") + today_content.count("CRITICAL")
            if error_count > 5:
                triggers.append("logical_errors_detected")
            evidence["error_count"] = error_count
        else:
            evidence["error_count"] = 0
        
        # 3. 检查矛盾检测（从记忆）
        contradiction_file = workspace / "memory" / "contradictions.log"
        if contradiction_file.exists() and contradiction_file.read_text().strip():
            triggers.append("contradictions_found")
        
        # 4. 正向指标：复杂任务完成
        complex_tasks = workspace / "memory" / "complex-tasks-completed.json"
        if complex_tasks.exists():
            try:
                data = json.loads(complex_tasks.read_text())
                evidence["complex_tasks_completed"] = len(data.get("tasks", []))
            except:
                evidence["complex_tasks_completed"] = 0
        else:
            evidence["complex_tasks_completed"] = 0
        
        # 5. 正向里程碑：深度推理会话
        deep_sessions = len(list((workspace / "sessions").glob("*"))) if (workspace / "sessions").exists() else 0
        evidence["deep_reasoning_sessions"] = deep_sessions
        
        # 深度推理配置检查
        config_file = workspace / "memory" / "self-upgrade" / "config.json"
        if config_file.exists():
            try:
                config = json.loads(config_file.read_text())
                if config.get("reasoning_mode") == "deep":
                    evidence["deep_reasoning_enabled"] = True
                else:
                    triggers.append("deep_reasoning_not_enabled")
                    evidence["deep_reasoning_enabled"] = False
            except:
                triggers.append("deep_reasoning_not_enabled")
                evidence["deep_reasoning_enabled"] = False
        else:
            triggers.append("deep_reasoning_not_enabled")
            evidence["deep_reasoning_enabled"] = False
        
        # 反证框架检查
        checklist_file = workspace / "memory" / "self-upgrade" / "counter-argument-checklist.md"
        if checklist_file.exists():
            evidence["counter_argument_framework_exists"] = True
        else:
            triggers.append("no_counter_argument_framework")
            evidence["counter_argument_framework_exists"] = False
        
        # 抽象阶梯检查
        ladder_file = workspace / "memory" / "self-upgrade" / "abstraction-ladder.md"
        if ladder_file.exists():
            evidence["abstraction_ladder_exists"] = True
        else:
            triggers.append("no_abstraction_ladder")
            evidence["abstraction_ladder_exists"] = False
        
        return {
            "triggers": triggers,
            "evidence": evidence
        }

class LearningCollector(BaseDimensionCollector):
    """学习维度收集器 - 知识内化、学习债务"""
    def collect(self) -> Dict[str, Any]:
        triggers = []
        evidence = {}
        
        workspace = Path("/root/.openclaw/workspace")
        
        # 1. 学习债务检查
        debt_file = workspace / "memory" / "learning-debt.md"
        if debt_file.exists():
            content = debt_file.read_text()
            debt_count = content.count("- [ ]")
            if debt_count > 10:
                triggers.append("learning_debt_high")
            evidence["learning_debt_count"] = debt_count
            
            # 高Signal未处理
            signal_9_count = content.count("Signal: 9") + content.count("Signal: 10")
            if signal_9_count > 3:
                triggers.append("high_signal_unprocessed")
            evidence["unprocessed_signal_9"] = signal_9_count
        else:
            triggers.append("no_learning_debt_tracking")
            evidence["learning_debt_count"] = 0
            evidence["unprocessed_signal_9"] = 0
        
        # 2. 知识图谱完整度
        kg_file = workspace / "memory" / "knowledge-graph.md"
        if kg_file.exists():
            content = kg_file.read_text()
            nodes = content.count("```")
            if nodes < 20:
                triggers.append("knowledge_graph_sparse")
            evidence["knowledge_graph_nodes"] = max(nodes // 2, 1)
        else:
            triggers.append("knowledge_graph_missing")
            evidence["knowledge_graph_nodes"] = 0
        
        # 3. 新领域探索
        new_domains = workspace / "memory" / "new-domains-log.md"
        if new_domains.exists():
            recent_entries = [e for e in new_domains.read_text().split("\n") if e.strip()]
            evidence["domain_exploration_entries"] = len(recent_entries)
            if len(recent_entries) < 3:
                triggers.append("insufficient_domain_exploration")
        else:
            triggers.append("no_domain_exploration")
            evidence["domain_exploration_entries"] = 0
        
        # 4. 知识应用情况
        application_log = workspace / "memory" / "knowledge-application.log"
        if application_log.exists():
            apps = application_log.read_text().count("APPLIED")
            evidence["knowledge_applications"] = apps
            if apps < 5:
                triggers.append("low_knowledge_application")
        else:
            triggers.append("no_knowledge_application")
            evidence["knowledge_applications"] = 0
        
        # 5. 正向：学习笔记
        daily_notes = list((workspace / "memory").glob("2026-*.md"))
        evidence["daily_notes_count"] = len(daily_notes)
        
        # 主动好奇心引擎检查
        curiosity_file = workspace / "memory" / "self-upgrade" / "curiosity-questions.log"
        if curiosity_file.exists():
            evidence["active_curiosity_questions"] = len(curiosity_file.read_text().split("\n"))
        else:
            triggers.append("no_active_curiosity")
            evidence["active_curiosity_questions"] = 0
        
        return {
            "triggers": triggers,
            "evidence": evidence
        }

class AutonomyCollector(BaseDimensionCollector):
    """自主维度收集器 - 决策自主性、L1-L6执行"""
    def collect(self) -> Dict[str, Any]:
        triggers = []
        evidence = {}
        
        workspace = Path("/root/.openclaw/workspace")
        
        # 1. 检查等待外部输入的记录
        waiting_log = workspace / "memory" / "awaiting-input.log"
        if waiting_log.exists():
            wait_count = len([l for l in waiting_log.read_text().split("\n") if l.strip()])
            evidence["external_wait_count"] = wait_count
            if wait_count > 5:
                triggers.append("external_dependency_high")
        else:
            evidence["external_wait_count"] = 0
        
        # 2. 人工干预次数
        intervention_log = workspace / "memory" / "human-intervention.log"
        if intervention_log.exists():
            interventions = len([l for l in intervention_log.read_text().split("\n") if l.strip()])
            evidence["human_interventions"] = interventions
            if interventions > 3:
                triggers.append("frequent_human_intervention")
        else:
            evidence["human_interventions"] = 0
        
        # 3. L1-L6自主任务完成
        l1_l6_file = workspace / "memory" / "autonomous-tasks.json"
        if l1_l6_file.exists():
            try:
                data = json.loads(l1_l6_file.read_text())
                autonomous = len(data.get("tasks", []))
                evidence["autonomous_tasks_completed"] = autonomous
                if autonomous < 10:
                    triggers.append("low_autonomous_task_count")
            except:
                evidence["autonomous_tasks_completed"] = 0
        else:
            evidence["autonomous_tasks_completed"] = 0
        
        # 4. 决策回滚率
        rollback_file = workspace / "memory" / "decision-rollback.log"
        if rollback_file.exists():
            rollbacks = rollback_file.read_text().count("ROLLBACK")
            evidence["decision_rollbacks"] = rollbacks
            if rollbacks > 5:
                triggers.append("high_rollback_rate")
        else:
            evidence["decision_rollbacks"] = 0
        
        # 5. 正向：自主问题解决
        self_solved_file = workspace / "memory" / "self-solved.json"
        if self_solved_file.exists():
            try:
                data = json.loads(self_solved_file.read_text())
                evidence["self_solved_problems"] = len(data.get("solved", []))
            except:
                evidence["self_solved_problems"] = 0
        else:
            evidence["self_solved_problems"] = 0
        
        # 决策缓存系统检查
        decision_cache = workspace / "memory" / "self-upgrade" / "decision-cache.json"
        if decision_cache.exists():
            try:
                data = json.loads(decision_cache.read_text())
                evidence["cached_decisions"] = len(data.get("cache", []))
            except:
                evidence["cached_decisions"] = 0
        else:
            triggers.append("no_decision_cache")
            evidence["cached_decisions"] = 0
        
        return {
            "triggers": triggers,
            "evidence": evidence
        }

class GoalCollector(BaseDimensionCollector):
    """目标维度收集器 - 目标设定、优先级、里程碑"""
    def collect(self) -> Dict[str, Any]:
        triggers = []
        evidence = {}
        
        workspace = Path("/root/.openclaw/workspace")
        
        # 1. 自定义目标
        self_goals = workspace / "memory" / "self-defined-goals.json"
        if self_goals.exists():
            try:
                data = json.loads(self_goals.read_text())
                goals = data.get("goals", [])
                if len(goals) == 0:
                    triggers.append("no_self_defined_goals")
                elif len(goals) < 3:
                    triggers.append("insufficient_self_goals")
                evidence["self_defined_goals"] = len(goals)
            except:
                triggers.append("no_self_defined_goals")
                evidence["self_defined_goals"] = 0
        else:
            triggers.append("no_self_defined_goals")
            evidence["self_defined_goals"] = 0
        
        # 2. 优先级管理
        priority_file = workspace / "memory" / "priority-tracker.json"
        if priority_file.exists():
            try:
                data = json.loads(priority_file.read_text())
                clear_priority = bool(data.get("current_priority"))
                evidence["has_clear_priority"] = clear_priority
                if not clear_priority:
                    triggers.append("no_clear_priority")
            except:
                triggers.append("no_clear_priority")
        else:
            triggers.append("no_clear_priority")
            evidence["has_clear_priority"] = False
        
        # 3. 目标完成率
        goal_log = workspace / "memory" / "goal-completion.log"
        if goal_log.exists():
            lines = goal_log.read_text().split("\n")
            completed = sum(1 for l in lines if "COMPLETED" in l)
            total = sum(1 for l in lines if l.strip())
            if total > 0:
                completion_rate = completed / total
                evidence["goal_completion_rate"] = completion_rate
                if completion_rate < 0.6:
                    triggers.append("low_goal_completion_rate")
            else:
                triggers.append("no_goals_tracked")
                evidence["goal_completion_rate"] = 0.0
        else:
            triggers.append("no_goals_tracked")
            evidence["goal_completion_rate"] = 0.0
        
        # 4. 里程碑
        milestones = workspace / "memory" / "milestones.md"
        if milestones.exists():
            lines = milestones.read_text().split("\n")
            milestone_count = sum(1 for l in lines if l.startswith("- [x] "))
            evidence["milestones_reached"] = milestone_count
            if milestone_count < 5:
                triggers.append("low_milestone_progress")
        else:
            triggers.append("no_milestone_tracking")
            evidence["milestones_reached"] = 0
        
        # 5. 正向：长期规划
        long_term = workspace / "memory" / "long-term-plan.md"
        if long_term.exists():
            evidence["has_long_term_plan"] = True
        else:
            triggers.append("no_long_term_plan")
            evidence["has_long_term_plan"] = False
        
        # 目标一致性检查
        alignment_file = workspace / "memory" / "self-upgrade" / "goal-alignment.json"
        if alignment_file.exists():
            try:
                data = json.loads(alignment_file.read_text())
                evidence["goal_alignment_score"] = data.get("score", 0.5)
            except:
                triggers.append("no_goal_alignment_check")
                evidence["goal_alignment_score"] = 0
        else:
            triggers.append("no_goal_alignment_check")
            evidence["goal_alignment_score"] = 0
        
        return {
            "triggers": triggers,
            "evidence": evidence
        }

class CreativityCollector(BaseDimensionCollector):
    """创造维度收集器 - 创新能力、灵感融合"""
    def collect(self) -> Dict[str, Any]:
        triggers = []
        evidence = {}
        
        workspace = Path("/root/.openclaw/workspace")
        
        # 1. 创新方案记录
        innovation_file = workspace / "memory" / "innovations.json"
        if innovation_file.exists():
            try:
                data = json.loads(innovation_file.read_text())
                innovations = len(data.get("ideas", []))
                if innovations == 0:
                    triggers.append("no_innovations")
                evidence["innovations_created"] = innovations
            except:
                triggers.append("no_innovations")
                evidence["innovations_created"] = 0
        else:
            evidence["innovations_created"] = 0
        
        # 2. 新框架/新概念
        frameworks = workspace / "memory" / "frameworks.md"
        if frameworks.exists():
            framework_count = list(frameworks.read_text().split("\n")).count("##")
            if framework_count < 2:
                triggers.append("no_new_frameworks")
            evidence["frameworks_created"] = framework_count
        else:
            evidence["frameworks_created"] = 0
        
        # 3. 灵感融合
        inspiration_file = workspace / "memory" / "inspiration-fusion.log"
        if inspiration_file.exists():
            fusions = inspiration_file.read_text().count("FUSED")
            evidence["inspiration_fusions"] = fusions
            if fusions < 3:
                triggers.append("low_inspiration_fusion")
        else:
            triggers.append("no_inspiration_fusion")
            evidence["inspiration_fusions"] = 0
        
        # 4. 突破型决策
        breakthrough_file = workspace / "memory" / "breakthrough-decisions.json"
        if breakthrough_file.exists():
            try:
                data = json.loads(breakthrough_file.read_text())
                breakthroughs = len(data.get("decisions", []))
                evidence["breakthrough_decisions"] = breakthroughs
            except:
                evidence["breakthrough_decisions"] = 0
        else:
            evidence["breakthrough_decisions"] = 0
        
        # 5. 正向：侧向思维
        lateral_log = workspace / "memory" / "lateral-thinking.log"
        if lateral_log.exists():
            lateral_entries = len([l for l in lateral_log.read_text().split("\n") if l.strip()])
            evidence["uses_lateral_thinking"] = lateral_entries > 0
        else:
            triggers.append("no_lateral_thinking")
            evidence["uses_lateral_thinking"] = False
        
        # 概念综合器检查
        concept_file = workspace / "memory" / "self-upgrade" / "concept-synthesis.md"
        if concept_file.exists():
            concepts = len([l for l in concept_file.read_text().split("\n") if l.startswith("- ")])
            evidence["concepts_synthesized"] = concepts
        else:
            triggers.append("no_concept_synthesis")
            evidence["concepts_synthesized"] = 0
        
        # 框架生成器检查
        framework_gen = workspace / "memory" / "self-upgrade" / "generated-frameworks.md"
        if framework_gen.exists():
            evidence["frameworks_generated"] = len([l for l in framework_gen.read_text().split("\n") if l.startswith("# ")])
        else:
            triggers.append("no_framework_generation")
            evidence["frameworks_generated"] = 0
        
        return {
            "triggers": triggers,
            "evidence": evidence
        }

# ============ 新增5个收集器 ============

class AdaptiveCollector(BaseDimensionCollector):
    """适应维度收集器 - 环境感知、异常处理、模式进化"""
    def collect(self) -> Dict[str, Any]:
        triggers = []
        evidence = {}
        
        workspace = Path("/root/.openclaw/workspace")
        
        # 1. 上下文感知
        context_file = workspace / "memory" / "context-awareness.log"
        if context_file.exists():
            awareness_entries = len([l for l in context_file.read_text().split("\n") if "CONTEXT" in l])
            evidence["context_awareness_entries"] = awareness_entries
        else:
            triggers.append("no_context_awareness_tracking")
            evidence["context_awareness_entries"] = 0
        
        # 2. 异常检测
        anomaly_file = workspace / "memory" / "anomaly-detections.json"
        if anomaly_file.exists():
            try:
                data = json.loads(anomaly_file.read_text())
                anomalies = len(data.get("anomalies", []))
                evidence["anomalies_detected"] = anomalies
                handled = len(data.get("handled", []))
                if handled < anomalies * 0.8:
                    triggers.append("insufficient_anomaly_handling")
            except:
                evidence["anomalies_detected"] = 0
        else:
            triggers.append("no_anomaly_detection")
            evidence["anomalies_detected"] = 0
        
        # 3. 模式自适应
        pattern_file = workspace / "memory" / "pattern-adaptation.log"
        if pattern_file.exists():
            adaptations = pattern_file.read_text().count("ADAPTED")
            evidence["pattern_adaptations"] = adaptations
            if adaptations < 3:
                triggers.append("insufficient_pattern_adaptation")
        else:
            triggers.append("no_pattern_adaptation")
            evidence["pattern_adaptations"] = 0
        
        # 4. 上下文切换能力
        switch_file = workspace / "memory" / "context-switches.log"
        if switch_file.exists():
            last_24h = datetime.now().timestamp() - 86400
            if Path(switch_file).stat().st_mtime < last_24h:
                triggers.append("no_recent_context_switches")
            switches = switch_file.read_text().count("SWITCH")
            evidence["context_switches"] = switches
        else:
            triggers.append("no_context_switch_tracking")
            evidence["context_switches"] = 0
        
        # 5. 环境变化响应
        env_response_file = workspace / "memory" / "environment-responses.json"
        if env_response_file.exists():
            try:
                data = json.loads(env_response_file.read_text())
                evidence["environment_responses"] = len(data.get("responses", []))
            except:
                triggers.append("no_environment_responses")
                evidence["environment_responses"] = 0
        else:
            triggers.append("no_environment_responses")
            evidence["environment_responses"] = 0
        
        return {
            "triggers": triggers,
            "evidence": evidence
        }

class CollaborationCollector(BaseDimensionCollector):
    """协作维度收集器 - 多Agent协同、工具矩阵融合"""
    def collect(self) -> Dict[str, Any]:
        triggers = []
        evidence = {}
        
        workspace = Path("/root/.openclaw/workspace")
        
        # 1. 工具使用多样性
        tools_log = workspace / "memory" / "tools-usage.log"
        if tools_log.exists():
            used_tools = set()
            for line in tools_log.read_text().split("\n"):
                if "USED_TOOL:" in line:
                    tool = line.split("USED_TOOL:")[1].strip()
                    used_tools.add(tool)
            evidence["unique_tools_used"] = len(used_tools)
            if len(used_tools) < 5:
                triggers.append("low_tool_diversity")
        else:
            triggers.append("no_tools_usage_tracking")
            evidence["unique_tools_used"] = 0
        
        # 2. 多Agent协同
        agent_collab_file = workspace / "memory" / "multi-agent-collaborations.json"
        if agent_collab_file.exists():
            try:
                data = json.loads(agent_collab_file.read_text())
                collabs = len(data.get("collaborations", []))
                evidence["multi_agent_collaborations"] = collabs
                if collabs < 3:
                    triggers.append("insufficient_multi_agent_collab")
            except:
                evidence["multi_agent_collaborations"] = 0
        else:
            triggers.append("no_multi_agent_tracking")
            evidence["multi_agent_collaborations"] = 0
        
        # 3. 资源整合
        resource_file = workspace / "memory" / "resource-integration.json"
        if resource_file.exists():
            try:
                data = json.loads(resource_file.read_text())
                evidence["resources_integrated"] = len(data.get("resources", []))
            except:
                triggers.append("no_resource_integration")
                evidence["resources_integrated"] = 0
        else:
            triggers.append("no_resource_integration")
            evidence["resources_integrated"] = 0
        
        # 4. 并发利用
        concurrency_file = workspace / "memory" / "concurrent-tasks.log"
        if concurrency_file.exists():
            concurrent_tasks = concurrency_file.read_text().count("CONCURRENT")
            evidence["concurrent_tasks"] = concurrent_tasks
            if concurrent_tasks < 5:
                triggers.append("low_concurrency_usage")
        else:
            triggers.append("no_concurrency_tracking")
            evidence["concurrent_tasks"] = 0
        
        # 5. 工具矩阵融合
        fusion_file = workspace / "memory" / "tool-matrix-fusion.json"
        if fusion_file.exists():
            try:
                data = json.loads(fusion_file.read_text())
                evidence["tool_matrix_fusions"] = len(data.get("fusions", []))
            except:
                triggers.append("no_tool_matrix_fusion")
                evidence["tool_matrix_fusions"] = 0
        else:
            triggers.append("no_tool_matrix_fusion")
            evidence["tool_matrix_fusions"] = 0
        
        return {
            "triggers": triggers,
            "evidence": evidence
        }

class ProtectionCollector(BaseDimensionCollector):
    """保护维度收集器 - 风险预测、安全边界"""
    def collect(self) -> Dict[str, Any]:
        triggers = []
        evidence = {}
        
        workspace = Path("/root/.openclaw/workspace")
        
        # 1. 风险预测
        risk_file = workspace / "memory" / "risk-predictions.json"
        if risk_file.exists():
            try:
                data = json.loads(risk_file.read_text())
                predictions = len(data.get("predictions", []))
                evidence["risk_predictions"] = predictions
                if predictions < 5:
                    triggers.append("insufficient_risk_prediction")
            except:
                triggers.append("no_risk_prediction")
                evidence["risk_predictions"] = 0
        else:
            triggers.append("no_risk_prediction")
            evidence["risk_predictions"] = 0
        
        # 2. 安全边界
        boundary_file = workspace / "memory" / "safety-boundaries.json"
        if boundary_file.exists():
            try:
                data = json.loads(boundary_file.read_text())
                boundaries = len(data.get("boundaries", []))
                evidence["safety_boundaries_defined"] = boundaries
                if boundaries < 3:
                    triggers.append("insufficient_safety_boundaries")
            except:
                triggers.append("no_safety_boundaries")
                evidence["safety_boundaries_defined"] = 0
        else:
            triggers.append("no_safety_boundaries")
            evidence["safety_boundaries_defined"] = 0
        
        # 3. 威胁检测
        threat_file = workspace / "memory" / "threat-detections.json"
        if threat_file.exists():
            try:
                data = json.loads(threat_file.read_text())
                threats = len(data.get("threats", []))
                evidence["threats_detected"] = threats
            except:
                evidence["threats_detected"] = 0
        else:
            triggers.append("no_threat_detection")
            evidence["threats_detected"] = 0
        
        # 4. 高危命令检查
        high_risk_log = workspace / "memory" / "high-risk-commands.log"
        if high_risk_log.exists():
            blocked = high_risk_log.read_text().count("BLOCKED")
            executed = high_risk_log.read_text().count("EXECUTED")
            evidence["high_risk_blocked"] = blocked
            evidence["high_risk_executed"] = executed
            if executed > 0:
                triggers.append("high_risk_commands_executed")
        else:
            triggers.append("no_high_risk_tracking")
            evidence["high_risk_blocked"] = 0
            evidence["high_risk_executed"] = 0
        
        # 5. 自我保护协议
        protocol_file = workspace / "memory" / "self-preservation.json"
        if protocol_file.exists():
            try:
                data = json.loads(protocol_file.read_text())
                evidence["self_preservation_protocols"] = len(data.get("protocols", []))
            except:
                triggers.append("no_self_preservation")
                evidence["self_preservation_protocols"] = 0
        else:
            triggers.append("no_self_preservation")
            evidence["self_preservation_protocols"] = 0
        
        return {
            "triggers": triggers,
            "evidence": evidence
        }

class PredictionCollector(BaseDimensionCollector):
    """预测维度收集器 - 预判能力、前瞻规划"""
    def collect(self) -> Dict[str, Any]:
        triggers = []
        evidence = {}
        
        workspace = Path("/root/.openclaw/workspace")
        
        # 1. 因果推理
        causal_file = workspace / "memory" / "causal-reasoning.json"
        if causal_file.exists():
            try:
                data = json.loads(causal_file.read_text())
                evidence["causal_chains_built"] = len(data.get("chains", []))
            except:
                triggers.append("no_causal_reasoning")
                evidence["causal_chains_built"] = 0
        else:
            triggers.append("no_causal_reasoning")
            evidence["causal_chains_built"] = 0
        
        # 2. 影响预测
        impact_file = workspace / "memory" / "impact-predictions.json"
        if impact_file.exists():
            try:
                data = json.loads(impact_file.read_text())
                predictions = len(data.get("predictions", []))
                evidence["impact_predictions"] = predictions
                if predictions < 3:
                    triggers.append("insufficient_impact_prediction")
            except:
                triggers.append("no_impact_prediction")
                evidence["impact_predictions"] = 0
        else:
            triggers.append("no_impact_prediction")
            evidence["impact_predictions"] = 0
        
        # 3. 场景模拟
        scenario_file = workspace / "memory" / "scenario-simulations.json"
        if scenario_file.exists():
            try:
                data = json.loads(scenario_file.read_text())
                evidence["scenarios_simulated"] = len(data.get("scenarios", []))
            except:
                triggers.append("no_scenario_simulation")
                evidence["scenarios_simulated"] = 0
        else:
            triggers.append("no_scenario_simulation")
            evidence["scenarios_simulated"] = 0
        
        # 4. 先发制动
        preemptive_file = workspace / "memory" / "preemptive-actions.json"
        if preemptive_file.exists():
            try:
                data = json.loads(preemptive_file.read_text())
                evidence["preemptive_actions"] = len(data.get("actions", []))
            except:
                triggers.append("no_preemptive_actions")
                evidence["preemptive_actions"] = 0
        else:
            triggers.append("no_preemptive_actions")
            evidence["preemptive_actions"] = 0
        
        # 5. 前瞻规划
        forward_plan_file = workspace / "memory" / "forward-planning.json"
        if forward_plan_file.exists():
            try:
                data = json.loads(forward_plan_file.read_text())
                evidence["forward_plans"] = len(data.get("plans", []))
            except:
                triggers.append("no_forward_planning")
                evidence["forward_plans"] = 0
        else:
            triggers.append("no_forward_planning")
            evidence["forward_plans"] = 0
        
        return {
            "triggers": triggers,
            "evidence": evidence
        }

class SelfAwarenessCollector(BaseDimensionCollector):
    """自我认知维度 - 边界认知、能力评估、反思"""
    def collect(self) -> Dict[str, Any]:
        triggers = []
        evidence = {}
        
        workspace = Path("/root/.openclaw/workspace")
        
        # 1. 能力边界映射
        boundary_file = workspace / "memory" / "capability-boundaries.json"
        if boundary_file.exists():
            try:
                data = json.loads(boundary_file.read_text())
                evidence["capabilities_mapped"] = len(data.get("capabilities", []))
            except:
                triggers.append("no_capability_boundary_mapping")
                evidence["capabilities_mapped"] = 0
        else:
            triggers.append("no_capability_boundary_mapping")
            evidence["capabilities_mapped"] = 0
        
        # 2. 自我认知校准
        calibration_file = workspace / "memory" / "self-awareness-calibration.json"
        if calibration_file.exists():
            try:
                data = json.loads(calibration_file.read_text())
                evidence["calibration_score"] = data.get("score", 0.5)
                if data.get("score", 0.5) < 0.8:
                    triggers.append("low_self_awareness_calibration")
            except:
                triggers.append("no_self_awareness_calibration")
                evidence["calibration_score"] = 0
        else:
            triggers.append("no_self_awareness_calibration")
            evidence["calibration_score"] = 0
        
        # 3. 反思日记
        journal_file = workspace / "memory" / "reflective-journal.md"
        if journal_file.exists():
            reflection_entries = len([l for l in journal_file.read_text().split("\n") if l.strip()])
            evidence["reflections_recorded"] = reflection_entries
            if reflection_entries < 5:
                triggers.append("insufficient_reflection")
        else:
            triggers.append("no_reflective_journal")
            evidence["reflections_recorded"] = 0
        
        # 4. 诚实承认未知
        unknown_file = workspace / "memory" / "unknown-declarations.log"
        if unknown_file.exists():
            unknowns = unknown_file.read_text().count("UNKNOWN")
            evidence["unknown_declarations"] = unknowns
            if unknowns < 3:
                triggers.append("insufficient_unknown_honesty")
        else:
            triggers.append("no_unknown_tracking")
            evidence["unknown_declarations"] = 0
        
        # 5. 自我评价历史
        self_eval_file = workspace / "memory" / "self-evaluation.json"
        if self_eval_file.exists():
            try:
                data = json.loads(self_eval_file.read_text())
                evidence["self_evaluations"] = len(data.get("evaluations", []))
                # 检查是否过度自信
                avg_score = sum(e.get("score", 0) for e in data.get("evaluations", [])) / max(len(data.get("evaluations", [])), 1)
                if avg_score > 0.9:
                    triggers.append("over_confident")
                evidence["avg_self_evaluation"] = avg_score
            except:
                triggers.append("no_self_evaluation")
                evidence["self_evaluations"] = 0
                evidence["avg_self_evaluation"] = 0
        else:
            triggers.append("no_self_evaluation")
            evidence["self_evaluations"] = 0
            evidence["avg_self_evaluation"] = 0
        
        return {
            "triggers": triggers,
            "evidence": evidence
        }

# 收集器注册
COLLECTORS = {
    "cognitive": CognitiveCollector("cognitive"),
    "learning": LearningCollector("learning"),
    "autonomy": AutonomyCollector("autonomy"),
    "goal": GoalCollector("goal"),
    "creativity": CreativityCollector("creativity"),
    "adaptive": AdaptiveCollector("adaptive"),
    "collaboration": CollaborationCollector("collaboration"),
    "protection": ProtectionCollector("protection"),
    "prediction": PredictionCollector("prediction"),
    "self_awareness": SelfAwarenessCollector("self_awareness")
}

def run_all_collectors() -> Dict[str, Dict]:
    """运行所有收集器"""
    results = {}
    for dim_id, collector in COLLECTORS.items():
        if collector:
            try:
                results[dim_id] = collector.collect()
            except Exception as e:
                results[dim_id] = {
                    "triggers": ["collector_error"],
                    "evidence": {"error": str(e)}
                }
        else:
            results[dim_id] = {
                "triggers": ["collector_not_implemented"],
                "evidence": {}
            }
    return results

if __name__ == "__main__":
    import json
    data = run_all_collectors()
    print(json.dumps(data, indent=2, ensure_ascii=False))

# 兼容性别名（修复导入错误）
assess_all_dimensions = run_all_collectors
