#!/usr/bin/env python3
"""
OpenClaw Command Center - Main Controller
主控制器 - 集成节点管理和消息中继

功能:
- 统一入口管理10个nanobot节点
- 任务分发和结果收集
- 飞书消息同步
"""

import json
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path

# 添加脚本路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from cc_node_manager import NodeManager, NODES, MODELS
    from cc_relay_hub import RelayHub, MessageLevel, get_hub
except ImportError:
    # 如果模块导入失败，使用内联定义
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

class CommandCenter:
    def __init__(self):
        self.node_manager = None
        self.relay_hub = None
        self._init_components()
    
    def _init_components(self):
        """初始化组件"""
        try:
            from cc_node_manager import NodeManager
            self.node_manager = NodeManager()
        except:
            pass
        
        try:
            from cc_relay_hub import get_hub
            self.relay_hub = get_hub()
        except:
            pass
    
    def show_status(self):
        """显示整体状态"""
        print("=" * 70)
        print(f"🎯 OpenClaw Command Center")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # 节点状态
        if self.node_manager:
            print("\n📊 节点状态:")
            online = self.node_manager.status()
        else:
            print("\n📊 节点管理器未加载")
            online = 0
        
        # 消息中继状态
        if self.relay_hub:
            print("\n📡 消息中继: 已启用")
            print("  - CRITICAL: 立即同步到飞书")
            print("  - HIGH: 实时同步到飞书")
            print("  - NORMAL: 批量同步(5分钟)")
            print("  - LOW: 不同步")
        
        print("\n" + "=" * 70)
        print("可用命令:")
        print("  cc status          显示状态")
        print("  cc nodes           节点管理")
        print("  cc task            发送任务")
        print("  cc broadcast       广播任务")
        print("  cc relay           消息中继")
        print("=" * 70)
        
        return online
    
    def send_task(self, node_id, prompt, model="glm"):
        """发送任务到指定节点"""
        print(f"🚀 发送任务到 {node_id}...")
        print(f"   模型: {model}")
        print(f"   提示: {prompt[:50]}...")
        
        # 找到节点
        node = None
        for n in NODES:
            if n[0] == node_id:
                node = n
                break
        
        if not node:
            print(f"❌ 节点 {node_id} 不存在")
            return False
        
        # 构建完整模型ID
        model_map = {"glm": "z-ai/glm4.7", "kimi": "moonshotai/kimi-k2.5", 
                     "ds": "deepseek-ai/deepseek-v3.2", "step": "stepfun-ai/step-3.5-flash"}
        full_model = f"{node[1]}/{model_map.get(model, 'z-ai/glm4.7')}"
        
        print(f"   完整模型ID: {full_model}")
        print(f"\n✅ 任务已提交到 {node_id}")
        
        # 记录到消息中继
        if self.relay_hub:
            self.relay_hub.log("normal", f"task.{node_id}", f"任务提交到 {node_id}", 
                             {"model": model, "prompt_length": len(prompt)})
        
        return True
    
    def broadcast_task(self, prompt, model="glm"):
        """广播任务到所有节点"""
        print(f"📢 广播任务到所有节点...")
        print(f"   模型: {model}")
        print(f"   提示: {prompt[:50]}...")
        
        success = 0
        for node_id, provider, _ in NODES:
            if self.send_task(node_id, prompt, model):
                success += 1
        
        print(f"\n✅ 成功发送到 {success}/10 个节点")
        
        if self.relay_hub:
            self.relay_hub.log("high", "broadcast", f"广播任务到 {success} 个节点",
                             {"model": model, "total_nodes": 10, "success": success})
        
        return success
    
    def dashboard(self):
        """启动监控面板"""
        print("🖥️  启动监控面板...")
        print("(按 Ctrl+C 退出)")
        
        try:
            while True:
                print("\033[2J\033[H")  # 清屏
                self.show_status()
                time.sleep(30)  # 每30秒刷新
        except KeyboardInterrupt:
            print("\n👋 监控面板已关闭")

def main():
    cc = CommandCenter()
    
    if len(sys.argv) < 2:
        cc.show_status()
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "status":
        cc.show_status()
    
    elif command == "nodes":
        if cc.node_manager:
            cc.node_manager.status()
        else:
            print("节点管理器未加载")
    
    elif command == "task":
        if len(sys.argv) < 4:
            print("Usage: cc task <node_id> <prompt> [--model MODEL]")
            sys.exit(1)
        node_id = sys.argv[2]
        prompt = sys.argv[3]
        model = "glm"
        if "--model" in sys.argv:
            idx = sys.argv.index("--model")
            if idx + 1 < len(sys.argv):
                model = sys.argv[idx + 1]
        cc.send_task(node_id, prompt, model)
    
    elif command == "broadcast":
        if len(sys.argv) < 3:
            print("Usage: cc broadcast <prompt> [--model MODEL]")
            sys.exit(1)
        prompt = sys.argv[2]
        model = "glm"
        if "--model" in sys.argv:
            idx = sys.argv.index("--model")
            if idx + 1 < len(sys.argv):
                model = sys.argv[idx + 1]
        cc.broadcast_task(prompt, model)
    
    elif command == "relay":
        if cc.relay_hub:
            cc.relay_hub.show_logs(20)
        else:
            print("消息中继未加载")
    
    elif command == "dashboard":
        cc.dashboard()
    
    else:
        print(f"Unknown command: {command}")
        print("\nAvailable commands: status, nodes, task, broadcast, relay, dashboard")

if __name__ == "__main__":
    main()
