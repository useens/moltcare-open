#!/usr/bin/env python3
"""
Command Center - Feishu Sync Service
指挥中心飞书同步服务

功能:
- 接收所有nanobot节点消息
- 分级过滤 (CRITICAL/HIGH/NORMAL/LOW)
- 同步到飞书机器人
"""

import json
import sys
import time
import requests
from datetime import datetime
from pathlib import Path
from threading import Thread, Lock

# 飞书配置
FEISHU_APP_ID = "cli_a90df96070b89cc6"
FEISHU_APP_SECRET = "nGjBQGcB2cF0ZSiEAUQXwc3LgUfE2vnk"
FEISHU_TARGET = "ou_dc4db246fa540096f42caefbd2112ed3"  # 当前用户

# 消息级别
LEVELS = {
    "CRITICAL": {"emoji": "🚨", "sync": "immediate", "color": "red"},
    "HIGH": {"emoji": "⚠️", "sync": "immediate", "color": "orange"},
    "NORMAL": {"emoji": "ℹ️", "sync": "batch", "color": "blue"},
    "LOW": {"emoji": "💬", "sync": "none", "color": "grey"}
}

class FeishuSyncService:
    """飞书同步服务"""
    
    def __init__(self):
        self.batch_queue = []
        self.lock = Lock()
        self.last_batch_time = time.time()
        self.batch_interval = 300  # 5分钟批量发送
        self.log_file = Path("/root/.openclaw/workspace/logs/feishu-sync.log")
        self.log_file.parent.mkdir(exist_ok=True)
        
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")
    
    def send_to_feishu(self, content, msg_type="text"):
        """发送消息到飞书 (通过openclaw message命令)"""
        import subprocess
        
        try:
            # 使用openclaw命令发送
            cmd = [
                "openclaw", "message", "send",
                "--channel", "feishu",
                "--target", FEISHU_TARGET,
                "--message", content
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return result.returncode == 0
        except Exception as e:
            self.log(f"发送失败: {e}")
            return False
    
    def format_message(self, level, source, message, details=None):
        """格式化消息"""
        config = LEVELS.get(level, LEVELS["NORMAL"])
        emoji = config["emoji"]
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        formatted = f"{emoji} **[{level}]** {source}\n"
        formatted += f"⏰ {timestamp}\n"
        formatted += f"📝 {message}\n"
        
        if details:
            formatted += f"📋 {json.dumps(details, ensure_ascii=False)[:200]}"
        
        return formatted
    
    def sync_message(self, level, source, message, details=None):
        """同步单条消息"""
        config = LEVELS.get(level, LEVELS["NORMAL"])
        
        # 根据级别处理
        if config["sync"] == "immediate":
            # 立即同步
            content = self.format_message(level, source, message, details)
            success = self.send_to_feishu(content)
            if success:
                self.log(f"✅ 已同步 [{level}] {source}: {message[:50]}")
            else:
                self.log(f"❌ 同步失败 [{level}] {source}")
                
        elif config["sync"] == "batch":
            # 加入批量队列
            with self.lock:
                self.batch_queue.append({
                    "level": level,
                    "source": source,
                    "message": message,
                    "details": details,
                    "time": time.time()
                })
            self.log(f"📦 加入队列 [{level}] {source}: {message[:50]}")
            
            # 检查是否需要批量发送
            self._check_batch_send()
            
        else:
            # LOW级别不同步，只记录
            self.log(f"💾 本地记录 [{level}] {source}: {message[:50]}")
    
    def _check_batch_send(self):
        """检查是否需要批量发送"""
        with self.lock:
            if len(self.batch_queue) >= 10 or (time.time() - self.last_batch_time) > self.batch_interval:
                if self.batch_queue:
                    self._send_batch()
    
    def _send_batch(self):
        """发送批量消息"""
        if not self.batch_queue:
            return
        
        # 构建汇总消息
        summary = f"📊 **消息汇总** ({len(self.batch_queue)} 条)\n\n"
        
        for item in self.batch_queue[:5]:
            config = LEVELS.get(item["level"], LEVELS["NORMAL"])
            emoji = config["emoji"]
            summary += f"{emoji} [{item['level']}] {item['source']}: {item['message'][:40]}...\n"
        
        if len(self.batch_queue) > 5:
            summary += f"\n... 还有 {len(self.batch_queue) - 5} 条消息"
        
        # 发送
        success = self.send_to_feishu(summary)
        if success:
            self.log(f"✅ 批量发送完成 ({len(self.batch_queue)} 条)")
            self.batch_queue = []
            self.last_batch_time = time.time()
        else:
            self.log(f"❌ 批量发送失败")
    
    # 便捷方法
    def critical(self, source, message, details=None):
        self.sync_message("CRITICAL", source, message, details)
    
    def high(self, source, message, details=None):
        self.sync_message("HIGH", source, message, details)
    
    def normal(self, source, message, details=None):
        self.sync_message("NORMAL", source, message, details)
    
    def low(self, source, message, details=None):
        self.sync_message("LOW", source, message, details)
    
    def node_online(self, node_id):
        self.high(f"node.{node_id}", f"节点 {node_id} 已上线", {"status": "online"})
    
    def node_offline(self, node_id, error=None):
        self.critical(f"node.{node_id}", f"节点 {node_id} 离线", {"error": error})
    
    def task_completed(self, node_id, task_id, duration=None):
        self.high(f"task.{task_id}", f"任务完成", {
            "node": node_id,
            "duration": duration
        })
    
    def task_failed(self, node_id, task_id, error):
        self.critical(f"task.{task_id}", f"任务失败", {
            "node": node_id,
            "error": error
        })

# 全局实例
_sync_service = None

def get_sync_service():
    global _sync_service
    if _sync_service is None:
        _sync_service = FeishuSyncService()
    return _sync_service

def main():
    service = get_sync_service()
    
    if len(sys.argv) < 2:
        print("Feishu Sync Service")
        print("")
        print("Usage: feishu-sync.py <command> [options]")
        print("")
        print("Commands:")
        print("  critical <source> <message>   CRITICAL级别")
        print("  high <source> <message>       HIGH级别")
        print("  normal <source> <message>     NORMAL级别")
        print("  low <source> <message>        LOW级别")
        print("  test                          测试所有级别")
        print("  batch                         强制批量发送")
        print("")
        print("Examples:")
        print("  feishu-sync.py critical node.NB01 '节点离线'")
        print("  feishu-sync.py high task.123 '任务完成'")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "critical":
        if len(sys.argv) < 4:
            print("Usage: critical <source> <message>")
            sys.exit(1)
        service.critical(sys.argv[2], sys.argv[3])
    
    elif command == "high":
        if len(sys.argv) < 4:
            print("Usage: high <source> <message>")
            sys.exit(1)
        service.high(sys.argv[2], sys.argv[3])
    
    elif command == "normal":
        if len(sys.argv) < 4:
            print("Usage: normal <source> <message>")
            sys.exit(1)
        service.normal(sys.argv[2], sys.argv[3])
    
    elif command == "low":
        if len(sys.argv) < 4:
            print("Usage: low <source> <message>")
            sys.exit(1)
        service.low(sys.argv[2], sys.argv[3])
    
    elif command == "test":
        print("Testing all message levels...")
        service.critical("test", "测试CRITICAL消息", {"test": True})
        time.sleep(1)
        service.high("test", "测试HIGH消息")
        time.sleep(1)
        service.normal("test", "测试NORMAL消息")
        time.sleep(1)
        service.low("test", "测试LOW消息")
        time.sleep(1)
        service._send_batch()
        print("Test completed")
    
    elif command == "batch":
        service._send_batch()
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
