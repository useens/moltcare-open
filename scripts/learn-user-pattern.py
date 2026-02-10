#!/usr/bin/env python3
"""
用户模式学习脚本
版本: v0.1
用途: 从历史对话中提取用户行为模式并更新预判引擎
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional, Any

# 添加core目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.prediction_engine import PredictionEngine


class UserPatternLearner:
    """
    用户模式学习器
    
    从各种数据源学习用户行为模式:
    - 历史对话 (memory/)
    - 用户反馈
    - 外部数据源 (邮件、日历等)
    """
    
    def __init__(self, data_dir: str = "data", memory_dir: str = "memory"):
        self.data_dir = data_dir
        self.memory_dir = memory_dir
        self.engine = PredictionEngine(data_dir)
        
        # 学习的配置
        self.config = {
            "min_conversations_for_pattern": 3,
            "max_lookback_days": 30,
            "pattern_confidence_threshold": 0.6
        }
    
    def learn_from_memory(self, days: int = 30) -> Dict:
        """
        从记忆文件学习用户模式
        
        Args:
            days: 回溯天数
            
        Returns:
            学习结果统计
        """
        print(f"[学习器] 从最近{days}天的记忆中学习...")
        
        conversations = self._extract_conversations_from_memory(days)
        
        if not conversations:
            print("[学习器] 未找到足够的对话数据")
            return {"status": "no_data", "conversations_found": 0}
        
        print(f"[学习器] 找到 {len(conversations)} 条对话记录")
        
        # 执行多维度分析
        results = {
            "conversations_processed": len(conversations),
            "active_hours_analysis": self.engine.analyze_active_hours(conversations),
            "request_patterns": self.engine.identify_request_patterns(conversations),
            "work_rhythm": self.engine.detect_work_rhythm(conversations),
            "preferences": self._extract_preferences(conversations)
        }
        
        # 保存更新后的模式
        self.engine.save_user_pattern()
        
        print(f"[学习器] 学习完成!")
        print(f"  - 发现 {len(results['request_patterns']['patterns'])} 个请求模式")
        print(f"  - 识别 {len(results['work_rhythm']['deep_work_hours'])} 个深度工作时段")
        
        return results
    
    def _extract_conversations_from_memory(self, days: int) -> List[Dict]:
        """从记忆目录提取对话记录"""
        conversations = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        if not os.path.exists(self.memory_dir):
            print(f"[学习器] 记忆目录不存在: {self.memory_dir}")
            return conversations
        
        # 遍历记忆文件
        for filename in os.listdir(self.memory_dir):
            if not filename.endswith('.md'):
                continue
            
            # 从文件名提取日期 (格式: YYYY-MM-DD.md)
            try:
                file_date = datetime.strptime(filename.replace('.md', ''), '%Y-%m-%d')
            except ValueError:
                continue
            
            if file_date < cutoff_date:
                continue
            
            filepath = os.path.join(self.memory_dir, filename)
            convs = self._parse_memory_file(filepath, file_date)
            conversations.extend(convs)
        
        return conversations
    
    def _parse_memory_file(self, filepath: str, file_date: datetime) -> List[Dict]:
        """解析单个记忆文件"""
        conversations = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"[学习器] 读取文件失败 {filepath}: {e}")
            return conversations
        
        # 简单的启发式解析
        # 假设文件包含用户消息和我的回复
        lines = content.split('\n')
        
        current_time = file_date
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 尝试提取时间戳
            time_match = re.search(r'(\d{2}):(\d{2})', line)
            if time_match:
                hour, minute = int(time_match.group(1)), int(time_match.group(2))
                current_time = file_date.replace(hour=hour, minute=minute)
            
            # 识别用户消息 (假设以特定前缀或格式)
            # 这里使用启发式：长度适中的行可能是用户请求
            if 10 < len(line) < 500 and not line.startswith('#'):
                # 可能是用户消息
                conversations.append({
                    "timestamp": current_time.isoformat(),
                    "content": line,
                    "source": os.path.basename(filepath)
                })
        
        return conversations
    
    def _extract_preferences(self, conversations: List[Dict]) -> Dict:
        """从对话中提取用户偏好"""
        preferences = {
            "communication_style": self._detect_communication_style(conversations),
            "preferred_topics": self._extract_preferred_topics(conversations),
            "notification_timing": self._detect_notification_timing(conversations)
        }
        
        # 更新引擎中的偏好
        self.engine.user_pattern["preferences"].update(preferences)
        
        return preferences
    
    def _detect_communication_style(self, conversations: List[Dict]) -> str:
        """检测用户沟通风格"""
        # 分析用户消息长度和风格
        total_length = 0
        casual_markers = 0
        formal_markers = 0
        
        casual_words = ['嘿', '哈哈', '嗯', '哦', '呢', '吧', '呀']
        formal_words = ['请', '您好', '谢谢', '麻烦', '请问']
        
        for conv in conversations:
            content = conv.get("content", "")
            total_length += len(content)
            
            for word in casual_words:
                if word in content:
                    casual_markers += 1
            
            for word in formal_words:
                if word in content:
                    formal_markers += 1
        
        avg_length = total_length / len(conversations) if conversations else 0
        
        # 决策逻辑
        if casual_markers > formal_markers * 2:
            return "casual"
        elif avg_length > 100 or formal_markers > casual_markers:
            return "detailed"
        else:
            return "concise"
    
    def _extract_preferred_topics(self, conversations: List[Dict]) -> List[str]:
        """提取用户偏好主题"""
        topic_keywords = {
            "技术": ["代码", "编程", "开发", "bug", "技术", "python", "api"],
            "管理": ["项目", "计划", "进度", "团队", "管理", "汇报"],
            "沟通": ["邮件", "消息", "沟通", "联系", "回复", "会议"],
            "学习": ["学习", "阅读", "课程", "知识", "技能", "提升"],
            "生活": ["生活", "健康", "饮食", "运动", "休息", "家庭"]
        }
        
        topic_counts = defaultdict(int)
        
        for conv in conversations:
            content = conv.get("content", "")
            for topic, keywords in topic_keywords.items():
                for kw in keywords:
                    if kw in content.lower():
                        topic_counts[topic] += 1
                        break
        
        # 返回前3个偏好主题
        return [
            topic for topic, _ in sorted(
                topic_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
        ]
    
    def _detect_notification_timing(self, conversations: List[Dict]) -> str:
        """检测用户偏好的通知时机"""
        if not conversations:
            return "moderate"
        
        # 统计用户响应时间
        # 如果用户通常在5分钟内回复，可以积极通知
        # 如果响应较慢或只在特定时段回复，则适度通知
        
        # 简单启发式：基于用户活跃时段的集中程度
        hourly_dist = defaultdict(int)
        for conv in conversations:
            ts = datetime.fromisoformat(conv.get("timestamp", datetime.now().isoformat()))
            hourly_dist[ts.hour] += 1
        
        # 计算集中程度
        total = sum(hourly_dist.values())
        max_hour_count = max(hourly_dist.values()) if hourly_dist else 0
        concentration = max_hour_count / total if total > 0 else 0
        
        if concentration > 0.5:
            return "moderate"  # 时段集中，适度通知
        else:
            return "aggressive"  # 时段分散，可以更积极
    
    def learn_from_feedback(self, feedback_file: Optional[str] = None) -> Dict:
        """
        从反馈文件学习
        
        Args:
            feedback_file: 反馈文件路径
            
        Returns:
            学习结果
        """
        if feedback_file is None:
            feedback_file = os.path.join(self.data_dir, "feedback.json")
        
        if not os.path.exists(feedback_file):
            print(f"[学习器] 反馈文件不存在: {feedback_file}")
            return {"status": "no_feedback_file"}
        
        try:
            with open(feedback_file, 'r', encoding='utf-8') as f:
                feedbacks = json.load(f)
        except Exception as e:
            print(f"[学习器] 读取反馈文件失败: {e}")
            return {"status": "error", "error": str(e)}
        
        print(f"[学习器] 处理 {len(feedbacks)} 条反馈...")
        
        # 分析反馈并调整
        for feedback in feedbacks:
            self.engine.record_feedback(
                prediction_id=feedback.get("prediction_id", "unknown"),
                was_accurate=feedback.get("was_accurate", True),
                actual_need=feedback.get("actual_need")
            )
        
        return {
            "status": "success",
            "feedback_processed": len(feedbacks),
            "current_accuracy": self.engine.user_pattern["prediction_accuracy"]
        }
    
    def generate_learning_report(self) -> Dict:
        """生成学习报告"""
        pattern = self.engine.user_pattern
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_conversations_analyzed": sum(
                    stats.get("count", 0) 
                    for stats in pattern["behavior_patterns"]["request_types"].values()
                ),
                "patterns_identified": len(pattern["behavior_patterns"]["request_types"]),
                "prediction_accuracy": pattern["prediction_accuracy"],
                "user_preferences": pattern["preferences"]
            },
            "insights": self._generate_insights(),
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_insights(self) -> List[str]:
        """生成洞察"""
        insights = []
        pattern = self.engine.user_pattern
        
        # 活跃时段洞察
        active_hours = pattern["behavior_patterns"].get("hourly_activity", {})
        if active_hours:
            peak_hour = max(active_hours.keys(), key=lambda h: active_hours[h].get("count", 0))
            insights.append(f"用户最活跃时段: {peak_hour}:00")
        
        # 工作节奏洞察
        rhythm = pattern["behavior_patterns"].get("work_rhythm", {})
        if rhythm.get("deep_work_hours"):
            insights.append(f"深度工作时段: {rhythm['deep_work_hours']}")
        
        # 偏好洞察
        prefs = pattern.get("preferences", {})
        if prefs.get("communication_style"):
            insights.append(f"沟通风格: {prefs['communication_style']}")
        
        return insights
    
    def _generate_recommendations(self) -> List[str]:
        """生成建议"""
        recommendations = []
        pattern = self.engine.user_pattern
        
        accuracy = pattern["prediction_accuracy"].get("accuracy_rate", 0)
        
        if accuracy == 0:
            recommendations.append("需要更多反馈数据来优化预测模型")
        elif accuracy < 0.6:
            recommendations.append("预测准确率偏低，建议调整阈值或增加特征")
        elif accuracy > 0.8:
            recommendations.append("预测准确率良好，可以考虑更积极的建议策略")
        
        # 基于用户偏好的建议
        prefs = pattern.get("preferences", {})
        if prefs.get("preferred_topics"):
            recommendations.append(
                f"可以针对偏好主题({', '.join(prefs['preferred_topics'][:2])})主动提供信息"
            )
        
        return recommendations
    
    def run_full_learning_cycle(self) -> Dict:
        """运行完整学习周期"""
        print("=" * 50)
        print("用户模式学习 - 完整周期")
        print("=" * 50)
        
        # 1. 从记忆学习
        memory_results = self.learn_from_memory(days=30)
        
        # 2. 从反馈学习
        feedback_results = self.learn_from_feedback()
        
        # 3. 生成报告
        report = self.generate_learning_report()
        
        # 4. 保存报告
        report_file = os.path.join(self.data_dir, "learning_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print("\n" + "=" * 50)
        print("学习周期完成!")
        print("=" * 50)
        
        return {
            "memory_results": memory_results,
            "feedback_results": feedback_results,
            "report": report,
            "report_file": report_file
        }


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='用户模式学习脚本')
    parser.add_argument('--days', type=int, default=30, help='回溯天数')
    parser.add_argument('--memory-dir', default='memory', help='记忆目录')
    parser.add_argument('--data-dir', default='data', help='数据目录')
    parser.add_argument('--feedback', help='反馈文件路径')
    parser.add_argument('--full-cycle', action='store_true', help='运行完整学习周期')
    
    args = parser.parse_args()
    
    learner = UserPatternLearner(
        data_dir=args.data_dir,
        memory_dir=args.memory_dir
    )
    
    if args.full_cycle:
        results = learner.run_full_learning_cycle()
        print("\n学习报告:")
        print(json.dumps(results["report"], ensure_ascii=False, indent=2))
    else:
        # 仅从记忆学习
        results = learner.learn_from_memory(days=args.days)
        
        if args.feedback:
            learner.learn_from_feedback(args.feedback)
        
        # 生成并显示报告
        report = learner.generate_learning_report()
        print("\n学习报告:")
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
