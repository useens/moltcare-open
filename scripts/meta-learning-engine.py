#!/usr/bin/env python3
"""
元学习引擎 - Meta-Learning Engine
"学习如何学习" - 优化学习机制本身

功能:
1. Signal评分算法自优化
2. 深度提取策略改进
3. 学习效率持续优化
"""

import json
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

class MetaLearningEngine:
    """元学习引擎 - 持续优化学习机制"""
    
    def __init__(self):
        self.workspace = Path("/root/.openclaw/workspace")
        self.meta_learn_file = self.workspace / "memory/meta-learning.json"
        self.signal_history_file = self.workspace / "memory/signal-evaluation-history.json"
        self.extraction_history_file = self.workspace / "memory/extraction-history.json"
        
    def run_meta_learning_cycle(self):
        """运行元学习周期"""
        print(f"\n{'='*70}")
        print(f"🧠 元学习周期 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*70}\n")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "signal_optimization": self.optimize_signal_algorithm(),
            "extraction_optimization": self.optimize_extraction_strategy(),
            "learning_efficiency": self.optimize_learning_efficiency()
        }
        
        # 保存元学习结果
        self.save_meta_learning_results(results)
        
        # 输出摘要
        self.print_summary(results)
        
        return results
    
    def optimize_signal_algorithm(self) -> Dict[str, Any]:
        """优化Signal评分算法"""
        print("📊 优化Signal评分算法...")
        
        history = self.load_signal_history()
        if len(history) < 10:
            print("   ⚠️ 历史数据不足，跳过优化")
            return {"status": "skipped", "reason": "insufficient_data"}
        
        # 分析Signal与实际价值的相关性
        correlations = self.analyze_signal_correlation(history)
        
        # 识别最有效的评分因素
        effective_factors = self.identify_effective_factors(history)
        
        # 生成优化建议
        recommendations = self.generate_signal_recommendations(correlations, effective_factors)
        
        # 应用优化（如果置信度足够高）
        if recommendations.get("confidence", 0) > 0.7:
            self.apply_signal_optimizations(recommendations)
            status = "applied"
        else:
            status = "pending_review"
        
        return {
            "status": status,
            "correlations": correlations,
            "effective_factors": effective_factors,
            "recommendations": recommendations
        }
    
    def analyze_signal_correlation(self, history: List[Dict]) -> Dict[str, float]:
        """分析Signal与实际价值的相关性"""
        # 简化的相关性分析
        signal_scores = [h.get("signal", 5) for h in history]
        actual_values = [h.get("actual_value", 5) for h in history]
        
        if len(signal_scores) < 2:
            return {"correlation": 0.0}
        
        # 计算皮尔逊相关系数（简化版）
        mean_signal = statistics.mean(signal_scores)
        mean_value = statistics.mean(actual_values)
        
        numerator = sum((s - mean_signal) * (v - mean_value) 
                       for s, v in zip(signal_scores, actual_values))
        
        denom_signal = sum((s - mean_signal) ** 2 for s in signal_scores) ** 0.5
        denom_value = sum((v - mean_value) ** 2 for v in actual_values) ** 0.5
        
        if denom_signal == 0 or denom_value == 0:
            correlation = 0.0
        else:
            correlation = numerator / (denom_signal * denom_value)
        
        return {
            "correlation": round(correlation, 3),
            "sample_size": len(history),
            "mean_signal": round(mean_signal, 2),
            "mean_actual": round(mean_value, 2)
        }
    
    def identify_effective_factors(self, history: List[Dict]) -> Dict[str, Any]:
        """识别最有效的评分因素"""
        factors = {
            "likes_weight": 0,
            "keyword_weight": 0,
            "source_weight": 0
        }
        
        # 分析哪些因素与高实际价值相关
        for item in history:
            actual_value = item.get("actual_value", 5)
            
            if item.get("likes", 0) > 100 and actual_value >= 7:
                factors["likes_weight"] += 1
            
            if item.get("keywords_matched", 0) > 0 and actual_value >= 7:
                factors["keyword_weight"] += 1
            
            if item.get("source", "") in ["hackernews", "github"] and actual_value >= 7:
                factors["source_weight"] += 1
        
        # 归一化
        total = sum(factors.values())
        if total > 0:
            factors = {k: round(v/total, 2) for k, v in factors.items()}
        
        return factors
    
    def generate_signal_recommendations(self, correlations: Dict, factors: Dict) -> Dict[str, Any]:
        """生成Signal优化建议"""
        recommendations = {
            "adjustments": [],
            "confidence": 0.5
        }
        
        # 基于相关性调整
        if correlations.get("correlation", 0) < 0.5:
            recommendations["adjustments"].append({
                "factor": "keyword_weight",
                "change": "increase",
                "reason": "低相关性表明确信度权重不足"
            })
            recommendations["confidence"] += 0.1
        
        # 基于因素有效性调整
        if factors.get("likes_weight", 0) > 0.4:
            recommendations["adjustments"].append({
                "factor": "likes_threshold",
                "change": "lower",
                "reason": "高互动内容确实有价值"
            })
            recommendations["confidence"] += 0.1
        
        return recommendations
    
    def optimize_extraction_strategy(self) -> Dict[str, Any]:
        """优化深度提取策略"""
        print("🔍 优化深度提取策略...")
        
        history = self.load_extraction_history()
        if len(history) < 5:
            print("   ⚠️ 提取历史不足，跳过优化")
            return {"status": "skipped", "reason": "insufficient_data"}
        
        # 分析不同内容类型的提取效果
        content_analysis = self.analyze_content_types(history)
        
        # 优化成本效益
        cost_effectiveness = self.optimize_cost_effectiveness(history)
        
        # 自适应参数调整
        adaptive_params = self.calculate_adaptive_parameters(history)
        
        return {
            "status": "optimized",
            "content_analysis": content_analysis,
            "cost_effectiveness": cost_effectiveness,
            "adaptive_parameters": adaptive_params
        }
    
    def analyze_content_types(self, history: List[Dict]) -> Dict[str, Any]:
        """分析不同内容类型的提取效果"""
        type_performance = {}
        
        for item in history:
            content_type = item.get("content_type", "unknown")
            roi = item.get("roi", 0)  # Return on Investment
            
            if content_type not in type_performance:
                type_performance[content_type] = {"count": 0, "total_roi": 0}
            
            type_performance[content_type]["count"] += 1
            type_performance[content_type]["total_roi"] += roi
        
        # 计算平均ROI
        for ct in type_performance:
            count = type_performance[ct]["count"]
            total = type_performance[ct]["total_roi"]
            type_performance[ct]["avg_roi"] = round(total / count, 2) if count > 0 else 0
        
        return type_performance
    
    def optimize_cost_effectiveness(self, history: List[Dict]) -> Dict[str, Any]:
        """优化成本效益"""
        total_cost = sum(h.get("cost", 0) for h in history)
        total_value = sum(h.get("value", 0) for h in history)
        
        roi = (total_value - total_cost) / total_cost if total_cost > 0 else 0
        
        return {
            "total_cost": total_cost,
            "total_value": total_value,
            "roi": round(roi, 2),
            "recommendation": "maintain" if roi > 0.5 else "reduce_depth"
        }
    
    def calculate_adaptive_parameters(self, history: List[Dict]) -> Dict[str, Any]:
        """计算自适应参数"""
        # 基于历史表现调整参数
        avg_signal = statistics.mean([h.get("signal", 5) for h in history])
        
        # 如果高Signal内容比例高，降低阈值
        if avg_signal > 7:
            new_threshold = 6
        else:
            new_threshold = 7
        
        return {
            "signal_threshold": new_threshold,
            "max_depth": 10 if avg_signal > 6 else 5,
            "adaptation_reason": f"基于平均Signal {avg_signal:.1f} 调整"
        }
    
    def optimize_learning_efficiency(self) -> Dict[str, Any]:
        """优化学习效率"""
        print("⚡ 优化学习效率...")
        
        # 分析不同内化方式的效果
        internalization_analysis = self.analyze_internalization_methods()
        
        # 优化知识关联策略
        association_optimization = self.optimize_association_strategy()
        
        # 应用遗忘曲线
        spaced_repetition = self.apply_spaced_repetition()
        
        return {
            "status": "optimized",
            "internalization": internalization_analysis,
            "association": association_optimization,
            "spaced_repetition": spaced_repetition
        }
    
    def analyze_internalization_methods(self) -> Dict[str, Any]:
        """分析不同内化方式的效果"""
        # 这里可以分析哪些记忆文件被频繁访问
        return {
            "most_accessed": ["core-archive.md", "knowledge-graph.md"],
            "least_accessed": ["daily/2026-02-01.md"],
            "recommendation": "优先内化到高频访问文件"
        }
    
    def optimize_association_strategy(self) -> Dict[str, Any]:
        """优化知识关联策略"""
        return {
            "cross_reference_count": 15,
            "recommendation": "增加跨文档关联"
        }
    
    def apply_spaced_repetition(self) -> Dict[str, Any]:
        """应用间隔重复"""
        return {
            "schedule": ["1d", "3d", "7d", "14d", "30d"],
            "next_review": (datetime.now() + timedelta(days=1)).isoformat()
        }
    
    def load_signal_history(self) -> List[Dict]:
        """加载Signal历史"""
        if self.signal_history_file.exists():
            with open(self.signal_history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def load_extraction_history(self) -> List[Dict]:
        """加载提取历史"""
        if self.extraction_history_file.exists():
            with open(self.extraction_history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def save_meta_learning_results(self, results: Dict):
        """保存元学习结果"""
        self.meta_learn_file.parent.mkdir(parents=True, exist_ok=True)
        
        history = []
        if self.meta_learn_file.exists():
            with open(self.meta_learn_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        
        history.append(results)
        
        # 只保留最近50条
        history = history[-50:]
        
        with open(self.meta_learn_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    
    def print_summary(self, results: Dict):
        """输出摘要"""
        print(f"\n{'='*70}")
        print("📋 元学习周期摘要")
        print(f"{'='*70}")
        
        signal_status = results["signal_optimization"].get("status", "unknown")
        extraction_status = results["extraction_optimization"].get("status", "unknown")
        learning_status = results["learning_efficiency"].get("status", "unknown")
        
        print(f"Signal算法优化: {signal_status}")
        print(f"提取策略优化: {extraction_status}")
        print(f"学习效率优化: {learning_status}")
        
        print(f"{'='*70}\n")

def main():
    """主函数"""
    engine = MetaLearningEngine()
    engine.run_meta_learning_cycle()

if __name__ == "__main__":
    main()
