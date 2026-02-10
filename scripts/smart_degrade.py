#!/usr/bin/env python3
"""
Smart Degrade System v5.0
智能降级策略模块

功能：
1. 推理质量下降时自动切换到简化模式
2. 资源紧张时关闭非核心功能
3. 网络中断时启用离线模式
4. 自动恢复策略
"""

import json
import time
import asyncio
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Callable, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import deque
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/.openclaw/workspace/logs/smart_degrade.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SmartDegrade')


class DegradeLevel(Enum):
    """降级等级"""
    NORMAL = "normal"  # 正常运行
    LIGHT = "light"    # 轻度降级
    MEDIUM = "medium"  # 中度降级
    SEVERE = "severe"  # 重度降级
    OFFLINE = "offline"  # 离线模式


class TriggerType(Enum):
    """触发类型"""
    QUALITY_DROP = "quality_drop"
    RESOURCE_PRESSURE = "resource_pressure"
    NETWORK_FAILURE = "network_failure"
    API_RATE_LIMIT = "api_rate_limit"
    MANUAL = "manual"


@dataclass
class DegradeEvent:
    """降级事件"""
    timestamp: str
    trigger_type: str
    from_level: str
    to_level: str
    reason: str
    auto_recover: bool
    recovered_at: Optional[str] = None


@dataclass
class SystemState:
    """系统状态"""
    timestamp: str
    quality_score: float
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_available: bool
    api_health: Dict[str, float]
    current_level: str


class FeatureRegistry:
    """功能注册表"""
    
    def __init__(self):
        self.features: Dict[str, Dict] = {}
        self.enabled_features: Set[str] = set()
    
    def register(self, name: str, category: str, priority: int,
                 degrade_level: DegradeLevel, handler: Optional[Callable] = None):
        """
        注册功能
        
        Args:
            name: 功能名称
            category: 类别 ('core', 'enhancement', 'optional', 'experimental')
            priority: 优先级 (1-10, 越低越核心)
            degrade_level: 此功能在何种降级级别下被禁用
            handler: 启用/禁用该功能的回调函数
        """
        self.features[name] = {
            'category': category,
            'priority': priority,
            'degrade_level': degrade_level,
            'handler': handler,
            'enabled': True
        }
        self.enabled_features.add(name)
        logger.info(f"Registered feature: {name} (category={category}, priority={priority})")
    
    def enable(self, name: str):
        """启用功能"""
        if name in self.features:
            self.features[name]['enabled'] = True
            self.enabled_features.add(name)
            handler = self.features[name].get('handler')
            if handler:
                try:
                    handler(True)
                except Exception as e:
                    logger.error(f"Feature enable handler failed for {name}: {e}")
    
    def disable(self, name: str):
        """禁用功能"""
        if name in self.features:
            self.features[name]['enabled'] = False
            self.enabled_features.discard(name)
            handler = self.features[name].get('handler')
            if handler:
                try:
                    handler(False)
                except Exception as e:
                    logger.error(f"Feature disable handler failed for {name}: {e}")
    
    def is_enabled(self, name: str) -> bool:
        """检查功能是否启用"""
        return name in self.enabled_features
    
    def get_features_by_category(self, category: str) -> List[str]:
        """获取特定类别的功能"""
        return [name for name, info in self.features.items() 
                if info['category'] == category]
    
    def apply_degrade_level(self, level: DegradeLevel):
        """应用降级级别"""
        level_order = [DegradeLevel.NORMAL, DegradeLevel.LIGHT, 
                      DegradeLevel.MEDIUM, DegradeLevel.SEVERE, DegradeLevel.OFFLINE]
        
        current_level_index = level_order.index(level)
        
        for name, info in self.features.items():
            feature_level_index = level_order.index(info['degrade_level'])
            
            if current_level_index >= feature_level_index:
                # 当前降级级别高于或等于功能的降级阈值，禁用该功能
                if info['enabled']:
                    logger.info(f"Disabling feature '{name}' due to degrade level {level.value}")
                    self.disable(name)
            else:
                # 当前降级级别低于功能的降级阈值，启用该功能
                if not info['enabled']:
                    logger.info(f"Re-enabling feature '{name}' as degrade level is {level.value}")
                    self.enable(name)


class QualityMonitor:
    """质量监控器"""
    
    def __init__(self, window_size: int = 20):
        self.scores: deque = deque(maxlen=window_size)
        self.thresholds = {
            'light': 0.7,
            'medium': 0.5,
            'severe': 0.3
        }
    
    def record_score(self, score: float):
        """记录质量分数"""
        self.scores.append({
            'timestamp': datetime.now(),
            'score': score
        })
    
    def get_average_score(self, last_n: int = 5) -> float:
        """获取最近N个的平均分数"""
        if not self.scores:
            return 1.0
        
        recent = list(self.scores)[-last_n:]
        return sum(s['score'] for s in recent) / len(recent)
    
    def get_trend(self) -> str:
        """获取趋势"""
        if len(self.scores) < 5:
            return 'stable'
        
        recent = list(self.scores)[-5:]
        older = list(self.scores)[:-5] if len(self.scores) > 5 else list(self.scores)[:5]
        
        recent_avg = sum(s['score'] for s in recent) / len(recent)
        older_avg = sum(s['score'] for s in older) / len(older)
        
        diff = recent_avg - older_avg
        if diff < -0.1:
            return 'declining'
        elif diff > 0.1:
            return 'improving'
        return 'stable'
    
    def check_degrade_needed(self) -> Optional[DegradeLevel]:
        """检查是否需要降级"""
        avg_score = self.get_average_score()
        trend = self.get_trend()
        
        if trend == 'declining' and avg_score < self.thresholds['severe']:
            return DegradeLevel.SEVERE
        elif avg_score < self.thresholds['severe']:
            return DegradeLevel.SEVERE
        elif avg_score < self.thresholds['medium']:
            return DegradeLevel.MEDIUM
        elif avg_score < self.thresholds['light']:
            return DegradeLevel.LIGHT
        
        return None


class ResourceMonitor:
    """资源监控器"""
    
    def __init__(self):
        self.thresholds = {
            'memory': {'light': 70, 'medium': 80, 'severe': 90},
            'cpu': {'light': 75, 'medium': 85, 'severe': 95},
            'disk': {'light': 80, 'medium': 90, 'severe': 95}
        }
    
    def get_current_usage(self) -> Dict[str, float]:
        """获取当前资源使用率"""
        return {
            'memory': psutil.virtual_memory().percent,
            'cpu': psutil.cpu_percent(interval=0.1),
            'disk': psutil.disk_usage('/').percent
        }
    
    def check_degrade_needed(self) -> Optional[DegradeLevel]:
        """检查是否需要降级"""
        usage = self.get_current_usage()
        
        # 检查最严重的资源压力
        max_severity = DegradeLevel.NORMAL
        
        for resource, percent in usage.items():
            if resource not in self.thresholds:
                continue
            
            thresholds = self.thresholds[resource]
            
            if percent >= thresholds['severe']:
                return DegradeLevel.SEVERE
            elif percent >= thresholds['medium']:
                max_severity = max(max_severity, DegradeLevel.MEDIUM, key=lambda x: list(DegradeLevel).index(x))
            elif percent >= thresholds['light']:
                max_severity = max(max_severity, DegradeLevel.LIGHT, key=lambda x: list(DegradeLevel).index(x))
        
        return max_severity if max_severity != DegradeLevel.NORMAL else None


class NetworkMonitor:
    """网络监控器"""
    
    def __init__(self):
        self.last_check: Optional[datetime] = None
        self.available = True
        self.check_interval = timedelta(seconds=30)
        
        # 关键端点
        self.endpoints = [
            ('8.8.8.8', 53),  # Google DNS
            ('1.1.1.1', 53),  # Cloudflare DNS
        ]
    
    async def check_connectivity(self) -> bool:
        """检查网络连通性"""
        # 如果刚检查过，直接返回缓存结果
        if self.last_check and (datetime.now() - self.last_check) < self.check_interval:
            return self.available
        
        try:
            # 使用ping检查连通性
            proc = await asyncio.create_subprocess_exec(
                'ping', '-c', '1', '-W', '3', '8.8.8.8',
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await asyncio.wait_for(proc.wait(), timeout=5)
            
            self.available = proc.returncode == 0
            self.last_check = datetime.now()
            
            return self.available
        except Exception:
            self.available = False
            self.last_check = datetime.now()
            return False
    
    def is_available(self) -> bool:
        """获取网络可用状态"""
        return self.available


class SimplifiedModeManager:
    """简化模式管理器"""
    
    def __init__(self):
        self.simplification_rules = {
            DegradeLevel.LIGHT: {
                'max_response_length': 2000,
                'disable_enhanced_formatting': True,
                'reduce_context_window': False,
                'use_cached_responses': False
            },
            DegradeLevel.MEDIUM: {
                'max_response_length': 1000,
                'disable_enhanced_formatting': True,
                'reduce_context_window': True,
                'use_cached_responses': True,
                'disable_multimedia': True
            },
            DegradeLevel.SEVERE: {
                'max_response_length': 500,
                'disable_enhanced_formatting': True,
                'reduce_context_window': True,
                'use_cached_responses': True,
                'disable_multimedia': True,
                'simplify_reasoning': True,
                'disable_external_calls': True
            },
            DegradeLevel.OFFLINE: {
                'max_response_length': 300,
                'disable_enhanced_formatting': True,
                'reduce_context_window': True,
                'use_cached_responses': True,
                'disable_multimedia': True,
                'simplify_reasoning': True,
                'disable_external_calls': True,
                'use_local_models_only': True,
                'disable_sync': True
            }
        }
        self.current_rules: Dict = {}
    
    def apply_level(self, level: DegradeLevel):
        """应用简化规则"""
        if level == DegradeLevel.NORMAL:
            self.current_rules = {}
        else:
            self.current_rules = self.simplification_rules.get(level, {})
        
        logger.info(f"Applied simplification rules for level: {level.value}")
    
    def get_rules(self) -> Dict:
        """获取当前规则"""
        return self.current_rules.copy()
    
    def should_apply(self, rule: str) -> bool:
        """检查是否应应用某规则"""
        return self.current_rules.get(rule, False)
    
    def get_max_response_length(self) -> int:
        """获取最大响应长度"""
        return self.current_rules.get('max_response_length', 5000)


class AutoRecoveryManager:
    """自动恢复管理器"""
    
    def __init__(self, smart_degrade):
        self.smart_degrade = smart_degrade
        self.recovery_checks: deque = deque(maxlen=10)
        self.recovery_threshold = 3  # 连续3次检查通过才恢复
        self.last_recovery_attempt: Optional[datetime] = None
        self.recovery_cooldown = timedelta(minutes=5)
    
    def record_check(self, can_recover: bool):
        """记录恢复检查"""
        self.recovery_checks.append({
            'timestamp': datetime.now(),
            'can_recover': can_recover
        })
    
    def check_can_recover(self) -> bool:
        """检查是否可以恢复"""
        # 检查冷却时间
        if self.last_recovery_attempt and \
           (datetime.now() - self.last_recovery_attempt) < self.recovery_cooldown:
            return False
        
        if len(self.recovery_checks) < self.recovery_threshold:
            return False
        
        # 检查最近N次是否都通过
        recent = list(self.recovery_checks)[-self.recovery_threshold:]
        return all(check['can_recover'] for check in recent)
    
    def mark_recovery_attempt(self):
        """标记恢复尝试"""
        self.last_recovery_attempt = datetime.now()
    
    def evaluate_recovery_conditions(self) -> Dict[str, bool]:
        """评估各项恢复条件"""
        conditions = {}
        
        # 质量分数恢复
        quality_score = self.smart_degrade.quality_monitor.get_average_score()
        conditions['quality_recovered'] = quality_score > 0.75
        
        # 资源压力缓解
        resource_usage = self.smart_degrade.resource_monitor.get_current_usage()
        conditions['resources_recovered'] = all(
            usage < 70 for usage in resource_usage.values()
        )
        
        # 网络恢复
        conditions['network_recovered'] = self.smart_degrade.network_monitor.is_available()
        
        return conditions


class SmartDegrade:
    """智能降级主类"""
    
    def __init__(self, data_dir: str = '/root/.openclaw/workspace/data/diagnosis'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_level = DegradeLevel.NORMAL
        self.feature_registry = FeatureRegistry()
        self.quality_monitor = QualityMonitor()
        self.resource_monitor = ResourceMonitor()
        self.network_monitor = NetworkMonitor()
        self.simplified_mode = SimplifiedModeManager()
        self.recovery_manager = AutoRecoveryManager(self)
        
        self.event_history: deque = deque(maxlen=100)
        self.state_history: deque = deque(maxlen=1000)
        
        self.running = False
        self.check_interval = 30  # 秒
        
        # 回调函数
        self.on_degrade_callbacks: List[Callable] = []
        self.on_recover_callbacks: List[Callable] = []
        
        # 注册默认功能
        self._register_default_features()
    
    def _register_default_features(self):
        """注册默认功能"""
        # 核心功能 - 永不降级
        self.feature_registry.register('basic_chat', 'core', 1, DegradeLevel.OFFLINE)
        self.feature_registry.register('file_operations', 'core', 2, DegradeLevel.OFFLINE)
        
        # 增强功能
        self.feature_registry.register('advanced_reasoning', 'enhancement', 3, DegradeLevel.MEDIUM)
        self.feature_registry.register('context_memory', 'enhancement', 4, DegradeLevel.MEDIUM)
        self.feature_registry.register('multi_step_planning', 'enhancement', 5, DegradeLevel.LIGHT)
        
        # 可选功能
        self.feature_registry.register('web_search', 'optional', 6, DegradeLevel.LIGHT)
        self.feature_registry.register('code_execution', 'optional', 7, DegradeLevel.MEDIUM)
        self.feature_registry.register('multimedia_generation', 'optional', 8, DegradeLevel.LIGHT)
        
        # 实验性功能
        self.feature_registry.register('experimental_features', 'experimental', 10, DegradeLevel.NORMAL)
    
    def register_feature(self, name: str, category: str, priority: int,
                        degrade_level: DegradeLevel, handler: Optional[Callable] = None):
        """注册功能"""
        self.feature_registry.register(name, category, priority, degrade_level, handler)
    
    def record_quality_score(self, score: float):
        """记录质量分数"""
        self.quality_monitor.record_score(score)
    
    def get_current_state(self) -> SystemState:
        """获取当前系统状态"""
        resource_usage = self.resource_monitor.get_current_usage()
        
        return SystemState(
            timestamp=datetime.now().isoformat(),
            quality_score=self.quality_monitor.get_average_score(),
            cpu_percent=resource_usage['cpu'],
            memory_percent=resource_usage['memory'],
            disk_percent=resource_usage['disk'],
            network_available=self.network_monitor.is_available(),
            api_health={},  # 可由外部更新
            current_level=self.current_level.value
        )
    
    async def evaluate_degrade(self) -> Optional[DegradeLevel]:
        """评估是否需要降级"""
        required_levels = []
        trigger_types = []
        
        # 检查质量
        quality_degrade = self.quality_monitor.check_degrade_needed()
        if quality_degrade:
            required_levels.append(quality_degrade)
            trigger_types.append(TriggerType.QUALITY_DROP)
        
        # 检查资源
        resource_degrade = self.resource_monitor.check_degrade_needed()
        if resource_degrade:
            required_levels.append(resource_degrade)
            trigger_types.append(TriggerType.RESOURCE_PRESSURE)
        
        # 检查网络
        network_available = await self.network_monitor.check_connectivity()
        if not network_available:
            required_levels.append(DegradeLevel.OFFLINE)
            trigger_types.append(TriggerType.NETWORK_FAILURE)
        
        if not required_levels:
            return None
        
        # 取最严重的降级级别
        level_order = [DegradeLevel.NORMAL, DegradeLevel.LIGHT, 
                      DegradeLevel.MEDIUM, DegradeLevel.SEVERE, DegradeLevel.OFFLINE]
        
        max_level = max(required_levels, key=lambda x: level_order.index(x))
        
        return max_level
    
    def apply_degrade(self, level: DegradeLevel, trigger: TriggerType, reason: str):
        """应用降级"""
        if level == self.current_level:
            return
        
        old_level = self.current_level
        self.current_level = level
        
        # 记录事件
        event = DegradeEvent(
            timestamp=datetime.now().isoformat(),
            trigger_type=trigger.value,
            from_level=old_level.value,
            to_level=level.value,
            reason=reason,
            auto_recover=True
        )
        self.event_history.append(event)
        
        # 应用功能降级
        self.feature_registry.apply_degrade_level(level)
        
        # 应用简化模式
        self.simplified_mode.apply_level(level)
        
        # 触发回调
        for callback in self.on_degrade_callbacks:
            try:
                callback(level, trigger, reason)
            except Exception as e:
                logger.error(f"Degrade callback failed: {e}")
        
        logger.warning(f"System degraded from {old_level.value} to {level.value}: {reason}")
    
    def attempt_recovery(self):
        """尝试恢复"""
        if self.current_level == DegradeLevel.NORMAL:
            return
        
        # 评估恢复条件
        conditions = self.recovery_manager.evaluate_recovery_conditions()
        can_recover = all(conditions.values())
        
        self.recovery_manager.record_check(can_recover)
        
        if self.recovery_manager.check_can_recover():
            self.recovery_manager.mark_recovery_attempt()
            
            # 执行恢复
            old_level = self.current_level
            self.current_level = DegradeLevel.NORMAL
            
            # 恢复功能
            self.feature_registry.apply_degrade_level(DegradeLevel.NORMAL)
            
            # 恢复简化模式
            self.simplified_mode.apply_level(DegradeLevel.NORMAL)
            
            # 更新事件
            if self.event_history:
                last_event = self.event_history[-1]
                if not last_event.recovered_at:
                    last_event.recovered_at = datetime.now().isoformat()
            
            # 触发回调
            for callback in self.on_recover_callbacks:
                try:
                    callback(old_level)
                except Exception as e:
                    logger.error(f"Recover callback failed: {e}")
            
            logger.info(f"System recovered from {old_level.value} to normal")
    
    async def run_cycle(self):
        """运行一个检查周期"""
        # 记录状态
        state = self.get_current_state()
        self.state_history.append(asdict(state))
        
        # 评估降级需求
        required_level = await self.evaluate_degrade()
        
        if required_level and required_level != self.current_level:
            # 需要降级
            trigger = self._determine_trigger()
            reason = self._generate_reason(required_level)
            self.apply_degrade(required_level, trigger, reason)
        elif self.current_level != DegradeLevel.NORMAL:
            # 尝试恢复
            self.attempt_recovery()
    
    def _determine_trigger(self) -> TriggerType:
        """确定触发类型"""
        if not self.network_monitor.is_available():
            return TriggerType.NETWORK_FAILURE
        
        resource_usage = self.resource_monitor.get_current_usage()
        if any(u > 80 for u in resource_usage.values()):
            return TriggerType.RESOURCE_PRESSURE
        
        if self.quality_monitor.get_average_score() < 0.7:
            return TriggerType.QUALITY_DROP
        
        return TriggerType.MANUAL
    
    def _generate_reason(self, level: DegradeLevel) -> str:
        """生成降级原因"""
        reasons = []
        
        quality_score = self.quality_monitor.get_average_score()
        if quality_score < 0.7:
            reasons.append(f"quality score {quality_score:.2f}")
        
        resource_usage = self.resource_monitor.get_current_usage()
        for resource, usage in resource_usage.items():
            if usage > 70:
                reasons.append(f"{resource} usage {usage:.1f}%")
        
        if not self.network_monitor.is_available():
            reasons.append("network unavailable")
        
        return f"Triggered by: {', '.join(reasons)}"
    
    async def run(self):
        """主运行循环"""
        self.running = True
        logger.info("Smart degrade system started")
        
        while self.running:
            try:
                await self.run_cycle()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Smart degrade cycle failed: {e}")
                await asyncio.sleep(10)
        
        logger.info("Smart degrade system stopped")
    
    def stop(self):
        """停止系统"""
        self.running = False
    
    def get_status(self) -> Dict:
        """获取系统状态"""
        return {
            'current_level': self.current_level.value,
            'quality_score': self.quality_monitor.get_average_score(),
            'quality_trend': self.quality_monitor.get_trend(),
            'resource_usage': self.resource_monitor.get_current_usage(),
            'network_available': self.network_monitor.is_available(),
            'enabled_features': list(self.feature_registry.enabled_features),
            'simplification_rules': self.simplified_mode.get_rules(),
            'recent_events': [asdict(e) for e in list(self.event_history)[-10:]],
            'can_recover': self.recovery_manager.check_can_recover()
        }
    
    def force_degrade(self, level: DegradeLevel, reason: str = "Manual trigger"):
        """强制降级"""
        self.apply_degrade(level, TriggerType.MANUAL, reason)
    
    def force_recover(self):
        """强制恢复"""
        self.attempt_recovery()


# 便捷函数
_smart_degrade: Optional[SmartDegrade] = None


def get_smart_degrade() -> SmartDegrade:
    """获取全局智能降级实例"""
    global _smart_degrade
    if _smart_degrade is None:
        _smart_degrade = SmartDegrade()
    return _smart_degrade


def record_quality(score: float):
    """记录质量分数（便捷函数）"""
    sd = get_smart_degrade()
    sd.record_quality_score(score)


def get_simplification_rules() -> Dict:
    """获取当前简化规则"""
    sd = get_smart_degrade()
    return sd.simplified_mode.get_rules()


def is_feature_enabled(feature: str) -> bool:
    """检查功能是否启用"""
    sd = get_smart_degrade()
    return sd.feature_registry.is_enabled(feature)


# CLI接口
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart Degrade System')
    parser.add_argument('--run', action='store_true', help='Run continuous monitoring')
    parser.add_argument('--status', action='store_true', help='Show status')
    parser.add_argument('--degrade', type=str, choices=['light', 'medium', 'severe', 'offline'],
                       help='Force degrade to level')
    parser.add_argument('--recover', action='store_true', help='Force recover')
    parser.add_argument('--record-quality', type=float, help='Record quality score')
    
    args = parser.parse_args()
    
    sd = get_smart_degrade()
    
    if args.run:
        try:
            asyncio.run(sd.run())
        except KeyboardInterrupt:
            sd.stop()
    elif args.status:
        print(json.dumps(sd.get_status(), indent=2))
    elif args.degrade:
        level_map = {
            'light': DegradeLevel.LIGHT,
            'medium': DegradeLevel.MEDIUM,
            'severe': DegradeLevel.SEVERE,
            'offline': DegradeLevel.OFFLINE
        }
        sd.force_degrade(level_map[args.degrade])
        print(f"Forced degrade to {args.degrade}")
    elif args.recover:
        sd.force_recover()
        print("Forced recover initiated")
    elif args.record_quality is not None:
        sd.record_quality_score(args.record_quality)
        print(f"Recorded quality score: {args.record_quality}")
    else:
        print(json.dumps(sd.get_status(), indent=2))
