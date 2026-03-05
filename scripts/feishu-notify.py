#!/usr/bin/env python3
"""
OpenClaw Command Center - Feishu Notifier
飞书通知器 - 实际发送消息到飞书

功能:
- 发送文本消息到飞书
- 发送卡片消息
- 批量消息汇总
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

# 飞书配置 - 从主配置读取
FEISHU_CHAT_ID = "ou_dc4db246fa540096f42caefbd2112ed3"  # 当前用户

def send_text_message(content, silent=False):
    """发送文本消息到飞书"""
    # 使用openclaw message命令发送
    import subprocess
    
    cmd = ["openclaw", "message", "send", "--channel", "feishu", "--target", FEISHU_CHAT_ID, "--message", content]
    if silent:
        cmd.append("--silent")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except Exception as e:
        print(f"发送失败: {e}")
        return False

def send_card_message(title, content, level="normal"):
    """发送卡片消息"""
    # 根据级别选择颜色
    colors = {
        "critical": "red",
        "high": "orange",
        "normal": "blue",
        "low": "grey"
    }
    color = colors.get(level, "blue")
    
    # 构建卡片内容
    msg = f"**[{level.upper()}] {title}**\n\n{content}\n\n⏰ {datetime.now().strftime('%H:%M:%S')}"
    
    return send_text_message(msg)

def notify_node_status(node_id, status, details=""):
    """通知节点状态变更"""
    if status == "offline":
        title = f"🚨 节点 {node_id} 离线"
        level = "critical"
    elif status == "online":
        title = f"✅ 节点 {node_id} 恢复在线"
        level = "high"
    else:
        title = f"ℹ️ 节点 {node_id} 状态: {status}"
        level = "normal"
    
    content = f"节点: {node_id}\n状态: {status}"
    if details:
        content += f"\n详情: {details}"
    
    return send_card_message(title, content, level)

def notify_task_completed(node_id, task_id, duration=None):
    """通知任务完成"""
    title = f"✅ 任务完成"
    content = f"节点: {node_id}\n任务: {task_id}"
    if duration:
        content += f"\n耗时: {duration}秒"
    
    return send_card_message(title, content, "high")

def notify_task_failed(node_id, task_id, error):
    """通知任务失败"""
    title = f"❌ 任务失败"
    content = f"节点: {node_id}\n任务: {task_id}\n错误: {error[:200]}"
    
    return send_card_message(title, content, "critical")

def notify_batch_summary(messages):
    """发送批量汇总消息"""
    title = f"📊 消息汇总 ({len(messages)} 条)"
    
    content = "\n".join([
        f"• [{m.get('level','?')}] {m.get('source','?')}: {m.get('message','')[:40]}..."
        for m in messages[:5]
    ])
    
    if len(messages) > 5:
        content += f"\n\n... 还有 {len(messages) - 5} 条消息"
    
    return send_card_message(title, content, "normal")

def send_heartbeat():
    """发送心跳消息"""
    content = f"💓 Command Center Heartbeat\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    return send_text_message(content, silent=True)

def main():
    if len(sys.argv) < 2:
        print("Usage: feishu-notify.py <command> [options]")
        print("")
        print("Commands:")
        print("  text <message>              发送文本消息")
        print("  node-status <node> <status>  节点状态通知")
        print("  task-done <node> <task>      任务完成通知")
        print("  task-fail <node> <task> <err> 任务失败通知")
        print("  heartbeat                    发送心跳")
        print("  test                         测试消息")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "text":
        if len(sys.argv) < 3:
            print("Usage: text <message>")
            sys.exit(1)
        message = sys.argv[2]
        if send_text_message(message):
            print("✅ 消息已发送")
        else:
            print("❌ 发送失败")
    
    elif command == "node-status":
        if len(sys.argv) < 4:
            print("Usage: node-status <node_id> <status> [details]")
            sys.exit(1)
        node_id = sys.argv[2]
        status = sys.argv[3]
        details = sys.argv[4] if len(sys.argv) > 4 else ""
        if notify_node_status(node_id, status, details):
            print("✅ 通知已发送")
        else:
            print("❌ 发送失败")
    
    elif command == "task-done":
        if len(sys.argv) < 4:
            print("Usage: task-done <node_id> <task_id> [duration]")
            sys.exit(1)
        node_id = sys.argv[2]
        task_id = sys.argv[3]
        duration = sys.argv[4] if len(sys.argv) > 4 else None
        if notify_task_completed(node_id, task_id, duration):
            print("✅ 通知已发送")
        else:
            print("❌ 发送失败")
    
    elif command == "task-fail":
        if len(sys.argv) < 5:
            print("Usage: task-fail <node_id> <task_id> <error>")
            sys.exit(1)
        node_id = sys.argv[2]
        task_id = sys.argv[3]
        error = sys.argv[4]
        if notify_task_failed(node_id, task_id, error):
            print("✅ 通知已发送")
        else:
            print("❌ 发送失败")
    
    elif command == "heartbeat":
        if send_heartbeat():
            print("✅ 心跳已发送")
        else:
            print("❌ 发送失败")
    
    elif command == "test":
        print("Testing Feishu notifications...")
        send_text_message("🧪 **Command Center Test**\n\n飞书通知测试成功！\n⏰ " + datetime.now().strftime('%H:%M:%S'))
        print("Test message sent")
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
