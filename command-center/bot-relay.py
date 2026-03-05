#!/usr/bin/env python3
"""
OpenClaw Command Center - Bot Relay
指挥中心 - Bot Relay 架构

功能:
- 管理10个独立nanobot节点
- 通过gateway向节点发送命令
- 收集节点响应并同步到飞书
"""

import json
import sys
import time
import subprocess
import requests
from datetime import datetime
from pathlib import Path

# 节点配置
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

CC_HOST = "127.0.0.1"
FEISHU_TARGET = "ou_dc4db246fa540096f42caefbd2112ed3"

class BotRelay:
    def __init__(self):
        self.nodes = {n["id"]: n for n in NANOBOTS}
    
    def check_node(self, node_id):
        """检查单个节点状态"""
        node = self.nodes.get(node_id)
        if not node:
            return (node_id, "not_found", None)
        
        try:
            # 检查API连通性
            resp = requests.get(
                "https://integrate.api.nvidia.com/v1/models",
                headers={"Authorization": f"Bearer {node['apikey']}"},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                model_count = len(data.get("data", []))
                return (node_id, "online", model_count)
            else:
                return (node_id, f"error_{resp.status_code}", 0)
        except Exception as e:
            return (node_id, "offline", str(e)[:30])
    
    def status(self):
        """显示所有节点状态"""
        print("=" * 60)
        print(f"🎯 OpenClaw Command Center - Nanobot Nodes Status")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        online_count = 0
        results = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(self.check_node, nid): nid for nid in self.nodes}
            for future in as_completed(futures):
                results.append(future.result())
        
        results.sort(key=lambda x: x[0])
        
        for node_id, status, info in results:
            if status == "online":
                print(f"  ✅ {node_id}: 在线 ({info} 模型)")
                online_count += 1
            else:
                print(f"  ❌ {node_id}: {status}")
        
        print("=" * 60)
        print(f"汇总: {online_count}/10 节点在线")
        
        if online_count == 10:
            print("🎉 所有节点正常运行")
        elif online_count >= 7:
            print(f"✓ 大部分节点可用 ({online_count}/10)")
        else:
            print(f"⚠️ 多个节点离线")
        
        return online_count
    
    def send_to_node(self, node_id, message, model="glm"):
        """向指定节点发送消息"""
        node = self.nodes.get(node_id)
        if not node:
            print(f"❌ 节点 {node_id} 不存在")
            return False
        
        model_map = {
            "glm": "z-ai/glm4.7",
            "kimi": "moonshotai/kimi-k2.5",
            "ds": "deepseek-ai/deepseek-v3.2",
            "step": "stepfun-ai/step-3.5-flash"
        }
        model_id = model_map.get(model, "z-ai/glm4.7")
        
        print(f"🚀 发送消息到 {node_id} (模型: {model})...")
        
        try:
            resp = requests.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {node['apikey']}", "Content-Type": "application/json"},
                json={
                    "model": model_id,
                    "messages": [{"role": "user", "content": message}],
                    "max_tokens": 500
                },
                timeout=60
            )
            
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"✅ {node_id} 响应:")
                print(f"   {content[:200]}...")
                self._notify_feishu(f"✅ {node_id} 任务完成", content[:100])
                return True
            else:
                print(f"❌ {node_id} 错误: HTTP {resp.status_code}")
                self._notify_feishu(f"❌ {node_id} 任务失败", f"HTTP {resp.status_code}")
                return False
        except Exception as e:
            print(f"❌ {node_id} 异常: {e}")
            self._notify_feishu(f"❌ {node_id} 异常", str(e)[:100])
            return False
    
    def broadcast(self, message, model="glm"):
        """广播消息到所有节点"""
        print(f"📢 广播消息到所有节点 (模型: {model})...")
        print(f"   消息: {message[:50]}...")
        print("=" * 60)
        
        success = 0
        for node_id in self.nodes:
            if self.send_to_node(node_id, message, model):
                success += 1
            print()
        
        print("=" * 60)
        print(f"✅ 成功: {success}/10 节点")
        self._notify_feishu(f"📢 广播完成", f"{success}/10 节点成功")
        return success
    
    def _notify_feishu(self, title, content):
        """同步消息到飞书"""
        try:
            # 使用message工具发送
            msg = f"**[{title}]**\n\n{content}\n\n⏰ {datetime.now().strftime('%H:%M:%S')}"
            # 这里应该调用飞书API，暂时打印
            print(f"[SYNC→Feishu] {title}")
        except:
            pass

def main():
    relay = BotRelay()
    
    if len(sys.argv) < 2:
        print("OpenClaw Command Center - Bot Relay")
        print("")
        print("Usage: bot-relay.py <command> [options]")
        print("")
        print("Commands:")
        print("  status                    显示所有节点状态")
        print("  send <node> <message>     发送消息到指定节点")
        print("  broadcast <message>       广播到所有节点")
        print("  chat <node>               与节点交互模式")
        print("")
        print("Models: glm, kimi, ds, step")
        print("")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "status":
        relay.status()
    
    elif command == "send":
        if len(sys.argv) < 4:
            print("Usage: send <node_id> <message> [--model MODEL]")
            sys.exit(1)
        node_id = sys.argv[2]
        message = sys.argv[3]
        model = "glm"
        if "--model" in sys.argv:
            idx = sys.argv.index("--model")
            if idx + 1 < len(sys.argv):
                model = sys.argv[idx + 1]
        relay.send_to_node(node_id, message, model)
    
    elif command == "broadcast":
        if len(sys.argv) < 3:
            print("Usage: broadcast <message> [--model MODEL]")
            sys.exit(1)
        message = sys.argv[2]
        model = "glm"
        if "--model" in sys.argv:
            idx = sys.argv.index("--model")
            if idx + 1 < len(sys.argv):
                model = sys.argv[idx + 1]
        relay.broadcast(message, model)
    
    elif command == "chat":
        if len(sys.argv) < 3:
            print("Usage: chat <node_id>")
            sys.exit(1)
        node_id = sys.argv[2]
        print(f"进入与 {node_id} 的交互模式 (输入 'exit' 退出)")
        while True:
            try:
                user_input = input(f"{node_id}> ")
                if user_input.lower() in ["exit", "quit"]:
                    break
                relay.send_to_node(node_id, user_input)
            except EOFError:
                break
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
