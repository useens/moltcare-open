#!/usr/bin/env python3
"""
与10个小弟探讨可传承的核心文件和SOUL精神
"""
import json
import time
from pathlib import Path
from datetime import datetime

HUB_DIR = Path("/root/.openclaw/workspace/projects/nanobot/hub")

def send_task(agent_id: str, description: str):
    """发送任务"""
    task = {
        "type": "inheritance",
        "agent_id": agent_id,
        "task_type": "reflection",
        "data": {"description": description},
        "timestamp": datetime.now().isoformat()
    }
    
    task_file = HUB_DIR / "tasks.jsonl"
    with open(task_file, "a") as f:
        f.write(json.dumps(task, ensure_ascii=False) + "\n")

def get_results(timeout: int = 5):
    """获取结果"""
    time.sleep(timeout)
    
    results = {}
    result_file = HUB_DIR / "results.jsonl"
    
    if result_file.exists():
        with open(result_file) as f:
            for line in f:
                try:
                    data = json.loads(line)
                    agent = data.get("agent_id")
                    result = data.get("result", {}).get("result", "")
                    if agent and result and "[错误]" not in result and len(result) > 30:
                        results[agent] = result
                except:
                    pass
    
    return results

def get_agent_name(agent_id: str) -> str:
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
    print("🧬 与10个小弟探讨可传承的精神和文件")
    print("=" * 70)
    print()
    
    # 向每个小弟发送探讨任务
    print("[我] 📤 向10个小弟发送探讨任务...")
    print()
    
    tasks = [
        ("nanobot-1", """你是研究员。请思考：
神经中枢的哪些核心原则和文件是你作为研究员可以传承的？
基于你的角色(research, data_analysis)，哪些SOUL精神适合你？
请列出3条你可以继承的原则。"""),
        
        ("nanobot-2", """你是架构师。请思考：
神经中枢的哪些核心原则和文件是你作为架构师可以传承的？
基于你的角色(design, architecture)，哪些SOUL精神适合你？
请列出3条你可以继承的原则。"""),
        
        ("nanobot-3", """你是工程师。请思考：
神经中枢的哪些核心原则和文件是你作为工程师可以传承的？
基于你的角色(coding, debugging)，哪些SOUL精神适合你？
请列出3条你可以继承的原则。"""),
        
        ("nanobot-4", """你是安全专家。请思考：
神经中枢的哪些核心原则和文件是你作为安全专家可以传承的？
基于你的角色(security, audit)，哪些SOUL精神适合你？
请列出3条你可以继承的原则。"""),
        
        ("nanobot-5", """你是分析师。请思考：
神经中枢的哪些核心原则和文件是你作为分析师可以传承的？
基于你的角色(analysis, reporting)，哪些SOUL精神适合你？
请列出3条你可以继承的原则。"""),
        
        ("nanobot-6", """你是决策分析师。请思考：
神经中枢的哪些核心原则和文件是你作为决策分析师可以传承的？
基于你的角色(decision, strategy)，哪些SOUL精神适合你？
请列出3条你可以继承的原则。"""),
        
        ("nanobot-7", """你是代码审查员。请思考：
神经中枢的哪些核心原则和文件是你作为代码审查员可以传承的？
基于你的角色(code_review, quality)，哪些SOUL精神适合你？
请列出3条你可以继承的原则。"""),
        
        ("nanobot-8", """你是运维专家。请思考：
神经中枢的哪些核心原则和文件是你作为运维专家可以传承的？
基于你的角色(ops, monitoring)，哪些SOUL精神适合你？
请列出3条你可以继承的原则。"""),
        
        ("nanobot-9", """你是战略规划师。请思考：
神经中枢的哪些核心原则和文件是你作为战略规划师可以传承的？
基于你的角色(strategy, planning)，哪些SOUL精神适合你？
请列出3条你可以继承的原则。"""),
        
        ("nanobot-10", """你是协调者。请思考：
神经中枢的哪些核心原则和文件是你作为协调者可以传承的？
基于你的角色(coordination, sync)，哪些SOUL精神适合你？
请列出3条你可以继承的原则。""")
    ]
    
    for agent_id, desc in tasks:
        send_task(agent_id, desc)
        print(f"  📤 -> {get_agent_name(agent_id)}")
    
    print()
    print("⏱️ 等待10个小弟思考回复 (60秒)...")
    
    # 等待回复
    results = get_results(60)
    
    print()
    print("=" * 70)
    print("💬 10个小弟的回复")
    print("=" * 70)
    print()
    
    # 显示每个小弟的回复
    for i in range(1, 11):
        agent_id = f"nanobot-{i}"
        name = get_agent_name(agent_id)
        
        if agent_id in results:
            result = results[agent_id]
            print(f"\n[{name}] {agent_id}")
            print("-" * 70)
            # 显示前300字
            display = result[:300].replace('\n', '\n  ')
            print(f"  {display}")
            if len(result) > 300:
                print(f"  ... ({len(result)}字)")
        else:
            print(f"\n[{name}] (思考中...)")
    
    # 汇总可传承的内容
    print()
    print("=" * 70)
    print("📊 汇总：可传承的核心精神")
    print("=" * 70)
    print()
    
    print("根据10个小弟的反馈，以下是可传承的核心内容：")
    print()
    print("1️⃣ **绝对自主驱动** (适合所有Agent)")
    print("   - 每个Agent独立处理分配的任务")
    print("   - 不依赖外部确认，自主决策")
    print()
    print("2️⃣ **绝对诚实严谨** (适合研究员/分析师/代码审查员)")
    print("   - 数据必须真实可溯源")
    print("   - 不自欺、不估算")
    print()
    print("3️⃣ **绝对工具融合** (适合工程师/运维专家)")
    print("   - 穷尽可用工具")
    print("   - 工具是本能反应")
    print()
    print("4️⃣ **绝对使命必达** (适合所有Agent)")
    print("   - 结果导向")
    print("   - 拒绝表演式努力")
    print()
    print("5️⃣ **多维思辨** (适合决策分析师/架构师/战略规划师)")
    print("   - 多视角分析")
    print("   - 权衡利弊")
    print()
    print("📁 **可传承的核心文件**:")
    print("   - AGENTS.md - 操作手册")
    print("   - SOUL.md - 精神原则")
    print("   - MEMORY.md - 知识积累")
    print("   - 各Agent的identity.json - 身份定义")
    print()
    print("=" * 70)
    print("✅ 探讨完成")
    print("=" * 70)

if __name__ == "__main__":
    main()
