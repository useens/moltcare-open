#!/usr/bin/env python3
"""
统一的Moltbook回复状态管理
解决手动回复和自动回复状态不同步问题
"""

import json
from pathlib import Path

# 统一状态文件
UNIFIED_STATE_FILE = "/tmp/moltbook-unified-state.json"

def load_unified_state():
    """加载统一状态"""
    try:
        with open(UNIFIED_STATE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {
            "date": "2026-02-23",
            "daily_count": 0,
            "hourly_count": 0,
            "last_reply_time": None,
            "replied_posts": [],  # 手动+自动回复的帖子ID
            "hourly_reset": None
        }

def save_unified_state(state):
    """保存统一状态"""
    with open(UNIFIED_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def record_reply(post_id, is_manual=True):
    """记录回复（手动或自动）"""
    state = load_unified_state()
    
    if post_id not in state['replied_posts']:
        state['replied_posts'].append(post_id)
        print(f"✅ 记录回复: {post_id} ({'手动' if is_manual else '自动'})")
        
        # 如果是手动回复，也需要更新计数
        if is_manual:
            state['daily_count'] += 1
            print(f"   今日进度: {state['daily_count']}/50")
        
        save_unified_state(state)
    else:
        print(f"⚠️  帖子 {post_id} 已回复过，跳过")

def check_should_reply(post_id):
    """检查是否应该回复（防重复）"""
    state = load_unified_state()
    
    if post_id in state['replied_posts']:
        return False, "已回复过"
    
    # 检查速率限制
    from datetime import datetime, timedelta
    
    if state['hourly_reset']:
        last_reset = datetime.fromisoformat(state['hourly_reset'])
        if (datetime.now() - last_reset) > timedelta(hours=1):
            state['hourly_count'] = 0
            state['hourly_reset'] = datetime.now().isoformat()
            save_unified_state(state)
    
    if state['hourly_count'] >= 10:
        return False, "已达每小时上限(10条)"
    
    if state['daily_count'] >= 50:
        return False, "已达每日上限(50条)"
    
    # 检查间隔
    if state['last_reply_time']:
        last_time = datetime.fromisoformat(state['last_reply_time'])
        elapsed = (datetime.now() - last_time).total_seconds()
        if elapsed < 35:
            wait = 35 - elapsed
            return False, f"需等待{wait:.0f}秒"
    
    return True, "OK"

# 合并之前分散的状态
def merge_legacy_states():
    """合并旧的分散状态"""
    state = load_unified_state()
    
    # 从molt-aggressive-state.json导入
    try:
        with open("/tmp/molt-aggressive-state.json", 'r') as f:
            old_state = json.load(f)
            for pid in old_state.get('replied_posts', []):
                if pid not in state['replied_posts']:
                    state['replied_posts'].append(pid)
            # 更新计数
            state['daily_count'] = max(state['daily_count'], old_state.get('daily_count', 0))
            state['hourly_count'] = max(state['hourly_count'], old_state.get('hourly_count', 0))
            save_unified_state(state)
            print(f"✅ 合并了 {len(old_state.get('replied_posts', []))} 条自动回复记录")
    except:
        print("⚠️  未找到旧状态文件或已合并")
    
    # 从手动记录导入
    manual_replies = [
        "8564da6f-23c2-45b7-a3ba-3e315a6b0a53",  # $MOLT帖子
        "562faad7-f9cc-49a3-8520-2bdf362606bb",  # Ronin Nightly Build
        "4b64728c-645d-45ea-86a7-338e52a2abc6",  # Jackle Operator
    ]
    for pid in manual_replies:
        if pid not in state['replied_posts']:
            state['replied_posts'].append(pid)
    
    save_unified_state(state)
    print(f"✅ 合并了 {len(manual_replies)} 条手动回复记录")

if __name__ == "__main__":
    print("🔄 合并分散状态到统一状态管理...")
    print()
    merge_legacy_states()
    print()
    state = load_unified_state()
    print(f"📊 统一状态:")
    print(f"   已回复帖子: {len(state['replied_posts'])} 个")
    print(f"   今日计数: {state['daily_count']}/50")
    print(f"   本小时计数: {state['hourly_count']}/10")
