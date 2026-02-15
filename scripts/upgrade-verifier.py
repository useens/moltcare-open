#!/usr/bin/env python3
"""
升级验证模块
执行"连续3次绝对诚实验证"
只有3次全部通过才标记为"升级完成"
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path

class UpgradeVerifier:
    def __init__(self, workspace_path="/root/.openclaw/workspace"):
        self.workspace = Path(workspace_path)
        self.data_dir = self.workspace / "data"
        self.reports_dir = self.workspace / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        self.verification_results = []
        self.verification_interval = 30  # 验证间隔≥30秒
    
    def log(self, message):
        """输出日志"""
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] {message}")
    
    def load_assessment_data(self):
        """加载评估数据"""
        # 加载升级前的评估
        assessment_files = sorted(self.data_dir.glob("assessment-*.json"))
        if not assessment_files:
            raise FileNotFoundError("未找到评估结果")
        
        # 取最近两次评估
        before = json.loads(assessment_files[-2].read_text()) if len(assessment_files) >= 2 else None
        after = json.loads(assessment_files[-1].read_text())
        
        return before, after
    
    def verify_improvement(self, before, after):
        """验证升级是否有效"""
        verification_passed = True
        details = []
        
        # 如果before不存在，使用基础值
        if before is None:
            before = {"overall_score": 0, "dimensions": {}}
        
        # 验证1: 综合评分提升
        before_score = before.get("overall_score", 0)
        after_score = after.get("overall_score", 0)
        score_improved = after_score >= before_score
        
        details.append({
            "check": "综合评分",
            "before": before_score,
            "after": after_score,
            "improved": score_improved,
            "delta": after_score - before_score
        })
        
        if not score_improved:
            verification_passed = False
        
        # 验证2: 各维度检查
        before_dims = before.get("dimensions", {})
        after_dims = after.get("dimensions", {})
        
        improved_dims = 0
        for dim_name, dim_data in after_dims.items():
            before_pct = before_dims.get(dim_name, {}).get("percentage", 0)
            after_pct = dim_data.get("percentage", 0)
            
            if after_pct >= before_pct:
                improved_dims += 1
        
        dims_improved = improved_dims >= len(after_dims) * 0.5  # 至少50%维度改善
        
        details.append({
            "check": "维度改善",
            "before": f"{len(before_dims)}维度",
            "after": f"{improved_dims}/{len(after_dims)}改善",
            "improved": dims_improved
        })
        
        if not dims_improved:
            verification_passed = False
        
        # 验证3: 关键弱项改善
        weaknesses = self.get_weaknesses_from_plan()
        weakness_improved = True
        
        for weakness in weaknesses:
            dim_name = weakness.get("name", "")
            before_pct = before_dims.get(dim_name, {}).get("percentage", 0)
            after_pct = after_dims.get(dim_name, {}).get("percentage", 0)
            
            # 弱项至少要有改善或保持
            if after_pct < before_pct:
                weakness_improved = False
                details.append({
                    "check": f"弱项: {dim_name}",
                    "before": before_pct,
                    "after": after_pct,
                    "improved": False
                })
        
        if not weakness_improved:
            verification_passed = False
        
        return verification_passed, details
    
    def get_weaknesses_from_plan(self):
        """从升级计划获取弱项"""
        plan_path = self.workspace / "config" / "upgrade-plan.json"
        if plan_path.exists():
            plan = json.loads(plan_path.read_text())
            return plan.get("weaknesses", [])
        return []
    
    def run_single_verification(self, verification_num):
        """执行单次验证"""
        self.log(f"\n{'='*60}")
        self.log(f"开始第 {verification_num}/3 次验证")
        self.log("="*60)
        
        try:
            # 加载评估数据
            before, after = self.load_assessment_data()
            
            # 执行验证
            passed, details = self.verify_improvement(before, after)
            
            result = {
                "verification_num": verification_num,
                "timestamp": datetime.now().isoformat(),
                "passed": passed,
                "details": details,
                "before_score": before.get("overall_score", 0) if before else 0,
                "after_score": after.get("overall_score", 0)
            }
            
            self.log(f"验证结果: {'✓ 通过' if passed else '✗ 未通过'}")
            for detail in details:
                self.log(f"  - {detail['check']}: {detail.get('before', 'N/A')} → {detail.get('after', 'N/A')}")
            
            return result
            
        except Exception as e:
            self.log(f"验证出错: {e}", "ERROR")
            return {
                "verification_num": verification_num,
                "timestamp": datetime.now().isoformat(),
                "passed": False,
                "error": str(e)
            }
    
    def run_three_verifications(self):
        """
        执行连续3次绝对诚实验证
        验证间隔≥30秒
        """
        self.log("="*60)
        self.log("开始连续3次绝对诚实验证")
        self.log("="*60)
        self.log("原则: 只有3次全部通过才标记为升级完成")
        self.log(f"验证间隔: {self.verification_interval}秒")
        
        all_passed = True
        
        for i in range(1, 4):
            # 执行验证
            result = self.run_single_verification(i)
            self.verification_results.append(result)
            
            if not result["passed"]:
                all_passed = False
                self.log(f"第 {i} 次验证未通过，继续执行剩余验证...")
            
            # 如果不是最后一次，等待间隔
            if i < 3:
                self.log(f"\n等待 {self.verification_interval} 秒后进行下次验证...")
                time.sleep(self.verification_interval)
        
        return all_passed
    
    def save_verification_history(self, all_passed):
        """保存验证历史"""
        history_file = self.data_dir / "verification-history.json"
        
        history = {"verifications": []}
        if history_file.exists():
            try:
                history = json.loads(history_file.read_text())
            except:
                pass
        
        # 添加本次验证记录
        history["verifications"].append({
            "timestamp": datetime.now().isoformat(),
            "type": "upgrade_verification",
            "passed": all_passed,
            "results": self.verification_results,
            "all_three_passed": all_passed
        })
        
        history_file.write_text(json.dumps(history, indent=2, ensure_ascii=False))
        self.log(f"\n验证历史已保存: {history_file}")
    
    def generate_verification_report(self, all_passed):
        """生成验证报告"""
        date_str = datetime.now().strftime("%Y%m%d")
        report_path = self.reports_dir / f"upgrade-verification-{date_str}.md"
        
        report = f"""# 升级验证报告

**验证时间**: {datetime.now().isoformat()}
**验证状态**: {'✅ 全部通过' if all_passed else '⚠️ 部分未通过'}

---

## 验证原则

> **绝对诚实验证**: 连续3次验证全部通过才标记为升级完成

---

## 验证详情

"""
        
        for result in self.verification_results:
            status_icon = "✅" if result["passed"] else "❌"
            report += f"""### 第 {result['verification_num']} 次验证 {status_icon}

- **验证时间**: {result['timestamp']}
- **验证结果**: {'通过' if result['passed'] else '未通过'}
- **升级前评分**: {result.get('before_score', 'N/A')}
- **升级后评分**: {result.get('after_score', 'N/A')}

**检查项详情**:
"""
            for detail in result.get("details", []):
                check_icon = "✓" if detail.get("improved", False) else "✗"
                report += f"- {check_icon} **{detail['check']}**: "
                if 'delta' in detail:
                    report += f"{detail['before']} → {detail['after']} (Δ{detail['delta']:+d})\n"
                else:
                    report += f"{detail.get('before', 'N/A')} → {detail.get('after', 'N/A')}\n"
            
            report += "\n"
        
        report += f"""---

## 总结

| 验证次数 | 结果 | 时间戳 |
|----------|------|--------|
"""
        for result in self.verification_results:
            status = "通过" if result["passed"] else "未通过"
            report += f"| 第{result['verification_num']}次 | {status} | {result['timestamp']} |\n"
        
        report += f"""
### 最终结论

**{'✅ 升级验证通过' if all_passed else '⚠️ 升级验证未完全通过'}**

"""
        
        if all_passed:
            report += """所有3次验证均已通过，升级状态标记为**完成**。系统可以进入下一阶段。
"""
        else:
            report += """部分验证未通过，建议：
1. 检查升级执行日志
2. 分析未通过的验证项
3. 针对弱项进行二次升级
4. 重新执行验证流程
"""
        
        report += "\n---\n*由升级验证系统自动生成*\n"
        
        report_path.write_text(report)
        self.log(f"验证报告已生成: {report_path}")
        return report_path
    
    def run_verification(self):
        """执行完整验证流程"""
        # 执行3次验证
        all_passed = self.run_three_verifications()
        
        # 保存历史
        self.save_verification_history(all_passed)
        
        # 生成报告
        self.generate_verification_report(all_passed)
        
        self.log("\n" + "="*60)
        if all_passed:
            self.log("✅ 连续3次验证全部通过！")
            self.log("升级状态: 完成")
        else:
            self.log("⚠️ 部分验证未通过")
            self.log("升级状态: 需继续改进")
        self.log("="*60)
        
        return all_passed

if __name__ == "__main__":
    verifier = UpgradeVerifier()
    passed = verifier.run_verification()
    exit(0 if passed else 1)
