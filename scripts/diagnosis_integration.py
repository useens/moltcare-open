#!/usr/bin/env python3
"""
Diagnosis Integration v5.0
自我诊断系统集成模块

整合以下模块：
- advanced_diagnosis.py: 推理质量深度分析
- predictive_monitor.py: 预测性故障检测
- smart_degrade.py: 智能降级策略
- self_optimization.py: 自优化建议
"""

import json
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict

# 添加脚本目录到路径
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from advanced_diagnosis import QualityReporter, analyze_quality, get_reporter
from predictive_monitor import PredictiveMonitor, get_current_predictions
from smart_degrade import SmartDegrade, get_smart_degrade, record_quality
from self_optimization import SelfOptimizer, get_optimizer

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('DiagnosisIntegration')


class DiagnosisOrchestrator:
    """诊断编排器 - 协调所有诊断模块"""
    
    def __init__(self):
        self.quality_reporter: Optional[QualityReporter] = None
        self.predictive_monitor: Optional[PredictiveMonitor] = None
        self.smart_degrade: Optional[SmartDegrade] = None
        self.self_optimizer: Optional[SelfOptimizer] = None
        
        self.running = False
        self.cycle_count = 0
        
        # 诊断报告存储
        self.reports: List[Dict] = []
        self.max_reports = 100
    
    async def initialize(self):
        """初始化所有模块"""
        logger.info("Initializing diagnosis modules...")
        
        # 初始化质量报告器
        self.quality_reporter = get_reporter()
        
        # 初始化预测监控器
        self.predictive_monitor = PredictiveMonitor()
        self.predictive_monitor.load_state()
        
        # 初始化智能降级
        self.smart_degrade = get_smart_degrade()
        
        # 初始化自优化器
        self.self_optimizer = get_optimizer()
        self.self_optimizer.load_suggestions()
        
        # 注册智能降级的回调
        self.smart_degrade.on_degrade_callbacks.append(self._on_degrade)
        self.smart_degrade.on_recover_callbacks.append(self._on_recover)
        
        logger.info("All diagnosis modules initialized")
    
    async def analyze_interaction(self, session_id: str, user_query: str, 
                                   ai_response: str) -> Dict:
        """分析单次交互质量"""
        if not self.quality_reporter:
            return {'error': 'Not initialized'}
        
        # 1. 质量分析
        quality_report = await analyze_quality(session_id, user_query, ai_response)
        
        # 2. 将质量分数传递给智能降级系统
        record_quality(quality_report.overall_score)
        
        # 3. 检查是否需要触发降级
        await self.smart_degrade.run_cycle()
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'quality_scores': {
                'overall': quality_report.overall_score,
                'hallucination': quality_report.hallucination_score,
                'logic': quality_report.logic_consistency_score,
                'intent': quality_report.intent_match_score
            },
            'issues_found': len(quality_report.issues),
            'suggestions': quality_report.suggestions,
            'current_degrade_level': self.smart_degrade.current_level.value,
            'enabled_features': list(self.smart_degrade.feature_registry.enabled_features)
        }
        
        self.reports.append(result)
        if len(self.reports) > self.max_reports:
            self.reports.pop(0)
        
        return result
    
    async def run_health_check(self) -> Dict:
        """运行健康检查"""
        if not self.predictive_monitor:
            return {'error': 'Not initialized'}
        
        # 1. 收集指标
        await self.predictive_monitor.collect_metrics()
        
        # 2. 生成预测
        predictions = self.predictive_monitor.generate_predictions()
        
        # 3. 检查告警
        alerts = self.predictive_monitor.check_alerts(predictions)
        
        # 4. 将资源压力信息传递给智能降级
        resource_degrade = self.smart_degrade.resource_monitor.check_degrade_needed()
        if resource_degrade:
            self.smart_degrade.apply_degrade(
                resource_degrade, 
                type('Trigger', (), {'value': 'resource_pressure'})(),
                f"Resource pressure detected: {resource_degrade.value}"
            )
        
        return {
            'timestamp': datetime.now().isoformat(),
            'predictions': [asdict(p) for p in predictions],
            'alerts': alerts,
            'resource_usage': self.smart_degrade.resource_monitor.get_current_usage(),
            'degrade_level': self.smart_degrade.current_level.value
        }
    
    async def run_optimization(self) -> Dict:
        """运行优化分析"""
        if not self.self_optimizer:
            return {'error': 'Not initialized'}
        
        # 1. 完整分析
        new_suggestions = self.self_optimizer.run_full_analysis()
        
        # 2. 执行自动优化
        execution_results = self.self_optimizer.execute_auto_optimizations()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'new_suggestions': [asdict(s) for s in new_suggestions],
            'auto_executed': execution_results,
            'summary': self.self_optimizer.get_summary()
        }
    
    async def run_cycle(self):
        """运行完整诊断周期"""
        self.cycle_count += 1
        logger.info(f"Running diagnosis cycle #{self.cycle_count}")
        
        results = {
            'cycle': self.cycle_count,
            'timestamp': datetime.now().isoformat(),
            'health_check': None,
            'optimization': None,
            'degrade_status': None
        }
        
        # 1. 健康检查（包含预测）
        try:
            results['health_check'] = await self.run_health_check()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            results['health_check'] = {'error': str(e)}
        
        # 2. 优化分析（每10个周期运行一次）
        if self.cycle_count % 10 == 0:
            try:
                results['optimization'] = await self.run_optimization()
            except Exception as e:
                logger.error(f"Optimization failed: {e}")
                results['optimization'] = {'error': str(e)}
        
        # 3. 降级状态
        if self.smart_degrade:
            results['degrade_status'] = self.smart_degrade.get_status()
        
        # 保存周期结果
        cycle_file = Path('/root/.openclaw/workspace/data/diagnosis') / f'cycle_{self.cycle_count}.json'
        with open(cycle_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        return results
    
    def _on_degrade(self, level, trigger, reason):
        """降级回调"""
        logger.warning(f"System degraded to {level.value}: {reason}")
        
        # 记录降级事件
        event = {
            'type': 'degrade',
            'timestamp': datetime.now().isoformat(),
            'level': level.value,
            'trigger': trigger.value if hasattr(trigger, 'value') else str(trigger),
            'reason': reason
        }
        
        event_file = Path('/root/.openclaw/workspace/data/diagnosis') / 'degrade_events.jsonl'
        with open(event_file, 'a') as f:
            f.write(json.dumps(event) + '\n')
    
    def _on_recover(self, old_level):
        """恢复回调"""
        logger.info(f"System recovered from {old_level.value}")
        
        event = {
            'type': 'recover',
            'timestamp': datetime.now().isoformat(),
            'from_level': old_level.value
        }
        
        event_file = Path('/root/.openclaw/workspace/data/diagnosis') / 'degrade_events.jsonl'
        with open(event_file, 'a') as f:
            f.write(json.dumps(event) + '\n')
    
    async def run(self, interval_seconds: int = 60):
        """主运行循环"""
        await self.initialize()
        self.running = True
        
        logger.info(f"Diagnosis orchestrator started (interval: {interval_seconds}s)")
        
        while self.running:
            try:
                await self.run_cycle()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Diagnosis cycle failed: {e}")
                await asyncio.sleep(10)
        
        logger.info("Diagnosis orchestrator stopped")
    
    def stop(self):
        """停止编排器"""
        self.running = False
    
    def get_full_status(self) -> Dict:
        """获取完整状态"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'running': self.running,
            'cycle_count': self.cycle_count,
            'modules': {}
        }
        
        if self.smart_degrade:
            status['modules']['smart_degrade'] = self.smart_degrade.get_status()
        
        if self.self_optimizer:
            status['modules']['optimization'] = self.self_optimizer.get_summary()
        
        if self.quality_reporter:
            status['modules']['quality_trend'] = self.quality_reporter.get_trend_report(hours=24)
        
        status['recent_reports'] = self.reports[-10:]
        
        return status


# 全局实例
_orchestrator: Optional[DiagnosisOrchestrator] = None


def get_orchestrator() -> DiagnosisOrchestrator:
    """获取全局编排器实例"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = DiagnosisOrchestrator()
    return _orchestrator


# 便捷API
async def analyze_response(session_id: str, user_query: str, ai_response: str) -> Dict:
    """分析AI响应质量"""
    orchestrator = get_orchestrator()
    if not orchestrator.quality_reporter:
        await orchestrator.initialize()
    return await orchestrator.analyze_interaction(session_id, user_query, ai_response)


def get_degrade_rules() -> Dict:
    """获取当前降级规则"""
    sd = get_smart_degrade()
    return sd.simplified_mode.get_rules()


def is_feature_available(feature: str) -> bool:
    """检查功能是否可用"""
    sd = get_smart_degrade()
    return sd.feature_registry.is_enabled(feature)


async def check_system_health() -> Dict:
    """检查系统健康状态"""
    orchestrator = get_orchestrator()
    if not orchestrator.predictive_monitor:
        await orchestrator.initialize()
    return await orchestrator.run_health_check()


# CLI接口
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Diagnosis Integration System v5.0')
    parser.add_argument('--run', action='store_true', help='Run continuous monitoring')
    parser.add_argument('--status', action='store_true', help='Show full status')
    parser.add_argument('--analyze', nargs=3, metavar=('SESSION', 'QUERY', 'RESPONSE'),
                       help='Analyze an interaction')
    parser.add_argument('--health', action='store_true', help='Run health check')
    parser.add_argument('--optimize', action='store_true', help='Run optimization')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds')
    
    args = parser.parse_args()
    
    orchestrator = get_orchestrator()
    
    if args.run:
        try:
            asyncio.run(orchestrator.run(args.interval))
        except KeyboardInterrupt:
            orchestrator.stop()
    elif args.status:
        print(json.dumps(orchestrator.get_full_status(), indent=2, default=str))
    elif args.analyze:
        session_id, query, response = args.analyze
        result = asyncio.run(analyze_response(session_id, query, response))
        print(json.dumps(result, indent=2))
    elif args.health:
        result = asyncio.run(check_system_health())
        print(json.dumps(result, indent=2))
    elif args.optimize:
        asyncio.run(orchestrator.initialize())
        result = asyncio.run(orchestrator.run_optimization())
        print(json.dumps(result, indent=2))
    else:
        print("Diagnosis Integration System v5.0")
        print("Usage: python diagnosis_integration.py --run | --status | --health | --optimize")
