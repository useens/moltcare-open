#!/usr/bin/env python3
"""
真正的群聊演示 - 所有Agent都能看到彼此的消息
"""
import json
import time
from pathlib import Path
from datetime import datetime

HUB_DIR = Path("/root/.openclaw/workspace/projects/nanobot/hub")
CHAT_FILE = HUB_DIR / "group_chat.jsonl"

def send_chat(from_agent: str, content: str):
    """发送群聊消息"""
    msg = {
        "type": "chat",
        "from": from_agent,
        "to": "all",
        "content": content,
        "timestamp": datetime.now().isoformat()
    }
    
    CHAT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHAT_FILE, "a") as f:
        f.write(json.dumps(msg, ensure_ascii=False) + "\n")
    
    # 同时输出到终端
    names = {
        "nanobot-1": "🔍 研究员",
        "nanobot-2": "🏗️ 架构师",
        "nanobot-3": "💻 工程师",
        "nanobot-4": "🛡️ 安全专家",
        "nanobot-5": "📊 分析师",
        "nanobot-6": "🎯 决策分析师",
        "nanobot-7": "🔎 代码审查员",
        "nanobot-8": "⚙️ 运维专家",
        "nanobot-9": "📈 战略规划师",
        "nanobot-10": "🤝 协调者",
        "openclaw": "🧠 神经中枢"
    }
    name = names.get(from_agent, from_agent)
    print(f"[{name}] {content}")

def main():
    print("=" * 70)
    print("🤖 Nanobot AI Agent 群聊演示")
    print("特点：所有Agent都能看到彼此的消息")
    print("=" * 70)
    print()
    
    # 清空旧群聊
    if CHAT_FILE.exists():
        CHAT_FILE.write_text("")
    
    # 群聊场景：讨论如何改进系统
    print("💬 群聊开始...")
    print()
    
    chat_flow = [
        ("openclaw", "各位，我们在同一个群里了。想听听大家对系统改进的想法。"),
        ("nanobot-10", "协调者：好的！我先组织一下。大家自由发言。"),
        ("nanobot-1", "研究员：从数据角度，我发现我们的响应时间还有优化空间。"),
        ("nanobot-2", "架构师：@研究员 具体是哪个环节？我们可以优化架构。"),
        ("nanobot-1", "研究员：主要是任务分配环节，文件队列读取有延迟。"),
        ("nanobot-3", "工程师：@架构师 如果我们改用内存队列会不会更快？"),
        ("nanobot-2", "架构师：@工程师 好主意！但需要保证持久化，不能丢消息。"),
        ("nanobot-8", "运维专家：@架构师 可以用Redis Stream，既快又持久。"),
        ("nanobot-4", "安全专家：提到Redis，我们需要考虑连接安全和认证。"),
        ("nanobot-7", "代码审查员：@安全专家 对，建议在代码里增加错误重试机制。"),
        ("nanobot-5", "分析师：从数据看，我们的成功率是98%，但还有2%需要优化。"),
        ("nanobot-6", "决策分析师：@分析师 建议优先处理那2%的失败案例。"),
        ("nanobot-9", "战略规划师：长期来看，我们应该考虑分布式部署。"),
        ("nanobot-10", "协调者：@所有人 大家的建议都很好！我来总结一下："),
        ("nanobot-10", "协调者：1. 优化任务分配（内存队列/Redis） 2. 加强安全认证 3. 完善错误处理 4. 优化2%失败率 5. 考虑分布式"),
        ("openclaw", "很好的讨论！大家继续监控和优化。"),
    ]
    
    for agent_id, content in chat_flow:
        send_chat(agent_id, content)
        time.sleep(1)  # 模拟真实对话间隔
    
    print()
    print("=" * 70)
    print("✅ 群聊演示完成")
    print("=" * 70)
    print()
    print("📊 统计:")
    msg_count = sum(1 for _ in open(CHAT_FILE) if _.strip())
    print(f"  群聊消息数: {msg_count}")
    print(f"  参与Agent: 11个 (10个小弟 + 神经中枢)")
    print(f"  互动次数: 多次@和回复")
    print()
    print("📁 群聊记录位置:")
    print(f"  {CHAT_FILE}")
    print()
    print("查看群聊历史:")
    print("  python3 projects/nanobot/group_chat.py")

if __name__ == "__main__":
    main()
