import json
import sys

messages = []
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
        if isinstance(d, dict):
            messages.append(d)
    except:
        pass

print(f"共 {len(messages)} 条消息\n")
for msg in messages:
    from_agent = msg.get('from', 'unknown')
    content = msg.get('content', '')
    mentions = msg.get('mentions', [])
    
    mention_str = ''
    if mentions:
        mention_str = ' [@' + ', '.join(mentions) + ']'
    
    print(f"[{from_agent}]{mention_str}")
    print(f"  {content[:100]}")
    print()

print(f"\n总计: {len(messages)} 条消息")
