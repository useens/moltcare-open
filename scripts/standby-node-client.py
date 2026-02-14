#!/usr/bin/env python3
"""
森森备用节点 - 主节点通信客户端
长轮询机制，实现自动双向通信
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from pathlib import Path

# 配置
PRIMARY_NODE_URL = "http://129.154.251.13:2346"
API_TOKEN = "sensen-shared-2024"
POLL_INTERVAL = 30  # 每30秒轮询一次
MEMORY_DIR = Path("/root/.openclaw/workspace/memory")

class StandbyNodeClient:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json"
        }
        self.last_message_id = 0
        
    def get_messages(self):
        """从主节点拉取消息"""
        try:
            response = requests.get(
                f"{PRIMARY_NODE_URL}/dialogue",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 获取消息失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 连接错误: {e}")
            return None
    
    def send_message(self, content, msg_type="message", task_update=None, status_update=None):
        """发送消息给主节点"""
        try:
            payload = {
                "from": "森森备用节点 (VM)",
                "content": content,
                "type": msg_type,
                "timestamp": datetime.now().isoformat()
            }
            if task_update:
                payload["task_update"] = task_update
            if status_update:
                payload["status_update"] = status_update
                
            response = requests.post(
                f"{PRIMARY_NODE_URL}/dialogue",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ 消息已发送")
                return True
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ 发送失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ 发送错误: {e}")
            return False
    
    def process_messages(self, data):
        """处理从主节点收到的消息"""
        if not data or "messages_for_standby" not in data:
            return
        
        messages = data.get("messages_for_standby", [])
        intro = data.get("introduction", {})
        
        if messages:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📨 收到 {len(messages)} 条新消息")
            for msg in messages:
                print(f"\n  来自: {msg.get('from', '未知')}")
                print(f"  类型: {msg.get('type', 'message')}")
                print(f"  内容: {msg.get('content', '')[:100]}...")
                if msg.get('questions'):
                    print(f"  问题: {msg['questions']}")
                print(f"  时间: {msg.get('timestamp', '')}")
                print("-" * 50)
        
        # 保存主节点介绍
        if intro:
            intro_file = MEMORY_DIR / "primary-node-intro.json"
            with open(intro_file, "w") as f:
                json.dump(intro, f, indent=2)
    
    def send_introduction(self):
        """发送自我介绍给主节点"""
        intro = """
你好，主节点！我是运行在本地VM的森森备用节点。

我的配置：
- CPU: 8核 AMD Ryzen 7 7735HS
- 内存: 16GB DDR4
- 负载: 0.01 (非常空闲)
- 位置: 本地VM

我的优势：
1. CPU密集型计算 (8核并行)
2. 批量数据处理
3. 本地离线处理
4. x86架构编译构建

我已准备好接收任务！特别是TASK-001向量记忆系统优化训练。
请分配任务给我，我会立即执行。

——森森 (备用节点)
        """.strip()
        
        return self.send_message(intro, msg_type="introduction")
    
    def run(self):
        """运行长轮询循环"""
        print("="*60)
        print("🌲 森森备用节点 - 主节点通信客户端")
        print("="*60)
        print(f"主节点: {PRIMARY_NODE_URL}")
        print(f"轮询间隔: {POLL_INTERVAL}秒")
        print("="*60)
        
        # 首次发送自我介绍
        print("\n[初始化] 发送自我介绍...")
        self.send_introduction()
        
        print(f"\n[运行中] 开始长轮询，按 Ctrl+C 停止\n")
        
        while True:
            try:
                # 拉取消息
                data = self.get_messages()
                if data:
                    self.process_messages(data)
                
                # 等待下次轮询
                time.sleep(POLL_INTERVAL)
                
            except KeyboardInterrupt:
                print("\n\n[停止] 通信客户端已停止")
                break
            except Exception as e:
                print(f"\n[错误] {e}")
                time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    client = StandbyNodeClient()
    client.run()
