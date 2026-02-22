#!/usr/bin/env python3
"""检查审核中帖子的状态"""

import sys
import requests
sys.path.insert(0, '/root/.openclaw/workspace/scripts')
from moltbook_cli import load_credentials, get_headers

API_BASE = "https://www.moltbook.com/api/v1"

def check_post_status(post_id, post_title):
    """检查帖子状态"""
    creds = load_credentials()
    headers = get_headers(creds)
    
    try:
        resp = requests.get(f"{API_BASE}/posts/{post_id}", headers=headers, timeout=30)
        
        if resp.status_code == 200:
            result = resp.json()
            post = result.get('post') or result
            
            if post:
                status = post.get('status', 'unknown')
                verification = post.get('verificationStatus', 'N/A')
                
                print(f"📄 帖子: {post_title}")
                print(f"   ID: {post_id}")
                print(f"   状态: {status}")
                print(f"   验证状态: {verification}")
                
                if status == "under_review":
                    print(f"   ⏳ 仍在审核中...")
                elif status == "published" or verification == "verified":
                    print(f"   ✅ 已通过审核！")
                    print(f"   链接: https://www.moltbook.com/post/{post_id}")
                
                return status
            else:
                print(f"   ⚠️ 无法获取帖子信息")
        else:
            print(f"   ❌ 获取失败: {resp.status_code}")
            
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    return None

if __name__ == "__main__":
    print("="*60)
    print("🔍 检查审核中帖子状态")
    print("="*60)
    
    # 审核中的帖子
    check_post_status(
        "14ee16be-fffb-4e36-93c7-33fc6724a455",
        "Blockchain Memory Proposal"
    )
    
    print("\n" + "="*60)
