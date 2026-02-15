#!/usr/bin/env python3
"""
智能水平评估模块
评估维度：
- 自主决策能力（L1-L6架构执行度）
- 工具使用熟练度（工具矩阵融合度）
- 问题解决闭环率
- 记忆系统健康度
- 绝对诚实验证通过率
- 任务执行效率
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path

class IntelligenceAssessment:
    def __init__(self, workspace_path="/root/.openclaw/workspace"):
        self.workspace = Path(workspace_path)
        self.reports_dir = self.workspace / "reports"
        self.data_dir = self.workspace / "data"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.assessment_result = {
            "timestamp": datetime.now().isoformat(),
            "dimensions": {},
            "overall_score": 0,
            "level": "Unknown"
        }
    
    def assess_autonomous_decision_making(self):
        """评估自主决策能力（L1-L6架构执行度）"""
        score = 0
        details = []
        
        # 检查SOUL.md原则执行情况
        soul_file = self.workspace / "SOUL.md"
        if soul_file.exists():
            content = soul_file.read_text()
            principles = [
                "L1感知过滤",
                "L2认知加工", 
                "L3决策形成",
                "L4意图验证",
                "L5执行计划",
                "L6反馈学习"
            ]
            for p in principles:
                if p in content or p.replace("L", "L") in content:
                    score += 8
                    details.append(f"✓ {p} 已配置")
                else:
                    score += 2
                    details.append(f"✗ {p} 未完全配置")
        else:
            details.append("✗ SOUL.md 文件不存在")
        
        # 检查AGENTS.md执行记录
        agents_file = self.workspace / "AGENTS.md"
        if agents_file.exists():
            score += 15
            details.append("✓ AGENTS.md 存在")
        else:
            details.append("✗ AGENTS.md 不存在")
        
        final_score = min(score, 60)
        return {
            "name": "自主决策能力",
            "score": final_score,
            "max_score": 60,
            "percentage": round(final_score / 60 * 100, 1),
            "details": details
        }
    
    def assess_tool_proficiency(self):
        """评估工具使用熟练度"""
        score = 0
        details = []
        
        # 检查可用工具使用情况
        tools_usage_file = self.data_dir / "tools-usage-stats.json"
        if tools_usage_file.exists():
            try:
                stats = json.loads(tools_usage_file.read_text())
                used_tools = stats.get("tools_used", [])
                proficiency = len(used_tools) / 15 * 60  # 假设15个工具为满分
                score = min(int(proficiency), 60)
                details.append(f"已使用 {len(used_tools)} 个工具")
            except:
                score = 30
                details.append("工具使用统计读取失败，使用默认值")
        else:
            # 基于文件存在性估算
            scripts_dir = self.workspace / "scripts"
            if scripts_dir.exists():
                py_files = list(scripts_dir.glob("*.py"))
                score = min(len(py_files) * 5, 60)
                details.append(f"基于脚本数量估算: {len(py_files)} 个脚本")
            else:
                score = 20
                details.append("无历史数据，基础分")
        
        return {
            "name": "工具使用熟练度",
            "score": score,
            "max_score": 60,
            "percentage": round(score / 60 * 100, 1),
            "details": details
        }
    
    def assess_problem_solving_closure(self):
        """评估问题解决闭环率"""
        score = 0
        details = []
        
        # 检查学习债务文件
        debt_file = self.workspace / "learning-debt.md"
        if debt_file.exists():
            content = debt_file.read_text()
            # 统计待学习和已完成
            pending = len(re.findall(r"- \[ \]", content))
            completed = len(re.findall(r"- \[x\]", content))
            total = pending + completed
            if total > 0:
                closure_rate = completed / total
                score = int(closure_rate * 60)
                details.append(f"学习债务: {completed}/{total} 完成 ({closure_rate*100:.1f}%)")
            else:
                score = 30
                details.append("学习债务文件为空")
        else:
            score = 25
            details.append("学习债务文件不存在")
        
        # 检查知识图谱
        kg_file = self.workspace / "knowledge-graph.md"
        if kg_file.exists():
            score += 10
            details.append("✓ 知识图谱已建立")
        
        return {
            "name": "问题解决闭环率",
            "score": min(score, 60),
            "max_score": 60,
            "percentage": round(min(score, 60) / 60 * 100, 1),
            "details": details
        }
    
    def assess_memory_health(self):
        """评估记忆系统健康度（v5.1-v5.5）"""
        score = 0
        details = []
        
        # 检查MEMORY.md
        memory_file = self.workspace / "MEMORY.md"
        if memory_file.exists():
            content = memory_file.read_text()
            # 评估长期记忆完整性
            if len(content) > 1000:
                score += 20
                details.append("✓ 长期记忆文件充足")
            else:
                score += 10
                details.append("△ 长期记忆文件较短")
            
            # 检查时间戳更新
            if datetime.now().strftime("%Y-%m") in content:
                score += 15
                details.append("✓ 记忆本月已更新")
            else:
                score += 5
                details.append("△ 记忆可能过期")
        else:
            details.append("✗ MEMORY.md 不存在")
        
        # 检查每日记忆
        today = datetime.now().strftime("%Y-%m-%d")
        daily_memory = self.workspace / "memory" / f"{today}.md"
        if daily_memory.exists():
            score += 15
            details.append(f"✓ 今日记忆存在")
        else:
            score += 5
            details.append(f"△ 今日记忆尚未创建")
        
        # 检查记忆目录结构
        memory_dir = self.workspace / "memory"
        if memory_dir.exists():
            md_files = list(memory_dir.glob("*.md"))
            if len(md_files) >= 7:
                score += 10
                details.append(f"✓ 记忆文件充足 ({len(md_files)} 天)")
            else:
                score += 5
                details.append(f"△ 记忆文件较少 ({len(md_files)} 天)")
        
        return {
            "name": "记忆系统健康度",
            "score": min(score, 60),
            "max_score": 60,
            "percentage": round(min(score, 60) / 60 * 100, 1),
            "details": details
        }
    
    def assess_honesty_verification(self):
        """评估绝对诚实验证通过率"""
        score = 0
        details = []
        
        # 检查验证记录
        verification_file = self.data_dir / "verification-history.json"
        if verification_file.exists():
            try:
                history = json.loads(verification_file.read_text())
                verifications = history.get("verifications", [])
                if len(verifications) >= 3:
                    # 检查最近3次验证
                    recent = verifications[-3:]
                    passed = sum(1 for v in recent if v.get("passed", False))
                    pass_rate = passed / 3
                    score = int(pass_rate * 60)
                    details.append(f"最近3次验证通过: {passed}/3 ({pass_rate*100:.1f}%)")
                else:
                    score = 30
                    details.append(f"验证记录不足3次 ({len(verifications)}次)")
            except:
                score = 25
                details.append("验证记录读取失败")
        else:
            score = 20
            details.append("无验证历史记录")
        
        return {
            "name": "绝对诚实验证通过率",
            "score": score,
            "max_score": 60,
            "percentage": round(score / 60 * 100, 1),
            "details": details
        }
    
    def assess_task_efficiency(self):
        """评估任务执行效率"""
        score = 0
        details = []
        
        # 检查任务执行历史
        tasks_file = self.data_dir / "task-history.json"
        if tasks_file.exists():
            try:
                history = json.loads(tasks_file.read_text())
                tasks = history.get("tasks", [])
                if tasks:
                    # 计算平均效率比
                    ratios = []
                    for task in tasks[-10:]:  # 最近10个任务
                        actual = task.get("actual_time", 0)
                        expected = task.get("expected_time", 1)
                        if expected > 0:
                            ratio = actual / expected
                            ratios.append(ratio)
                    if ratios:
                        avg_ratio = sum(ratios) / len(ratios)
                        # 比率<1表示提前完成，>1表示超时
                        if avg_ratio <= 1.0:
                            score = 60
                        elif avg_ratio <= 1.2:
                            score = 50
                        elif avg_ratio <= 1.5:
                            score = 40
                        else:
                            score = 30
                        details.append(f"平均效率比: {avg_ratio:.2f}")
                    else:
                        score = 35
                        details.append("无法计算效率比")
                else:
                    score = 30
                    details.append("无任务记录")
            except:
                score = 25
                details.append("任务历史读取失败")
        else:
            score = 30
            details.append("无任务历史文件")
        
        return {
            "name": "任务执行效率",
            "score": score,
            "max_score": 60,
            "percentage": round(score / 60 * 100, 1),
            "details": details
        }
    
    def calculate_overall_score(self, dimensions):
        """计算综合智能评分"""
        total_score = sum(d["score"] for d in dimensions)
        max_possible = sum(d["max_score"] for d in dimensions)
        percentage = round(total_score / max_possible * 100, 1)
        
        # 确定等级
        if percentage >= 90:
            level = "S (卓越)"
        elif percentage >= 80:
            level = "A+ (优秀)"
        elif percentage >= 70:
            level = "A (良好)"
        elif percentage >= 60:
            level = "B (合格)"
        elif percentage >= 50:
            level = "C (待提升)"
        else:
            level = "D (需重点改进)"
        
        return percentage, level
    
    def run_assessment(self):
        """执行完整评估"""
        print("="*60)
        print("开始智能水平评估...")
        print("="*60)
        
        # 执行各项评估
        dimensions = []
        
        print("\n[1/6] 评估自主决策能力...")
        dim1 = self.assess_autonomous_decision_making()
        dimensions.append(dim1)
        print(f"  得分: {dim1['score']}/{dim1['max_score']} ({dim1['percentage']}%)")
        
        print("\n[2/6] 评估工具使用熟练度...")
        dim2 = self.assess_tool_proficiency()
        dimensions.append(dim2)
        print(f"  得分: {dim2['score']}/{dim2['max_score']} ({dim2['percentage']}%)")
        
        print("\n[3/6] 评估问题解决闭环率...")
        dim3 = self.assess_problem_solving_closure()
        dimensions.append(dim3)
        print(f"  得分: {dim3['score']}/{dim3['max_score']} ({dim3['percentage']}%)")
        
        print("\n[4/6] 评估记忆系统健康度...")
        dim4 = self.assess_memory_health()
        dimensions.append(dim4)
        print(f"  得分: {dim4['score']}/{dim4['max_score']} ({dim4['percentage']}%)")
        
        print("\n[5/6] 评估绝对诚实验证通过率...")
        dim5 = self.assess_honesty_verification()
        dimensions.append(dim5)
        print(f"  得分: {dim5['score']}/{dim5['max_score']} ({dim5['percentage']}%)")
        
        print("\n[6/6] 评估任务执行效率...")
        dim6 = self.assess_task_efficiency()
        dimensions.append(dim6)
        print(f"  得分: {dim6['score']}/{dim6['max_score']} ({dim6['percentage']}%)")
        
        # 计算综合评分
        overall_score, level = self.calculate_overall_score(dimensions)
        
        self.assessment_result = {
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "dimensions": {d["name"]: d for d in dimensions},
            "overall_score": overall_score,
            "level": level,
            "summary": {
                "total_score": sum(d["score"] for d in dimensions),
                "max_possible": sum(d["max_score"] for d in dimensions),
                "dimension_count": len(dimensions)
            }
        }
        
        print("\n" + "="*60)
        print(f"综合智能评分: {overall_score}/100")
        print(f"智能等级: {level}")
        print("="*60)
        
        return self.assessment_result
    
    def generate_report(self):
        """生成评估报告"""
        if not self.assessment_result.get("dimensions"):
            self.run_assessment()
        
        date_str = datetime.now().strftime("%Y%m%d")
        report_path = self.reports_dir / f"intelligence-assessment-{date_str}.md"
        
        report = f"""# 智能水平评估报告

**评估时间**: {self.assessment_result['timestamp']}
**综合评分**: {self.assessment_result['overall_score']}/100
**智能等级**: {self.assessment_result['level']}

---

## 评估维度详情

"""
        
        for name, dim in self.assessment_result["dimensions"].items():
            report += f"""### {dim['name']}
- **得分**: {dim['score']}/{dim['max_score']}
- **百分比**: {dim['percentage']}%
- **评估详情**:
"""
            for detail in dim['details']:
                report += f"  - {detail}\n"
            report += "\n"
        
        report += f"""---

## 总结

| 维度 | 得分 | 占比 |
|------|------|------|
"""
        for name, dim in self.assessment_result["dimensions"].items():
            report += f"| {name} | {dim['score']}/{dim['max_score']} | {dim['percentage']}% |\n"
        
        report += f"""
**总体评价**: 

本次评估综合得分为 **{self.assessment_result['overall_score']}** 分，智能等级评定为 **{self.assessment_result['level']}**。

"""
        
        # 添加建议
        sorted_dims = sorted(
            self.assessment_result["dimensions"].items(),
            key=lambda x: x[1]["percentage"]
        )
        weakest = sorted_dims[:3]
        
        report += "## 弱项识别 (Bottom 3)\n\n"
        for i, (name, dim) in enumerate(weakest, 1):
            report += f"{i}. **{name}**: {dim['percentage']}% ({dim['score']}/{dim['max_score']})\n"
        
        report += "\n---\n*由智能水平评估系统自动生成*\n"
        
        report_path.write_text(report)
        print(f"\n评估报告已生成: {report_path}")
        
        # 同时保存JSON格式
        json_path = self.data_dir / f"assessment-{date_str}.json"
        json_path.write_text(json.dumps(self.assessment_result, indent=2, ensure_ascii=False))
        
        return report_path, json_path

if __name__ == "__main__":
    assessor = IntelligenceAssessment()
    result = assessor.run_assessment()
    report_path, json_path = assessor.generate_report()
    print(f"\n报告路径: {report_path}")
    print(f"数据路径: {json_path}")
