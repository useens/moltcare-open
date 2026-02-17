#!/usr/bin/env python3
"""
森森量化反馈系统 - 核心引擎
实时追踪所有关键指标，驱动数据化进化
"""

import json
import os
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
METRICS_DIR = WORKSPACE / "metrics"
DAILY_DIR = METRICS_DIR / "daily"
VALIDATION_DIR = METRICS_DIR / "validation"

class MetricsEngine:
    """量化反馈引擎"""
    
    def __init__(self):
        self.dashboard_file = METRICS_DIR / "dashboard.json"
        self.load_dashboard()
    
    def load_dashboard(self):
        """加载仪表盘"""
        if self.dashboard_file.exists():
            with open(self.dashboard_file) as f:
                self.dashboard = json.load(f)
        else:
            self.dashboard = self._create_default_dashboard()
    
    def _create_default_dashboard(self):
        """创建默认仪表盘"""
        return {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "summary": {"honest_score": 0, "target_score": 75, "gap": 75},
            "dimensions": {},
            "active_debts": {},
            "today_progress": {"completed": [], "failed": []}
        }
    
    def update_metric(self, dimension, metric_name, value, evidence=None):
        """更新单个指标"""
        if dimension not in self.dashboard["dimensions"]:
            self.dashboard["dimensions"][dimension] = {"score": 0, "metrics": {}}
        
        self.dashboard["dimensions"][dimension]["metrics"][metric_name] = {
            "value": value,
            "updated_at": datetime.now().isoformat(),
            "evidence": evidence or ""
        }
        
        self._recalculate_dimension_score(dimension)
        self._save_dashboard()
    
    def _recalculate_dimension_score(self, dimension):
        """重新计算维度得分"""
        metrics = self.dashboard["dimensions"][dimension].get("metrics", {})
        if not metrics:
            return
        
        # 简化算法：有值指标的平均达成率
        scores = []
        for name, data in metrics.items():
            if "target" in str(data):
                # 计算达成率
                target = data.get("target", 100)
                value = data.get("value", 0)
                if target > 0:
                    achievement = min(100, (value / target) * 100)
                    scores.append(achievement)
        
        if scores:
            self.dashboard["dimensions"][dimension]["score"] = round(sum(scores) / len(scores), 1)
    
    def validate_debt_completion(self, debt_id, validation_type="auto"):
        """验证债务真正完成"""
        validation_record = {
            "debt_id": debt_id,
            "timestamp": datetime.now().isoformat(),
            "type": validation_type,
            "checks": []
        }
        
        # 检查1：学习笔记文件存在
        note_file = WORKSPACE / "memory" / "debt-learning" / f"{debt_id}.md"
        validation_record["checks"].append({
            "name": "note_file_exists",
            "passed": note_file.exists(),
            "path": str(note_file)
        })
        
        # 检查2：关联系统改进（如果有）
        # TODO: 解析笔记内容，提取action items并验证
        
        # 保存验证记录
        validation_file = VALIDATION_DIR / f"{debt_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(validation_file, 'w') as f:
            json.dump(validation_record, f, indent=2)
        
        return validation_record
    
    def generate_daily_report(self):
        """生成每日报告"""
        report = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "overall_score": self._calculate_overall_score(),
            "dimension_scores": {
                name: data["score"] 
                for name, data in self.dashboard["dimensions"].items()
            },
            "red_flags": self._identify_red_flags(),
            "recommendations": self._generate_recommendations()
        }
        
        # 保存报告
        report_file = DAILY_DIR / f"report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def _calculate_overall_score(self):
        """计算综合得分"""
        scores = []
        weights = {
            "execution": 0.25,
            "cognitive_depth": 0.20,
            "system_robustness": 0.20,
            "autonomy": 0.15,
            "evolution_speed": 0.10,
            "metacognition": 0.10
        }
        
        for dim_name, dim_data in self.dashboard["dimensions"].items():
            if dim_name in weights:
                scores.append(dim_data.get("score", 0) * weights[dim_name])
        
        return round(sum(scores), 1) if scores else 0
    
    def _identify_red_flags(self):
        """识别危险信号"""
        flags = []
        
        # 检查各维度
        for dim_name, dim_data in self.dashboard["dimensions"].items():
            score = dim_data.get("score", 0)
            if score < 50:
                flags.append({
                    "level": "critical",
                    "dimension": dim_name,
                    "score": score,
                    "message": f"{dim_name}得分过低，需立即干预"
                })
            elif score < 60:
                flags.append({
                    "level": "warning",
                    "dimension": dim_name,
                    "score": score,
                    "message": f"{dim_name}需要关注"
                })
        
        return flags
    
    def _generate_recommendations(self):
        """生成改进建议"""
        recs = []
        
        # 基于数据生成建议
        exec_score = self.dashboard.get("dimensions", {}).get("execution", {}).get("score", 0)
        if exec_score < 70:
            recs.append("优先：提高任务完成度，减少半成品")
        
        robust_score = self.dashboard.get("dimensions", {}).get("system_robustness", {}).get("score", 0)
        if robust_score < 60:
            recs.append("紧急：修复系统健壮性问题（Cron/向量检索）")
        
        return recs
    
    def _save_dashboard(self):
        """保存仪表盘"""
        self.dashboard["last_updated"] = datetime.now().isoformat()
        self.dashboard["summary"]["honest_score"] = self._calculate_overall_score()
        
        with open(self.dashboard_file, 'w') as f:
            json.dump(self.dashboard, f, indent=2)
    
    def display_status(self):
        """显示当前状态"""
        print("=" * 60)
        print(f"🎯 森森量化反馈系统 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 60)
        print(f"\n综合得分: {self.dashboard['summary']['honest_score']:.1f} / 100")
        print(f"目标得分: {self.dashboard['summary']['target_score']:.1f}")
        print(f"差距: {self.dashboard['summary']['gap']:.1f}")
        
        print("\n📊 维度得分:")
        for name, data in self.dashboard["dimensions"].items():
            score = data.get("score", 0)
            emoji = "🔴" if score < 60 else "🟡" if score < 75 else "🟢"
            print(f"  {emoji} {name:20s}: {score:.1f}")
        
        print(f"\n📝 活跃债务: {self.dashboard.get('active_debts', {}).get('total', 'N/A')}条")
        
        # 危险信号
        flags = self._identify_red_flags()
        if flags:
            print("\n⚠️  危险信号:")
            for flag in flags:
                print(f"  [{flag['level'].upper()}] {flag['message']}")
        
        print("\n" + "=" * 60)


if __name__ == "__main__":
    engine = MetricsEngine()
    engine.display_status()
    
    # 验证今日完成的债务
    today_debts = ["DEBT-JACKLE-001", "DEBT-FRED-001", "DEBT-GOOD-SAMARITAN-001", "DEBT-SAME-RIVER-001"]
    print("\n🔍 验证今日债务完成度:")
    for debt_id in today_debts:
        result = engine.validate_debt_completion(debt_id)
        passed = sum(1 for c in result["checks"] if c["passed"])
        total = len(result["checks"])
        status = "✅" if passed == total else "⚠️"
        print(f"  {status} {debt_id}: {passed}/{total} 检查通过")
    
    # 生成每日报告
    report = engine.generate_daily_report()
    print(f"\n📄 每日报告已生成: metrics/daily/report_{datetime.now().strftime('%Y%m%d')}.json")
