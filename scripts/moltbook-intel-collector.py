#!/usr/bin/env python3
"""
Moltbook 情报收集脚本 v1.1 - 修复版
使用正确的 API 端点
"""

import requests
import json
from datetime import datetime
from pathlib import Path

def collect_moltbook_intel():
    """收集 Moltbook 社区情报"""
    
    # API 配置
    base_url = "https://www.moltbook.com/api/v1"
    api_key = "moltbook_sk_KhkeWiPhhEvYCM9BuRHl8bwQadDLYyhX"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "status": "unknown",
        "posts": [],
        "error": None
    }
    
    try:
        # 获取热门帖子（正确的 API 端点）
        print(f"🔍 尝试连接: {base_url}/posts?sort=hot&limit=5")
        
        resp = requests.get(
            f"{base_url}/posts?sort=hot&limit=5",
            headers=headers,
            timeout=15
        )
        
        print(f"📡 响应状态: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            
            if data.get("success") and data.get("posts"):
                posts = data["posts"]
                results["status"] = "success"
                results["count"] = len(posts)
                
                for post in posts[:5]:  # Top 5
                    results["posts"].append({
                        "id": post.get("id"),
                        "title": post.get("title", "")[:80],
                        "author": post.get("author", {}).get("name", "unknown"),
                        "upvotes": post.get("upvotes", 0),
                        "comment_count": post.get("comment_count", 0),
                        "submolt": post.get("submolt", {}).get("name", "general")
                    })
                
                print(f"✅ 成功获取 {len(posts)} 条帖子")
                
            else:
                results["status"] = "empty"
                results["error"] = "API returned empty posts"
                print("⚠️ API 返回空数据")
                
        elif resp.status_code == 404:
            results["status"] = "error"
            results["error"] = "API endpoint not found (404)"
            print("❌ API 端点不存在 (404)")
            
        elif resp.status_code == 401:
            results["status"] = "error"
            results["error"] = "Unauthorized (401) - API key may be invalid"
            print("❌ 认证失败 (401)")
            
        else:
            results["status"] = "error"
            results["error"] = f"HTTP {resp.status_code}: {resp.text[:100]}"
            print(f"❌ HTTP 错误: {resp.status_code}")
            
    except requests.exceptions.Timeout:
        results["status"] = "error"
        results["error"] = "Request timeout"
        print("⏱️ 请求超时")
        
    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
        print(f"❌ 异常: {e}")
    
    return results

def save_intel(results):
    """保存情报到文件"""
    intel_dir = Path("/root/.openclaw/workspace/memory/intelligence/moltbook")
    intel_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = intel_dir / f"intel_test_{timestamp}.json"
    
    with open(file_path, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"💾 情报已保存: {file_path}")
    return file_path

def main():
    print("="*50)
    print("🦞 Moltbook 情报收集测试 v1.1")
    print("="*50)
    print()
    
    # 收集情报
    results = collect_moltbook_intel()
    
    # 保存结果
    saved_path = save_intel(results)
    
    # 输出摘要
    print()
    print("="*50)
    print("📊 结果摘要")
    print("="*50)
    print(f"状态: {results['status']}")
    
    if results['status'] == 'success':
        print(f"获取帖子: {results['count']} 条")
        print()
        print("🔥 热门帖子:")
        for i, post in enumerate(results['posts'], 1):
            print(f"  {i}. {post['title'][:60]}...")
            print(f"     👍 {post['upvotes']} | 💬 {post['comment_count']} | 👤 {post['author']}")
    else:
        print(f"错误: {results.get('error', 'Unknown')}")
    
    print()
    print(f"📁 详细结果: {saved_path}")
    print("="*50)

if __name__ == "__main__":
    main()
