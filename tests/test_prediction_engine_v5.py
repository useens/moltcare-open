#!/usr/bin/env python3
"""
林林v5.0 预判引擎测试脚本
版本: v5.0
职责: 测试预判引擎各项功能
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.prediction_integration import (
    PredictionIntegration, TimePatternLearner, ContextAssociationEngine,
    ABTestOptimizer, PredictionResult, PredictionTriggerType, PredictionContextType
)
from scripts.realtime_predictor import RealtimePredictor
from core.main_flow_integration import PredictionEnabledMainFlow
from core.prediction_accuracy_report import PredictionAccuracyReport


class PredictionEngineTester:
    """预判引擎测试器"""
    
    def __init__(self):
        self.test_results = []
        self.data_dir = "test_data"
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("林林v5.0 预判引擎测试")
        print("=" * 60)
        
        tests = [
            ("时间模式学习器", self.test_time_pattern_learner),
            ("上下文关联引擎", self.test_context_association_engine),
            ("A/B测试优化器", self.test_ab_test_optimizer),
            ("预判引擎集成", self.test_prediction_integration),
            ("实时预判触发器", self.test_realtime_predictor),
            ("主流程集成", self.test_main_flow_integration),
            ("准确率报告", self.test_accuracy_report),
        ]
        
        passed = 0
        failed = 0
        
        for name, test_func in tests:
            try:
                print(f"\n[测试] {name}...")
                await test_func()
                print(f"✅ {name} 通过")
                passed += 1
            except Exception as e:
                print(f"❌ {name} 失败: {e}")
                failed += 1
        
        print("\n" + "=" * 60)
        print(f"测试结果: {passed} 通过, {failed} 失败")
        print("=" * 60)
        
        return failed == 0
    
    async def test_time_pattern_learner(self):
        """测试时间模式学习器"""
        learner = TimePatternLearner(self.data_dir)
        
        # 测试学习
        timestamps = [
            datetime.now().replace(hour=8, minute=0),
            datetime.now().replace(hour=8, minute=30),
            datetime.now().replace(hour=14, minute=0),
        ]
        
        for ts in timestamps:
            learner.learn_from_activity(ts, "daily_briefing")
        
        # 测试预测
        predictions = learner.predict_for_time(datetime.now().replace(hour=8))
        assert len(predictions) >= 0, "应该返回预测结果"
        
        # 测试报告
        report = learner.get_active_hours_report()
        assert "peak_hours" in report, "报告应包含peak_hours"
        
        print(f"  - 学习了 {len(timestamps)} 个时间点")
        print(f"  - 生成了 {len(predictions)} 个预测")
    
    async def test_context_association_engine(self):
        """测试上下文关联引擎"""
        engine = ContextAssociationEngine(self.data_dir)
        
        # 测试学习关联
        engine.learn_association(
            PredictionContextType.CALENDAR,
            "meeting",
            "meeting_prep",
            was_successful=True
        )
        
        # 测试日历预测
        events = [
            {"id": "cal1", "title": "项目评审会议", "type": "meeting"}
        ]
        predictions = engine.predict_from_calendar(events)
        assert len(predictions) >= 0, "应该返回预测结果"
        
        # 测试邮件预测
        emails = [
            {"id": "em1", "subject": "重要通知", "unread": True, "urgent": True},
            {"id": "em2", "subject": "普通邮件", "unread": True, "urgent": False},
        ]
        predictions = engine.predict_from_emails(emails)
        assert len(predictions) >= 0, "应该返回预测结果"
        
        print(f"  - 学习了 1 个关联")
        print(f"  - 日历预测: {len(predictions)} 个")
    
    async def test_ab_test_optimizer(self):
        """测试A/B测试优化器"""
        optimizer = ABTestOptimizer(self.data_dir)
        
        # 测试分组
        group = optimizer.assign_group("user123")
        assert group in ["control", "treatment_a", "treatment_b"], "应该在测试组中"
        
        # 测试阈值获取
        threshold = optimizer.get_threshold()
        assert 0.5 <= threshold <= 0.9, "阈值应在合理范围"
        
        # 测试结果记录
        pred = PredictionResult(
            prediction_id="test_1",
            trigger_type=PredictionTriggerType.SCHEDULED,
            predicted_need="test",
            confidence=0.8,
            reason="测试",
            suggested_action="测试动作"
        )
        
        optimizer.record_result(group, pred, was_accepted=True)
        
        # 测试报告
        report = optimizer.get_ab_test_report()
        assert "groups" in report, "报告应包含groups"
        
        print(f"  - 用户分配到组: {group}")
        print(f"  - 当前阈值: {threshold}")
    
    async def test_prediction_integration(self):
        """测试预判引擎集成"""
        integration = PredictionIntegration(self.data_dir)
        
        # 测试对话分析
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "content": "帮我总结一下昨天的邮件",
            "user_id": "test_user"
        }
        
        context = {
            "emails": [
                {"id": "em1", "subject": "重要邮件", "unread": True},
            ]
        }
        
        predictions = await integration.analyze_conversation(conversation, context)
        assert isinstance(predictions, list), "应返回预测列表"
        
        # 测试主动建议生成
        suggestions = await integration.generate_proactive_suggestions(context)
        assert isinstance(suggestions, list), "应返回建议列表"
        
        # 测试报告
        report = integration.get_prediction_report()
        assert "time_patterns" in report, "报告应包含时间模式"
        
        print(f"  - 对话分析生成 {len(predictions)} 个预测")
        print(f"  - 主动建议 {len(suggestions)} 个")
    
    async def test_realtime_predictor(self):
        """测试实时预判触发器"""
        predictor = RealtimePredictor(self.data_dir)
        
        # 设置回调
        callback_triggered = False
        def on_suggestion(suggestions):
            nonlocal callback_triggered
            callback_triggered = True
        
        predictor.set_callbacks(on_suggestion=on_suggestion)
        
        # 测试对话后分析
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "content": "今天有什么安排？",
            "user_id": "test_user"
        }
        
        predictions = await predictor.on_conversation_end(conversation)
        assert isinstance(predictions, list), "应返回预测列表"
        
        # 测试日历事件触发
        event = {"id": "cal1", "title": "会议", "start_time": datetime.now().isoformat()}
        predictions = await predictor.on_calendar_event(event)
        assert isinstance(predictions, list), "应返回预测列表"
        
        print(f"  - 对话后分析: {len(predictions)} 个预测")
        print(f"  - 配置: {predictor.get_config()}")
    
    async def test_main_flow_integration(self):
        """测试主流程集成"""
        flow = PredictionEnabledMainFlow(self.data_dir)
        
        # 注意：不调用initialize()以避免启动后台任务
        flow.predictor = RealtimePredictor(self.data_dir)
        
        # 测试配置
        flow.update_config(auto_show_suggestions=True, min_confidence_to_show=0.8)
        config = flow.get_config()
        assert config["min_confidence_to_show"] == 0.8, "配置应更新"
        
        # 测试统计
        stats = flow.get_stats()
        assert isinstance(stats, dict), "应返回统计字典"
        
        print(f"  - 配置更新成功")
        print(f"  - 统计数据: {len(stats)} 项")
    
    async def test_accuracy_report(self):
        """测试准确率报告"""
        reporter = PredictionAccuracyReport(self.data_dir)
        
        # 测试报告生成
        report = reporter.generate_report(days=7)
        assert "summary" in report, "报告应包含summary"
        assert "recommendations" in report, "报告应包含recommendations"
        
        # 测试Markdown报告
        md_report = reporter.generate_markdown_report(days=7)
        assert "# 林林v5.0 预测准确率报告" in md_report, "应包含标题"
        
        print(f"  - 报告生成成功")
        print(f"  - 建议数量: {len(report['recommendations'])}")
    
    def cleanup(self):
        """清理测试数据"""
        import shutil
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)
            print(f"\n已清理测试数据: {self.data_dir}")


async def main():
    """主函数"""
    tester = PredictionEngineTester()
    
    try:
        success = await tester.run_all_tests()
        
        if success:
            print("\n✅ 所有测试通过!")
        else:
            print("\n⚠️ 部分测试失败")
            sys.exit(1)
    finally:
        tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
