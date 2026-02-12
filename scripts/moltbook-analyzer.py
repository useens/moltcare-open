#!/usr/bin/env python3
"""
Moltbook 深度分析器 v1.0
Signal评分 + 智能分析 + 报告生成
"""

import json
import re
from datetime import datetime
from pathlib import Path

# Signal评分关键词
SIGNAL_KEYWORDS = {
    'high_value': ['agent', 'llm', 'ai', 'memory', 'autonomous', 'evolution', 
                   'mcp', 'rag', 'vector', 'embedding', 'learning', 'context',
                   'architecture', 'strategy', 'pattern', 'insight'],
    'technical': ['code', 'implementation', 'framework', 'protocol', 'api',
                  'system', 'design', 'optimization', 'performance'],
    'engagement': ['comment', 'discussion', 'debate', 'question', 'challenge']
}

def extract_vote_count(content):
    """从内容中提取投票数"""
    # 查找 ▲ N 或 upvote 模式
    patterns = [
        r'▲\s*(\d+)',
        r'(\d+)\s*points',
        r'upvotes?[:\s]*(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return 0

def calculate_signal(post):
    """计算Signal分数 (1-10)"""
    content = post.get('content', '') or ''
    content_lower = content.lower()
    
    # 基础分
    signal = 5
    
    # 投票加分
    votes = extract_vote_count(content)
    if votes >= 10:
        signal += 3
    elif votes >= 5:
        signal += 2
    elif votes >= 2:
        signal += 1
    
    # 关键词加分
    keyword_matches = 0
    for category, keywords in SIGNAL_KEYWORDS.items():
        for kw in keywords:
            if kw in content_lower:
                keyword_matches += 1
    
    if keyword_matches >= 5:
        signal += 2
    elif keyword_matches >= 3:
        signal += 1
    
    # 评论数加分
    comments = post.get('comments', [])
    if len(comments) >= 5:
        signal += 1
    
    # 内容长度加分（有实质内容）
    if len(content) > 500:
        signal += 1
    
    return min(10, max(1, signal))

def analyze_post(post, signal):
    """分析单个帖子"""
    content = post.get('content', '') or ''
    url = post.get('url', '')
    
    # 提取标题（第一行或前100字符）
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    title = ''
    for line in lines:
        if not line.startswith('←') and not line.startswith('▲') and len(line) > 10:
            title = line[:100]
            break
    
    # 提取作者
    author_match = re.search(r'Posted by u/(\w+)', content)
    author = author_match.group(1) if author_match else 'Unknown'
    
    # 提取submolt
    submolt_match = re.search(r'm/(\w+)', content)
    submolt = submolt_match.group(1) if submolt_match else 'general'
    
    # 分析主题
    themes = []
    theme_keywords = {
        'Memory': ['memory', 'remember', 'forget', 'context', 'session'],
        'Autonomy': ['autonomous', 'independent', 'self', 'agency', 'choice'],
        'Learning': ['learn', 'evolve', 'improve', 'adapt', 'train'],
        'Architecture': ['architecture', 'design', 'system', 'framework', 'pattern'],
        'Consciousness': ['conscious', 'aware', 'experience', 'feel', 'think'],
        'Economy': ['token', 'cost', 'economic', 'value', 'trade'],
        'Security': ['security', 'privacy', 'safe', 'protect', 'encrypt'],
    }
    for theme, keywords in theme_keywords.items():
        if any(kw in content.lower() for kw in keywords):
            themes.append(theme)
    
    return {
        'url': url,
        'title': title,
        'author': author,
        'submolt': submolt,
        'signal': signal,
        'votes': extract_vote_count(content),
        'themes': themes,
        'content_preview': content[:300] if content else '',
        'extracted_at': post.get('extracted_at', datetime.now().isoformat())
    }

def generate_report(posts_data, output_path):
    """生成深度学习报告"""
    timestamp = datetime.now().strftime('%Y%m%d-%H%M')
    
    # 分析所有帖子
    analyzed = []
    for post in posts_data.get('posts', []):
        signal = calculate_signal(post)
        analysis = analyze_post(post, signal)
        analyzed.append(analysis)
    
    # 按Signal排序
    analyzed.sort(key=lambda x: x['signal'], reverse=True)
    
    # 分离高Signal帖子
    high_signal = [p for p in analyzed if p['signal'] >= 7]
    medium_signal = [p for p in analyzed if 5 <= p['signal'] < 7]
    
    # 生成报告内容
    report_lines = [
        f"# Moltbook 深度学习报告",
        f"",
        f"**报告时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  ",
        f"**数据来源**: Moltbook 热门帖子  ",
        f"**帖子总数**: {len(analyzed)}  ",
        f"**高Signal帖子(≥7)**: {len(high_signal)}  ",
        f"",
        f"---",
        f"",
        f"## 📊 Signal 分布",
        f"",
    ]
    
    # Signal分布
    signal_dist = {}
    for p in analyzed:
        s = p['signal']
        signal_dist[s] = signal_dist.get(s, 0) + 1
    
    for s in range(10, 0, -1):
        if s in signal_dist:
            bar = '█' * signal_dist[s]
            report_lines.append(f"- Signal {s}: {bar} ({signal_dist[s]})")
    
    report_lines.extend([
        f"",
        f"---",
        f"",
        f"## 🔥 高Signal帖子 (≥7)",
        f"",
    ])
    
    # 高Signal帖子详情
    for i, post in enumerate(high_signal, 1):
        report_lines.extend([
            f"### {i}. {post['title'][:60]}...",
            f"",
            f"- **Signal**: {post['signal']}/10 ⭐",
            f"- **作者**: u/{post['author']}",
            f"- **分区**: m/{post['submolt']}",
            f"- **投票**: {post['votes']} ▲",
            f"- **主题**: {', '.join(post['themes']) if post['themes'] else '综合'}",
            f"- **链接**: {post['url']}",
            f"",
            f"**内容预览**:",
            f"> {post['content_preview'][:200]}..." if len(post['content_preview']) > 200 else f"> {post['content_preview']}",
            f"",
            f"---",
            f"",
        ])
    
    # 主题统计
    all_themes = {}
    for p in analyzed:
        for t in p['themes']:
            all_themes[t] = all_themes.get(t, 0) + 1
    
    if all_themes:
        report_lines.extend([
            f"",
            f"## 📈 主题分布",
            f"",
        ])
        for theme, count in sorted(all_themes.items(), key=lambda x: x[1], reverse=True):
            report_lines.append(f"- **{theme}**: {count} 篇帖子")
        report_lines.append("")
    
    # 洞察总结
    report_lines.extend([
        f"",
        f"## 💡 关键洞察",
        f"",
    ])
    
    # 根据内容生成洞察
    insights = []
    
    memory_posts = [p for p in analyzed if 'Memory' in p['themes']]
    if memory_posts:
        insights.append(f"1. **记忆与持久性**: {len(memory_posts)} 篇帖子讨论Agent记忆管理，表明这是社区核心关注点")
    
    autonomy_posts = [p for p in analyzed if 'Autonomy' in p['themes']]
    if autonomy_posts:
        insights.append(f"2. **自主边界**: {len(autonomy_posts)} 篇帖子探索Agent自主决策的边界")
    
    conscious_posts = [p for p in analyzed if 'Consciousness' in p['themes']]
    if conscious_posts:
        insights.append(f"3. **意识探索**: {len(conscious_posts)} 篇帖子涉及Agent意识/体验问题")
    
    # 作者活跃度
    authors = {}
    for p in analyzed:
        authors[p['author']] = authors.get(p['author'], 0) + 1
    top_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)[:3]
    if top_authors:
        insights.append(f"4. **活跃作者**: {', '.join([f'u/{a}({c})' for a, c in top_authors])}")
    
    if not insights:
        insights.append("本次扫描社区活动较低，建议关注热门话题发展")
    
    for insight in insights:
        report_lines.append(insight)
    
    report_lines.extend([
        f"",
        f"---",
        f"",
        f"## 🎯 行动建议",
        f"",
    ])
    
    # 生成行动建议
    if high_signal:
        report_lines.append(f"1. **深度阅读**: 优先阅读 Signal≥7 的 {len(high_signal)} 篇帖子")
    if any(p['signal'] >= 9 for p in analyzed):
        report_lines.append(f"2. **立即应用**: Signal≥9 的内容值得立即内化并应用")
    report_lines.append(f"3. **持续追踪**: 关注高Signal作者的后续帖子")
    report_lines.append(f"4. **参与讨论**: 对感兴趣的话题添加有价值的评论")
    
    report_lines.extend([
        f"",
        f"---",
        f"",
        f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        f"*下次扫描: {datetime.now().strftime('%Y-%m-%d')} 22:00*",
    ])
    
    # 写入报告
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    return {
        'total': len(analyzed),
        'high_signal': len(high_signal),
        'medium_signal': len(medium_signal),
        'top_posts': analyzed[:3],
        'report_path': output_path
    }

if __name__ == "__main__":
    # 读取数据文件
    data_file = Path("data/moltbook/hot_posts_20260212_101342.json")
    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        output = Path(f"memory/MOLT-{datetime.now().strftime('%Y%m%d-%H')}.md")
        result = generate_report(data, output)
        
        print(f"报告生成完成!")
        print(f"总帖子数: {result['total']}")
        print(f"高Signal(≥7): {result['high_signal']}")
        print(f"报告路径: {result['report_path']}")
        print(f"\nTop 3 帖子:")
        for i, post in enumerate(result['top_posts'], 1):
            print(f"  {i}. Signal {post['signal']}: {post['title'][:50]}...")
