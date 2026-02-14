#!/usr/bin/env python3
"""
Moltbook深度扫描分析器
分析提取的帖子数据，计算Signal评分，生成学习报告
"""

import json
import re
from datetime import datetime
from pathlib import Path

# Signal评分配置
SIGNAL_CONFIG = {
    "base_score": 5,
    "vote_weights": {1000: 3, 500: 2, 100: 1, 0: 0},
    "comment_weights": {1000: 3, 500: 2, 100: 1, 0: 0},
    "keyword_bonus": 1,
    "high_value_keywords": [
        "agent", "llm", "ai", "memory", "autonomous", "evolution", 
        "mcp", "rag", "vector", "embedding", "learning", "skill",
        "infrastructure", "protocol", "framework"
    ]
}

def calculate_signal(post):
    """计算帖子Signal评分"""
    score = SIGNAL_CONFIG["base_score"]
    
    # 从内容中提取投票和评论数
    content = post.get("content", "")
    
    # 提取投票数 (▲ N ▼ 格式)
    vote_match = re.search(r'▲\s*(\d+)', content)
    votes = int(vote_match.group(1)) if vote_match else 0
    
    # 提取评论数
    comment_match = re.search(r'💬\s*(\d+)\s*comments?', content, re.IGNORECASE)
    comments = int(comment_match.group(1)) if comment_match else 0
    
    # 投票加分
    for threshold, bonus in sorted(SIGNAL_CONFIG["vote_weights"].items(), reverse=True):
        if votes >= threshold:
            score += bonus
            break
    
    # 评论加分
    for threshold, bonus in sorted(SIGNAL_CONFIG["comment_weights"].items(), reverse=True):
        if comments >= threshold:
            score += bonus
            break
    
    # 关键词加分
    content_lower = content.lower()
    keyword_hits = sum(1 for kw in SIGNAL_CONFIG["high_value_keywords"] if kw in content_lower)
    score += min(keyword_hits, 3)  # 最多加3分
    
    return {
        "score": min(score, 10),  # 最高10分
        "votes": votes,
        "comments": comments,
        "keyword_hits": keyword_hits
    }

def analyze_post(post, signal_data):
    """分析单个帖子内容"""
    content = post.get("content", "")
    url = post.get("url", "")
    
    # 提取标题（第一行或前100字符）
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    title = ""
    for line in lines:
        if not line.startswith('←') and not line.startswith('m/') and not line.startswith('▲'):
            title = line[:100]
            break
    
    # 提取作者
    author_match = re.search(r'Posted by (u/\w+)', content)
    author = author_match.group(1) if author_match else "Unknown"
    
    # 提取分类
    category_match = re.search(r'←\s*(m/\w+)', content)
    category = category_match.group(1) if category_match else "m/general"
    
    # 提取关键洞察（前300字符的非元数据内容）
    insight = ""
    for line in lines[2:] if len(lines) > 2 else lines:
        if len(line) > 50 and not line.startswith('←') and not line.startswith('m/') and not line.startswith('▲') and not line.startswith('💬'):
            insight = line[:300]
            break
    
    return {
        "url": url,
        "title": title,
        "author": author,
        "category": category,
        "signal": signal_data["score"],
        "votes": signal_data["votes"],
        "comments": signal_data["comments"],
        "insight": insight,
        "extracted_at": post.get("extracted_at", "")
    }

def generate_learning_report(posts_data, output_dir="reports"):
    """生成学习报告"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    report_file = output_path / f"MOLT-{timestamp}.md"
    
    # 分类统计
    high_signal = [p for p in posts_data if p["signal"] >= 7]
    medium_signal = [p for p in posts_data if 5 <= p["signal"] < 7]
    low_signal = [p for p in posts_data if p["signal"] < 5]
    
    # 生成报告
    report = f"""# Moltbook深度学习报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**扫描范围**: 前10热门帖子  
**Signal阈值**: ≥7深度提取

---

## 扫描摘要

| 指标 | 数值 |
|------|------|
| 总帖子数 | {len(posts_data)} |
| Signal≥7 (高价值) | {len(high_signal)} |
| Signal 5-6 (中价值) | {len(medium_signal)} |
| Signal<5 (低价值) | {len(low_signal)} |
| 平均Signal | {sum(p['signal'] for p in posts_data) / len(posts_data):.1f} |

---

## 高价值内容 (Signal≥7)

"""
    
    if high_signal:
        for i, post in enumerate(high_signal, 1):
            report += f"""### {i}. {post['title']}
- **作者**: {post['author']}
- **分类**: {post['category']}
- **Signal**: {post['signal']}/10 ⭐
- **互动**: {post['votes']} 票 / {post['comments']} 评论
- **URL**: {post['url']}
- **关键洞察**: {post['insight']}

---

"""
    else:
        report += "本次扫描未发现Signal≥7的高价值内容。\n\n---\n\n"
    
    # 中价值内容
    report += """## 中价值内容 (Signal 5-6)

"""
    if medium_signal:
        for post in medium_signal:
            report += f"- **{post['title'][:60]}**... | {post['author']} | Signal:{post['signal']} | [{post['votes']}/{post['comments']}]\n"
    else:
        report += "无\n"
    
    # 技术洞察
    report += """
---

## 技术洞察与趋势分析

### Agent策略观察
"""
    
    # 分析关键词
    all_content = " ".join([p.get("content", "") for p in posts_data])
    topic_counts = {}
    for keyword in SIGNAL_CONFIG["high_value_keywords"]:
        count = all_content.lower().count(keyword)
        if count > 0:
            topic_counts[keyword] = count
    
    top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    if top_topics:
        report += "\n热门技术话题:\n"
        for topic, count in top_topics:
            report += f"- **{topic}**: 出现 {count} 次\n"
    else:
        report += "\n暂无显著技术话题聚焦\n"
    
    # 社区趋势
    report += """
### 社区趋势
"""
    
    categories = {}
    for post in posts_data:
        cat = post["category"]
        categories[cat] = categories.get(cat, 0) + 1
    
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        report += f"- **{cat}**: {count} 个帖子\n"
    
    # 行动建议
    report += """
---

## 行动建议

"""
    
    if high_signal:
        report += "### 立即行动 (Signal≥9)\n"
        report += "- 对高Signal内容进行深度学习\n"
        report += "- 提取可执行洞察并应用\n"
        report += "- 考虑与作者建立联系\n\n"
    
    report += """### 持续监控
- 继续关注热门话题的技术演进
- 跟踪高价值作者的后续动态
- 定期更新学习笔记

---

*报告生成: Moltbook深度扫描器*  
*协议: 超进化v3.5 - Signal评分机制*
"""
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    return report_file, high_signal

def main():
    # 读取提取的数据
    data_file = "data/moltbook/hot_posts_20260214_180524.json"
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    posts = data.get("posts", [])
    
    # 分析每个帖子
    analyzed_posts = []
    for post in posts:
        signal_data = calculate_signal(post)
        analysis = analyze_post(post, signal_data)
        analyzed_posts.append(analysis)
    
    # 按Signal排序
    analyzed_posts.sort(key=lambda x: x["signal"], reverse=True)
    
    # 生成报告
    report_file, high_signal = generate_learning_report(analyzed_posts)
    
    # 输出摘要
    print("="*60)
    print("Moltbook深度扫描完成")
    print("="*60)
    print(f"\n报告文件: {report_file}")
    print(f"高价值内容: {len(high_signal)} 个")
    
    print("\nSignal评分排行:")
    for post in analyzed_posts:
        star = "⭐" if post["signal"] >= 7 else ""
        print(f"  Signal {post['signal']}/10 | {post['votes']:>2}票/{post['comments']:>2}评 | {post['category']} | {post['title'][:50]}... {star}")
    
    return analyzed_posts

if __name__ == "__main__":
    main()
