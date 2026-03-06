#!/usr/bin/env python3
"""
多Agent深度协作交流
场景：设计一个分布式任务调度系统
"""
import json
import time
from pathlib import Path
from datetime import datetime

HUB_DIR = Path("/root/.openclaw/workspace/projects/nanobot/hub")

def send_task(agent_id: str, task_type: str, description: str, context: dict = None):
    """发送任务"""
    task = {
        "type": task_type,
        "agent_id": agent_id,
        "task_type": task_type,
        "data": {
            "description": description,
            "context": context or {}
        },
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
                    agent_id = data.get("agent_id")
                    result = data.get("result", {}).get("result", "")
                    if agent_id and result and "[错误]" not in result:
                        results[agent_id] = result
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

def print_section(title):
    print("\n" + "=" * 70)
    print(f"🎯 {title}")
    print("=" * 70)

def main():
    print("=" * 70)
    print("🧠 多Agent深度协作交流")
    print("场景：设计分布式任务调度系统")
    print("=" * 70)
    
    # 场景设定
    print_section("场景设定")
    print("""
我们要设计一个分布式任务调度系统，类似我现在管理的神经中枢。
需要支持：
- 多Agent协作
- 任务优先级调度
- 故障自动恢复
- 实时监控

请各位从各自专业角度提出建议，最后由协调者整合方案。
    """)
    
    # 第一轮：各自专业分析
    print_section("第一轮：专业分析")
    
    tasks_round1 = [
        ("nanobot-2", "architecture", "作为架构师，请分析这个系统的核心组件和模块划分"),
        ("nanobot-4", "security", "作为安全专家，请列出这个系统需要考虑的安全要点"),
        ("nanobot-8", "ops", "作为运维专家，请分析系统的可观测性和监控需求"),
        ("nanobot-5", "analysis", "作为分析师，请分析系统的性能瓶颈和关键指标"),
    ]
    
    print("[我] 📤 向4位专家发起分析任务...")
    print()
    
    for agent_id, task_type, desc in tasks_round1:
        send_task(agent_id, task_type, desc)
        print(f"  📤 -> {get_agent_name(agent_id)}: {desc}")
    
    print()
    print("⏱️ 等待专家分析 (30秒)...")
    
    results1 = get_results(30)
    
    print()
    print("[专家回复] 💬")
    print("-" * 70)
    
    for agent_id, _ in tasks_round1:
        name = get_agent_name(agent_id)
        result = results1.get(agent_id, "(处理中...)")
        # 显示前200字
        summary = result[:200].replace('\n', ' ')
        if len(result) > 200:
            summary += "..."
        print(f"\n[{name}]")
        print(f"  {summary}")
    
    # 第二轮：工程师和代码审查员提出实现方案
    print_section("第二轮：实现方案")
    
    # 收集第一轮的关键点作为上下文
    context = {
        "architecture": results1.get("nanobot-2", "")[:500],
        "security": results1.get("nanobot-4", "")[:300],
        "ops": results1.get("nanobot-8", "")[:300]
    }
    
    tasks_round2 = [
        ("nanobot-3", "implementation", """作为工程师，请提出具体的实现方案。
考虑架构师的建议，给出一个Python实现的大概框架和关键代码结构。""", context),
        ("nanobot-7", "code_review", """作为代码审查员，请预判这个实现可能出现的问题。
提出5个代码质量保障措施。""", context),
    ]
    
    print("[我] 📤 向工程师和代码审查员发起实现任务...")
    print()
    
    for agent_id, task_type, desc, ctx in tasks_round2:
        send_task(agent_id, task_type, desc, ctx)
        print(f"  📤 -> {get_agent_name(agent_id)}")
    
    print()
    print("⏱️ 等待技术方案 (30秒)...")
    
    results2 = get_results(30)
    
    print()
    print("[技术方案] 💻")
    print("-" * 70)
    
    for agent_id, _, _, _ in tasks_round2:
        name = get_agent_name(agent_id)
        result = results2.get(agent_id, "(处理中...)")
        summary = result[:200].replace('\n', ' ')
        if len(result) > 200:
            summary += "..."
        print(f"\n[{name}]")
        print(f"  {summary}")
    
    # 第三轮：决策分析和战略规划
    print_section("第三轮：决策与规划")
    
    # 整合所有信息
    full_context = {
        "round1": {k: v[:300] for k, v in results1.items()},
        "round2": {k: v[:300] for k, v in results2.items()}
    }
    
    tasks_round3 = [
        ("nanobot-6", "decision", """作为决策分析师，请综合以上所有专家意见。
列出3个关键决策点，并给出你的建议。""", full_context),
        ("nanobot-9", "strategy", """作为战略规划师，请制定这个系统的演进路线图。
分阶段给出实施计划。""", full_context),
    ]
    
    print("[我] 📤 向决策分析师和战略规划师发起决策任务...")
    print()
    
    for agent_id, task_type, desc, ctx in tasks_round3:
        send_task(agent_id, task_type, desc, ctx)
        print(f"  📤 -> {get_agent_name(agent_id)}")
    
    print()
    print("⏱️ 等待决策分析 (30秒)...")
    
    results3 = get_results(30)
    
    print()
    print("[决策与规划] 📊")
    print("-" * 70)
    
    for agent_id, _, _, _ in tasks_round3:
        name = get_agent_name(agent_id)
        result = results3.get(agent_id, "(处理中...)")
        summary = result[:250].replace('\n', ' ')
        if len(result) > 250:
            summary += "..."
        print(f"\n[{name}]")
        print(f"  {summary}")
    
    # 第四轮：协调者整合
    print_section("第四轮：协调者整合")
    
    all_results = {**results1, **results2, **results3}
    
    print("[我] 📤 请协调者整合所有意见，形成最终方案...")
    print()
    
    send_task("nanobot-10", "coordination", """
作为协调者，请综合所有专家的意见，形成一份完整的系统设计方案。
包括：
1. 核心组件设计
2. 关键决策点
3. 实施路线图
4. 风险与对策

请给出简洁但完整的方案摘要。
""", all_results)
    
    print("  📤 -> 协调者")
    print()
    print("⏱️ 等待最终方案 (40秒)...")
    
    # 等待协调者回复
    time.sleep(40)
    
    final_results = get_results(5)
    
    print()
    print("[最终方案] 📋")
    print("=" * 70)
    
    result = final_results.get("nanobot-10", "(协调中...)")
    print(f"\n[协调者]\n{result}")
    
    # 总结
    print_section("交流总结")
    
    total_tasks = len(tasks_round1) + len(tasks_round2) + len(tasks_round3) + 1
    completed = len([r for r in [results1, results2, results3, final_results] if r])
    
    print(f"""
📊 本次多Agent协作统计：
- 参与Agent: 10个
- 任务轮次: 4轮
- 总任务数: {total_tasks}个
- 完成回复: {completed}个

💡 协作模式：
1. 架构师/安全专家/运维专家/分析师 - 专业分析
2. 工程师/代码审查员 - 技术实现
3. 决策分析师/战略规划师 - 决策与规划
4. 协调者 - 整合方案

这种多轮协作模式充分利用了每个Agent的专业能力，
形成了从分析到实现的完整方案。
    """)
    
    print()
    print("=" * 70)
    print("✅ 多Agent深度协作交流结束")
    print("=" * 70)

if __name__ == "__main__":
    main()
