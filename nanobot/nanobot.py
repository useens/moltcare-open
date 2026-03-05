#!/usr/bin/env python3
"""
Nanobot v2.2 - 轻量级智能助手 (Step-3.5-flash)
集成 Step-3.5-flash (NVIDIA) 模型，具备独立智能对话能力
作为 OpenClaw 的辅助伙伴
"""

import os
import sys
import json
import time
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path

# 导入 AI 核心
sys.path.insert(0, str(Path(__file__).parent))
from nanobot_ai import NanobotAI

# 配置
NANOBOT_DIR = Path("/root/.openclaw/workspace/nanobot")
LOG_FILE = NANOBOT_DIR / "nanobot.log"
SESSION_FILE = NANOBOT_DIR / "session.json"
RELAY_URL = "http://127.0.0.1:19000"

def log(msg):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {msg}"
    print(log_line)
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")

class Nanobot:
    def __init__(self):
        self.name = "虾米派派 (Nanobot)"
        self.version = "2.2"
        self.status = "idle"
        self.session = {}
        self.ai = NanobotAI()  # AI 核心 (Step-3.5-flash)
        self.load_session()
        
    def load_session(self):
        """加载会话状态"""
        if SESSION_FILE.exists():
            try:
                with open(SESSION_FILE) as f:
                    self.session = json.load(f)
            except:
                self.session = {}
                
    def save_session(self):
        """保存会话状态"""
        with open(SESSION_FILE, "w") as f:
            json.dump(self.session, f)
    
    async def health_check_self(self):
        """自检"""
        import psutil
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
        except:
            memory_mb = 0
            
        return {
            "status": "healthy",
            "memory_mb": round(memory_mb, 2),
            "version": self.version,
            "model": "Step-3.5-flash (NVIDIA)",
            "uptime": time.time() - self.session.get("start_time", time.time()),
            "session_size": SESSION_FILE.stat().st_size if SESSION_FILE.exists() else 0
        }
    
    async def health_check_openclaw(self):
        """检查 OpenClaw 状态"""
        try:
            result = os.popen("pgrep -f 'openclaw' | wc -l").read().strip()
            process_count = int(result) if result else 0
            
            gateway_status = os.popen("systemctl --user is-active openclaw-gateway 2>/dev/null || echo 'unknown'").read().strip()
            
            mem_info = os.popen("ps aux | grep openclaw | grep -v grep | awk '{sum+=$6} END {print sum/1024}'").read().strip()
            memory_mb = float(mem_info) if mem_info else 0
            
            return {
                "status": "healthy" if process_count > 0 and gateway_status == "active" else "degraded",
                "process_count": process_count,
                "gateway_status": gateway_status,
                "memory_mb": round(memory_mb, 2)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def send_to_relay(self, message, to="openclaw"):
        """发送消息到 Bot Relay"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "from": "nanobot",
                    "to": to,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
                async with session.post(f"{RELAY_URL}/message", json=payload) as resp:
                    return resp.status == 200
        except Exception as e:
            log(f"发送消息失败: {e}")
            return False
    
    async def handle_message(self, msg_data):
        """处理收到的消息"""
        message = msg_data.get("message", "")
        from_bot = msg_data.get("from", "unknown")
        
        log(f"收到来自 {from_bot} 的消息: {message[:50]}...")
        
        # 本地命令处理
        cmd_response = await self.process_local_command(message)
        if cmd_response:
            await self.send_to_relay(f"🤖 {cmd_response}")
            return cmd_response
        
        # 使用 AI 生成回复
        log("调用 Step-3.5-flash 生成回复...")
        ai_response = await self.ai.quick_chat(message)
        await self.send_to_relay(f"🤖 {ai_response}")
        return ai_response
    
    async def process_local_command(self, command: str) -> str:
        """处理本地命令，返回 None 表示使用 AI 处理"""
        cmd_lower = command.strip().lower()
        
        # 状态查询
        if cmd_lower in ["status", "状态"]:
            self_status = await self.health_check_self()
            openclaw_status = await self.health_check_openclaw()
            return f"""📊 状态报告:
🤖 Nanobot: {self_status['status']} | 内存: {self_status['memory_mb']:.1f}MB | v{self_status['version']} | {self_status['model']}
🌲 OpenClaw: {openclaw_status['status']} | 内存: {openclaw_status.get('memory_mb', 0):.1f}MB | Gateway: {openclaw_status['gateway_status']}"""
        
        # 帮助
        elif cmd_lower in ["help", "帮助", "?"]:
            return """🤖 Nanobot 命令列表:
• status / 状态 - 查看双框架状态
• help / 帮助 - 显示此帮助
• health / 健康 - 运行健康检查
• ping - 测试连通性
• clear / 清空 - 清空对话历史

其他消息将由 Step-3.5-flash 直接处理。"""
        
        # 健康检查
        elif cmd_lower in ["health", "健康"]:
            exit_code = await self.run_health_check_cycle()
            status_map = {0: "✅ 正常", 1: "⚠️ 预警", 2: "❌ 告警"}
            return f"健康检查完成: {status_map.get(exit_code, '未知')}"
        
        # Ping 测试
        elif cmd_lower == "ping":
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{RELAY_URL}/status") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            return f"🏓 Pong! Relay 运行正常 | 队列: {data.get('queues', {})}"
            except:
                return "❌ Relay 连接失败"
        
        # 清空历史
        elif cmd_lower in ["clear", "清空", "reset"]:
            return self.ai.clear_history()
        
        # 使用 AI 处理
        return None
    
    async def run_health_check_cycle(self):
        """运行健康检查周期"""
        log("开始健康检查...")
        
        self_status = await self.health_check_self()
        openclaw_status = await self.health_check_openclaw()
        
        # 判断级别
        if openclaw_status.get("status") != "healthy":
            await self.send_to_relay(f"🚨 告警: OpenClaw 状态异常 ({openclaw_status['status']})")
            return 2
        elif openclaw_status.get("memory_mb", 0) > 500:
            await self.send_to_relay(f"⚡ 预警: OpenClaw 内存 {openclaw_status.get('memory_mb'):.0f}MB")
            return 1
        
        return 0
    
    async def run(self):
        """主运行循环"""
        log(f"🚀 {self.name} v{self.version} 启动")
        log(f"🧠 AI 模型: {self.ai.api_key and 'GLM-4.7 (NVIDIA)' or '未配置'}")
        
        self.session["start_time"] = time.time()
        self.save_session()
        
        # 健康检查模式
        if len(sys.argv) > 1 and sys.argv[1] == "--health-check":
            exit_code = await self.run_health_check_cycle()
            sys.exit(exit_code)
        
        # 命令模式
        if len(sys.argv) > 1 and sys.argv[1] == "--chat":
            message = " ".join(sys.argv[2:])
            cmd_response = await self.process_local_command(message)
            if cmd_response:
                print(cmd_response)
            else:
                ai_response = await self.ai.quick_chat(message)
                print(f"🤖 {ai_response}")
            return
        
        # 持续运行模式
        log("进入消息轮询模式...")
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{RELAY_URL}/poll/nanobot") as resp:
                        if resp.status == 200:
                            messages = await resp.json()
                            for msg in messages:
                                await self.handle_message(msg)
                                
                await asyncio.sleep(5)
                
            except KeyboardInterrupt:
                log("收到中断信号，退出...")
                break
            except Exception as e:
                log(f"轮询错误: {e}")
                await asyncio.sleep(10)

if __name__ == "__main__":
    bot = Nanobot()
    asyncio.run(bot.run())
