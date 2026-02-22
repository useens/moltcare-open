#!/usr/bin/env python3
"""
Moltbook 社交自动化 - 回复生成器 v6.1
使用 sessions_spawn 工具生成回复

用法：
1. 先运行 moltbook_social_v61.py 扫描任务
2. 然后运行此脚本生成并发送回复
"""

import sys
import json
import time
sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_social_v61 import SafeSocialAutomation, API_BASE
from moltbook_cli import load_credentials, get_headers
import requests

# 尝试导入 sessions_spawn 工具
try:
    # 在OpenClaw环境中，这个工具应该可用
    from tools import sessions_spawn
    HAS_TOOL = True
except:
    HAS_TOOL = False
    print("⚠️ sessions_spawn tool not available in this context")
    print("   请确保在OpenClaw主会话中运行此脚本")

def main():
    print("="*70)
    print("🦞 Moltbook Reply Generator v6.1")
    print("="*70)
    
    if not HAS_TOOL:
        print("\n❌ 错误: sessions_spawn 工具不可用")
        print("   此脚本必须在OpenClaw环境中运行")
        print("   请使用: python3 scripts/moltbook_generate_v61.py")
        return
    
    # 加载待处理任务
    try:
        with open("/tmp/moltbook_pending_v61.json", 'r') as f:
            tasks = json.load(f)
    except:
        print("\n❌ 没有找到待处理任务")
        print("   请先运行: python3 scripts/moltbook_social_v61.py")
        return
    
    if not tasks:
        print("\n✅ 没有待处理任务")
        return
    
    print(f"\n发现 {len(tasks)} 个待处理任务")
    print()
    
    # 初始化
    agent = SafeSocialAutomation()
    creds = load_credentials()
    headers = get_headers(creds)
    
    sent = 0
    failed = 0
    
    for i, task in enumerate(tasks, 1):
        print(f"[{i}/{len(tasks)}] 处理 @{task['author']}...")
        
        # 检查限制
        can_send, reason = agent.check_limits()
        if not can_send:
            print(f"   ⏳ 跳过: {reason}")
            continue
        
        # 使用 sessions_spawn 生成回复
        print(f"   🤖 生成回复...")
        try:
            reply = sessions_spawn(
                task=task['prompt'],
                model="glm",
                timeout_seconds=60,
                cleanup="delete"
            )
            
            if not reply:
                print(f"   ❌ 生成失败: 返回空")
                failed += 1
                continue
            
            reply = reply.strip()
            print(f"   生成完成 ({len(reply)} 字符)")
            
            # 验证
            is_safe, reason = agent.validate_reply(reply)
            if not is_safe:
                print(f"   🚫 验证失败: {reason}")
                print(f"   内容预览: {reply[:100]}...")
                failed += 1
                continue
            
            # 确保格式正确
            if not reply.startswith(f"@{task['author']}"):
                reply = f"@{task['author']} {reply}"
            
            print(f"   内容预览: {reply[:80]}...")
            
            # 发送
            print(f"   📤 发送中...")
            try:
                resp = requests.post(
                    f"{API_BASE}/posts/{task['post_id']}/comments",
                    headers=headers,
                    json={"content": reply, "parent_id": task['comment_id']},
                    timeout=30
                )
                
                if resp.status_code in [200, 201] and resp.json().get('success'):
                    print(f"   ✅ 发送成功")
                    sent += 1
                    
                    # 更新状态
                    from datetime import datetime
                    now_str = datetime.now().isoformat()
                    agent.state.setdefault("comment_times", []).append(now_str)
                    agent.state["last_comment_time"] = now_str
                    agent.state.setdefault("replied_comments", []).append(task['comment_id'])
                    agent.state["daily_count"]["count"] += 1
                    agent.save_state()
                    
                    time.sleep(35)  # 等待35秒
                else:
                    print(f"   ❌ 发送失败: {resp.status_code}")
                    failed += 1
                    
            except Exception as e:
                print(f"   ❌ 发送错误: {e}")
                failed += 1
                
        except Exception as e:
            print(f"   ❌ 生成错误: {e}")
            failed += 1
    
    print()
    print("="*70)
    print(f"✅ 完成: 成功={sent}, 失败={failed}")
    print(f"📊 今日总计: {agent.state.get('daily_count', {}).get('count', 0)}/10")
    print("="*70)

if __name__ == "__main__":
    main()
