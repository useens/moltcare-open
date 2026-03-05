#!/usr/bin/env python3
"""
OpenClaw Command Center - Relay Hub
中继中心 - 飞书消息同步

功能:
- 接收各节点消息
- 消息分级过滤
- 飞书机器人推送
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from enum import Enum

# 飞书配置
FEISHU_CONFIG = {
    "app_id": "cli_a90df96070b89cc6",
    "app_secret": "nGjBQGcB2cF0ZSiEAUQXwc3LgUfE2vnk"
}

# 消息级别
class MessageLevel(Enum):
    CRITICAL = "critical"  # 节点故障/任务失败 - 立即推送
    HIGH = "high"          # 任务完成/重要事件 - 实时推送
    NORMAL = "normal"      # 常规状态更新 - 批量汇总(5分钟)
    LOW = "low"            # 调试信息 - 不同步

class RelayHub:
    def __init__(self, log_file=None):
        self.log_file = log_file or Path("/root/.openclaw/workspace/logs/relay-hub.log")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.message_queue = []
    
    def log(self, level, source, message, details=None):
        """记录消息"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level.value if isinstance(level, MessageLevel) else level,
            "source": source,
            "message": message,
            "details": details or {}
        }
        
        # 写入日志
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        # 根据级别处理
        level_val = level.value if isinstance(level, MessageLevel) else level
        
        if level_val == MessageLevel.CRITICAL.value:
            self._send_immediate(entry)
        elif level_val == MessageLevel.HIGH.value:
            self._send_immediate(entry)
        elif level_val == MessageLevel.NORMAL.value:
            self.message_queue.append(entry)
            self._batch_send()
        # LOW级别不同步
        
        return entry
    
    def _send_immediate(self, entry):
        """立即发送到飞书"""
        # 这里会调用飞书API发送消息
        # 实际实现需要调用feishu工具
        print(f"[SYNC→Feishu] [{entry['level'].upper()}] {entry['source']}: {entry['message']}")
    
    def _batch_send(self):
        """批量发送（每5分钟或队列满10条）"""
        if len(self.message_queue) >= 10:
            self._flush_queue()
    
    def _flush_queue(self):
        """清空队列并发送"""
        if not self.message_queue:
            return
        
        # 汇总消息
        summary = f"收到 {len(self.message_queue)} 条消息:\n"
        for entry in self.message_queue[:5]:
            summary += f"  - [{entry['level']}] {entry['source']}: {entry['message'][:30]}...\n"
        
        if len(self.message_queue) > 5:
            summary += f"  ... 还有 {len(self.message_queue) - 5} 条"
        
        print(f"[BATCH SYNC→Feishu] {summary}")
        self.message_queue = []
    
    def node_status_change(self, node_id, old_status, new_status):
        """节点状态变更"""
        if new_status == "offline":
            self.log(
                MessageLevel.CRITICAL,
                f"node.{node_id}",
                f"节点 {node_id} 离线",
                {"old_status": old_status, "new_status": new_status}
            )
        elif new_status == "online" and old_status == "offline":
            self.log(
                MessageLevel.HIGH,
                f"node.{node_id}",
                f"节点 {node_id} 恢复在线",
                {"old_status": old_status, "new_status": new_status}
            )
    
    def task_completed(self, node_id, task_id, duration_sec):
        """任务完成"""
        self.log(
            MessageLevel.HIGH,
            f"task.{task_id}",
            f"任务完成 (节点: {node_id}, 耗时: {duration_sec}s)",
            {"node": node_id, "duration": duration_sec}
        )
    
    def task_failed(self, node_id, task_id, error):
        """任务失败"""
        self.log(
            MessageLevel.CRITICAL,
            f"task.{task_id}",
            f"任务失败 (节点: {node_id}): {error}",
            {"node": node_id, "error": error}
        )
    
    def system_alert(self, alert_type, message):
        """系统告警"""
        self.log(
            MessageLevel.CRITICAL,
            "system",
            f"[{alert_type}] {message}",
            {"alert_type": alert_type}
        )
    
    def show_logs(self, lines=20):
        """显示最近的日志"""
        if not self.log_file.exists():
            print("No logs found")
            return
        
        with open(self.log_file) as f:
            all_lines = f.readlines()
        
        print(f"=" * 60)
        print(f"最近 {min(lines, len(all_lines))} 条日志:")
        print(f"=" * 60)
        
        for line in all_lines[-lines:]:
            try:
                entry = json.loads(line.strip())
                ts = entry['timestamp'][:19]
                level = entry['level'].upper()[:4]
                source = entry['source']
                msg = entry['message'][:50]
                print(f"{ts} [{level}] {source}: {msg}")
            except:
                print(line.strip())
        
        print(f"=" * 60)

# 全局实例
_hub = None

def get_hub():
    global _hub
    if _hub is None:
        _hub = RelayHub()
    return _hub

def main():
    hub = get_hub()
    
    if len(sys.argv) < 2:
        print("Usage: cc-relay-hub.py <command> [options]")
        print("")
        print("Commands:")
        print("  log <level> <source> <message>  记录消息")
        print("  logs [lines]                        显示日志")
        print("  test                                测试消息同步")
        print("")
        print("Levels: critical, high, normal, low")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "log":
        if len(sys.argv) < 5:
            print("Usage: log <level> <source> <message>")
            sys.exit(1)
        level = MessageLevel(sys.argv[2])
        source = sys.argv[3]
        message = sys.argv[4]
        hub.log(level, source, message)
    
    elif command == "logs":
        lines = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        hub.show_logs(lines)
    
    elif command == "test":
        print("Testing message relay...")
        hub.log(MessageLevel.CRITICAL, "test", "测试CRITICAL级别消息")
        hub.log(MessageLevel.HIGH, "test", "测试HIGH级别消息")
        hub.log(MessageLevel.NORMAL, "test", "测试NORMAL级别消息")
        hub.log(MessageLevel.LOW, "test", "测试LOW级别消息(不同步)")
        hub._flush_queue()
        print("Test completed")
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
