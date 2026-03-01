#!/usr/bin/env python3
"""
Polymarket 自动汇报脚本
每30分钟检查并汇报新预警
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from polymarket_monitor import PolymarketMonitor
import requests
import json
from datetime import datetime

# 飞书用户ID
FEISHU_USER_ID = "ou_dc4db246fa540096f42caefbd2112ed3"


def send_feishu_message(content: str):
    """发送飞书消息 - 使用OpenClaw message工具"""
    # 写入临时文件，由外部脚本调用
    with open('/tmp/polymarket_alert.txt', 'w') as f:
        f.write(content)
    print(content)


def check_and_report():
    """检查并汇报"""
    monitor = PolymarketMonitor()
    
    # 执行扫描
    alerts = monitor.scan_once()
    stats = monitor.get_statistics()
    
    # 获取活跃预警
    active_alerts = monitor.get_active_alerts()
    
    # 构建报告
    now = datetime.now().strftime("%H:%M")
    
    if alerts:
        # 有新预警，发送详细报告
        message = f"""🚨 **Polymarket 概率飙升预警** ({now})

检测到 **{len(alerts)}** 个概率显著变化事件：
"""
        for i, alert in enumerate(alerts[:5], 1):
            direction = "📈 上涨" if alert.probability > alert.previous_probability else "📉 下跌"
            message += f"""
**{i}. {alert.title[:40]}...**
   {direction} {alert.change_percent:.1f}%
   概率: {alert.previous_probability:.1f}% → **{alert.probability:.1f}%**
   类别: {alert.category}
   交易量: ${alert.volume:,.0f}
"""
        
        message += f"""
📊 **累计统计**
   总预警: {stats['total_alerts']} | 已解决: {stats['resolved_predictions']} | 准确率: {stats['accuracy_rate']:.1f}%
"""
        send_feishu_message(message)
        return True
    
    elif len(active_alerts) > 0:
        # 没有新预警但有活跃预警，简要汇报
        print(f"[{now}] 无新预警，当前 {len(active_alerts)} 个活跃预警")
        return False
    
    else:
        # 首次运行，积累数据中
        print(f"[{now}] 系统运行正常，正在积累历史数据...")
        return False


if __name__ == "__main__":
    check_and_report()
