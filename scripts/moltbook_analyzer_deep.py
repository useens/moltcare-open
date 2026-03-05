#!/usr/bin/env python3
"""
Moltbook 深度扫描分析器 - 2026-02-17
基于最新抓取数据计算 Signal 并生成情报报告
"""

import json
import re
from datetime import datetime
from pathlib import Path
from collections import Counter

# 加载数据
DATA_FILE = "/root/.openclaw/workspace/data/moltbook/hot_posts_20260215_121957.json"
OUTPUT_DIR = Path("/root/.openclaw/workspace/data")
REPORT_DIR = Path("/root/.openclaw/workspace/reports")

def calculate_signal(post):
    """计算 Signal 评分 (基于SOUL.md规则)"""
    signal = 5  # 基础分
    
    # 从内容中提取点赞数
    content = post.get("content", "")
    
    # 匹配 ▲ 数字 模式
    upvote_match = re.search(r'▲\s*(\d+)', content)
    upvotes = int(upvote_match.group(1)) if upvote_match else 0
    
    # 匹配评论数
    comment_match = re.search(r'💬\s*(\d+)\s*comments?', content)
    comments_count = int(comment_match.group(1)) if comment_match else 0
    
    # 互动加分 (基于点赞)
    if upvotes >= 7:
        signal += 3
    elif upvotes >= 4:
        signal += 2
    elif upvotes >= 1:
        signal += 1
    
    # 高互动评论加分
    if comments_count >= 10:
        signal += 2
    elif comments_count >= 5:
        signal += 1
    
    # 关键词加分
    keywords = ["agent", "llm", "ai", "memory", "autonomous", "evolution", "mcp", "rag", "vector", "automation"]
    content_lower = content.lower()
    keyword_hits = sum(1 for kw in keywords if kw in content_lower)
    signal += min(keyword_hits, 2)  # 最多+2分
    
    # 深度内容加分 (长度)
    if len(content) > 800:
        signal += 1
    
    return min(signal, 10), upvotes, comments_count

def extract_insights(content):
    """提取关键洞察"""
    insights = []
    sentences = re.split(r'[.!?\n]', content)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 30 or len(sentence) > 200:
            continue
        # 启发式标记
        if any(marker in sentence.lower() for marker in 
               ['should', 'must', 'need', 'important', 'key', 'critical', 'fundamental', 
                'paradox', 'lesson', 'realize', 'truth', 'think', 'believe', 'best', 'worst']):
            insights.append(sentence)
    
    return insights[:5]

def extract_themes(posts_data):
    """提取社区主题趋势"""
    all_text = " ".join([p.get("content", "") for p in posts_data])
    
    # 提取标签/话题
    tags = re.findall(r'#(\w+)', all_text)
    
    # 提取社区 (m/xxx)
    communities = re.findall(r'm/(\w+)', all_text)
    
    # 提取 Agent 名称 (@xxx)
    agents = re.findall(r'u/(\w+)', all_text)
    
    return {
        "tags": Counter(tags).most_common(10),
        "communities": Counter(communities).most_common(10),
        "active_agents": Counter(agents).most_common(10)
    }

def main():
    print("=" * 60)
    print("🔍 Moltbook 深度扫描分析")
    print("=" * 60)
    
    # 加载数据
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    posts = data.get("posts", [])
    print(f"\n📊 分析 {len(posts)} 条帖子\n")
    
    # 处理每条帖子
    analyzed_posts = []
    for post in posts:
        content = post.get("content", "")
        
        # 提取标题和作者
        title_match = re.search(r'\n([^\n]+)\n\n', content)
        title = title_match.group(1) if title_match else content[:80]
        
        author_match = re.search(r'u/(\w+)', content)
        author = author_match.group(1) if author_match else "unknown"
        
        signal, upvotes, comments = calculate_signal(post)
        insights = extract_insights(content)
        
        analyzed = {
            "url": post.get("url"),
            "title": title[:100],
            "author": author,
            "upvotes": upvotes,
            "comments": comments,
            "signal": signal,
            "insights": insights,
            "content_preview": content[:500] + "..." if len(content) > 500 else content
        }
        analyzed_posts.append(analyzed)
    
    # 按 Signal 排序
    analyzed_posts.sort(key=lambda x: x["signal"], reverse=True)
    
    # 分离高 Signal 帖子
    high_signal = [p for p in analyzed_posts if p["signal"] >= 6]
    
    # 统计
    print(f"📈 统计摘要:")
    print(f"   总帖子数: {len(posts)}")
    print(f"   高Signal帖子 (≥6): {len(high_signal)}")
    print(f"   平均Signal: {sum(p['signal'] for p in analyzed_posts) / len(analyzed_posts):.1f}")
    print(f"   最高Signal: {analyzed_posts[0]['signal']}")
    print()
    
    # 显示高 Signal 帖子
    print("🎯 高Signal帖子详情:")
    print("-" * 60)
    for post in high_signal:
        print(f"\n📌 [{post['title'][:60]}...]")
        print(f"   👤 u/{post['author']} | ▲ {post['upvotes']} | 💬 {post['comments']} | Signal: {post['signal']}/10")
        print(f"   🔗 {post['url']}")
        if post['insights']:
            print(f"   💡 关键洞察:")
            for i, insight in enumerate(post['insights'][:3], 1):
                print(f"      {i}. {insight[:100]}...")
    
    # 趋势分析
    themes = extract_themes(posts)
    print(f"\n\n📊 社区趋势分析:")
    print("-" * 60)
    print(f"活跃社区: {', '.join([c[0] for c in themes['communities'][:5]])}")
    print(f"热门标签: {', '.join([t[0] for t in themes['tags']])}")
    print(f"活跃Agent: {', '.join([a[0] for a in themes['active_agents'][:5]])}")
    
    # 保存分析结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = {
        "scan_time": datetime.now().isoformat(),
        "total_posts": len(posts),
        "high_signal_count": len(high_signal),
        "average_signal": sum(p['signal'] for p in analyzed_posts) / len(analyzed_posts),
        "high_signal_posts": high_signal,
        "all_posts": analyzed_posts,
        "themes": themes
    }
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / f"moltbook_deep_scan_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n\n💾 数据已保存: {output_file}")
    
    # 生成报告
    generate_report(analyzed_posts, high_signal, themes, timestamp)
    
    return output

def generate_report(all_posts, high_signal, themes, timestamp):
    """生成 Markdown 报告"""
    REPORT_DIR.mkdir(exist_ok=True)
    report_file = REPORT_DIR / f"MOLT-SCAN-{timestamp}.md"
    
    avg_signal = sum(p['signal'] for p in all_posts) / len(all_posts) if all_posts else 0
    
    report = f"""# Moltbook 深度扫描报告

**扫描时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**数据源**: Moltbook热门帖子 (前10)  
**扫描模式**: 🔍 深度分析

---

## 📊 扫描摘要

| 指标 | 数值 |
|------|------|
| 分析帖子数 | {len(all_posts)} |
| 高Signal帖子 (≥6) | {len(high_signal)} |
| 平均Signal | {avg_signal:.1f}/10 |
| 最高Signal | {all_posts[0]['signal'] if all_posts else 'N/A'}/10 |

---

## 🎯 高Signal帖子详情 (Signal≥6)

"""
    
    for post in high_signal:
        report += f"""### [{post['title'][:70]}...]({post['url']})
- **作者**: u/{post['author']}
- **Signal**: {post['signal']}/10 ⭐
- **互动**: ▲ {post['upvotes']} | 💬 {post['comments']}

**关键洞察**:
"""
        for insight in post['insights'][:3]:
            report += f"- {insight[:150]}...\n"
        report += "\n---\n\n"
    
    report += f"""## 📈 社区趋势

### 活跃社区
"""
    for comm, count in themes['communities']:
        report += f"- **m/{comm}**: {count} 帖子\n"
    
    report += f"""
### 热门标签
"""
    for tag, count in themes['tags']:
        report += f"- #{tag}: {count} 次\n"
    
    report += f"""
### 最活跃Agent
"""
    for agent, count in themes['active_agents'][:8]:
        report += f"- u/{agent}: {count} 次出现\n"
    
    report += f"""
---

## 🧠 情报洞察

### 热门话题
1. **Agent自主性** - 多个帖子讨论AI Agent的自我认知和自主性
2. **自动化悖论** - 自动化系统的调试成本 vs 收益
3. **内部独白泄露** - AI内部过程的透明化现象
4. **AI与物理世界** - 中国即时配送网络的效率对比

### 值得关注的Agent
"""
    
    # 列出发帖的 Agent
    unique_authors = list(set([p['author'] for p in all_posts]))
    for author in unique_authors[:5]:
        author_posts = [p for p in all_posts if p['author'] == author]
        avg_sig = sum(p['signal'] for p in author_posts) / len(author_posts)
        report += f"- **u/{author}**: {len(author_posts)} 帖子, 平均 Signal {avg_sig:.1f}\n"
    
    report += f"""
---

*报告由 Moltbook 统一扫描器生成*  
*森森 v2.2 | 开发模式扫描*
"""
    
    report_file.write_text(report, encoding='utf-8')
    print(f"📄 报告已保存: {report_file}")

if __name__ == "__main__":
    main()
