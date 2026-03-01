"""
Polymarket 每日报告
发送准确率统计和昨日活动总结
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from polymarket_monitor import PolymarketMonitor
from polymarket_feishu import init_notifier, send_accuracy
import sqlite3
from datetime import datetime, timedelta


def get_yesterday_activity(db_path: str) -> dict:
    """获取昨日活动统计"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # 昨日预警数
    cursor.execute('''
        SELECT COUNT(*) FROM events 
        WHERE date(detected_at) = ?
    ''', (yesterday,))
    alerts_yesterday = cursor.fetchone()[0]
    
    # 昨日解决数
    cursor.execute('''
        SELECT COUNT(*) FROM events 
        WHERE status = 'resolved' 
        AND date(detected_at) = ?
    ''', (yesterday,))
    resolved_yesterday = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "alerts": alerts_yesterday,
        "resolved": resolved_yesterday
    }


def main():
    monitor = PolymarketMonitor()
    
    # 初始化飞书通知
    init_notifier()
    
    # 获取统计数据
    stats = monitor.get_statistics()
    
    # 获取昨日活动
    yesterday = get_yesterday_activity(monitor.db_path)
    
    # 构建日报消息
    today = datetime.now().strftime("%Y年%m月%d日")
    
    message = f"""
📊 Polymarket 监测日报 - {today}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 昨日活动
  • 新预警事件: {yesterday['alerts']} 个
  • 事件解决: {yesterday['resolved']} 个

📊 累计统计
  • 总预警次数: {stats['total_alerts']}
  • 已解决预测: {stats['resolved_predictions']}
  • 正确预测: {stats['correct_predictions']}
  • 累计准确率: {stats['accuracy_rate']:.1f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
系统运行正常，持续监测中...
    """
    
    print(message)
    
    # 发送飞书通知
    send_accuracy(stats)


if __name__ == "__main__":
    main()
