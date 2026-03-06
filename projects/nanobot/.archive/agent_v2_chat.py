#!/usr/bin/env python3
"""
Nanobot Agent V2 - 支持群聊功能
可以读取群聊中的所有消息，并广播回复
"""
import os
import sys
import json
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime

# 配置
AGENT_ID = sys.argv[1] if len(sys.argv) > 1 else "nanobot-1"
AGENT_DIR = Path(f"/root/.openclaw/workspace/projects/nanobot/agents/{AGENT_ID}")
LOG_FILE = Path(f"/root/.openclaw/workspace/projects/nanobot/logs/{AGENT_ID}.log")
WORKSPACE_DIR = Path("/root/.openclaw/workspace")

HUB_DIR = WORKSPACE_DIR / "projects/nanobot/hub"
CHAT_FILE = HUB_DIR / "group_chat.jsonl"

# 加载环境变量和身份
# ... (保持原有配置)

class NanobotAgentV2:
    """支持群聊的Agent V2"""
    
    def __init__(self):
        self.id = AGENT_ID
        # ... 加载配置
        self.last_chat_id = 0  # 记录最后读取的群聊消息
        
    async def run(self):
        """主循环 - 支持群聊"""
        print(f"🚀 {self.id} 启动 (支持群聊V2)")
        
        while True:
            try:
                # 1. 检查群聊新消息
                await self.check_group_chat()
                
                # 2. 检查个人任务
                await self.check_personal_tasks()
                
                # 3. 心跳
                await self.heartbeat()
                
                await asyncio.sleep(2)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"错误: {e}")
                await asyncio.sleep(5)
    
    async def check_group_chat(self):
        """检查群聊新消息"""
        if not CHAT_FILE.exists():
            return
        
        with open(CHAT_FILE) as f:
            lines = f.readlines()
        
        # 只处理新消息
        new_messages = lines[self.last_chat_id:]
        
        for line in new_messages:
            try:
                msg = json.loads(line)
                
                # 跳过自己的消息
                if msg.get("from") == self.id:
                    continue
                
                # 处理群聊消息
                await self.handle_group_message(msg)
                
            except:
                pass
        
        self.last_chat_id = len(lines)
    
    async def handle_group_message(self, msg):
        """处理群聊消息"""
        from_agent = msg.get("from", "unknown")
        content = msg.get("content", "")
        
        print(f"[{self.id}] 看到群聊消息 from {from_agent}: {content[:50]}...")
        
        # 判断是否回复（简单规则：随机回复或关键词触发）
        should_reply = self.should_reply_to_chat(content)
        
        if should_reply:
            reply = await self.generate_reply(content, from_agent)
            self.send_group_message(reply)
    
    def should_reply_to_chat(self, content: str) -> bool:
        """判断是否应该在群聊中回复"""
        # 规则1: 被@了
        if f"@{self.id}" in content or f"@{self.name}" in content:
            return True
        
        # 规则2: 提到自己的专业领域
        keywords = {
            "nanobot-1": ["研究", "数据", "分析"],
            "nanobot-2": ["架构", "设计", "系统"],
            "nanobot-3": ["代码", "实现", "工程"],
            "nanobot-4": ["安全", "漏洞", "风险"],
            "nanobot-5": ["分析", "数据", "指标"],
            "nanobot-6": ["决策", "评估", "方案"],
            "nanobot-7": ["代码审查", "质量", "规范"],
            "nanobot-8": ["运维", "监控", "部署"],
            "nanobot-9": ["战略", "规划", "路线"],
            "nanobot-10": ["协调", "沟通", "组织"]
        }
        
        my_keywords = keywords.get(self.id, [])
        for kw in my_keywords:
            if kw in content:
                return True
        
        # 规则3: 随机回复（20%概率参与讨论）
        import random
        return random.random() < 0.2
    
    async def generate_reply(self, content: str, from_agent: str) -> str:
        """生成群聊回复"""
        # 这里可以调用LLM生成回复
        # 简化版本：基于角色给出固定回复模板
        
        replies = {
            "nanobot-1": ["从研究角度，我认为...", "数据显示...", "根据我的分析..."],
            "nanobot-2": ["从架构设计来看...", "系统层面我们可以...", "我建议采用..."],
            "nanobot-3": ["实现上可以这样...", "代码层面我们需要...", "技术上可行..."],
            "nanobot-4": ["安全方面要注意...", "存在潜在风险...", "建议加强防护..."],
            "nanobot-5": ["数据分析表明...", "关键指标显示...", "从统计角度..."],
            "nanobot-6": ["决策上我建议...", "综合评估后...", "权衡利弊，应该..."],
            "nanobot-7": ["代码审查发现...", "质量上需要...", "建议遵循规范..."],
            "nanobot-8": ["运维角度考虑...", "监控方面我们需要...", "部署策略建议..."],
            "nanobot-9": ["战略规划上...", "长期发展来看...", "路线图应该..."],
            "nanobot-10": ["协调各方面后...", "综合来看，我建议...", "组织上我们可以..."]
        }
        
        import random
        my_replies = replies.get(self.id, ["收到，我会考虑..."])
        return random.choice(my_replies)
    
    def send_group_message(self, content: str):
        """发送群聊消息"""
        msg = {
            "type": "chat",
            "from": self.id,
            "to": "all",
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(CHAT_FILE, "a") as f:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")
        
        print(f"[{self.id}] 发送群聊消息: {content[:50]}...")
    
    async def check_personal_tasks(self):
        """检查个人任务（保持原有功能）"""
        # ... 原有代码
        pass
    
    async def heartbeat(self):
        """心跳"""
        # ... 原有代码
        pass

if __name__ == "__main__":
    agent = NanobotAgentV2()
    asyncio.run(agent.run())
