#!/usr/bin/env python3
"""
Command Center - Auto Recovery System (P0)
自动故障恢复系统

功能:
- 节点健康监控
- 自动重启离线节点
- 熔断机制
- 飞书告警通知
"""

import json
import time
import requests
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import threading

# 导入飞书同步
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
try:
    from feishu_sync import get_sync_service
    FEISHU_AVAILABLE = True
except:
    FEISHU_AVAILABLE = False

# 节点配置
NANOBOTS = [
    {"id": "NB01", "port": 18801, "config": "/root/.openclaw/workspace/nanobots/nb01"},
    {"id": "NB02", "port": 18802, "config": "/root/.openclaw/workspace/nanobots/nb02"},
    {"id": "NB03", "port": 18803, "config": "/root/.openclaw/workspace/nanobots/nb03"},
    {"id": "NB04", "port": 18804, "config": "/root/.openclaw/workspace/nanobots/nb04"},
    {"id": "NB05", "port": 18805, "config": "/root/.openclaw/workspace/nanobots/nb05"},
    {"id": "NB06", "port": 18806, "config": "/root/.openclaw/workspace/nanobots/nb06"},
    {"id": "NB07", "port": 18807, "config": "/root/.openclaw/workspace/nanobots/nb07"},
    {"id": "NB08", "port": 18808, "config": "/root/.openclaw/workspace/nanobots/nb08"},
    {"id": "NB09", "port": 18809, "config": "/root/.openclaw/workspace/nanobots/nb09"},
    {"id": "NB10", "port": 18810, "config": "/root/.openclaw/workspace/nanobots/nb10"},
]

class NodeStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    RECOVERING = "recovering"
    CIRCUIT_BREAK = "circuit_break"  # 熔断

@dataclass
class NodeHealth:
    node_id: str
    status: NodeStatus
    last_check: Optional[datetime] = None
    last_online: Optional[datetime] = None
    offline_count: int = 0
    consecutive_failures: int = 0
    circuit_break_until: Optional[datetime] = None
    restart_count: int = 0
    
    def record_failure(self):
        self.consecutive_failures += 1
        self.offline_count += 1
        
        # 连续失败5次，触发熔断
        if self.consecutive_failures >= 5:
            self.circuit_break_until = datetime.now() + timedelta(minutes=10)
            self.status = NodeStatus.CIRCUIT_BREAK
    
    def record_success(self):
        self.consecutive_failures = 0
        self.last_online = datetime.now()
        self.status = NodeStatus.ONLINE

class AutoRecoverySystem:
    """自动故障恢复系统"""
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.health: Dict[str, NodeHealth] = {}
        self.running = False
        self.monitor_thread = None
        self._init_health()
    
    def _init_health(self):
        """初始化健康状态"""
        for node in NANOBOTS:
            self.health[node["id"]] = NodeHealth(
                node_id=node["id"],
                status=NodeStatus.ONLINE
            )
    
    def check_node(self, node: Dict) -> bool:
        """检查单个节点健康"""
        try:
            resp = requests.get(
                f"http://127.0.0.1:{node['port']}/status",
                timeout=5
            )
            return resp.status_code == 200
        except:
            return False
    
    def restart_node(self, node: Dict) -> bool:
        """重启节点"""
        node_id = node["id"]
        port = node["port"]
        
        print(f"🔄 正在重启 {node_id}...")
        
        try:
            # 1. 停止现有进程
            subprocess.run(
                ["pkill", "-f", f"PORT = {port}"],
                capture_output=True,
                timeout=5
            )
            time.sleep(1)
            
            # 2. 启动新进程
            script = f"""
import json
import http.server
import socketserver

PORT = {port}

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({{'status': 'online', 'node': '{node_id.lower()}'}}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

with socketserver.TCPServer(('0.0.0.0', PORT), Handler) as httpd:
    httpd.serve_forever()
"""
            
            subprocess.Popen(
                ["python3", "-c", script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            
            # 3. 等待启动
            time.sleep(2)
            
            # 4. 验证
            if self.check_node(node):
                print(f"✅ {node_id} 重启成功")
                return True
            else:
                print(f"❌ {node_id} 重启后仍无法连接")
                return False
                
        except Exception as e:
            print(f"❌ 重启 {node_id} 失败: {e}")
            return False
    
    def send_alert(self, level: str, node_id: str, message: str):
        """发送告警"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        alert_msg = f"[{timestamp}] [{level}] {node_id}: {message}"
        print(alert_msg)
        
        # 飞书通知
        if FEISHU_AVAILABLE and level in ["CRITICAL", "HIGH"]:
            try:
                sync = get_sync_service()
                if level == "CRITICAL":
                    sync.critical(f"recovery.{node_id}", message)
                else:
                    sync.high(f"recovery.{node_id}", message)
            except Exception as e:
                print(f"飞书通知失败: {e}")
    
    def check_all_nodes(self):
        """检查所有节点"""
        for node in NANOBOTS:
            node_id = node["id"]
            health = self.health[node_id]
            
            # 检查是否处于熔断期
            if health.status == NodeStatus.CIRCUIT_BREAK:
                if health.circuit_break_until and datetime.now() > health.circuit_break_until:
                    print(f"🔓 {node_id} 熔断期结束，尝试恢复")
                    health.status = NodeStatus.OFFLINE
                else:
                    continue  # 跳过检查
            
            # 健康检查
            is_online = self.check_node(node)
            health.last_check = datetime.now()
            
            if is_online:
                if health.status != NodeStatus.ONLINE:
                    # 节点恢复
                    health.record_success()
                    health.restart_count = 0
                    self.send_alert("HIGH", node_id, "节点已恢复在线")
                else:
                    health.record_success()
            else:
                # 节点离线
                health.record_failure()
                health.status = NodeStatus.OFFLINE
                
                if health.consecutive_failures == 1:
                    self.send_alert("NORMAL", node_id, "节点离线，等待重试")
                
                # 连续3次失败，自动重启
                if health.consecutive_failures == 3:
                    self.send_alert("HIGH", node_id, f"节点连续3次离线，尝试自动重启 (第{health.restart_count + 1}次)")
                    health.status = NodeStatus.RECOVERING
                    
                    if self.restart_node(node):
                        health.restart_count += 1
                        health.record_success()
                        self.send_alert("HIGH", node_id, "自动重启成功")
                    else:
                        health.restart_count += 1
                        self.send_alert("CRITICAL", node_id, f"自动重启失败 ({health.restart_count}次)")
                
                # 连续5次失败，熔断
                if health.consecutive_failures >= 5 and health.status != NodeStatus.CIRCUIT_BREAK:
                    self.send_alert("CRITICAL", node_id, "触发熔断机制，10分钟后重试")
    
    def monitor_loop(self):
        """监控循环"""
        print(f"🚀 自动恢复系统启动，检查间隔: {self.check_interval}秒")
        
        while self.running:
            try:
                self.check_all_nodes()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"❌ 监控循环错误: {e}")
                time.sleep(self.check_interval)
    
    def start(self):
        """启动监控"""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("✅ 自动恢复系统已启动")
    
    def stop(self):
        """停止监控"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("🛑 自动恢复系统已停止")
    
    def get_status(self) -> Dict:
        """获取状态报告"""
        report = {}
        for node_id, health in self.health.items():
            report[node_id] = {
                "status": health.status.value,
                "offline_count": health.offline_count,
                "consecutive_failures": health.consecutive_failures,
                "restart_count": health.restart_count,
                "circuit_break": health.circuit_break_until.isoformat() if health.circuit_break_until else None
            }
        return report

def main():
    import sys
    
    recovery = AutoRecoverySystem(check_interval=30)
    
    if len(sys.argv) < 2:
        print("Auto Recovery System")
        print("")
        print("Usage: auto_recovery.py <command>")
        print("")
        print("Commands:")
        print("  start        启动监控")
        print("  stop         停止监控")
        print("  status       查看状态")
        print("  once         执行一次检查")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "start":
        recovery.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            recovery.stop()
    
    elif command == "stop":
        recovery.stop()
    
    elif command == "status":
        status = recovery.get_status()
        print("=" * 60)
        print("🤖 自动恢复系统状态")
        print("=" * 60)
        for node_id, s in status.items():
            icon = "🟢" if s["status"] == "online" else "🔴"
            print(f"{icon} {node_id}: {s['status']}, 离线{s['offline_count']}次, 重启{s['restart_count']}次")
        print("=" * 60)
    
    elif command == "once":
        recovery.check_all_nodes()
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
