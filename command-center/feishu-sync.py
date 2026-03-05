#!/usr/bin/env python3
"""
Command Center - Feishu Sync
指挥中心飞书同步模块

功能:
- 将节点消息同步到飞书
- 支持4级消息分级
- 自动汇总报告
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

# 飞书配置
FEISHU_USER = "ou_dc4db246fa540096f42caefbd2112ed3"
LOG_FILE = Path("/root/.openclaw/workspace/command-center/sync.log")

class FeishuSync:
    def __init__(self):
        self.log_file = LOG_FILE
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def send_card(self, title, content, level="normal"):
        """发送卡片消息到飞书"""
        # 构建消息
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # 根据级别添加图标
        icons = {
            "critical": "🚨",
            "high": "🔔",
            "normal": "ℹ️",
            "low": "📝"
        }
        icon = icons.get(level, "ℹ️")
        
        # 格式化消息
        message = f"{icon} **[{level.upper()}] {title}**\n\n{content}\n\n⏰ {timestamp}"
        
        # 记录到日志
        self._log(level, title, content)
        
        # 尝试使用openclaw message发送
        try:
            import subprocess
            cmd = [
                "openclaw", "message", "send",
                "--channel", "feishu",
                "--target", FEISHU_USER,
                "--message", message
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        except Exception as e:
            print(f"发送失败: {e}")
            return False
    
    def _log(self, level, title, content):
        """记录到本地日志"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "title": title,
            "content": content[:200]
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    def node_online(self, node_id):
        """节点上线通知"""
        return self.send_card(f"节点 {node_id} 已上线", f"Nanobot {node_id} 已连接到指挥中心", "high")
    
    def node_offline(self, node_id, reason=""):
        """节点离线通知"""
        content = f"Nanobot {node_id} 失去连接"
        if reason:
            content += f"\n原因: {reason}"
        return self.send_card(f"🚨 节点 {node_id} 离线", content, "critical")
    
    def task_completed(self, node_id, task_summary=""):
        """任务完成通知"""
        content = f"节点 {node_id} 已完成任务"
        if task_summary:
            content += f"\n\n摘要: {task_summary[:100]}"
        return self.send_card(f"✅ 任务完成", content, "normal")
    
    def task_failed(self, node_id, error):
        """任务失败通知"""
        return self.send_card(
            f"❌ 任务失败",
            f"节点: {node_id}\n错误: {error[:200]}",
            "critical"
        )
    
    def broadcast_summary(self, results):
        """广播任务汇总"""
        success = sum(1 for r in results if r.get("success"))
        failed = len(results) - success
        
        content = f"成功: {success}/10\n失败: {failed}/10\n\n"
        for r in results:
            icon = "✅" if r.get("success") else "❌"
            content += f"{icon} {r['node']}\n"
        
        return self.send_card(f"📢 广播任务汇总", content, "high")
    
    def heartbeat(self):
        """心跳消息"""
        return self.send_card(
            "💓 指挥中心心跳",
            f"所有系统正常运行\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "low"
        )
    
    def show_logs(self, lines=20):
        """显示最近日志"""
        if not self.log_file.exists():
            print("暂无日志")
            return
        
        with open(self.log_file) as f:
            all_lines = f.readlines()
        
        print(f"=" * 60)
        print(f"最近 {min(lines, len(all_lines))} 条同步记录:")
        print(f"=" * 60)
        
        for line in all_lines[-lines:]:
            try:
                entry = json.loads(line.strip())
                ts = entry['timestamp'][11:19]
                level = entry['level'].upper()[:4]
                title = entry['title'][:40]
                print(f"{ts} [{level}] {title}")
            except:
                print(line.strip()[:60])
        
        print(f"=" * 60)

def main():
    sync = FeishuSync()
    
    if len(sys.argv) < 2:
        print("Command Center - Feishu Sync")
        print("")
        print("Usage: feishu-sync.py <command> [options]")
        print("")
        print("Commands:")
        print("  node-online <node_id>      节点上线通知")
        print("  node-offline <node_id>     节点离线通知")
        print("  task-done <node_id>         任务完成通知")
        print("  task-fail <node_id> <err>   任务失败通知")
        print("  heartbeat                   发送心跳")
        print("  logs [lines]                查看同步日志")
        print("  test                        测试消息")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "node-online":
        if len(sys.argv) < 3:
            print("Usage: node-online <node_id>")
            sys.exit(1)
        sync.node_online(sys.argv[2])
    
    elif command == "node-offline":
        if len(sys.argv) < 3:
            print("Usage: node-offline <node_id> [reason]")
            sys.exit(1)
        reason = sys.argv[3] if len(sys.argv) > 3 else ""
        sync.node_offline(sys.argv[2], reason)
    
    elif command == "task-done":
        if len(sys.argv) < 3:
            print("Usage: task-done <node_id> [summary]")
            sys.exit(1)
        summary = sys.argv[3] if len(sys.argv) > 3 else ""
        sync.task_completed(sys.argv[2], summary)
    
    elif command == "task-fail":
        if len(sys.argv) < 4:
            print("Usage: task-fail <node_id> <error>")
            sys.exit(1)
        sync.task_failed(sys.argv[2], sys.argv[3])
    
    elif command == "heartbeat":
        sync.heartbeat()
    
    elif command == "logs":
        lines = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        sync.show_logs(lines)
    
    elif command == "test":
        print("发送测试消息...")
        sync.send_card("测试消息", "这是从指挥中心发送的测试消息\n如果收到说明飞书同步正常！", "high")
        print("测试消息已发送")
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
