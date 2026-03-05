#!/usr/bin/env python3
"""
OpenClaw Command Center - Node Manager
指挥中心节点管理器

功能:
- 监控10个nanobot节点状态
- 负载均衡任务分配
- 节点健康检查
"""

import json
import sys
import time
import random
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置
CONFIG_FILE = Path("/root/.openclaw/workspace/config/nanobot-models-10.json")
NODES = [
    ("NB01", "nvidia-build-nb01", "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"),
    ("NB02", "nvidia-build-nb02", "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"),
    ("NB03", "nvidia-build-nb03", "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"),
    ("NB04", "nvidia-build-nb04", "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"),
    ("NB05", "nvidia-build-nb05", "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"),
    ("NB06", "nvidia-build-nb06", "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"),
    ("NB07", "nvidia-build-nb07", "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"),
    ("NB08", "nvidia-build-nb08", "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"),
    ("NB09", "nvidia-build-nb09", "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"),
    ("NB10", "nvidia-build-nb10", "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"),
]

MODELS = {
    "glm": "z-ai/glm4.7",
    "kimi": "moonshotai/kimi-k2.5",
    "ds": "deepseek-ai/deepseek-v3.2",
    "step": "stepfun-ai/step-3.5-flash"
}

class NodeManager:
    def __init__(self):
        self.node_status = {}
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                self.config = json.load(f)
    
    def check_node(self, node_id, provider, api_key):
        """检查单个节点状态"""
        import requests
        try:
            resp = requests.get(
                "https://integrate.api.nvidia.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                model_count = len(data.get("data", []))
                return (node_id, "online", model_count)
            else:
                return (node_id, f"error_{resp.status_code}", 0)
        except Exception as e:
            return (node_id, f"offline", str(e)[:30])
    
    def status(self):
        """显示所有节点状态"""
        print("=" * 60)
        print(f"🎯 OpenClaw Command Center - 节点状态")
        print(f"⏰ 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        online_count = 0
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self.check_node, nid, prov, key): nid 
                for nid, prov, key in NODES
            }
            
            results = []
            for future in as_completed(futures):
                results.append(future.result())
            
            results.sort(key=lambda x: x[0])
            
            for node_id, status, info in results:
                if status == "online":
                    print(f"  ✅ {node_id}: 在线 ({info} 个模型)")
                    online_count += 1
                else:
                    print(f"  ❌ {node_id}: {status} ({info})")
        
        print("=" * 60)
        print(f"汇总: {online_count}/10 节点在线")
        
        if online_count == 10:
            print("🎉 所有节点正常运行")
        elif online_count >= 7:
            print(f"✓ 大部分节点可用 ({online_count}/10)")
        else:
            print(f"⚠️ 多个节点离线，需要检查")
        
        return online_count
    
    def select_node(self, strategy="round_robin"):
        """选择节点（负载均衡）"""
        if strategy == "random":
            return random.choice(NODES)
        elif strategy == "round_robin":
            # 简单的轮询
            if not hasattr(self, '_rr_index'):
                self._rr_index = 0
            node = NODES[self._rr_index % len(NODES)]
            self._rr_index += 1
            return node
        else:
            return NODES[0]
    
    def get_node_by_id(self, node_id):
        """根据ID获取节点"""
        for node in NODES:
            if node[0] == node_id:
                return node
        return None
    
    def get_model_full_id(self, node_provider, model_alias):
        """获取完整模型ID"""
        model_id = MODELS.get(model_alias, MODELS["glm"])
        return f"{node_provider}/{model_id}"

def main():
    manager = NodeManager()
    
    if len(sys.argv) < 2:
        print("Usage: cc-node-manager.py <command> [options]")
        print("")
        print("Commands:")
        print("  status              显示所有节点状态")
        print("  select [strategy]   选择节点 (random/round_robin)")
        print("  info <node_id>      显示节点详细信息")
        print("")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "status":
        manager.status()
    elif command == "select":
        strategy = sys.argv[2] if len(sys.argv) > 2 else "round_robin"
        node = manager.select_node(strategy)
        print(f"Selected: {node[0]} ({node[1]})")
    elif command == "info":
        if len(sys.argv) < 3:
            print("Usage: info <node_id>")
            sys.exit(1)
        node = manager.get_node_by_id(sys.argv[2])
        if node:
            print(f"Node: {node[0]}")
            print(f"Provider: {node[1]}")
            print(f"API Key: {node[2][:20]}...")
            print(f"Models: {', '.join(MODELS.keys())}")
        else:
            print(f"Node {sys.argv[2]} not found")
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
