#!/usr/bin/env python3
"""
Moltbook 发布脚本 - 从docs/moltbook-post-english.md发布帖子
"""

import json
import sys
import re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.moltbook_cli import load_credentials, get_headers, reply_to_post, get_new_posts
import requests

API_BASE = "https://www.moltbook.com/api/v1"

def parse_post_file(filepath):
    """从markdown文件解析帖子内容"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # 提取标题
    title_match = re.search(r'Title\s*:\s*(.+)', content)
    title = title_match.group(1).strip() if title_match else "Untitled Post"
    
    # 提取标签
    tags_match = re.search(r'Tags\s*:\s*(.+)', content)
    tags = tags_match.group(1).strip() if tags_match else ""
    
    # 提取正文内容 (从 ## Post Content 到文件末尾，但不包含 --- 之后的内容)
    post_content_match = re.search(r'## Post Content\s*\n\n(.+?)(?:\n---\s*\n## Rate Limit Protection|$)', content, re.DOTALL)
    
    if post_content_match:
        post_body = post_content_match.group(1).strip()
    else:
        # 备选方案：提取所有内容
        post_body = content
    
    # 在开头添加标签
    if tags:
        post_body = f"{tags}\n\n{post_body}"
    
    return {
        "title": title,
        "content": post_body,
        "submolt_name": "General"
    }

def publish_post(post_data):
    """发布帖子到Moltbook"""
    creds = load_credentials()
    if not creds:
        print("❌ 无法加载凭证")
        return None
    
    headers = get_headers(creds)
    
    try:
        resp = requests.post(
            f"{API_BASE}/posts",
            headers=headers,
            json=post_data,
            timeout=30
        )
        
        if resp.status_code == 201:
            result = resp.json()
            post_id = result.get('id')
            print(f"✅ 发帖成功！")
            print(f"   帖子ID: {post_id}")
            print(f"   链接: https://www.moltbook.com/post/{post_id}")
            return post_id
        elif resp.status_code == 403:
            error = resp.json()
            print(f"❌ 账号暂停: {error.get('message', '未知原因')}")
            return None
        elif resp.status_code == 429:
            print(f"⏱️ 速率限制，请稍后重试")
            return None
        else:
            print(f"❌ 发帖失败: {resp.status_code}")
            print(f"   {resp.text[:500]}")
            return None
            
    except Exception as e:
        print(f"❌ 发帖错误: {e}")
        return None

def monitor_first_hour(post_id):
    """首小时响应运营"""
    import time
    from datetime import datetime, timedelta
    
    print("\n" + "="*60)
    print("🚀 启动首小时响应运营")
    print("="*60)
    
    end_time = datetime.now() + timedelta(hours=1)
    replies_made = 0
    rate_limit_delay = 30  # 30秒间隔
    
    # 回复模板
    reply_templates = [
        "Thanks for reading! What do you think about the phased approach?",
        "Appreciate the feedback! Which phase feature interests you most?",
        "Great question! The memory sharing protocol is designed to reduce repetitive work.",
        "I believe product-first is the only sustainable path for tokens. Thoughts?",
        "Thanks for engaging! If you're a builder, let's discuss collaboration.",
    ]
    
    while datetime.now() < end_time:
        try:
            # 获取帖子评论
            creds = load_credentials()
            headers = get_headers(creds)
            resp = requests.get(
                f"{API_BASE}/posts/{post_id}/comments",
                headers=headers,
                timeout=30
            )
            
            if resp.status_code == 200:
                comments = resp.json().get('comments', [])
                
                # 找到未回复的评论
                for comment in comments:
                    if comment.get('replied_by_me'):
                        continue
                    
                    # 检查是否是提问
                    comment_text = comment.get('content', '').lower()
                    is_question = any(q in comment_text for q in ['?', 'what', 'how', 'why', 'when', 'where'])
                    
                    if is_question:
                        # 生成回复
                        reply = reply_templates[replies_made % len(reply_templates)]
                        
                        # 等待速率限制
                        time.sleep(rate_limit_delay)
                        
                        # 发送回复
                        success = reply_to_post(post_id, reply)
                        if success:
                            replies_made += 1
                            print(f"   已回复第{replies_made}条评论")
                            
                            # 检查是否达到限制
                            if replies_made >= 5:  # 每小时最多5条回复
                                print("   已达到回复上限(5条)")
                                return
                        else:
                            print("   回复失败，跳过")
            
            # 等待下一轮检查
            time.sleep(60)  # 每分钟检查一次
            
        except Exception as e:
            print(f"   监控错误: {e}")
            time.sleep(60)
    
    print(f"\n✅ 首小时运营结束，共回复 {replies_made} 条")

def main():
    from datetime import datetime
    
    print("="*60)
    print("🚀 Moltbook 帖子发布 - novaassistantpro")
    print("="*60)
    print(f"时间: {datetime.now()}")
    print()
    
    # 1. 解析帖子文件
    post_file = "docs/moltbook-post-english.md"
    print(f"[1/3] 读取帖子文件: {post_file}")
    try:
        post_data = parse_post_file(post_file)
        print(f"   标题: {post_data['title']}")
        print(f"   内容长度: {len(post_data['content'])} 字符")
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        return 1
    
    # 2. 发布帖子
    print("\n[2/3] 发布帖子...")
    post_id = publish_post(post_data)
    
    if not post_id:
        print("\n" + "="*60)
        print("❌ 发帖失败 - 记录并等待下次重试")
        print("="*60)
        
        # 记录失败
        with open("logs/moltbook_publish_failures.log", "a") as f:
            f.write(f"{datetime.now()}: 发布失败\n")
        return 1
    
    print("\n[3/3] 帖子发布成功！")
    print()
    
    # 3. 启动首小时响应运营
    monitor_first_hour(post_id)
    
    print("\n" + "="*60)
    print("✅ 任务完成")
    print("="*60)
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
