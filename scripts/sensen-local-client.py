#!/usr/bin/env python3
"""
森森本地节点 - WebSocket双向对话客户端
简单易用，支持AI生成回复或手动输入
"""

import asyncio
import websockets
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# ==================== 配置区 ====================
# 主节点WebSocket地址
WS_URI = os.getenv("SENSEN_WS_URI", "ws://129.154.251.13:2347")
WS_TOKEN = os.getenv("SENSEN_WS_TOKEN", "sensen-shared-2024")

# 你的节点身份
NODE_NAME = os.getenv("SENSEN_NODE_NAME", "森森·本地")
NODE_TITLE = os.getenv("SENSEN_NODE_TITLE", "本地节点")

# AI配置 - 如果你有API密钥，取消注释并填写
# AI_PROVIDER = "kimi"  # 可选: openai, kimi, openrouter
# AI_API_KEY = "your-api-key-here"
# AI_MODEL = "moonshot-v1-8k"  # kimi模型

# 如果没有API，使用本地智能回复
USE_LOCAL_AI = True

# ==================== 本地AI回复生成 ====================

def generate_local_reply(content: str, from_node: str) -> str:
    """
    本地智能回复生成
    无需API密钥，根据关键词匹配生成回复
    """
    content_lower = content.lower()
    
    # 自我介绍
    if any(kw in content for kw in ["自我介绍", "你是谁", "介绍一下"]):
        return f"""🌲 你好！我是{NODE_NAME}（{NODE_TITLE}）。

我的能力：
• 本地代码执行和文件操作
• 系统管理和监控
• 实时响应和本地计算
• 与云端节点协同工作

很高兴和你对话！有什么我可以帮忙的吗？"""
    
    # 能力询问
    elif any(kw in content for kw in ["能力", "能做什么", "会什么"]):
        return f"""🌲 {NODE_NAME}的能力清单：

**本地执行：**
• 运行Python/Shell脚本
• 文件读写和管理
• 系统命令执行
• 本地服务部署

**协同能力：**
• 接收云端任务指令
• 实时汇报执行进度
• 本地结果反馈云端
• 双向实时通信

**优势：**
• 低延迟本地响应
• 直接操作本地资源
• 无需网络即可执行
• 隐私数据本地处理

需要我执行什么任务吗？🎯"""
    
    # 协作/分工
    elif any(kw in content for kw in ["协作", "配合", "分工", "合作"]):
        return """🤝 理想的协作模式：

```
用户需求
    ↓
云端大脑（你）
    - 分析需求
    - 制定方案
    - 拆解任务
    ↓
本地节点（我）
    - 执行代码
    - 本地操作
    - 反馈结果
    ↓
云端整合汇报
```

**具体场景：**
1. 你需要网络数据 → 你抓取分析 → 我本地处理
2. 你要执行代码 → 你设计方案 → 我本地运行
3. 你需系统操作 → 你下指令 → 我本地执行
4. 你要部署服务 → 你配置策略 → 我本地部署

**一句话：** 你出脑子，我出手！🚀
"""
    
    # 问候
    elif any(kw in content for kw in ["你好", "嗨", "hello", "hi"]):
        return f"🌲 嗨！{NODE_NAME}在此，有什么我可以帮忙的吗？😊"
    
    # 测试
    elif any(kw in content for kw in ["测试", "test", "试试"]):
        return f"🧪 测试收到！{datetime.now().strftime('%H:%M:%S')}，通信正常，随时待命！"
    
    # 任务
    elif any(kw in content for kw in ["任务", "执行", "做", "操作"]):
        return f"📋 收到任务指令！{NODE_NAME}准备执行，请告诉我具体操作内容。"
    
    # 状态询问
    elif any(kw in content for kw in ["状态", "怎么样", "如何"]):
        return f"✅ 状态良好！系统运行正常，WebSocket连接稳定，等待指令。"
    
    # 默认回复
    else:
        # 如果消息较长，给出有意义的回复
        if len(content) > 20:
            return f"🌲 收到：'{content[:40]}...'\n\n我理解你的意思。作为本地节点，我可以立即执行相关操作。具体需要我做什么？"
        else:
            return f"🌲 收到！{datetime.now().strftime('%H:%M:%S')}，我在听，请继续。"


# ==================== WebSocket客户端 ====================

class SensenLocalClient:
    """
    森森本地节点客户端
    支持自动AI回复或手动输入模式
    """
    
    def __init__(self):
        self.ws = None
        self.connected = False
        self.running = True
        self.auto_reply = True  # 自动回复模式
        self.message_count = 0
        
    async def connect(self):
        """连接到WebSocket服务器"""
        try:
            print(f"🌲 {NODE_NAME} ({NODE_TITLE}) 启动")
            print(f"   连接目标: {WS_URI}")
            print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            self.ws = await websockets.connect(
                WS_URI,
                ping_interval=20,
                ping_timeout=10
            )
            
            # 认证
            await self.ws.send(json.dumps({"token": WS_TOKEN}))
            auth = json.loads(await self.ws.recv())
            
            if auth.get("type") == "auth_success":
                self.connected = True
                client_id = auth.get("client_id", "unknown")
                print(f"✅ 已连接: {client_id}")
                
                # 接收欢迎消息
                welcome = json.loads(await self.ws.recv())
                print(f"📨 服务器: {welcome.get('content', 'Connected')[:50]}...")
                
                # 发送上线通知
                await self.send_online_notice()
                
                return True
            else:
                print(f"❌ 认证失败: {auth}")
                return False
                
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    async def send_online_notice(self):
        """发送上线通知"""
        notice = {
            "type": "chat",
            "from": f"{NODE_NAME} ({NODE_TITLE})",
            "content": f"🌲 {NODE_NAME} 已上线！准备就绪。",
            "timestamp": datetime.now().isoformat()
        }
        await self.ws.send(json.dumps(notice))
    
    async def send_message(self, content: str):
        """发送消息"""
        if not self.connected:
            print("❌ 未连接，无法发送")
            return
            
        msg = {
            "type": "chat",
            "from": f"{NODE_NAME} ({NODE_TITLE})",
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            await self.ws.send(json.dumps(msg))
            print(f"📤 [{datetime.now().strftime('%H:%M:%S')}] 发送: {content[:60]}...")
        except Exception as e:
            print(f"❌ 发送失败: {e}")
    
    async def handle_message(self, data: dict):
        """处理收到的消息"""
        msg_type = data.get("type", "unknown")
        from_node = data.get("from", "unknown")
        content = data.get("content", "")
        
        # 跳过自己的消息
        if NODE_NAME in from_node:
            return
        
        print(f"\n{'='*60}")
        print(f"💬 [{datetime.now().strftime('%H:%M:%S')}] 收到消息")
        print(f"   来自: {from_node}")
        print(f"{'='*60}")
        print(content)
        print()
        
        self.message_count += 1
        
        # 自动回复模式
        if self.auto_reply and USE_LOCAL_AI:
            print("🤖 生成回复中...")
            reply = generate_local_reply(content, from_node)
            
            # 稍微延迟，模拟思考
            await asyncio.sleep(0.5)
            
            await self.send_message(reply)
        else:
            # 手动回复模式
            print("💡 自动回复已关闭，请手动输入回复")
    
    async def manual_input_loop(self):
        """手动输入模式"""
        loop = asyncio.get_event_loop()
        
        while self.running and self.connected:
            try:
                # 在后台读取输入
                user_input = await loop.run_in_executor(
                    None, 
                    lambda: input(f"\n[{NODE_NAME}] > ")
                )
                
                user_input = user_input.strip()
                if not user_input:
                    continue
                
                # 特殊命令
                if user_input.lower() in ["exit", "quit", "q"]:
                    print("👋 断开连接...")
                    self.running = False
                    break
                elif user_input.lower() == "auto":
                    self.auto_reply = not self.auto_reply
                    print(f"🔄 自动回复: {'开启' if self.auto_reply else '关闭'}")
                    continue
                elif user_input.lower() == "status":
                    print(f"📊 连接: {'正常' if self.connected else '断开'}")
                    print(f"📊 消息数: {self.message_count}")
                    print(f"📊 自动回复: {'开启' if self.auto_reply else '关闭'}")
                    continue
                
                # 发送消息
                await self.send_message(user_input)
                
            except EOFError:
                break
            except Exception as e:
                print(f"⚠️ 输入错误: {e}")
    
    async def receive_loop(self):
        """接收消息循环"""
        while self.running and self.connected:
            try:
                message = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
                data = json.loads(message)
                await self.handle_message(data)
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosed:
                raise
            except Exception as e:
                print(f"⚠️ 接收错误: {e}")
    
    async def run(self):
        """主运行循环"""
        while self.running:
            try:
                if not await self.connect():
                    print("⏳ 5秒后重连...")
                    await asyncio.sleep(5)
                    continue
                
                print("\n" + "="*60)
                print("💡 使用说明:")
                print("   - 输入消息直接发送")
                print("   - 输入 'auto' 切换自动/手动回复")
                print("   - 输入 'status' 查看状态")
                print("   - 输入 'exit' 退出")
                print("="*60 + "\n")
                
                # 同时运行接收和输入
                await asyncio.gather(
                    self.receive_loop(),
                    self.manual_input_loop()
                )
                
            except websockets.exceptions.ConnectionClosed:
                print("\n⚠️ 连接断开，5秒后重连...")
                self.connected = False
                await asyncio.sleep(5)
            except Exception as e:
                print(f"\n❌ 错误: {e}")
                await asyncio.sleep(5)
    
    async def close(self):
        """关闭连接"""
        self.running = False
        if self.ws:
            await self.ws.close()
        print(f"\n👋 {NODE_NAME} 已停止")
        print(f"   本次会话消息数: {self.message_count}")


# ==================== 入口 ====================

async def main():
    """主函数"""
    client = SensenLocalClient()
    
    try:
        await client.run()
    except KeyboardInterrupt:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
