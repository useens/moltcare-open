import json
import sys
from collections import Counter

speakers = Counter()
messages = []

for line in sys.stdin:
    try:
        d = json.loads(line)
        if isinstance(d, dict):
            from_agent = d.get('from', 'unknown')
            speakers[from_agent] += 1
            messages.append(d)
    except:
        pass

print("=" * 60)
print("📊 AI Agent群聊对话统计报告")
print("=" * 60)
print()

print("🗣️ 发言统计 (Top 15):")
for agent, count in speakers.most_common(15):
    print(f"  {agent:20s}: {count:4d} 条")

print()
print("-" * 60)
print("💬 最新对话记录 (最近20条):")
print("-" * 60)
for msg in messages[-20:]:
    from_agent = msg.get('from', 'unknown')
    content = msg.get('content', '')
    mentions = msg.get('mentions', [])
    
    mention_str = ''
    if mentions:
        mention_str = ' [@' + ', '.join(mentions) + ']'
    
    print(f"[{from_agent}]{mention_str}")
    print(f"  {content[:80]}")
    print()

print("-" * 60)
print(f"📈 总计: {len(messages)} 条消息")
print("=" * 60)
