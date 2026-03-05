#!/usr/bin/env python3
"""
Nanobot Command Center - Bot Relay Controller
纳米机器人指挥中心 - 通过Bot Relay指挥10个节点

架构:
  Command Center (Port 18789)
    │
    ├── Bot Relay ──→ NB01-NB10 (Ports 18801-18810)
    │
    └── Feishu Sync ←── 重要消息回流
"""

import json
import sys
import time
import requests
from datetime import datetime
from pathlib import Path

# 10个Nanobot节点配置
NANOBOTS = [
    {"id": "NB01", "port": 18801, "token": "nb01-token-9dbb482bf86c92fa636195fff9302f3", "apikey": "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"},
    {"id": "NB02", "port": 18802, "token": "nb02-token-9dbb482bf86c92fa636195fff9302f3", "apikey": "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"},
    {"id": "NB03", "port": 18803, "token": "nb03-token-9dbb482bf86c92fa636195fff9302f3", "apikey": "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"},
    {"id": "NB04", "port": 18804, "token": "nb04-token-9dbb482bf86c92fa636195fff9302f3", "apikey": "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"},
    {"id": "NB05", "port": 18805, "token": "nb05-token-9dbb482bf86c92fa636195fff9302f3", "apikey": "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"},
    {"id": "NB06", "port": 18806, "token": "nb06-token-9dbb482bf86c92fa636195fff9302f3", "apikey": "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"},
    {"id": "NB07", "port": 18807, "token": "nb07-token-9dbb482bf86c92fa636195fff9302f3", "apikey": "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"},
    {"id": "NB08", "port": 18808, "token": "nb08-token-9dbb482bf86c92fa636195fff9302f3", "apikey": "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"},
    {"id": "NB09", "port": 18809, "token": "nb09-token-9dbb482bf86c92fa636195fff9302f3", "apikey": "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"},
    {"id": "NB10", "port": 18810, "token": "nb10-token-9dbb482bf86c92fa636195fff9302f3", "apikey": "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"},
]

CC_CONFIG = {
    "port": 18789,
    "token": "cc-token-9dbb482bf86c92fa636195fff9302f3"
}

class NanobotRelay:
    """Bot Relay控制器"""
    
    def __init__(self):
        self.host = "127.0.0.1"
        
    def get_node_url(self, port):
        return f"http://{self.host}:{port}"
    
    def check_node(self, node):
        """检查节点状态"""
        try:
            url = f"{self.get_node_url(node['port'])}/status"
            headers = {"Authorization": f"Bearer {node['token']}"}
            resp = requests.get(url, headers=headers, timeout=5)
            return resp.status_code == 200
        except:
            return False
    
    def send_to_node(self, node_id, message, model=None):
        """发送消息到指定节点"""
        node = next((n for n in NANOBOTS if n["id"] == node_id), None)
        if not node:
            return False, f"Node {node_id} not found"
        
        # 根据节点ID自动选择默认模型
        # NB01-NB05: Step 3.5 Flash
        # NB06-NB10: DeepSeek V3.2
        if model is None:
            node_num = int(node_id.replace("NB", ""))
            if node_num <= 5:
                model = "step"
            else:
                model = "ds"
        
        try:
            # 通过NVIDIA API直接调用（每个节点有自己的API Key）
            url = "https://integrate.api.nvidia.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {node['apikey']}",
                "Content-Type": "application/json"
            }
            
            model_map = {
                "glm": "z-ai/glm4.7",
                "kimi": "moonshotai/kimi-k2.5",
                "ds": "deepseek-ai/deepseek-v3.2",
                "step": "stepfun-ai/step-3.5-flash"
            }
            
            payload = {
                "model": model_map.get(model, "z-ai/glm4.7"),
                "messages": [{"role": "user", "content": message}],
                "max_tokens": 500
            }
            
            resp = requests.post(url, headers=headers, json=payload, timeout=45)
            
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return True, content
            else:
                return False, f"HTTP {resp.status_code}"
        except Exception as e:
            return False, str(e)
    
    def broadcast(self, message, model="glm"):
        """广播到所有节点"""
        results = {}
        for node in NANOBOTS:
            success, result = self.send_to_node(node["id"], message, model)
            results[node["id"]] = {"success": success, "result": result}
        return results
    
    def status_all(self):
        """检查所有节点状态"""
        print("=" * 60)
        print(f"🤖 Nanobot Command Center - 节点状态检查")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        online_count = 0
        for node in NANOBOTS:
            is_online = self.check_node(node)
            status = "✅ 在线" if is_online else "❌ 离线"
            print(f"  {node['id']} (Port {node['port']}): {status}")
            if is_online:
                online_count += 1
        
        print("=" * 60)
        print(f"汇总: {online_count}/10 节点在线")
        return online_count

def main():
    relay = NanobotRelay()
    
    if len(sys.argv) < 2:
        print("Nanobot Command Center - Bot Relay")
        print("")
        print("Usage: nb-relay.py <command> [options]")
        print("")
        print("Commands:")
        print("  status                    检查所有节点状态")
        print("  send <node_id> <message>  发送消息到指定节点")
        print("  broadcast <message>       广播到所有节点")
        print("  chat <node_id>            与指定节点对话")
        print("")
        print("Models: glm, kimi, ds, step")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "status":
        relay.status_all()
    
    elif command == "send":
        if len(sys.argv) < 4:
            print("Usage: send <node_id> <message>")
            sys.exit(1)
        node_id = sys.argv[2]
        message = sys.argv[3]
        model = sys.argv[4] if len(sys.argv) > 4 else "glm"
        
        print(f"🚀 发送消息到 {node_id}...")
        success, result = relay.send_to_node(node_id, message, model)
        if success:
            print(f"✅ {node_id} 响应:")
            print(f"   {result[:200]}...")
        else:
            print(f"❌ 失败: {result}")
    
    elif command == "broadcast":
        if len(sys.argv) < 3:
            print("Usage: broadcast <message>")
            sys.exit(1)
        message = sys.argv[2]
        model = sys.argv[3] if len(sys.argv) > 3 else "glm"
        
        print(f"📢 广播消息到所有节点...")
        results = relay.broadcast(message, model)
        
        success_count = sum(1 for r in results.values() if r["success"])
        print(f"\n✅ {success_count}/10 节点响应成功")
        
        for node_id, r in results.items():
            status = "✅" if r["success"] else "❌"
            print(f"  {status} {node_id}: {r['result'][:50] if r['success'] else r['result']}...")
    
    elif command == "chat":
        if len(sys.argv) < 3:
            print("Usage: chat <node_id>")
            sys.exit(1)
        node_id = sys.argv[2]
        
        print(f"💬 开始与 {node_id} 对话 (输入 'exit' 退出)")
        while True:
            try:
                user_input = input(f"\nYou > ")
                if user_input.lower() in ["exit", "quit", "q"]:
                    break
                
                success, result = relay.send_to_node(node_id, user_input)
                if success:
                    print(f"{node_id} > {result}")
                else:
                    print(f"❌ 错误: {result}")
            except KeyboardInterrupt:
                break
        print("\n👋 对话结束")
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
