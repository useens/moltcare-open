#!/usr/bin/env python3
"""
学习债务自动处理规则 - 自主模式配置
触发条件：债务积压时自动执行
"""

DEBT_PROCESSING_RULES = {
    # 积压阈值
    "backlog_threshold": 50,
    
    # 当债务超过阈值时的自动行动
    "auto_actions": {
        "pause_scanning": True,  # 停止自动扫描
        "bulk_downgrade": {      # 批量降级低Signal债务
            "enabled": True,
            "downgrade_signals": [7, 8],  # Signal 7-8降级
            "mark_as": "deferred"  # 标记为延期处理
        },
        "focus_high_signal": [9, 10],  # 专注处理高Signal
    },
    
    # 每日处理配额
    "daily_quota": {
        "signal_10": 2,  # 每天最多2条Signal 10
        "signal_9": 3,   # 每天最多3条Signal 9
        "max_total": 5   # 每天最多5条
    },
    
    # 优先级主题（与当前项目相关）
    "priority_topics": [
        "multi-agent",      # Multi-Agent架构
        "mcp",             # MCP协议
        "memory",          # 记忆系统
        "architecture",    # 系统架构
        "security"         # 安全
    ]
}
