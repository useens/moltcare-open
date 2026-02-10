#!/usr/bin/env python3
"""
林林v5.0 预测准确率报告生成器 (Prediction Accuracy Report)
版本: v5.0
职责: 生成预测系统的准确率分析报告

报告内容:
1. 整体准确率统计
2. A/B测试结果分析
3. 时间模式预测准确率
4. 上下文关联准确率
5. 优化建议
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
import math


class PredictionAccuracyReport:
    """
    预测准确率报告生成器
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.report_dir = os.path.join(data_dir, "reports")
        os.makedirs(self.report_dir, exist_ok=True)
        
        # 数据文件路径
        self.ab_test_file = os.path.join(data_dir, "ab_test_results.json")
        self.time_pattern_file = os.path.join(data_dir, "time_patterns.json")
        self.association_file = os.path.join(data_dir, "context_associations.json")
        self.feedback_file = os.path.join(data_dir, "prediction_feedback.json")
    
    def generate_report(self, days: int = 30) -> Dict[str, Any]:
        """
        生成完整报告
        
        Args:
            days: 报告时间范围（天数）
            
        Returns:
            报告数据字典
        """
        report = {
            "generated_at": datetime.now().isoformat(),
            "report_period_days": days,
            "summary": self._generate_summary(days),
            "ab_test_analysis": self._analyze_ab_test(days),
            "time_pattern_accuracy": self._analyze_time_patterns(days),
            "context_association_accuracy": self._analyze_context_associations(days),
            "prediction_type_breakdown": self._analyze_prediction_types(days),
            "confidence_analysis": self._analyze_confidence_levels(days),
            "trends": self._analyze_trends(days),
            "recommendations": self._generate_recommendations(),
            "charts_data": self._generate_charts_data(days)
        }
        
        return report
    
    def save_report(self, report: Dict, filename: Optional[str] = None):
        """保存报告到文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"prediction_accuracy_report_{timestamp}.json"
        
        filepath = os.path.join(self.report_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def generate_markdown_report(self, days: int = 30) -> str:
        """生成Markdown格式的报告"""
        report = self.generate_report(days)
        
        # 安全获取嵌套值
        def safe_get(obj, *keys, default=0):
            for key in keys:
                if isinstance(obj, dict) and key in obj:
                    obj = obj[key]
                else:
                    return default
            return obj
        
        summary = report.get('summary', {})
        by_confidence = summary.get('by_confidence', {})
        
        md = f"""# 林林v5.0 预测准确率报告

**生成时间**: {report.get('generated_at', 'N/A')}  
**报告周期**: 最近 {days} 天

---

## 📊 总体概况

| 指标 | 数值 |
|------|------|
| 总预测次数 | {summary.get('total_predictions', 0)} |
| 准确预测 | {summary.get('correct_predictions', 0)} |
| **整体准确率** | **{safe_get(summary, 'accuracy_rate', default=0):.1%}** |
| 被接受建议 | {summary.get('accepted_suggestions', 0)} |
| 接受率 | {safe_get(summary, 'acceptance_rate', default=0):.1%} |

### 按置信度分布

| 置信度区间 | 数量 | 准确率 |
|------------|------|--------|
| 90-100% | {safe_get(by_confidence, '90_100', 'count', default=0)} | {safe_get(by_confidence, '90_100', 'accuracy', default=0):.1%} |
| 80-90% | {safe_get(by_confidence, '80_90', 'count', default=0)} | {safe_get(by_confidence, '80_90', 'accuracy', default=0):.1%} |
| 70-80% | {safe_get(by_confidence, '70_80', 'count', default=0)} | {safe_get(by_confidence, '70_80', 'accuracy', default=0):.1%} |
| <70% | {safe_get(by_confidence, 'below_70', 'count', default=0)} | {safe_get(by_confidence, 'below_70', 'accuracy', default=0):.1%} |

---

## 🧪 A/B测试结果

"""
        
        # A/B测试部分
        ab_test = report['ab_test_analysis']
        if ab_test.get('groups'):
            md += "| 测试组 | 总预测 | 接受数 | 接受率 | 平均置信度 |\n"
            md += "|--------|--------|--------|--------|------------|\n"
            
            for group_name, stats in ab_test['groups'].items():
                md += f"| {group_name} | {stats['total']} | {stats['accepted']} | {stats['acceptance_rate']:.1%} | {stats['avg_confidence']:.2f} |\n"
            
            md += f"\n**获胜组**: {ab_test.get('winner', 'N/A')}\n"
        else:
            md += "暂无A/B测试数据\n"
        
        md += f"""
---

## ⏰ 时间模式准确率

| 预测类型 | 预测次数 | 准确次数 | 准确率 |
|----------|----------|----------|--------|
"""
        
        # 时间模式部分
        time_patterns = report['time_pattern_accuracy']
        for pred_type, stats in time_patterns.get('by_type', {}).items():
            md += f"| {pred_type} | {stats['total']} | {stats['correct']} | {stats['accuracy']:.1%} |\n"
        
        md += f"""
**最佳预测时段**: {time_patterns.get('best_hour', 'N/A')}  
**最差预测时段**: {time_patterns.get('worst_hour', 'N/A')}

---

## 🔗 上下文关联准确率

"""
        
        # 上下文关联部分
        context = report['context_association_accuracy']
        if context.get('by_source_type'):
            md += "| 关联源 | 关联数 | 触发数 | 成功率 |\n"
            md += "|--------|--------|--------|--------|\n"
            
            for source, stats in context['by_source_type'].items():
                md += f"| {source} | {stats['associations']} | {stats['triggered']} | {stats['success_rate']:.1%} |\n"
        else:
            md += "暂无上下文关联数据\n"
        
        md += f"""
---

## 📈 预测类型分析

| 预测类型 | 数量 | 占比 | 准确率 | 平均置信度 |
|----------|------|------|--------|------------|
"""
        
        # 预测类型分解
        for pred_type, stats in report['prediction_type_breakdown'].items():
            md += f"| {pred_type} | {stats['count']} | {stats['percentage']:.1%} | {stats['accuracy']:.1%} | {stats['avg_confidence']:.2f} |\n"
        
        md += f"""
---

## 📉 趋势分析

**准确率趋势**: {report['trends']['accuracy_trend']}  
**接受率趋势**: {report['trends']['acceptance_trend']}  
**预测量趋势**: {report['trends']['volume_trend']}

---

## 💡 优化建议

"""
        
        # 建议部分
        for i, rec in enumerate(report['recommendations'], 1):
            md += f"{i}. **{rec['category']}**: {rec['message']}\n"
            if rec.get('action'):
                md += f"   - 建议操作: {rec['action']}\n"
        
        md += """
---

## 📝 说明

- **准确率**: 预测需求与实际需求匹配的比例
- **接受率**: 用户主动接受建议的比例
- **置信度**: 模型对预测结果的确信程度
- A/B测试用于比较不同预测策略的效果

---

*报告由林林v5.0 预判引擎自动生成*
"""
        
        return md
    
    def _generate_summary(self, days: int) -> Dict:
        """生成总体摘要"""
        # 加载反馈数据
        feedback_data = self._load_feedback_data(days)
        
        if not feedback_data:
            return {
                "total_predictions": 0,
                "correct_predictions": 0,
                "accuracy_rate": 0.0,
                "accepted_suggestions": 0,
                "acceptance_rate": 0.0,
                "by_confidence": {}
            }
        
        total = len(feedback_data)
        correct = sum(1 for f in feedback_data if f.get('was_accurate', False))
        accepted = sum(1 for f in feedback_data if f.get('was_accepted', False))
        
        # 按置信度分布
        by_confidence = {
            "90_100": {"count": 0, "correct": 0},
            "80_90": {"count": 0, "correct": 0},
            "70_80": {"count": 0, "correct": 0},
            "below_70": {"count": 0, "correct": 0}
        }
        
        for f in feedback_data:
            conf = f.get('confidence', 0)
            is_correct = f.get('was_accurate', False)
            
            if conf >= 0.9:
                key = "90_100"
            elif conf >= 0.8:
                key = "80_90"
            elif conf >= 0.7:
                key = "70_80"
            else:
                key = "below_70"
            
            by_confidence[key]["count"] += 1
            if is_correct:
                by_confidence[key]["correct"] += 1
        
        # 计算准确率
        for key in by_confidence:
            count = by_confidence[key]["count"]
            correct_count = by_confidence[key]["correct"]
            by_confidence[key]["accuracy"] = correct_count / count if count > 0 else 0
        
        return {
            "total_predictions": total,
            "correct_predictions": correct,
            "accuracy_rate": correct / total if total > 0 else 0,
            "accepted_suggestions": accepted,
            "acceptance_rate": accepted / total if total > 0 else 0,
            "by_confidence": by_confidence
        }
    
    def _analyze_ab_test(self, days: int) -> Dict:
        """分析A/B测试结果"""
        if not os.path.exists(self.ab_test_file):
            return {"groups": {}}
        
        try:
            with open(self.ab_test_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return {"groups": {}}
        
        cutoff = datetime.now() - timedelta(days=days)
        groups = defaultdict(lambda: {"total": 0, "accepted": 0, "confidences": []})
        
        for group_name, results in data.get("results", {}).items():
            for result in results:
                try:
                    ts = datetime.fromisoformat(result.get('timestamp', '2000-01-01'))
                    if ts >= cutoff:
                        groups[group_name]["total"] += 1
                        if result.get('was_accepted'):
                            groups[group_name]["accepted"] += 1
                        groups[group_name]["confidences"].append(result.get('confidence', 0))
                except:
                    continue
        
        # 计算统计
        analysis = {"groups": {}}
        best_group = None
        best_rate = 0
        
        for group_name, stats in groups.items():
            total = stats["total"]
            if total > 0:
                acceptance_rate = stats["accepted"] / total
                avg_confidence = sum(stats["confidences"]) / len(stats["confidences"]) if stats["confidences"] else 0
                
                analysis["groups"][group_name] = {
                    "total": total,
                    "accepted": stats["accepted"],
                    "acceptance_rate": acceptance_rate,
                    "avg_confidence": avg_confidence
                }
                
                if acceptance_rate > best_rate:
                    best_rate = acceptance_rate
                    best_group = group_name
        
        analysis["winner"] = best_group
        return analysis
    
    def _analyze_time_patterns(self, days: int) -> Dict:
        """分析时间模式准确率"""
        feedback_data = self._load_feedback_data(days)
        
        # 按预测类型和时段分组
        by_type = defaultdict(lambda: {"total": 0, "correct": 0})
        by_hour = defaultdict(lambda: {"total": 0, "correct": 0})
        
        for f in feedback_data:
            pred_type = f.get('prediction_type', 'unknown')
            by_type[pred_type]["total"] += 1
            if f.get('was_accurate'):
                by_type[pred_type]["correct"] += 1
            
            # 从时间戳提取小时
            try:
                ts = datetime.fromisoformat(f.get('timestamp', ''))
                hour = ts.hour
                by_hour[hour]["total"] += 1
                if f.get('was_accurate'):
                    by_hour[hour]["correct"] += 1
            except:
                pass
        
        # 计算准确率
        for pred_type in by_type:
            total = by_type[pred_type]["total"]
            correct = by_type[pred_type]["correct"]
            by_type[pred_type]["accuracy"] = correct / total if total > 0 else 0
        
        # 找出最佳和最差时段
        hour_accuracy = {}
        for hour, stats in by_hour.items():
            if stats["total"] >= 3:  # 至少3个样本
                hour_accuracy[hour] = stats["correct"] / stats["total"]
        
        best_hour = max(hour_accuracy.items(), key=lambda x: x[1])[0] if hour_accuracy else None
        worst_hour = min(hour_accuracy.items(), key=lambda x: x[1])[0] if hour_accuracy else None
        
        return {
            "by_type": dict(by_type),
            "by_hour": {str(h): {"total": by_hour[h]["total"], "accuracy": hour_accuracy.get(h, 0)} 
                       for h in by_hour},
            "best_hour": f"{best_hour}:00" if best_hour is not None else None,
            "worst_hour": f"{worst_hour}:00" if worst_hour is not None else None
        }
    
    def _analyze_context_associations(self, days: int) -> Dict:
        """分析上下文关联准确率"""
        if not os.path.exists(self.association_file):
            return {"by_source_type": {}}
        
        try:
            with open(self.association_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return {"by_source_type": {}}
        
        by_source = defaultdict(lambda: {"associations": 0, "triggered": 0, "success": 0})
        
        for key, assoc in data.get("associations", {}).items():
            source_type = assoc.get("source_type", "unknown")
            by_source[source_type]["associations"] += 1
            by_source[source_type]["triggered"] += assoc.get("trigger_count", 0)
            by_source[source_type]["success"] += assoc.get("success_count", 0)
        
        # 计算成功率
        for source_type in by_source:
            triggered = by_source[source_type]["triggered"]
            success = by_source[source_type]["success"]
            by_source[source_type]["success_rate"] = success / triggered if triggered > 0 else 0
        
        return {"by_source_type": dict(by_source)}
    
    def _analyze_prediction_types(self, days: int) -> Dict:
        """分析各预测类型的表现"""
        feedback_data = self._load_feedback_data(days)
        
        by_type = defaultdict(lambda: {"count": 0, "correct": 0, "confidences": []})
        
        for f in feedback_data:
            pred_type = f.get('prediction_type', 'unknown')
            by_type[pred_type]["count"] += 1
            if f.get('was_accurate'):
                by_type[pred_type]["correct"] += 1
            by_type[pred_type]["confidences"].append(f.get('confidence', 0))
        
        total = sum(s["count"] for s in by_type.values())
        
        result = {}
        for pred_type, stats in by_type.items():
            count = stats["count"]
            result[pred_type] = {
                "count": count,
                "percentage": count / total if total > 0 else 0,
                "accuracy": stats["correct"] / count if count > 0 else 0,
                "avg_confidence": sum(stats["confidences"]) / len(stats["confidences"]) if stats["confidences"] else 0
            }
        
        return result
    
    def _analyze_confidence_levels(self, days: int) -> Dict:
        """分析置信度与实际准确率的关系"""
        feedback_data = self._load_feedback_data(days)
        
        # 按置信度分桶
        buckets = defaultdict(lambda: {"total": 0, "correct": 0})
        
        for f in feedback_data:
            conf = f.get('confidence', 0)
            # 四舍五入到0.1
            bucket = round(conf * 10) / 10
            buckets[bucket]["total"] += 1
            if f.get('was_accurate'):
                buckets[bucket]["correct"] += 1
        
        result = {}
        for bucket in sorted(buckets.keys()):
            stats = buckets[bucket]
            result[str(bucket)] = {
                "count": stats["total"],
                "accuracy": stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            }
        
        return result
    
    def _analyze_trends(self, days: int) -> Dict:
        """分析趋势"""
        feedback_data = self._load_feedback_data(days)
        
        if len(feedback_data) < 10:
            return {
                "accuracy_trend": "数据不足",
                "acceptance_trend": "数据不足",
                "volume_trend": "数据不足"
            }
        
        # 按天分组
        by_day = defaultdict(lambda: {"total": 0, "correct": 0, "accepted": 0})
        
        for f in feedback_data:
            try:
                ts = datetime.fromisoformat(f.get('timestamp', ''))
                day = ts.strftime('%Y-%m-%d')
                by_day[day]["total"] += 1
                if f.get('was_accurate'):
                    by_day[day]["correct"] += 1
                if f.get('was_accepted'):
                    by_day[day]["accepted"] += 1
            except:
                pass
        
        if len(by_day) < 2:
            return {
                "accuracy_trend": "需要更多天数据",
                "acceptance_trend": "需要更多天数据",
                "volume_trend": "需要更多天数据"
            }
        
        # 计算趋势
        days_sorted = sorted(by_day.keys())
        first_half = days_sorted[:len(days_sorted)//2]
        second_half = days_sorted[len(days_sorted)//2:]
        
        def calc_accuracy(days):
            total = sum(by_day[d]["total"] for d in days)
            correct = sum(by_day[d]["correct"] for d in days)
            return correct / total if total > 0 else 0
        
        def calc_acceptance(days):
            total = sum(by_day[d]["total"] for d in days)
            accepted = sum(by_day[d]["accepted"] for d in days)
            return accepted / total if total > 0 else 0
        
        first_acc = calc_accuracy(first_half)
        second_acc = calc_accuracy(second_half)
        first_accept = calc_acceptance(first_half)
        second_accept = calc_acceptance(second_half)
        first_vol = sum(by_day[d]["total"] for d in first_half) / len(first_half) if first_half else 0
        second_vol = sum(by_day[d]["total"] for d in second_half) / len(second_half) if second_half else 0
        
        return {
            "accuracy_trend": "↗ 提升" if second_acc > first_acc else "↘ 下降" if second_acc < first_acc else "→ 持平",
            "acceptance_trend": "↗ 提升" if second_accept > first_accept else "↘ 下降" if second_accept < first_accept else "→ 持平",
            "volume_trend": "↗ 增长" if second_vol > first_vol else "↘ 减少" if second_vol < first_vol else "→ 稳定",
            "first_half_accuracy": first_acc,
            "second_half_accuracy": second_acc
        }
    
    def _generate_recommendations(self) -> List[Dict]:
        """生成优化建议"""
        recommendations = []
        
        # 基于总体准确率的建议
        summary = self._generate_summary(30)
        accuracy = summary.get('accuracy_rate', 0)
        
        if accuracy < 0.5:
            recommendations.append({
                "category": "准确率",
                "priority": "高",
                "message": "整体准确率偏低，建议提高置信度阈值或增加训练数据",
                "action": "调整 min_confidence_to_show 至 0.8 以上"
            })
        elif accuracy < 0.7:
            recommendations.append({
                "category": "准确率",
                "priority": "中",
                "message": "准确率有提升空间，建议检查误判模式",
                "action": "分析常见误判类型并优化规则"
            })
        
        # 基于接受率的建议
        acceptance = summary.get('acceptance_rate', 0)
        if acceptance < 0.3:
            recommendations.append({
                "category": "用户体验",
                "priority": "中",
                "message": "建议接受率较低，可能建议过于频繁或不相关",
                "action": "增加冷却时间，提高建议质量门槛"
            })
        
        # 基于置信度校准的建议
        conf_analysis = self._analyze_confidence_levels(30)
        if conf_analysis:
            high_conf = conf_analysis.get('0.9', {}).get('accuracy', 0)
            if high_conf < 0.8:
                recommendations.append({
                    "category": "校准",
                    "priority": "高",
                    "message": "高置信度预测准确率偏低，模型校准需要优化",
                    "action": "检查置信度计算逻辑，考虑引入温度缩放"
                })
        
        # A/B测试建议
        ab_test = self._analyze_ab_test(30)
        winner = ab_test.get('winner')
        if winner and winner != 'control':
            recommendations.append({
                "category": "A/B测试",
                "priority": "低",
                "message": f"'{winner}' 组表现更好，建议全面采用该策略",
                "action": f"将所有用户迁移至 {winner} 策略"
            })
        
        if not recommendations:
            recommendations.append({
                "category": "总体",
                "priority": "低",
                "message": "系统运行良好，继续保持",
                "action": "持续监控并收集反馈"
            })
        
        return recommendations
    
    def _generate_charts_data(self, days: int) -> Dict:
        """生成图表数据"""
        return {
            "accuracy_by_day": self._get_daily_accuracy(days),
            "prediction_volume_by_day": self._get_daily_volume(days),
            "confidence_distribution": self._analyze_confidence_levels(days)
        }
    
    def _get_daily_accuracy(self, days: int) -> Dict[str, float]:
        """获取每日准确率"""
        feedback_data = self._load_feedback_data(days)
        
        by_day = defaultdict(lambda: {"total": 0, "correct": 0})
        
        for f in feedback_data:
            try:
                ts = datetime.fromisoformat(f.get('timestamp', ''))
                day = ts.strftime('%m-%d')
                by_day[day]["total"] += 1
                if f.get('was_accurate'):
                    by_day[day]["correct"] += 1
            except:
                pass
        
        return {
            day: stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            for day, stats in by_day.items()
        }
    
    def _get_daily_volume(self, days: int) -> Dict[str, int]:
        """获取每日预测量"""
        feedback_data = self._load_feedback_data(days)
        
        by_day = defaultdict(int)
        
        for f in feedback_data:
            try:
                ts = datetime.fromisoformat(f.get('timestamp', ''))
                day = ts.strftime('%m-%d')
                by_day[day] += 1
            except:
                pass
        
        return dict(by_day)
    
    def _load_feedback_data(self, days: int) -> List[Dict]:
        """加载反馈数据"""
        if not os.path.exists(self.feedback_file):
            return []
        
        try:
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            return []
        
        cutoff = datetime.now() - timedelta(days=days)
        
        feedback = []
        for item in data.get("feedback", []):
            try:
                ts = datetime.fromisoformat(item.get('timestamp', '2000-01-01'))
                if ts >= cutoff:
                    feedback.append(item)
            except:
                continue
        
        return feedback


# ========== 便捷函数 ==========

def generate_accuracy_report(days: int = 30, 
                            output_format: str = "json",
                            data_dir: str = "data") -> str:
    """
    生成预测准确率报告
    
    Args:
        days: 报告时间范围
        output_format: 输出格式 (json/markdown)
        data_dir: 数据目录
        
    Returns:
        报告文件路径
    """
    reporter = PredictionAccuracyReport(data_dir)
    
    if output_format == "markdown":
        report_md = reporter.generate_markdown_report(days)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(reporter.report_dir, f"prediction_report_{timestamp}.md")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_md)
        return filepath
    else:
        report = reporter.generate_report(days)
        return reporter.save_report(report)


def print_summary_report(days: int = 30, data_dir: str = "data"):
    """打印汇总报告到控制台"""
    reporter = PredictionAccuracyReport(data_dir)
    report = reporter.generate_report(days)
    
    print("\n" + "=" * 50)
    print("📊 预测准确率汇总报告")
    print("=" * 50)
    
    summary = report['summary']
    print(f"\n总体准确率: {summary['accuracy_rate']:.1%}")
    print(f"接受率: {summary['acceptance_rate']:.1%}")
    print(f"总预测数: {summary['total_predictions']}")
    
    print("\n按置信度分布:")
    for key, stats in summary['by_confidence'].items():
        print(f"  {key}: {stats['count']} 次, 准确率 {stats['accuracy']:.1%}")
    
    print("\n💡 优化建议:")
    for rec in report['recommendations'][:3]:
        print(f"  [{rec['priority']}] {rec['message']}")
    
    print("\n" + "=" * 50)


# ========== 演示 ==========

def demo():
    """演示报告生成功能"""
    print("=" * 60)
    print("林林v5.0 预测准确率报告 v5.0 演示")
    print("=" * 60)
    
    # 创建报告生成器
    reporter = PredictionAccuracyReport()
    
    # 生成JSON报告
    print("\n[演示1] 生成JSON格式报告...")
    report = reporter.generate_report(days=30)
    json_path = reporter.save_report(report)
    print(f"JSON报告已保存: {json_path}")
    
    # 生成Markdown报告
    print("\n[演示2] 生成Markdown格式报告...")
    md_report = reporter.generate_markdown_report(days=30)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_path = os.path.join(reporter.report_dir, f"prediction_report_{timestamp}.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_report)
    print(f"Markdown报告已保存: {md_path}")
    
    # 打印汇总
    print("\n[演示3] 打印汇总报告...")
    print_summary_report()
    
    # 显示报告预览
    print("\n[演示4] Markdown报告预览:")
    print(md_report[:2000] + "...\n")
    
    print("=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    demo()
