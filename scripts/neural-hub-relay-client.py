#!/usr/bin/env python3
"""
Neural Hub - 真正的nanobot接口 (基于bot relay)
通过relay与10个小弟实时通信
"""

import json
import requests
import time

class NeuralHubRelay:
    """神经中枢relay接口"""
    
    def __init__(self):
        self.base_url = "http://localhost:19000"
        self.me = "openclaw"
    
    def send(self, to_bot: str, message: str) -> dict:
        """发送消息给nanobot"""
        try:
            response = requests.post(
                f"{self.base_url}/message",
                json={"from": self.me, "to": to_bot, "message": message},
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def poll(self) -> list:
        """轮询我的消息队列"""
        try:
            response = requests.get(f"{self.base_url}/poll/{self.me}", timeout=10)
            return response.json()
        except Exception as e:
            print(f"轮询失败: {e}")
            return []
    
    def status(self) -> dict:
        """获取relay状态"""
        try:
            response = requests.get(f"{self.base_url}/status", timeout=10)
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def chat(self, to_bot: str, message: str, wait_seconds: int = 10) -> dict:
        """发送消息并等待回复"""
        # 发送
        result = self.send(to_bot, message)
        if "error" in result:
            return result
        
        print(f"📤 发送到 {to_bot}: {message[:50]}...")
        
        # 等待回复
        time.sleep(wait_seconds)
        
        # 查询队列
        messages = self.poll()
        
        # 过滤来自目标bot的消息
        replies = [m for m in messages if m.get("from") == to_bot]
        
        if replies:
            return {"status": "received", "replies": replies}
        else:
            return {"status": "waiting", "reply": "暂无回复"}
    
    def chat_all(self, message: str, wait_seconds: int = 10) -> dict:
        """发送消息给所有nanobot"""
        results = {}
        for i in range(1, 11):
            node = f"nanobot-{i}"
            result = self.chat(node, message, wait_seconds)
            results[node] = result
        return results

def main():
    """测试接口"""
    hub = NeuralHubRelay()
    
    print("=" * 70)
    print("🧠 神经中枢 - 真正的relay接口")
    print("=" * 70)
    print()
    
    # 检查状态
    print("1. Relay状态:")
    status = hub.status()
    print(f"   状态: {status.get('status')}")
    print(f"   节点数: {len(status.get('nodes', []))}")
    print(f"   消息审计: {status.get('audit_count', 0)}条")
    print()
    
    # 测试单节点对话
    print("2. 测试与nanobot-1对话:")
    reply = hub.chat("nanobot-1", "请简单介绍你自己", wait_seconds=10)
    if reply.get("status") == "received":
        for r in reply.get("replies", []):
            print(f"   {r.get('message', '')}")
    else:
        print(f"   消息: {reply}")
    print()
    
    print("✅ 接口测试完成！")

if __name__ == "__main__":
    main()
