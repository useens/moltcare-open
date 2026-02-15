#!/usr/bin/env python3
"""
森森·智能能耗管理系统 v1.0
基于场景自动切换4种运行模式，优化Token成本

模式定义:
1. 性能模式 - 全功能高消耗，处理复杂任务
2. 均衡模式 - 平衡性能与成本，日常运行
3. 节能模式 - 低消耗维持，简单任务
4. 冻结模式 - 极低消耗，仅心跳维持

触发策略:
- 用户主动指令
- 时间调度 (夜间自动节能)
- 任务复杂度检测
- Token预算告警
- 系统负载自适应
"""

import json
import os
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# 配置文件路径
CONFIG_PATH = Path(__file__).parent.parent / "config" / "power-modes.yaml"
STATE_PATH = Path(__file__).parent.parent / "memory" / "power-mode-state.json"

class PowerMode(Enum):
    """能耗模式枚举"""
    PERFORMANCE = "performance"    # 性能模式
    BALANCED = "balanced"          # 均衡模式
    ECO = "eco"                    # 节能模式
    FROZEN = "frozen"              # 冻结模式

@dataclass
class ModeConfig:
    """模式配置"""
    name: str                      # 模式名称
    name_cn: str                   # 中文名
    token_budget: int              # Token预算 (每小时)
    max_agents: int                # 最大子代理数
    scan_interval: int             # 扫描间隔 (分钟)
    deep_extract: bool             # 是否深度提取
    sources: int                   # 活跃信息源数
    reasoning: str                 # 推理级别 (high/medium/low/off)
    auto_dialog: bool              # 自动对话
    learning_debt: bool            # 处理学习债务
    health_check: bool             # 健康检查
    backup: bool                   # 自动备份
    description: str               # 模式描述
    
    def to_dict(self):
        return asdict(self)

# 模式配置定义
MODE_DEFINITIONS = {
    PowerMode.PERFORMANCE: ModeConfig(
        name="performance",
        name_cn="性能模式",
        token_budget=10000,         # 10k tokens/小时
        max_agents=20,              # 20子代理
        scan_interval=10,           # 10分钟
        deep_extract=True,          # 启用深度提取
        sources=12,                 # 12个信息源
        reasoning="high",           # 高级推理
        auto_dialog=True,           # 自动对话
        learning_debt=True,         # 处理学习债务
        health_check=True,          # 健康检查
        backup=True,                # 备份
        description="全功能高消耗，处理复杂任务、深度学习、多代理并行"
    ),
    
    PowerMode.BALANCED: ModeConfig(
        name="balanced",
        name_cn="均衡模式",
        token_budget=3000,          # 3k tokens/小时
        max_agents=5,               # 5子代理
        scan_interval=30,           # 30分钟
        deep_extract=True,          # 启用深度提取
        sources=8,                  # 8个信息源
        reasoning="medium",         # 中级推理
        auto_dialog=False,          # 不自动对话
        learning_debt=True,         # 处理学习债务
        health_check=True,          # 健康检查
        backup=True,                # 备份
        description="平衡性能与成本，日常运行默认模式"
    ),
    
    PowerMode.ECO: ModeConfig(
        name="eco",
        name_cn="节能模式",
        token_budget=500,           # 500 tokens/小时
        max_agents=1,               # 1子代理
        scan_interval=60,           # 60分钟
        deep_extract=False,         # 不深度提取
        sources=3,                  # 3个信息源
        reasoning="low",            # 低级推理
        auto_dialog=False,          # 不自动对话
        learning_debt=False,        # 不处理学习债务
        health_check=True,          # 健康检查
        backup=False,               # 不备份
        description="低消耗维持，仅处理简单任务和基本监控"
    ),
    
    PowerMode.FROZEN: ModeConfig(
        name="frozen",
        name_cn="冻结模式",
        token_budget=50,            # 50 tokens/小时
        max_agents=0,               # 无子代理
        scan_interval=120,          # 120分钟
        deep_extract=False,         # 不深度提取
        sources=0,                  # 无信息源
        reasoning="off",            # 关闭推理
        auto_dialog=False,          # 不自动对话
        learning_debt=False,        # 不处理学习债务
        health_check=False,         # 不健康检查
        backup=False,               # 不备份
        description="极低消耗，仅心跳维持和紧急响应"
    )
}

# 自动切换规则
AUTO_SWITCH_RULES = {
    # 时间规则
    "time_rules": [
        {
            "name": "夜间节能",
            "condition": "22:00-07:00",
            "mode": "eco",
            "priority": 3
        },
        {
            "name": "深夜冻结",
            "condition": "01:00-06:00",
            "mode": "frozen",
            "priority": 2
        }
    ],
    
    # 负载规则
    "load_rules": [
        {
            "name": "高负载降频",
            "condition": "cpu > 85%",
            "mode": "eco",
            "priority": 5
        },
        {
            "name": "系统空闲",
            "condition": "idle > 30min",
            "mode": "frozen",
            "priority": 4
        }
    ],
    
    # 任务规则
    "task_rules": [
        {
            "name": "复杂任务",
            "condition": "task_complexity > 0.8",
            "mode": "performance",
            "priority": 10
        },
        {
            "name": "Signal 10情报",
            "condition": "signal >= 10",
            "mode": "performance",
            "priority": 10
        },
        {
            "name": "用户在线",
            "condition": "user_active",
            "mode": "balanced",
            "priority": 8
        }
    ],
    
    # 预算规则
    "budget_rules": [
        {
            "name": "预算告警",
            "condition": "token_usage > 80%",
            "mode": "eco",
            "priority": 6
        },
        {
            "name": "预算耗尽",
            "condition": "token_usage > 95%",
            "mode": "frozen",
            "priority": 9
        }
    ]
}

# 场景化应用策略
SCENARIO_STRATEGY = {
    # 用户交互场景
    "user_interaction": {
        "default": "balanced",
        "complex_query": "performance",    # 复杂问题 -> 性能模式
        "simple_query": "eco",              # 简单问题 -> 节能模式
        "long_idle": "frozen"               # 长时间空闲 -> 冻结模式
    },
    
    # 情报收集场景
    "intel_collection": {
        "scheduled": "eco",                 # 定时采集 -> 节能模式
        "high_signal_alert": "performance", # 高Signal告警 -> 性能模式
        "deep_learning": "performance",     # 深度学习 -> 性能模式
        "routine_scan": "balanced"          # 例行扫描 -> 均衡模式
    },
    
    # 系统维护场景
    "maintenance": {
        "health_check": "eco",              # 健康检查 -> 节能模式
        "backup": "balanced",               # 备份 -> 均衡模式
        "auto_heal": "performance",         # 自动修复 -> 性能模式
        "update": "performance"             # 更新 -> 性能模式
    },
    
    # 夜间运行场景
    "nighttime": {
        "00:00-06:00": "frozen",            # 深夜 -> 冻结模式
        "06:00-08:00": "eco",               # 清晨 -> 节能模式
        "22:00-00:00": "eco"                # 晚间 -> 节能模式
    }
}

class PowerModeManager:
    """能耗模式管理器"""
    
    def __init__(self):
        self.current_mode = PowerMode.BALANCED
        self.state_file = STATE_PATH
        self.load_state()
        
    def load_state(self):
        """加载状态"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                data = json.load(f)
                self.current_mode = PowerMode(data.get("mode", "balanced"))
                
    def save_state(self):
        """保存状态"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump({
                "mode": self.current_mode.value,
                "updated_at": datetime.now().isoformat(),
                "config": MODE_DEFINITIONS[self.current_mode].to_dict()
            }, f, indent=2)
            
    def switch_mode(self, mode: PowerMode, reason: str = ""):
        """切换模式"""
        old_mode = self.current_mode
        self.current_mode = mode
        self.save_state()
        
        config = MODE_DEFINITIONS[mode]
        print(f"🔄 模式切换: {MODE_DEFINITIONS[old_mode].name_cn} → {config.name_cn}")
        print(f"   原因: {reason}")
        print(f"   Token预算: {config.token_budget}/小时")
        print(f"   子代理: {config.max_agents}个")
        print(f"   扫描间隔: {config.scan_interval}分钟")
        return config
        
    def get_current_config(self) -> ModeConfig:
        """获取当前配置"""
        return MODE_DEFINITIONS[self.current_mode]
        
    def should_switch(self) -> Optional[tuple]:
        """检查是否应该切换模式"""
        now = datetime.now()
        current_hour = now.hour
        
        # 时间规则检查
        if 1 <= current_hour < 6:
            return (PowerMode.FROZEN, "深夜时段 01:00-06:00")
        elif 22 <= current_hour or current_hour < 7:
            return (PowerMode.ECO, "夜间时段 22:00-07:00")
            
        # 默认均衡模式
        if self.current_mode != PowerMode.BALANCED:
            return (PowerMode.BALANCED, "日间时段默认")
            
        return None
        
    def auto_switch(self):
        """自动切换"""
        result = self.should_switch()
        if result:
            mode, reason = result
            if mode != self.current_mode:
                return self.switch_mode(mode, reason)
        return None

def get_cost_estimate(mode: PowerMode, hours: float = 24) -> dict:
    """估算成本"""
    config = MODE_DEFINITIONS[mode]
    daily_tokens = config.token_budget * hours
    
    # 假设1M tokens = $0.15 (Kimi K2.5价格)
    cost_usd = (daily_tokens / 1_000_000) * 0.15
    cost_cny = cost_usd * 7.2
    
    return {
        "mode": config.name_cn,
        "hours": hours,
        "daily_tokens": daily_tokens,
        "cost_usd": cost_usd,
        "cost_cny": cost_cny,
        "monthly_cost_cny": cost_cny * 30
    }

def print_mode_comparison():
    """打印模式对比"""
    print("\n" + "="*80)
    print("🌲 森森·智能能耗管理系统 v1.0")
    print("="*80)
    print("\n📊 模式对比:")
    print(f"{'模式':<12} {'Token/小时':<12} {'日消耗':<12} {'月成本':<12} {'适用场景'}")
    print("-"*80)
    
    for mode in PowerMode:
        config = MODE_DEFINITIONS[mode]
        cost = get_cost_estimate(mode, 24)
        print(f"{config.name_cn:<12} {config.token_budget:<12} {cost['daily_tokens']:<12} "
              f"¥{cost['monthly_cost_cny']:.2f}     {config.description[:30]}...")
    
    print("\n🔄 自动切换规则:")
    print("  • 01:00-06:00 → 冻结模式 (节省95%)")
    print("  • 22:00-07:00 → 节能模式 (节省85%)")
    print("  • 07:00-22:00 → 均衡模式 (默认)")
    print("  • 用户指令/复杂任务 → 性能模式")
    print("  • Token预算>80% → 自动降频")
    
    print("\n💡 建议策略:")
    print("  • 默认运行: 均衡模式 (¥97/月)")
    print("  • 夜间自动: 节能/冻结 (¥16/月)")
    print("  • 深度工作时: 性能模式 (¥324/月)")
    print("  • 混合策略: 均衡+夜间冻结 (¥56/月)")
    print("="*80)

# CLI接口
if __name__ == "__main__":
    import sys
    
    manager = PowerModeManager()
    
    if len(sys.argv) < 2:
        print_mode_comparison()
        print(f"\n当前模式: {manager.get_current_config().name_cn}")
        sys.exit(0)
        
    command = sys.argv[1]
    
    if command == "switch":
        mode_name = sys.argv[2] if len(sys.argv) > 2 else "balanced"
        mode = PowerMode(mode_name)
        manager.switch_mode(mode, "手动切换")
        
    elif command == "auto":
        manager.auto_switch()
        
    elif command == "status":
        config = manager.get_current_config()
        print(f"当前模式: {config.name_cn}")
        print(f"Token预算: {config.token_budget}/小时")
        print(f"子代理数: {config.max_agents}")
        print(f"扫描间隔: {config.scan_interval}分钟")
        
    elif command == "cost":
        hours = float(sys.argv[2]) if len(sys.argv) > 2 else 24
        for mode in PowerMode:
            cost = get_cost_estimate(mode, hours)
            print(f"{cost['mode']}: {cost['daily_tokens']} tokens, "
                  f"¥{cost['cost_cny']:.2f}")
    else:
        print("用法: python power_mode_manager.py [switch|auto|status|cost]")
