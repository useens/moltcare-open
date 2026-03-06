#!/usr/bin/env python3
"""
与10个真正的Nanobot AI Agent对话
"""
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime

HUB_DIR = Path("/root/.openclaw/workspace/projects/nanobot/hub")
WORKSPACE = Path("/root/.openclaw/workspace")

class NeuralHubInterface:
    """神经中枢接口 - 与真正运行的Nanobot通信"""
    
    def __init__(self):
        self.agents = self._load_agents()
        
    def _load_agents(self):
        """加载Agent信息"""
        agents = {}
        reg_file = HUB_DIR / "registrations.jsonl"
        
        if reg_file.exists():
            with open(reg_file) as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if data.get("type") == "register":
                            agent_id = data.get("agent_id")
                            agents[agent_id] = data
                    except:
                        pass
        return agents
    
    def send_task(self, agent_id: str, task_type: str, task_data: dict):
        """发送任务给Agent"""
        task = {
            "type": "task",
            "agent_id": agent_id,
            "task_type": task_type,
            "data": task_data,
            "timestamp": datetime.now().isoformat()
        }
        
        # 写入任务队列
        task_file = HUB_DIR / "tasks.jsonl"
        task_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(task_file, "a") as f:
            f.write(json.dumps(task) + "\n")
        
        print(f"  📤 已发送任务给 [{agent_id}]: {task_type}")
        return task
    
    def check_results(self):
        """检查结果"""
        results = []
        result_file = HUB_DIR / "results.jsonl"
        
        if result_file.exists():
            with open(result_file) as f:
                lines = f.readlines()
                # 只取最近的结果
                for line in lines[-20:]:
                    try:
                        data = json.loads(line)
                        results.append(data)
                    except:
                        pass
        
        return results
    
    def get_agent_status(self, agent_id: str):
        """获取Agent状态"""
        # 检查心跳
        hb_file = HUB_DIR / "heartbeat.jsonl"
        last_hb = None
        
        if hb_file.exists():
            with open(hb_file) as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if data.get("agent_id") == agent_id:
                            last_hb = data.get("timestamp")
                    except:
                        pass
        
        return {
            "agent_id": agent_id,
            "registered": agent_id in self.agents,
            "last_heartbeat": last_hb
        }

def main():
    print("=" * 70)
    print("🧠 神经中枢 2.0 - 与10个真正的AI Agent对话")
    print("=" * 70)
    print()
    
    hub = NeuralHubInterface()
    
    # 1. 检查Agent状态
    print("[1] 📊 检查Agent状态...")
    print()
    
    for i in range(1, 11):
        agent_id = f"nanobot-{i}"
        status = hub.get_agent_status(agent_id)
        agent_info = hub.agents.get(agent_id, {})
        
        if status["registered"]:
            name = agent_info.get("name", agent_id)
            hb = "💓" if status["last_heartbeat"] else "💔"
            print(f"   {hb} {agent_id:12s} | {name:10s} | 已注册")
        else:
            print(f"   💔 {agent_id:12s} | 未注册")
    
    print()
    
    # 2. 广播问候
    print("[2] 🎤 向所有Agent广播问候...")
    print()
    
    for i in range(1, 11):
        agent_id = f"nanobot-{i}"
        agent_info = hub.agents.get(agent_id, {})
        name = agent_info.get("name", agent_id)
        
        # 发送问候任务
        hub.send_task(agent_id, "greeting", {
            "message": f"你好{name}，请介绍一下你的能力和当前状态"
        })
    
    print()
    print("   ⏱️ 等待Agent响应 (10秒)...")
    time.sleep(10)
    
    # 3. 分配具体任务
    print()
    print("[3] 📝 分配具体任务...")
    print()
    
    tasks = [
        ("nanobot-1", "research", "搜索今天AI领域的3条重要新闻"),
        ("nanobot-4", "security", "检查系统安全状态，列出3个安全检查项"),
        ("nanobot-7", "code_review", "列出代码审查的5个最佳实践"),
        ("nanobot-2", "architecture", "设计一个微服务架构的核心组件"),
        ("nanobot-9", "strategy", "制定下周工作计划的关键要素"),
    ]
    
    for agent_id, task_type, description in tasks:
        agent_info = hub.agents.get(agent_id, {})
        name = agent_info.get("name", agent_id)
        
        hub.send_task(agent_id, task_type, {
            "description": description
        })
    
    print()
    print("   ⏱️ 等待Agent执行任务 (30秒)...")
    time.sleep(30)
    
    # 4. 收集结果
    print()
    print("[4] 📋 收集任务结果...")
    print()
    
    results = hub.check_results()
    
    # 按Agent分组显示结果
    for i in range(1, 11):
        agent_id = f"nanobot-{i}"
        agent_info = hub.agents.get(agent_id, {})
        name = agent_info.get("name", agent_id)
        
        # 查找该Agent的结果
        agent_results = [r for r in results if r.get("agent_id") == agent_id]
        
        if agent_results:
            print(f"   ✅ [{name}]")
            for result in agent_results[-2:]:  # 只显示最近2个
                task_type = result.get("task_type", "unknown")
                result_data = result.get("result", {})
                result_text = result_data.get("result", "")[:100]
                print(f"      {task_type}: {result_text}...")
            print()
        else:
            print(f"   ⏳ [{name}] - 等待结果...")
    
    # 5. 总结
    print()
    print("[5] 🎯 对话总结")
    print()
    print(f"   活跃Agent: {len(hub.agents)} 个")
    print(f"   收到结果: {len(results)} 条")
    print(f"   系统状态: 运行正常")
    
    print()
    print("=" * 70)
    print("✅ 对话结束")
    print("=" * 70)

if __name__ == "__main__":
    main()
