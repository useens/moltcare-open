#!/usr/bin/env python3
"""
Command Center - Main Dashboard
指挥中心主控面板

功能:
- 实时显示所有节点状态
- 系统资源监控
- 任务队列监控
- 消息流显示
"""

import json
import sys
import time
import os
from datetime import datetime
from pathlib import Path

# 导入组件 - 直接内联定义避免模块导入问题
NANOBOTS = [
    {"id": "NB01", "port": 18801, "token": "nb01-token-***"},
    {"id": "NB02", "port": 18802, "token": "nb02-token-***"},
    {"id": "NB03", "port": 18803, "token": "nb03-token-***"},
    {"id": "NB04", "port": 18804, "token": "nb04-token-***"},
    {"id": "NB05", "port": 18805, "token": "nb05-token-***"},
    {"id": "NB06", "port": 18806, "token": "nb06-token-***"},
    {"id": "NB07", "port": 18807, "token": "nb07-token-***"},
    {"id": "NB08", "port": 18808, "token": "nb08-token-***"},
    {"id": "NB09", "port": 18809, "token": "nb09-token-***"},
    {"id": "NB10", "port": 18810, "token": "nb10-token-***"},
]

class SimpleRelay:
    def check_node(self, node):
        import requests
        try:
            resp = requests.get(f"http://127.0.0.1:{node['port']}/status", timeout=3)
            return resp.status_code == 200
        except:
            return False

class NanobotRelay(SimpleRelay):
    pass

class Dashboard:
    """监控面板"""
    
    def __init__(self):
        self.relay = NanobotRelay()
        self.running = False
        self.refresh_interval = 5  # 秒
    
    def clear_screen(self):
        """清屏"""
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def get_node_status(self):
        """获取所有节点状态"""
        status = {}
        for node in NANOBOTS:
            is_online = self.relay.check_node(node)
            status[node["id"]] = {
                "online": is_online,
                "port": node["port"],
                "model": "Step" if int(node["id"][2:]) <= 5 else "DeepSeek"
            }
        return status
    
    def get_system_stats(self):
        """获取系统统计"""
        try:
            import psutil
            return {
                "cpu": psutil.cpu_percent(),
                "memory": psutil.virtual_memory().percent,
                "disk": psutil.disk_usage('/').percent
            }
        except:
            return {"cpu": 0, "memory": 0, "disk": 0}
    
    def render(self):
        """渲染面板"""
        self.clear_screen()
        
        # 标题
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 20 + "🤖 NANOBOT COMMAND CENTER" + " " * 33 + "║")
        print("║" + " " * 25 + "指挥中心监控面板" + " " * 36 + "║")
        print("╠" + "═" * 78 + "╣")
        
        # 时间
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"║  ⏰ {now}" + " " * 60 + "║")
        print("╠" + "═" * 78 + "╣")
        
        # 节点状态
        print("║  📊 NANOBOT 节点状态" + " " * 55 + "║")
        print("╠" + "─" * 78 + "╣")
        
        status = self.get_node_status()
        
        # Step组
        print("║  ⚡ Step 3.5 Flash 组 (快速响应)" + " " * 41 + "║")
        for i in range(1, 6):
            node_id = f"NB{i:02d}"
            s = status.get(node_id, {})
            status_icon = "🟢" if s.get("online") else "🔴"
            port = s.get("port", "----")
            print(f"║    {status_icon} {node_id} (Port {port})" + " " * 52 + "║")
        
        print("╠" + "─" * 78 + "╣")
        
        # DeepSeek组
        print("║  🧠 DeepSeek V3.2 组 (深度推理)" + " " * 40 + "║")
        for i in range(6, 11):
            node_id = f"NB{i:02d}"
            s = status.get(node_id, {})
            status_icon = "🟢" if s.get("online") else "🔴"
            port = s.get("port", "----")
            print(f"║    {status_icon} {node_id} (Port {port})" + " " * 52 + "║")
        
        # 汇总
        online_count = sum(1 for s in status.values() if s.get("online"))
        print("╠" + "═" * 78 + "╣")
        print(f"║  汇总: {online_count}/10 节点在线" + " " * 54 + "║")
        
        # 系统资源
        print("╠" + "═" * 78 + "╣")
        print("║  💻 系统资源" + " " * 63 + "║")
        print("╠" + "─" * 78 + "╣")
        stats = self.get_system_stats()
        print(f"║    CPU: {stats['cpu']:5.1f}%" + " " * 63 + "║")
        print(f"║    内存: {stats['memory']:5.1f}%" + " " * 62 + "║")
        print(f"║    磁盘: {stats['disk']:5.1f}%" + " " * 62 + "║")
        
        # 帮助信息
        print("╠" + "═" * 78 + "╣")
        print("║  快捷键: [Ctrl+C] 退出面板" + " " * 48 + "║")
        print("║  命令行: python3 scripts/cc.py status" + " " * 35 + "║")
        print("╚" + "═" * 78 + "╝")
    
    def run(self):
        """运行面板"""
        self.running = True
        
        try:
            while self.running:
                self.render()
                time.sleep(self.refresh_interval)
        except KeyboardInterrupt:
            self.running = False
            print("\n\n👋 监控面板已关闭")

def main():
    dashboard = Dashboard()
    
    if len(sys.argv) < 2:
        # 直接运行面板
        dashboard.run()
    
    elif sys.argv[1] == "once":
        # 只显示一次
        dashboard.render()
    
    elif sys.argv[1] == "status":
        # 简单的状态显示
        status = dashboard.get_node_status()
        online = sum(1 for s in status.values() if s.get("online"))
        
        print("=" * 60)
        print(f"🤖 Nanobot Command Center - 节点状态")
        print("=" * 60)
        
        for node_id, s in sorted(status.items()):
            icon = "✅" if s.get("online") else "❌"
            model = s.get("model", "?")
            print(f"  {icon} {node_id} ({model})")
        
        print("=" * 60)
        print(f"汇总: {online}/10 节点在线")
    
    else:
        print("Usage: dashboard.py [once|status]")

if __name__ == "__main__":
    main()
