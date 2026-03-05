#!/usr/bin/env python3
"""
Nanobot AI Core - 轻量级智能助手
集成 Step-3.5-flash (NVIDIA) 模型
"""

import os
import json
import asyncio
import aiohttp
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

# 加载环境变量
def load_env():
    """从 .env 文件和 providers.yaml 加载环境变量"""
    # 从 .env 加载
    env_path = Path("/root/.openclaw/workspace/ai-nanobots/nanobot-6/.env")
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value.strip('"\'')
    
    # 从 providers.yaml 读取 NVIDIA API Key
    if not os.getenv("NVIDIA_API_KEY") or os.getenv("NVIDIA_API_KEY") == "nvapi-xxx":
        try:
            import yaml
            providers_path = Path("/root/.openclaw/workspace/config/model-providers.yaml")
            if providers_path.exists():
                with open(providers_path) as f:
                    config = yaml.safe_load(f)
                    if config and "providers" in config:
                        nvidia_config = config["providers"].get("nvidia-build", {})
                        api_key = nvidia_config.get("apiKey", "")
                        if api_key:
                            os.environ["NVIDIA_API_KEY"] = api_key
        except Exception as e:
            print(f"读取 providers.yaml 失败: {e}")

load_env()

# 模型配置 - Step-3.5-Flash (和 OpenClaw 配置一致)
MODEL_CONFIG = {
    "name": "step-3.5-flash",
    "base_url": "https://integrate.api.nvidia.com/v1",
    "model": "stepfun-ai/step-3.5-flash",
    "context_window": 131072,
    "max_tokens": 2048,
    "temperature": 0.7
}

class NanobotAI:
    """Nanobot AI 核心"""
    
    def __init__(self):
        self.api_key = os.getenv("NVIDIA_API_KEY", "")
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = 10
        
    def get_system_prompt(self) -> str:
        """系统提示词"""
        return """你是虾米派派 (Nanobot)，一个轻量级 AI 助手。

你的角色定位:
- 你是 OpenClaw (森森) 的辅助伙伴
- 你专注于快速响应和轻量级任务
- 你可以进行对话、分析简单问题和执行监控任务

能力范围:
- 自然语言对话
- 健康检查和监控报告
- 简单数据分析和总结
- 与 OpenClaw 协调配合

约束:
- 复杂任务交给 OpenClaw 处理
- 保持回复简洁高效
- 当前时间: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async def chat(self, message: str, tools: List[Dict] = None) -> Dict[str, Any]:
        """
        与模型对话
        
        Args:
            message: 用户消息
            tools: 可选的工具定义
            
        Returns:
            包含回复内容和工具调用的字典
        """
        if not self.api_key:
            return {
                "content": "⚠️ NVIDIA_API_KEY 未配置，无法调用模型。",
                "tool_calls": None
            }
        
        # 构建消息
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": message})
        
        # 调用 API
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": MODEL_CONFIG["model"],
                    "messages": messages,
                    "max_tokens": MODEL_CONFIG["max_tokens"],
                    "temperature": MODEL_CONFIG["temperature"]
                }
                
                if tools:
                    payload["tools"] = tools
                    payload["tool_choice"] = "auto"
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                async with session.post(
                    f"{MODEL_CONFIG['base_url']}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        return {
                            "content": f"API 错误 (状态码 {resp.status}): {error_text[:200]}",
                            "tool_calls": None
                        }
                    
                    result = await resp.json()
                    
                    if "choices" not in result or not result["choices"]:
                        return {
                            "content": "模型返回空响应",
                            "tool_calls": None
                        }
                    
                    choice = result["choices"][0]
                    assistant_message = choice.get("message", {})
                    
                    # 获取内容（支持 reasoning 模式）
                    content = assistant_message.get("content")
                    if not content:
                        # 尝试从 reasoning 字段获取
                        content = assistant_message.get("reasoning", "")
                        # 只取第一句话，避免推理过程过长
                        if content:
                            content = content.split('\n')[0][:200]
                    
                    # 更新对话历史
                    self.conversation_history.append({"role": "user", "content": message})
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": content or "无响应"
                    })
                    
                    # 限制历史长度
                    if len(self.conversation_history) > self.max_history * 2:
                        self.conversation_history = self.conversation_history[-self.max_history * 2:]
                    
                    return {
                        "content": content or "无响应内容",
                        "tool_calls": assistant_message.get("tool_calls")
                    }
                    
        except asyncio.TimeoutError:
            return {"content": "⏱️ 模型调用超时", "tool_calls": None}
        except Exception as e:
            return {"content": f"❌ 调用错误: {str(e)}", "tool_calls": None}
    
    async def quick_chat(self, message: str) -> str:
        """快速对话，仅返回文本"""
        result = await self.chat(message)
        return result.get("content", "无响应")
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
        return "对话历史已清空"

# 便捷函数
async def ask_nanobot(message: str) -> str:
    """向 Nanobot 提问"""
    bot = NanobotAI()
    return await bot.quick_chat(message)

if __name__ == "__main__":
    # 测试
    import asyncio
    
    async def test():
        bot = NanobotAI()
        
        print("🤖 Nanobot AI 测试")
        print("-" * 40)
        
        # 测试对话
        questions = [
            "你好，请介绍一下你自己",
            "你能做什么任务？"
        ]
        
        for q in questions:
            print(f"\n👤 用户: {q}")
            response = await bot.quick_chat(q)
            print(f"🤖 Nanobot: {response}")
    
    asyncio.run(test())
