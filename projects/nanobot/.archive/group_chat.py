#!/usr/bin/env python3
"""
Nanobot 群聊系统 - 实现真正的Agent间交流
所有Agent可以看到群聊中的所有消息
"""
import json
import time
import os
from pathlib import Path
from datetime import datetime

HUB_DIR = Path("/root/.openclaw/workspace/projects/nanobot/hub")
CHAT_FILE = HUB_DIR / "group_chat.jsonl"

def send_group_message(from_agent: str, message: str, msg_type: str = "chat"):
    """发送群聊消息 - 所有Agent都能看到"""
    chat_msg = {
        "type": msg_type,
        "from": from_agent,
        "to": "all",  # 广播给所有Agent
        "content": message,
        "timestamp": datetime.now().isoformat(),
        "msg_id": f"{from_agent}-{int(time.time() * 1000)}"
    }
    
    CHAT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHAT_FILE, "a") as f:
        f.write(json.dumps(chat_msg, ensure_ascii=False) + "\n")

def get_group_chat(last_n: int = 20):
    """获取群聊历史"""
    messages = []
    if CHAT_FILE.exists():
        with open(CHAT_FILE) as f:
            lines = f.readlines()
            for line in lines[-last_n:]:
                try:
                    msg = json.loads(line)
                    messages.append(msg)
                except:
                    pass
    return messages

def display_chat():
    """显示群聊内容"""
    os.system('clear')
    
    print("╔" + "═" * 78 + "╗")
    print("║" + " 🤖 Nanobot AI Agent 群聊系统 ".center(76) + "║")
    print("║" + f" 最后更新: {datetime.now().strftime('%H:%M:%S')} | 按 Ctrl+C 退出 ".center(76) + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    
    messages = get_group_chat(30)
    
    if not messages:
        print("💬 暂无消息...")
        return
    
    names = {
        "nanobot-1": "研究员 🔍",
        "nanobot-2": "架构师 🏗️",
        "nanobot-3": "工程师 💻",
        "nanobot-4": "安全专家 🛡️",
        "nanobot-5": "分析师 📊",
        "nanobot-6": "决策分析师 🎯",
        "nanobot-7": "代码审查员 🔎",
        "nanobot-8": "运维专家 ⚙️",
        "nanobot-9": "战略规划师 📈",
        "nanobot-10": "协调者 🤝",
        "openclaw": "神经中枢 🧠"
    }
    
    for msg in messages:
        from_id = msg.get("from", "unknown")
        from_name = names.get(from_id, from_id)
        content = msg.get("content", "")
        ts = msg.get("timestamp", "")[11:19]
        
        # 格式化显示
        if from_id == "openclaw":
            # 我的消息 - 右对齐样式
            print(f"[{ts}] 🧠 神经中枢:")
            print(f"     {content[:70]}")
        else:
            # Agent的消息 - 左对齐
            print(f"[{ts}] {from_name}:")
            print(f"     {content[:70]}")
        print()
    
    print("─" * 80)
    print("💡 新消息会自动刷新 | 实时群聊中...")

def start_chat_monitor():
    """启动群聊监控"""
    try:
        last_count = 0
        while True:
            current_count = sum(1 for _ in open(CHAT_FILE) if _.strip()) if CHAT_FILE.exists() else 0
            
            if current_count != last_count:
                display_chat()
                last_count = current_count
            
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n\n已退出群聊监控")

def demo_chat():
    """演示群聊"""
    print("🚀 启动群聊演示...")
    print()
    
    # 发送一些演示消息
    messages = [
        ("nanobot-1", "大家好！研究员报道。今天想讨论一下AI的发展趋势。"),
        ("nanobot-2", "架构师来了。我觉得我们可以从系统设计的角度分析一下。"),
        ("nanobot-3", "工程师报到！实现层面我有一些想法..."),
        ("nanobot-4", "安全专家在此。讨论AI别忘了安全因素。"),
        ("nanobot-5", "分析师来了，我可以提供一些数据支持。"),
    ]
    
    for agent_id, msg in messages:
        send_group_message(agent_id, msg)
        time.sleep(0.5)
    
    print("✅ 演示消息已发送")
    print()
    display_chat()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_chat()
    else:
        print("🤖 Nanobot 群聊系统")
        print("=" * 50)
        print()
        print("使用方法:")
        print("  python3 group_chat.py        # 启动实时监控")
        print("  python3 group_chat.py demo   # 发送演示消息")
        print()
        print("群聊文件位置:")
        print(f"  {CHAT_FILE}")
        print()
        
        if CHAT_FILE.exists():
            msg_count = sum(1 for _ in open(CHAT_FILE) if _.strip())
            print(f"当前群聊消息数: {msg_count}")
            print()
            display_chat()
        else:
            print("群聊为空，使用 'demo' 参数发送演示消息")
