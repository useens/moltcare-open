#!/usr/bin/env python3
"""
超进化引擎自适应频率方案 v1.0
根据Signal发现率动态调整扫描间隔
"""

class AdaptiveFrequencyManager:
    """
    自适应频率管理器
    
    核心逻辑:
    - Signal发现率高 → 延长间隔 (减少扫描频率)
    - Signal发现率低 → 缩短间隔 (增加扫描频率)
    
    边界控制:
    - 最小间隔: 5分钟 (最频繁)
    - 最大间隔: 30分钟 (最稀疏)
    - 默认间隔: 10分钟
    """
    
    def __init__(self):
        self.min_interval = 300      # 5分钟 (最短)
        self.max_interval = 1800     # 30分钟 (最长)
        self.default_interval = 600  # 10分钟 (默认)
        
        # 历史数据 (保存最近10次扫描)
        self.history = []
        self.max_history = 10
        
    def record_scan(self, high_signal_count: int, total_scanned: int):
        """记录一次扫描结果"""
        import time
        
        discovery_rate = high_signal_count / max(total_scanned, 1)
        
        self.history.append({
            'timestamp': time.time(),
            'high_signal': high_signal_count,
            'total': total_scanned,
            'discovery_rate': discovery_rate
        })
        
        # 只保留最近10次
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def calculate_next_interval(self) -> int:
        """
        计算下一次扫描间隔
        
        算法:
        1. 计算平均Signal发现率
        2. 发现率 > 20% → 延长间隔 (+2分钟)
        3. 发现率 < 5%  → 缩短间隔 (-2分钟)
        4. 5%-20%之间   → 保持当前间隔
        
        Returns:
            下一次扫描间隔(秒)
        """
        if len(self.history) < 3:
            return self.default_interval
        
        # 计算平均发现率
        avg_rate = sum(h['discovery_rate'] for h in self.history) / len(self.history)
        
        current_interval = self.history[-1].get('interval', self.default_interval) if self.history else self.default_interval
        
        # 根据发现率调整
        if avg_rate > 0.20:  # 发现率 > 20%
            # 高发现率 - 延长间隔
            new_interval = min(current_interval + 120, self.max_interval)
            reason = f"高发现率({avg_rate:.1%})，延长间隔"
            
        elif avg_rate < 0.05:  # 发现率 < 5%
            # 低发现率 - 缩短间隔
            new_interval = max(current_interval - 120, self.min_interval)
            reason = f"低发现率({avg_rate:.1%})，缩短间隔"
            
        else:
            # 正常范围 - 保持当前
            new_interval = current_interval
            reason = f"发现率正常({avg_rate:.1%})，保持间隔"
        
        # 记录这次使用的间隔
        if self.history:
            self.history[-1]['interval'] = new_interval
        
        return new_interval, reason
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        if not self.history:
            return {'status': 'no_data'}
        
        total_high = sum(h['high_signal'] for h in self.history)
        total_scanned = sum(h['total'] for h in self.history)
        avg_rate = total_high / max(total_scanned, 1)
        
        return {
            'scans_count': len(self.history),
            'total_high_signal': total_high,
            'total_scanned': total_scanned,
            'avg_discovery_rate': f"{avg_rate:.1%}",
            'current_interval': self.history[-1].get('interval', self.default_interval) if self.history else self.default_interval
        }


# 配置示例
ADAPTIVE_CONFIG = {
    "enabled": True,
    "min_interval": 300,      # 5分钟
    "max_interval": 1800,     # 30分钟
    "default_interval": 600,  # 10分钟
    
    # 调整阈值
    "high_rate_threshold": 0.20,  # >20% 延长间隔
    "low_rate_threshold": 0.05,   # <5% 缩短间隔
    
    # 调整步长
    "adjustment_step": 120,   # 每次调整2分钟
    
    # 历史记录数
    "history_size": 10
}


"""
使用示例:

# 初始化
freq_manager = AdaptiveFrequencyManager()

# 每次扫描后记录
freq_manager.record_scan(
    high_signal_count=5,  # 发现5条高Signal
    total_scanned=30      # 总共扫描30条
)

# 获取下一次间隔
next_interval, reason = freq_manager.calculate_next_interval()
print(f"下次扫描间隔: {next_interval}秒 ({reason})")

# 获取统计
stats = freq_manager.get_stats()
print(f"平均发现率: {stats['avg_discovery_rate']}")
"""
