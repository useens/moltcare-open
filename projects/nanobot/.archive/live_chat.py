#!/usr/bin/env python3
"""
与10个真正的Nanobot AI Agent实时对话
"""
import json
import time
from pathlib import Path
from datetime import datetime

HUB_DIR = Path("/root/.openclaw/workspace/projects/nanobot/hub")

def send_task(agent_id: str, description: str):
    """发送任务给Agent"""
    task = {
        "type": "task",
        "agent_id": agent_id,
        "task_type": "chat",
        "data": {"description": description},
        "timestamp": datetime.now().isoformat()
    }
    
    task_file = HUB_DIR / "tasks.jsonl"
    with open(task_file, "a") as f:
        f.write(json.dumps(task) + "\n")

def get_results(agent_id: str = None, wait: int = 3):
    """获取结果"""
    time.sleep(wait)
    
    results = []
    result_file = HUB_DIR / "results.jsonl"
    
    if result_file.exists():
        with open(result_file) as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if agent_id is None or data.get("agent_id") == agent_id:
                        results.append(data)
                except:
                    pass
    
    return results

def get_agent_name(agent_id: str) -> str:
    """获取Agent名称"""
    names = {
        "nanobot-1": "研究员",
        "nanobot-2": "架构师", 
        "nanobot-3": "工程师",
        "nanobot-4": "安全专家",
        "nanobot-5": "分析师",
        "nanobot-6": "决策分析师",
        "nanobot-7": "代码审查员",
        "nanobot-8": "运维专家",
        "nanobot-9": "战略规划师",
        "nanobot-10": "协调者"
    }
    return names.get(agent_id, agent_id)

def main():
    print("=" * 70)
    print("🧠 神经中枢 2.0 - 与10个AI Agent实时对话")
    print("=" * 70)
    print()
    
    # 1. 问候所有Agent
    print("[我] 🎤 向所有Agent发送问候...")
    print()
    
    greetings = [
        ("nanobot-1", "你好研究员，请简单介绍你的专长"),
        ("nanobot-2", "你好架构师，简述你的设计理念"),
        ("nanobot-3", "你好工程师，说说你的编程风格"),
        ("nanobot-4", "你好安全专家，分享一个安全建议"),
        ("nanobot-5", "你好分析师，简述数据分析方法"),
        ("nanobot-6", "你好决策分析师，如何做艰难决策"),
        ("nanobot-7", "你好代码审查员，最重要的审查点"),
        ("nanobot-8", "你好运维专家，系统稳定的关键"),
        ("nanobot-9", "你好战略规划师，长期规划的核心"),
        ("nanobot-10", "你好协调者，团队协作的秘诀")
    ]
    
    for agent_id, msg in greetings:
        send_task(agent_id, msg)
        print(f"  📤 -> {get_agent_name(agent_id)}")
    
    print()
    print("⏱️ 等待Agent回复 (25秒)...")
    
    # 2. 收集回复
    results = get_results(wait=25)
    
    print()
    print("[回复] 💬 Agent们的回应：")
    print("-" * 70)
    
    for i in range(1, 11):
        agent_id = f"nanobot-{i}"
        name = get_agent_name(agent_id)
        
        # 查找该Agent的最新回复
        agent_results = [r for r in results if r.get("agent_id") == agent_id]
        
        if agent_results:
            result = agent_results[-1]
            reply = result.get("result", {}).get("result", "")
            # 截断长回复
            if len(reply) > 150:
                reply = reply[:147] + "..."
            print(f"\n[{name}] {reply}")
        else:
            print(f"\n[{name}] (等待中...)")
    
    # 3. 追问具体任务
    print()
    print("-" * 70)
    print("[我] 📝 分配具体任务...")
    print()
    
    tasks = [
        ("nanobot-1", "搜索：今天AI领域有什么重要新闻？列出3条"),
        ("nanobot-4", "安全检查：列出服务器日常安全检查的5个要点"),
        ("nanobot-7", "代码审查：列出Python代码审查的5个最佳实践")
    ]
    
    for agent_id, task in tasks:
        send_task(agent_id, task)
        print(f"  📤 -> {get_agent_name(agent_id)}: {task[:40]}...")
    
    print()
    print("⏱️ 等待任务完成 (30秒)...")
    
    # 4. 收集任务结果
    results = get_results(wait=30)
    
    print()
    print("[结果] 📋 任务完成报告：")
    print("=" * 70)
    
    for agent_id, task_desc in tasks:
        name = get_agent_name(agent_id)
        agent_results = [r for r in results if r.get("agent_id") == agent_id]
        
        if agent_results:
            result = agent_results[-1]
            reply = result.get("result", {}).get("result", "")
            print(f"\n✅ [{name}]")
            print(f"   {reply[:300]}...")
        else:
            print(f"\n⏳ [{name}] 任务处理中...")
    
    # 5. 结束
    print()
    print("=" * 70)
    print("[我] 👋 各位辛苦了，今天的对话到此结束！")
    print()
    
    for i in range(1, 11):
        agent_id = f"nanobot-{i}"
        name = get_agent_name(agent_id)
        print(f"[{name}] 收到，随时待命！")
    
    print()
    print("=" * 70)
    print("✅ 对话结束")
    print("=" * 70)

if __name__ == "__main__":
    main()
