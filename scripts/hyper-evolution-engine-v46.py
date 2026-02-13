#!/usr/bin/env python3
"""
超进化引擎 v4.6.0 - 自适应频率版
根据Signal发现率动态调整扫描间隔
实现深度学习闭环
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/hyper-evolution.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('HyperEvolution')

# 自适应频率管理器
class AdaptiveFrequencyManager:
    """
    自适应频率管理器 - 根据Signal发现率动态调整扫描间隔
    
    核心逻辑:
    - 发现率高(>20%) → 延长间隔 → 充分深度学习闭环
    - 发现率低(<5%)  → 缩短间隔 → 不错过内容
    """
    
    def __init__(self, config_path="memory/adaptive_freq.json"):
        self.min_interval = 300       # 5分钟 (最短)
        self.max_interval = 1800      # 30分钟 (最长)
        self.default_interval = 600   # 10分钟 (默认)
        self.adjustment_step = 120    # 调整步长: 2分钟
        
        self.high_threshold = 0.20    # 高发现率阈值: 20%
        self.low_threshold = 0.05     # 低发现率阈值: 5%
        
        self.history = []
        self.max_history = 10
        self.config_path = Path(config_path)
        
        self.load_history()
    
    def load_history(self):
        """加载历史数据"""
        if self.config_path.exists():
            try:
                data = json.loads(self.config_path.read_text())
                self.history = data.get('history', [])
                logger.info(f"📊 加载历史记录: {len(self.history)} 次扫描")
            except Exception as e:
                logger.warning(f"⚠️  加载历史失败: {e}")
    
    def save_history(self):
        """保存历史数据"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.config_path.write_text(json.dumps({
                'history': self.history,
                'last_update': datetime.now().isoformat()
            }, indent=2))
        except Exception as e:
            logger.warning(f"⚠️  保存历史失败: {e}")
    
    def record_scan(self, high_signal_count: int, total_scanned: int, interval_used: int = None):
        """记录一次扫描结果"""
        discovery_rate = high_signal_count / max(total_scanned, 1)
        
        self.history.append({
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'high_signal': high_signal_count,
            'total': total_scanned,
            'discovery_rate': discovery_rate,
            'interval_used': interval_used or self.default_interval
        })
        
        # 只保留最近10次
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        self.save_history()
        
        logger.info(f"📈 记录扫描: Signal={high_signal_count}/{total_scanned} ({discovery_rate:.1%})")
    
    def calculate_next_interval(self) -> tuple:
        """
        计算下一次扫描间隔
        
        Returns:
            (interval_seconds, reason, stats)
        """
        if len(self.history) < 3:
            return self.default_interval, "历史数据不足，使用默认间隔", self.get_stats()
        
        # 计算最近5次的平均发现率
        recent_history = self.history[-5:]
        avg_rate = sum(h['discovery_rate'] for h in recent_history) / len(recent_history)
        
        current_interval = self.history[-1].get('interval_used', self.default_interval)
        
        # 根据发现率调整
        if avg_rate > self.high_threshold:
            # 高发现率 - 延长间隔，充分深度学习
            new_interval = min(current_interval + self.adjustment_step, self.max_interval)
            reason = f"🎯 高发现率({avg_rate:.1%})→延长间隔，充分深度学习闭环"
            
        elif avg_rate < self.low_threshold:
            # 低发现率 - 缩短间隔，不错过内容
            new_interval = max(current_interval - self.adjustment_step, self.min_interval)
            reason = f"🔍 低发现率({avg_rate:.1%})→缩短间隔，积极发现内容"
            
        else:
            # 正常范围 - 保持当前
            new_interval = current_interval
            reason = f"✅ 发现率正常({avg_rate:.1%})→保持当前间隔"
        
        stats = self.get_stats()
        stats['next_interval'] = new_interval
        stats['reason'] = reason
        
        return new_interval, reason, stats
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        if not self.history:
            return {
                'status': 'no_data',
                'scans_count': 0,
                'current_interval': self.default_interval
            }
        
        total_high = sum(h['high_signal'] for h in self.history)
        total_scanned = sum(h['total'] for h in self.history)
        avg_rate = total_high / max(total_scanned, 1)
        current_interval = self.history[-1].get('interval_used', self.default_interval)
        
        return {
            'status': 'active',
            'scans_count': len(self.history),
            'total_high_signal': total_high,
            'total_scanned': total_scanned,
            'avg_discovery_rate': avg_rate,
            'current_interval': current_interval,
            'interval_range': f"{self.min_interval}-{self.max_interval}秒"
        }


# 超进化引擎配置
CONFIG = {
    "version": "4.6.0",
    "codename": "HyperEngine-AdaptiveFreq",
    "adaptive_mode": True,
    "playwright_fixed": True,
    "chromium_path": "/usr/bin/chromium",
    "signal_threshold": 7,
    
    # 自适应频率配置
    "adaptive_freq": {
        "enabled": True,
        "min_interval": 300,      # 5分钟
        "max_interval": 1800,     # 30分钟
        "default_interval": 600,  # 10分钟
        "adjustment_step": 120,   # 2分钟
    }
}


async def adaptive_scan_cycle(freq_manager: AdaptiveFrequencyManager):
    """
    自适应扫描周期
    
    流程:
    1. 执行扫描
    2. 记录Signal发现数
    3. 计算下一次间隔
    4. 等待指定时间
    5. 重复
    """
    cycle = 0
    
    while True:
        cycle += 1
        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 自适应扫描周期 #{cycle}")
        logger.info(f"{'='*60}")
        
        # 1. 执行扫描 (模拟)
        logger.info("🔍 执行扫描...")
        
        # 这里集成实际的扫描逻辑
        # 模拟: 随机生成Signal发现数
        import random
        high_signal = random.randint(0, 8)  # 模拟0-8条高Signal
        total = 30  # 假设扫描30条
        
        # 2. 记录结果
        current_interval = freq_manager.history[-1]['interval_used'] if freq_manager.history else CONFIG['adaptive_freq']['default_interval']
        freq_manager.record_scan(high_signal, total, current_interval)
        
        # 3. 计算下一次间隔
        next_interval, reason, stats = freq_manager.calculate_next_interval()
        
        logger.info(f"📊 统计: {stats['total_high_signal']}/{stats['total_scanned']} 高Signal")
        logger.info(f"📈 平均发现率: {stats['avg_discovery_rate']:.1%}")
        logger.info(f"⏱️  当前间隔: {current_interval}秒 ({current_interval//60}分钟)")
        logger.info(f"🎯 调整: {reason}")
        logger.info(f"⏭️  下次间隔: {next_interval}秒 ({next_interval//60}分钟)")
        
        # 4. 等待
        logger.info(f"💤 等待 {next_interval}秒后继续...")
        await asyncio.sleep(next_interval)


async def main():
    """主函数"""
    logger.info("="*60)
    logger.info("🚀 超进化引擎 v4.6.0 - 自适应频率版")
    logger.info("="*60)
    logger.info(f"⏱️  频率范围: 5-30分钟 (根据Signal发现率自动调整)")
    logger.info(f"🎯 高发现率(>20%): 延长间隔，充分深度学习")
    logger.info(f"🔍 低发现率(<5%): 缩短间隔，积极发现内容")
    logger.info("="*60)
    
    # 初始化自适应频率管理器
    freq_manager = AdaptiveFrequencyManager()
    
    # 启动自适应扫描
    try:
        await adaptive_scan_cycle(freq_manager)
    except KeyboardInterrupt:
        logger.info("\n🛑 收到停止信号，保存状态...")
        freq_manager.save_history()
        logger.info("✅ 已保存状态，退出")


if __name__ == "__main__":
    asyncio.run(main())
