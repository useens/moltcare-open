#!/usr/bin/env python3
"""
弱项分析模块
分析评估结果，识别最弱3项，制定针对性升级方案
"""

import os
import json
from datetime import datetime
from pathlib import Path

class WeaknessAnalyzer:
    def __init__(self, workspace_path="/root/.openclaw/workspace"):
        self.workspace = Path(workspace_path)
        self.data_dir = self.workspace / "data"
        self.config_dir = self.workspace / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.weaknesses = []
        self.upgrade_plan = {}
    
    def load_latest_assessment(self):
        """加载最新的评估结果"""
        assessment_files = sorted(self.data_dir.glob("assessment-*.json"))
        if not assessment_files:
            raise FileNotFoundError("未找到评估结果文件")
        
        latest = assessment_files[-1]
        print(f"加载评估结果: {latest}")
        return json.loads(latest.read_text())
    
    def identify_weaknesses(self, assessment):
        """识别最弱的3个维度"""
        dimensions = assessment.get("dimensions", {})
        
        # 按百分比排序
        sorted_dims = sorted(
            dimensions.items(),
            key=lambda x: x[1]["percentage"]
        )
        
        # 取最弱的3个
        weakest = sorted_dims[:3]
        self.weaknesses = [
            {
                "name": name,
                "score": dim["score"],
                "max_score": dim["max_score"],
                "percentage": dim["percentage"],
                "details": dim["details"]
            }
            for name, dim in weakest
        ]
        
        return self.weaknesses
    
    def generate_upgrade_strategy(self, weakness):
        """为特定弱项生成升级策略"""
        name = weakness["name"]
        percentage = weakness["percentage"]
        
        strategies = {
            "自主决策能力": {
                "priority": "high" if percentage < 50 else "medium",
                "actions": [
                    "完善SOUL.md L1-L6架构配置",
                    "强化AGENTS.md启动自检流程",
                    "建立决策执行日志",
                    "实施L6反馈学习闭环"
                ],
                "resources": ["SOUL.md", "AGENTS.md", "scripts/decision-log.py"],
                "expected_improvement": 15,
                "duration_days": 7
            },
            "工具使用熟练度": {
                "priority": "high" if percentage < 50 else "medium",
                "actions": [
                    "系统化工具矩阵训练",
                    "创建工具组合场景库",
                    "实施跨工具协同练习",
                    "建立工具使用最佳实践文档"
                ],
                "resources": ["scripts/tool-training.py", "docs/tool-matrix.md"],
                "expected_improvement": 20,
                "duration_days": 14
            },
            "问题解决闭环率": {
                "priority": "high" if percentage < 50 else "medium",
                "actions": [
                    "清理learning-debt.md积压",
                    "建立学习→内化→应用→检验流程",
                    "完善知识图谱关联",
                    "实施每日学习复盘"
                ],
                "resources": ["learning-debt.md", "knowledge-graph.md"],
                "expected_improvement": 18,
                "duration_days": 10
            },
            "记忆系统健康度": {
                "priority": "high" if percentage < 50 else "medium",
                "actions": [
                    "完善MEMORY.md长期记忆",
                    "建立每日记忆自动归档",
                    "优化记忆检索效率",
                    "实施记忆定期整理"
                ],
                "resources": ["MEMORY.md", "memory/"],
                "expected_improvement": 15,
                "duration_days": 7
            },
            "绝对诚实验证通过率": {
                "priority": "critical" if percentage < 40 else "high",
                "actions": [
                    "严格执行连续3次验证机制",
                    "建立验证失败根因分析",
                    "完善数据真实性检查",
                    "实施验证结果可追溯"
                ],
                "resources": ["data/verification-history.json"],
                "expected_improvement": 25,
                "duration_days": 5
            },
            "任务执行效率": {
                "priority": "medium",
                "actions": [
                    "优化任务分解策略",
                    "建立时间预估模型",
                    "实施并行处理机制",
                    "完善任务执行监控"
                ],
                "resources": ["data/task-history.json"],
                "expected_improvement": 12,
                "duration_days": 14
            }
        }
        
        return strategies.get(name, {
            "priority": "medium",
            "actions": ["通用改进措施"],
            "resources": [],
            "expected_improvement": 10,
            "duration_days": 7
        })
    
    def create_upgrade_plan(self):
        """创建完整升级计划"""
        plan = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "based_on_assessment": None,
            "weaknesses": [],
            "phases": [],
            "target_score": 0,
            "estimated_completion": None
        }
        
        # 加载评估结果
        assessment = self.load_latest_assessment()
        plan["based_on_assessment"] = assessment.get("date", datetime.now().strftime("%Y-%m-%d"))
        plan["current_score"] = assessment.get("overall_score", 0)
        
        # 识别弱项
        weaknesses = self.identify_weaknesses(assessment)
        plan["weaknesses"] = weaknesses
        
        print(f"\n识别到 {len(weaknesses)} 个弱项:")
        for i, w in enumerate(weaknesses, 1):
            print(f"  {i}. {w['name']}: {w['percentage']}%")
        
        # 为每个弱项生成升级策略
        total_improvement = 0
        max_duration = 0
        
        for i, weakness in enumerate(weaknesses):
            strategy = self.generate_upgrade_strategy(weakness)
            
            phase = {
                "phase": i + 1,
                "target": weakness["name"],
                "current_percentage": weakness["percentage"],
                "strategy": strategy,
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }
            
            plan["phases"].append(phase)
            total_improvement += strategy["expected_improvement"]
            max_duration = max(max_duration, strategy["duration_days"])
        
        # 计算目标分数
        plan["target_score"] = min(plan["current_score"] + total_improvement / 6, 100)
        
        # 估算完成时间
        from datetime import timedelta
        completion_date = datetime.now() + timedelta(days=max_duration)
        plan["estimated_completion"] = completion_date.strftime("%Y-%m-%d")
        
        self.upgrade_plan = plan
        return plan
    
    def save_upgrade_plan(self):
        """保存升级计划"""
        plan_path = self.config_dir / "upgrade-plan.json"
        plan_path.write_text(json.dumps(self.upgrade_plan, indent=2, ensure_ascii=False))
        print(f"\n升级计划已保存: {plan_path}")
        return plan_path
    
    def generate_weakness_report(self):
        """生成弱项分析报告"""
        if not self.weaknesses:
            self.create_upgrade_plan()
        
        date_str = datetime.now().strftime("%Y%m%d")
        report_path = self.workspace / "reports" / f"weakness-analysis-{date_str}.md"
        
        report = f"""# 弱项分析报告

**分析时间**: {datetime.now().isoformat()}
**基于评估**: {self.upgrade_plan.get('based_on_assessment', 'N/A')}

---

## 当前状态

- **综合评分**: {self.upgrade_plan.get('current_score', 0)}/100
- **目标评分**: {self.upgrade_plan.get('target_score', 0):.1f}/100
- **预计完成**: {self.upgrade_plan.get('estimated_completion', 'N/A')}

---

## 优先改进项 (Top 3)

"""
        
        for i, weakness in enumerate(self.weaknesses, 1):
            phase = self.upgrade_plan["phases"][i-1]
            strategy = phase["strategy"]
            
            report += f"""### {i}. {weakness['name']}

- **当前得分**: {weakness['score']}/{weakness['max_score']} ({weakness['percentage']}%)
- **优先级**: {strategy['priority'].upper()}
- **预期提升**: +{strategy['expected_improvement']}%
- **预计周期**: {strategy['duration_days']} 天

**问题详情**:
"""
            for detail in weakness['details']:
                report += f"- {detail}\n"
            
            report += f"\n**升级行动**:\n"
            for action in strategy['actions']:
                report += f"1. {action}\n"
            
            report += f"\n**所需资源**:\n"
            for resource in strategy['resources']:
                report += f"- `{resource}`\n"
            
            report += "\n---\n\n"
        
        report += f"""## 执行计划

### 阶段安排

| 阶段 | 目标 | 优先级 | 周期 | 状态 |
|------|------|--------|------|------|
"""
        for phase in self.upgrade_plan["phases"]:
            strategy = phase["strategy"]
            report += f"| 阶段{phase['phase']} | {phase['target']} | {strategy['priority']} | {strategy['duration_days']}天 | {phase['status']} |\n"
        
        report += f"""
### 关键里程碑

1. **第1周**: 完成最高优先级弱项改进
2. **第2周**: 完成次要优先级改进  
3. **第3周**: 全面验证与调整
4. **持续**: 建立长期改进机制

---
*由弱项分析系统自动生成*
"""
        
        report_path.write_text(report)
        print(f"弱项分析报告已生成: {report_path}")
        return report_path
    
    def run_analysis(self):
        """执行完整分析流程"""
        print("="*60)
        print("开始弱项分析...")
        print("="*60)
        
        # 创建升级计划
        self.create_upgrade_plan()
        
        # 保存计划
        self.save_upgrade_plan()
        
        # 生成报告
        self.generate_weakness_report()
        
        print("\n" + "="*60)
        print("弱项分析完成")
        print(f"当前评分: {self.upgrade_plan.get('current_score', 0)}")
        print(f"目标评分: {self.upgrade_plan.get('target_score', 0):.1f}")
        print(f"预计完成: {self.upgrade_plan.get('estimated_completion', 'N/A')}")
        print("="*60)
        
        return self.upgrade_plan

if __name__ == "__main__":
    analyzer = WeaknessAnalyzer()
    plan = analyzer.run_analysis()
