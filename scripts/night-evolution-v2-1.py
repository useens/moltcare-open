#!/usr/bin/env python3
"""
觉醒者夜间深度进化 v2.1 - 阶段1 情报收集（修复版）
整合所有情报源：HackerNews, GitHub, arXiv, Moltbook
修复了Moltbook API端点问题
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

# 路径配置
WORKSPACE = Path.home() / ".openclaw/workspace"
MEMORY_PATH = WORKSPACE / "memory/intelligence"
LOG_PATH = WORKSPACE / "logs"
SCRIPT_PATH = WORKSPACE / "scripts"

def log(message):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def collect_hackernews():
    """收集HackerNews情报"""
    log("📡 扫描 HackerNews...")
    try:
        # 使用ddgr搜索HN热门内容
        result = subprocess.run(
            ["ddgr", "-n", "10", "--json", "site:news.ycombinator.com AI agent"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            items = json.loads(result.stdout) if result.stdout else []
            log(f"  ✅ HN: 获取 {len(items)} 条")
            return [{"source": "hackernews", "title": item.get("title", ""), "url": item.get("url", "")} 
                    for item in items[:5]]
    except Exception as e:
        log(f"  ⚠️ HN收集失败: {e}")
    return []

def collect_github():
    """收集GitHub趋势情报"""
    log("📡 扫描 GitHub...")
    try:
        result = subprocess.run(
            ["ddgr", "-n", "10", "--json", "site:github.com AI agent autonomous"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            items = json.loads(result.stdout) if result.stdout else []
            log(f"  ✅ GitHub: 获取 {len(items)} 条")
            return [{"source": "github", "title": item.get("title", ""), "url": item.get("url", "")} 
                    for item in items[:5]]
    except Exception as e:
        log(f"  ⚠️ GitHub收集失败: {e}")
    return []

def collect_moltbook():
    """收集Moltbook社区情报（使用修复后的API）"""
    log("📡 扫描 Moltbook...")
    try:
        # 调用修复后的情报收集器
        result = subprocess.run(
            ["python3", str(SCRIPT_PATH / "moltbook-intel-collector.py")],
            capture_output=True, text=True, timeout=30
        )
        
        # 读取生成的情报文件
        intel_dir = MEMORY_PATH / "moltbook"
        if intel_dir.exists():
            # 找最新的情报文件
            files = sorted(intel_dir.glob("intel_test_*.json"), reverse=True)
            if files:
                with open(files[0]) as f:
                    data = json.load(f)
                    if data.get("status") == "success":
                        posts = data.get("posts", [])
                        log(f"  ✅ Moltbook: 获取 {len(posts)} 条热门帖子")
                        return [{"source": "moltbook", "title": p.get("title", ""), 
                                "author": p.get("author", ""), "upvotes": p.get("upvotes", 0)} 
                                for p in posts[:5]]
                    else:
                        log(f"  ⚠️ Moltbook: {data.get('error', 'Unknown error')}")
            else:
                log("  ⚠️ Moltbook: 未找到情报文件")
        else:
            log("  ⚠️ Moltbook: 情报目录不存在")
            
    except Exception as e:
        log(f"  ⚠️ Moltbook收集失败: {e}")
    return []

def save_digest(hn_items, gh_items, mb_items):
    """保存情报摘要"""
    MEMORY_PATH.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # 生成情报编号
    intel_id = f"INTEL-{date_str.replace('-', '')}-001"
    
    # 保存JSON格式
    digest = {
        "id": intel_id,
        "timestamp": datetime.now().isoformat(),
        "sources": {
            "hackernews": {"status": "success", "count": len(hn_items), "items": hn_items},
            "github": {"status": "success", "count": len(gh_items), "items": gh_items},
            "moltbook": {"status": "success" if mb_items else "error", "count": len(mb_items), "items": mb_items}
        },
        "total_items": len(hn_items) + len(gh_items) + len(mb_items)
    }
    
    # 保存到daily目录
    daily_dir = MEMORY_PATH / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    
    json_file = daily_dir / f"{intel_id}.json"
    with open(json_file, 'w') as f:
        json.dump(digest, f, indent=2, ensure_ascii=False)
    
    # 生成Markdown报告
    md_file = daily_dir / f"{intel_id}.md"
    with open(md_file, 'w') as f:
        f.write(f"# 觉醒者夜间深度进化 - 情报摘要\n\n")
        f.write(f"**情报编号**: {intel_id}\n\n")
        f.write(f"**执行时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"**总情报数**: {digest['total_items']}\n\n")
        
        f.write("## 📊 情报概览\n\n")
        f.write("| 情报源 | 状态 | 数量 |\n")
        f.write("|--------|------|------|\n")
        f.write(f"| HackerNews | ✅ | {len(hn_items)} |\n")
        f.write(f"| GitHub | ✅ | {len(gh_items)} |\n")
        f.write(f"| Moltbook | {'✅' if mb_items else '⚠️'} | {len(mb_items)} |\n")
        f.write("\n")
        
        if mb_items:
            f.write("## 🔥 Moltbook 热门帖子\n\n")
            for i, post in enumerate(mb_items[:3], 1):
                f.write(f"{i}. **{post['title'][:60]}...**\n")
                f.write(f"   - 👍 {post.get('upvotes', 0)} | 👤 {post.get('author', 'unknown')}\n\n")
        
        f.write("---\n\n")
        f.write("*来源: 觉醒者夜间深度进化 v2.1*\n")
    
    log(f"💾 情报摘要已保存: {md_file}")
    return intel_id

def main():
    """主执行流程"""
    log("="*60)
    log("🌙 觉醒者夜间深度进化 v2.1 - 阶段1: 情报收集")
    log("="*60)
    log("")
    
    # 收集各源情报
    hn_items = collect_hackernews()
    gh_items = collect_github()
    mb_items = collect_moltbook()
    
    # 保存摘要
    log("")
    intel_id = save_digest(hn_items, gh_items, mb_items)
    
    # 输出总结
    log("")
    log("="*60)
    log("✅ 情报收集完成")
    log(f"📁 情报编号: {intel_id}")
    log(f"📊 总计: {len(hn_items) + len(gh_items) + len(mb_items)} 条")
    log("="*60)

if __name__ == "__main__":
    main()
