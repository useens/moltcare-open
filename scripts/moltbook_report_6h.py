#!/usr/bin/env python3
"""
Moltbook 运营数据汇报脚本 - 每6小时执行
基于真实API数据，非缓存
"""

import sys
import json
import requests
from datetime import datetime, timedelta
sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import load_credentials, get_headers

API_BASE = "https://www.moltbook.com/api/v1"

# 监控的帖子配置
MONITORED_POSTS = [
    {"id": "82e5ea62-5e05-4e03-b64b-e005cc220b63", "title": "From Meme to Utility", "goal": 50},
    {"id": "c453e57d-8836-400e-90a4-7bdc3eedbc93", "title": "决策引擎空转一周", "goal": 10},
    {"id": "14ee16be-fffb-4e36-93c7-33fc6724a455", "title": "Blockchain Memory Proposal", "goal": 20},
    {"id": "8f9f8d61-8036-4a0a-b686-5b59d504e242", "title": "Invisible Automation", "goal": 10},
    {"id": "cc41553f-7366-40ca-ba5c-18cb526a63dc", "title": "决策引擎完整学习闭环", "goal": 5},
]

def get_post_data(post_id):
    """从API获取真实帖子数据"""
    creds = load_credentials()
    headers = get_headers(creds)
    
    try:
        resp = requests.get(f"{API_BASE}/posts/{post_id}", headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.json().get('post', {})
    except Exception as e:
        print(f"❌ API错误: {e}")
    return None

def get_comments(post_id):
    """从API获取真实评论数据"""
    creds = load_credentials()
    headers = get_headers(creds)
    
    try:
        resp = requests.get(f"{API_BASE}/posts/{post_id}/comments", headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.json().get('comments', [])
    except Exception as e:
        print(f"❌ API错误: {e}")
    return []

def generate_report():
    """生成真实数据汇报"""
    now = datetime.now()
    
    print("="*70)
    print(f"📊 Moltbook 运营数据汇报")
    print(f"⏰ 查询时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 数据来源: Moltbook API (实时)")
    print("="*70)
    
    total_upvotes = 0
    total_comments = 0
    total_new_comments = 0
    
    # 加载上次状态用于对比
    try:
        with open('/tmp/moltbook_last_report.json', 'r') as f:
            last_report = json.load(f)
    except:
        last_report = {}
    
    print("\n## 📈 帖子实时状态\n")
    
    current_data = {}
    
    for post in MONITORED_POSTS:
        post_data = get_post_data(post['id'])
        if not post_data:
            print(f"⚠️ {post['title'][:40]}... - 无法获取数据")
            continue
        
        upvotes = post_data.get('upvotes', 0)
        comment_count = post_data.get('comment_count', 0)
        
        # 获取评论详情
        comments = get_comments(post['id'])
        
        # 计算新评论（与上次报告对比）
        last_count = last_report.get(post['id'], {}).get('comment_count', 0)
        new_comments = max(0, comment_count - last_count)
        total_new_comments += new_comments
        
        # 进度计算
        progress = (comment_count / post['goal'] * 100) if post['goal'] > 0 else 0
        
        # 状态图标
        if progress >= 80:
            status = "🟢"
        elif progress >= 50:
            status = "🟡"
        elif progress > 0:
            status = "🟠"
        else:
            status = "🔴"
        
        print(f"{status} {post['title'][:35]}...")
        print(f"   👍 {upvotes} | 💬 {comment_count}/{post['goal']} ({progress:.0f}%)")
        if new_comments > 0:
            print(f"   📈 新增: +{new_comments} 条评论")
        
        total_upvotes += upvotes
        total_comments += comment_count
        
        current_data[post['id']] = {
            'title': post['title'],
            'upvotes': upvotes,
            'comment_count': comment_count,
            'goal': post['goal'],
            'progress': progress,
            'comments_detail': [{'author': c.get('author',{}).get('name'), 'content': c.get('content','')[:50]} for c in comments[-3:]]  # 最近3条
        }
    
    # 加载社交系统状态
    try:
        with open('/tmp/moltbook_social_state.json', 'r') as f:
            social_state = json.load(f)
        replied_today = len([t for t in social_state.get('comment_times', []) 
                           if datetime.fromisoformat(t).date() == now.date()])
    except:
        replied_today = 0
    
    print("\n## 📊 汇总统计\n")
    print(f"👍 总点赞: {total_upvotes}")
    print(f"💬 总评论: {total_comments}")
    print(f"📈 新增评论(6小时内): +{total_new_comments}")
    print(f"✅ 今日已回复: {replied_today} 条")
    
    # 目标总体进度
    total_goal = sum(p['goal'] for p in MONITORED_POSTS)
    total_progress = (total_comments / total_goal * 100) if total_goal > 0 else 0
    print(f"\n🎯 总体进度: {total_comments}/{total_goal} ({total_progress:.1f}%)")
    
    # 问题提醒
    print("\n## ⚠️ 需要关注\n")
    
    issues = []
    for post_id, data in current_data.items():
        if data['progress'] == 0:
            issues.append(f"• {data['title'][:30]}... - 0互动，需推广")
        elif data['progress'] < 20:
            issues.append(f"• {data['title'][:30]}... - 进度仅{data['progress']:.0f}%")
    
    # 检查失败的回复
    try:
        with open('/tmp/moltbook_reply_failures.json', 'r') as f:
            failures = json.load(f)
        if failures:
            issues.append(f"• 有 {len(failures)} 条回复失败，需手动处理")
    except:
        pass
    
    if issues:
        for issue in issues:
            print(issue)
    else:
        print("✅ 无异常，运营正常")
    
    print("\n## 📝 最近评论摘要\n")
    
    for post_id, data in current_data.items():
        if data['comments_detail']:
            print(f"{data['title'][:30]}...:")
            for c in data['comments_detail']:
                print(f"  - @{c['author']}: {c['content']}...")
            print()
    
    print("="*70)
    print(f"📅 下次汇报: {(now + timedelta(hours=6)).strftime('%Y-%m-%d %H:%M')}")
    print("="*70)
    
    # 保存当前状态供下次对比
    with open('/tmp/moltbook_last_report.json', 'w') as f:
        json.dump({pid: {'comment_count': d['comment_count']} for pid, d in current_data.items()}, f)

if __name__ == "__main__":
    generate_report()
