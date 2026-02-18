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
            avg_depth = 0
            lines = reasoning_file.read_text().split('\n')[-100:]
            for line in lines:
                if "depth:" in line.lower():
                    try:
                        avg_depth += float(line.split("depth:")[1].strip())
                    except:
                        pass
            if reasoning_file.exists():
                # 近似计算
                avg_depth = len(lines) / max(len(lines), 1)
            if avg_depth < 3:
                triggers.append("shallow_reasoning")
            evidence["avg_reasoning_depth"] = avg_depth
        
        # 2. 检查逻辑错误（从执行日志）
        error_log = workspace / "logs" / "unified-monitor.log"
        if error_log.exists():
            content = error_log.read_text()
            error_count = content.count("ERROR") + content.count("❌")
            if error_count > 5:
                triggers.append("logical_errors_detected")
            evidence["error_count"] = error_count
        
        # 3. 检查矛盾检测（从记忆）
        contradiction_file = workspace / "memory" / "contradictions.log"
        if contradiction_file.exists() and contradiction_file.read_text().strip():
            triggers.append("contradictions_found")
        
        # 4. 正向指标：复杂任务完成
        complex_tasks = workspace / "memory" / "complex-tasks-completed.json"
        if complex_tasks.exists():
            data = json.loads(complex_tasks.read_text())
            evidence["complex_tasks_completed"] = len(data.get("tasks", []))
        else:
            evidence["complex_tasks_completed"] = 0
        
        # 5. 正向里程碑：深度推理会话
        deep_sessions = len(list((workspace / "sessions").glob("*"))) if (workspace / "sessions").exists() else 0
        evidence["deep_reasoning_sessions"] = deep_sessions
        
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
        
        # 2. 知识图谱完整度
        kg_file = workspace / "memory" / "knowledge-graph.md"
        if kg_file.exists():
            content = kg_file.read_text()
            nodes = content.count("```")
            if nodes < 20:
                triggers.append("knowledge_graph_sparse")
            evidence["knowledge_graph_nodes"] = nodes // 2
        else:
            triggers.append("knowledge_graph_missing")
            evidence["knowledge_graph_nodes"] = 0
        
        # 3. 新领域探索
        new_domains = workspace / "memory" / "new-domains-log.md"
        if new_domains.exists():
            recent_entries = new_domains.read_text().split("\n")[-10:]
            if len(recent_entries) > 5:
                evidence["recent_domain_exploration"] = True
            else:
                triggers.append("no_domain_exploration")
        else:
            triggers.append("no_domain_exploration")
        
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
            content = waiting_log.read_text()
            wait_count = content.split("\n").count("") + len(content.split("\n"))
            if wait_count > 5:
                triggers.append("external_dependency_high")
            evidence["external_wait_count"] = min(wait_count, 100)
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
                import json
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
            framework_count = frameworks.read_text().count("##")
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
            evidence["uses_lateral_thinking"] = True
        else:
            triggers.append("no_lateral_thinking")
            evidence["uses_lateral_thinking"] = False
        
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
    "adaptive": None,  # TODO
    "collaboration": None,  # TODO
    "protection": None,  # TODO
    "prediction": None,  # TODO
    "self_awareness": None,  # TODO
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
