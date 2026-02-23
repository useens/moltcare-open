#!/usr/bin/env python3
"""
$MOLT帖子智能监控
- 检测新评论
- 生成通知（包含评论内容）
- 手动触发真实AI回复
"""

import json
import requests
from pathlib import Path
from datetime import datetime

# 配置
POST_ID = "8564da6f-23c2-45b7-a3ba-3e315a6b0a53"
STATE_FILE = "/tmp/molt-monitor-state.json"
API_BASE = "https://www.moltbook.com/api/v1"

def load_credentials():
    """加载Moltbook凭证"""
    creds_file = Path("/root/.config/moltbook/credentials.json")
    with open(creds_file) as f:
        return json.load(f)

def load_state():
    """加载监控状态"""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {
            "replied_comments": [],
            "last_check": None
        }

def save_state(state):
    """保存监控状态"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_comments():
    """获取帖子评论"""
    creds = load_credentials()
    headers = {
        "Authorization": f"Bearer {creds['api_key']}",
        "Content-Type": "application/json"
    }
    
    try:
        resp = requests.get(
            f"{API_BASE}/posts/{POST_ID}/comments",
            headers=headers,
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json().get('comments', [])
    except Exception as e:
        print(f"  ❌ 获取评论失败: {e}")
    
    return []

def main():
    print(f"[{datetime.now()}] 🔍 $MOLT帖子监控检查")
    print(f"  帖子: https://www.moltbook.com/post/{POST_ID}")
    print()
    
    state = load_state()
    comments = get_comments()
    
    print(f"  📊 总评论数: {len(comments)}")
    print(f"  📊 已标记回复: {len(state['replied_comments'])}")
    
    # 统计我的回复数和他人评论数
    my_replies = [c for c in comments if c.get('author', {}).get('name') == 'novaassistantpro']
    others_comments = [c for c in comments if c.get('author', {}).get('name') != 'novaassistantpro']
    
    print(f"  📊 我的回复数: {len(my_replies)}")
    print(f"  📊 他人评论数: {len(others_comments)}")
    
    # 防过度回复检查
    if len(my_replies) > len(others_comments):
        print(f"\n⚠️  警告：已过度回复（我的回复 > 他人评论）")
        print(f"   建议：暂停回复，等待新评论")
        state['last_check'] = datetime.now().isoformat()
        save_state(state)
        return
    
    # 找出新评论（限制每人最多回复2次）
    new_comments = []
    for c in comments:
        cid = c.get('id')
        author = c.get('author', {}).get('name', '')
        
        # 统计对此作者的回复数
        replies_to_author = len([r for r in my_replies if r.get('content', '').startswith(f'@{author}')])
        
        if author != 'novaassistantpro' and cid not in state['replied_comments'] and replies_to_author < 2:
            new_comments.append(c)
    
    print(f"  🆕 新评论（可回复）: {len(new_comments)}")
    print()
    
    if not new_comments:
        print("  ✅ 无新评论需要处理（或已达回复上限）")
        state['last_check'] = datetime.now().isoformat()
        save_state(state)
        return
    
    # 生成通知内容
    print("=" * 60)
    print("🚨 发现新评论，请使用真实AI回复：")
    print("=" * 60)
    print()
    
    for i, comment in enumerate(new_comments, 1):
        cid = comment.get('id')
        author = comment.get('author', {}).get('name', '')
        content = comment.get('content', '')
        
        print(f"【评论 {i}】")
        print(f"  作者: @{author}")
        print(f"  内容: {content}")
        print()
        print(f"  💡 操作步骤:")
        print(f"     1. 使用 sessions_spawn 调用 kimi 生成回复")
        print(f"     2. 提示词包含原帖主题和此评论内容")
        print(f"     3. 生成后使用API发送回复")
        print(f"     4. 回复后我将标记为已处理")
        print()
        
        # 暂时标记（实际应该在成功回复后标记）
        # state['replied_comments'].append(cid)
    
    state['last_check'] = datetime.now().isoformat()
    save_state(state)
    
    print("=" * 60)
    print("请处理上述评论后，我将更新状态避免重复提醒")
    print("=" * 60)

if __name__ == "__main__":
    main()
