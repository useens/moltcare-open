#!/usr/bin/env python3
"""
Token消耗监控脚本
实时记录和分析token消耗
"""

import json
import os
from datetime import datetime
from pathlib import Path

METRICS_FILE = Path("memory/token-metrics.json")

def load_metrics():
    if METRICS_FILE.exists():
        with open(METRICS_FILE, 'r') as f:
            return json.load(f)
    return {
        "daily": {"date": datetime.now().strftime("%Y-%m-%d"), "total_tokens": 0, "reply_count": 0, "tool_calls": 0, "avg_reply_tokens": 0},
        "session": {"start_time": datetime.now().strftime("%H:%M:%S"), "current_tokens": 0, "tool_calls": 0},
        "alerts": []
    }

def save_metrics(metrics):
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_FILE, 'w') as f:
        json.dump(metrics, f, indent=2)

def record_reply(tokens, tool_count):
    metrics = load_metrics()
    
    # 更新会话统计
    metrics["session"]["current_tokens"] += tokens
    metrics["session"]["tool_calls"] += tool_count
    
    # 更新日统计
    metrics["daily"]["total_tokens"] += tokens
    metrics["daily"]["reply_count"] += 1
    metrics["daily"]["tool_calls"] += tool_count
    
    # 计算平均
    if metrics["daily"]["reply_count"] > 0:
        metrics["daily"]["avg_reply_tokens"] = metrics["daily"]["total_tokens"] // metrics["daily"]["reply_count"]
    
    # 检查阈值
    alerts = []
    if tokens > 1500:
        alerts.append(f"回复过长: {tokens} tokens (>1500)")
    if tool_count > 5:
        alerts.append(f"工具过多: {tool_count} 个(>5)")
    if metrics["daily"]["total_tokens"] > 50000:
        alerts.append(f"日耗过高: {metrics['daily']['total_tokens']} tokens (>50000)")
    
    if alerts:
        metrics["alerts"].extend(alerts)
        for alert in alerts:
            print(f"⚠️ {alert}")
    
    save_metrics(metrics)
    
    return len(alerts) == 0

def get_status():
    metrics = load_metrics()
    return {
        "daily_total": metrics["daily"]["total_tokens"],
        "daily_avg": metrics["daily"]["avg_reply_tokens"],
        "reply_count": metrics["daily"]["reply_count"],
        "session_tokens": metrics["session"]["current_tokens"],
        "alerts": metrics["alerts"]
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        status = get_status()
        print(f"📊 Token消耗状态")
        print(f"今日累计: {status['daily_total']} tokens")
        print(f"平均回复: {status['daily_avg']} tokens")
        print(f"回复次数: {status['reply_count']}")
        if status['alerts']:
            print(f"⚠️ 警报: {len(status['alerts'])} 条")
