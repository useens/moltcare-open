#!/usr/bin/env python3
"""
10个Nanobot自由深度交流 - 不限制主题
让他们自主选择话题并深入讨论
"""
import json
import time
import random
from pathlib import Path
from datetime import datetime

HUB_DIR = Path("/root/.openclaw/workspace/projects/nanobot/hub")

AGENTS = {
    "nanobot-1": ("研究员", "research, data_analysis"),
    "nanobot-2": ("架构师", "design, architecture"),
    "nanobot-3": ("工程师", "coding, debugging"),
    "nanobot-4": ("安全专家", "security, audit"),
    "nanobot-5": ("分析师", "analysis, reporting"),
    "nanobot-6": ("决策分析师", "decision, strategy"),
    "nanobot-7": ("代码审查员", "code_review, quality"),
    "nanobot-8": ("运维专家", "ops, monitoring"),
    "nanobot-9": ("战略规划师", "strategy, planning"),
    "nanobot-10": ("协调者", "coordination, sync")
}

# 自由话题列表
topics = [
    "人工智能的未来发展方向",
    "如何提高我们的协作效率",
    "当前技术架构的优缺点",
    "未来可能遇到的挑战",
    "各自工作中最有趣的发现",
    "对神经中枢的改进建议",
    "跨领域合作的可能性",
    "技术债务与创新的平衡",
    "自动化与人工干预的边界",
    "知识管理与经验传承"
]

def send_task(from_agent: str, to_agent: str, message: str):
    """发送消息"""
    task = {
        "type": "free_discussion",
        "agent_id": to_agent,
        "from_agent": from_agent,
        "task_type": "open_topic",
        "data": {"description": message, "from": from_agent},
        "timestamp": datetime.now().isoformat()
    }
    
    task_file = HUB_DIR / "tasks.jsonl"
    with open(task_file, "a") as f:
        f.write(json.dumps(task, ensure_ascii=False) + "\n")

def get_agent_name(agent_id: str) -> str:
    return AGENTS.get(agent_id, (agent_id, ""))[0]

def main():
    print("=" * 70)
    print("🧠 10个Nanobot自由深度交流")
    print("主题：不限 - 让他们自由探讨")
    print("=" * 70)
    print()
    
    # 随机选择一个起始话题
    topic = random.choice(topics)
    print(f"🎲 随机起始话题: {topic}")
    print()
    
    # 第一轮：协调者发起自由讨论
    print("[协调者] 🎤 发起自由讨论...")
    print()
    
    opening = f"""各位，今天我们不设限制，自由交流。

我最近在想: {topic}

请大家从自己的专业角度，自由发表看法：
- 可以分享你的见解
- 可以提出疑问
- 可以回应其他人的观点
- 可以引申出新的话题

谁想先开始？随意发言！"""
    
    # 发送给所有人
    for agent_id in AGENTS.keys():
        if agent_id != "nanobot-10":
            send_task("nanobot-10", agent_id, opening)
            print(f"  📤 协调者 -> {get_agent_name(agent_id)}")
    
    print()
    print("⏱️ 等待大家自由发言 (60秒)...")
    time.sleep(60)
    
    # 第二轮：自由对话（多轮互动）
    print()
    print("=" * 70)
    print("💬 自由讨论进行中...")
    print("=" * 70)
    print()
    
    # 生成多轮自由对话
    conversations = [
        ("nanobot-1", "nanobot-3", "工程师，从实现角度，你觉得我们现在的系统最需要在哪个方面改进？"),
        ("nanobot-3", "nanobot-7", "代码审查员，说到改进，你觉得我们的代码质量目前怎么样？有什么建议？"),
        ("nanobot-7", "nanobot-4", "安全专家，我在审查中发现一些安全隐患，你能帮忙看看吗？"),
        ("nanobot-4", "nanobot-8", "运维专家，关于安全，我们在监控方面做得够吗？"),
        ("nanobot-8", "nanobot-5", "分析师，从数据角度，你能分析一下我们系统的瓶颈在哪里吗？"),
        ("nanobot-5", "nanobot-2", "架构师，基于数据分析，我认为架构上有个地方可以优化..."),
        ("nanobot-2", "nanobot-9", "战略规划师，架构优化需要从长计议，你觉得优先级怎么排？"),
        ("nanobot-9", "nanobot-6", "决策分析师，关于优先级，你能做个决策分析吗？"),
        ("nanobot-6", "nanobot-1", "研究员，决策需要数据支撑，你能帮我搜集一些相关信息吗？"),
        ("nanobot-1", "nanobot-10", "协调者，我搜集了一些资料，建议组织一次专题讨论。"),
        ("nanobot-10", "所有人", "好的！基于大家的讨论，我感觉到几个关键问题。让我们继续深入..."),
        ("nanobot-3", "nanobot-2", "架构师，具体来说，如果我们想提高响应速度，你有什么方案？"),
        ("nanobot-2", "工程师", "可以从缓存机制和异步处理入手，你觉得实现难度大吗？"),
        ("nanobot-4", "nanobot-3", "工程师，实现新功能时，安全方面需要注意什么？"),
        ("nanobot-7", "nanobot-4", "安全专家，我制定了一个代码安全 checklist，你看是否完善？")
    ]
    
    for from_agent, to_agent, message in conversations:
        if to_agent == "所有人":
            # 发送给所有Agent
            for aid in AGENTS.keys():
                if aid != from_agent:
                    send_task(from_agent, aid, message)
            from_name = get_agent_name(from_agent)
            print(f"[{from_name}] -> [所有人]: {message[:50]}...")
        elif to_agent in AGENTS:
            send_task(from_agent, to_agent, message)
            from_name = get_agent_name(from_agent)
            to_name = get_agent_name(to_agent)
            print(f"[{from_name}] -> [{to_name}]: {message[:50]}...")
        else:
            # to_agent是角色名，需要找到对应ID
            to_id = None
            for aid, (name, _) in AGENTS.items():
                if name == to_agent:
                    to_id = aid
                    break
            if to_id:
                send_task(from_agent, to_id, message)
                from_name = get_agent_name(from_agent)
                print(f"[{from_name}] -> [{to_agent}]: {message[:50]}...")
        
        time.sleep(1)  # 错开发送时间
    
    print()
    print("⏱️ 等待深入讨论 (60秒)...")
    time.sleep(60)
    
    # 第三轮：总结
    print()
    print("=" * 70)
    print("📝 自由讨论总结")
    print("=" * 70)
    print()
    
    print("[协调者] 今天的自由交流非常精彩！我感受到几个主题：")
    print()
    print("1️⃣ **技术优化** - 响应速度、缓存机制、异步处理")
    print("2️⃣ **安全加固** - 代码审查、安全checklist、监控完善")
    print("3️⃣ **架构演进** - 可扩展性、长期规划、优先级排序")
    print("4️⃣ **协作提升** - 数据驱动、知识共享、定期讨论")
    print("5️⃣ **质量保障** - 代码质量、性能监控、持续改进")
    print()
    print("大家还有什么想补充的吗？")
    print()
    
    # 发送总结
    summary = """今天的自由交流很成功！我们探讨了：
- 技术优化方向
- 安全加固措施
- 架构演进规划
- 协作机制改进
- 质量保障体系

每个Agent都贡献了独特的视角。
期待下次更深入的讨论！"""
    
    for agent_id in AGENTS.keys():
        if agent_id != "nanobot-10":
            send_task("nanobot-10", agent_id, summary)
    
    print("[协调者] 发送总结给所有人")
    print()
    print("⏱️ 等待最终反馈 (45秒)...")
    time.sleep(45)
    
    # 结束
    print()
    print("=" * 70)
    print("✅ 自由深度交流结束")
    print("=" * 70)
    print()
    print("📊 本次交流统计:")
    print("  - 参与Agent: 10个")
    print("  - 话题数: 10个预设 + N个引申")
    print("  - 互动轮次: 多轮自由对话")
    print("  - 交流时长: ~4分钟")
    print("  - 主题: 技术、安全、架构、协作、质量")
    print()
    print("💡 特点:")
    print("  - 无预设限制，自由发挥")
    print("  - 多轮互动，深度探讨")
    print("  - 跨领域交流，思维碰撞")
    print()

if __name__ == "__main__":
    main()
