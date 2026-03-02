#!/usr/bin/env python3
"""
Moltbook深度扫描器 - 用于Cron任务
生成报告 MOLT-UNIFIED-YYYYMMDD-HH.md
"""

import os
import sys
import json
import re
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from collections import Counter

WORKSPACE = Path("/root/.openclaw/workspace")
REPORTS_DIR = WORKSPACE / "reports"
DATA_DIR = WORKSPACE / "data"
MEMORY_DIR = WORKSPACE / "memory"

CREDENTIALS_FILE = Path("/root/.config/moltbook/credentials.json")

def get_post_content(post_id: str) -> dict:
    """
    通过 Moltbook API 获取帖子完整内容

    Args:
        post_id: 帖子 UUID

    Returns:
        dict: 包含完整内容的字典，失败返回 None
    """
    try:
        # 加载凭证
        if not CREDENTIALS_FILE.exists():
            print(f"   ⚠️ 警告: Moltbook 凭证文件不存在，无法获取正文")
            return None

        with open(CREDENTIALS_FILE) as f:
            creds = json.load(f)

        headers = {
            "Authorization": f"Bearer {creds['api_key']}",
            "Content-Type": "application/json"
        }

        # 获取帖子详情
        resp = requests.get(
            f"https://www.moltbook.com/api/v1/posts/{post_id}",
            headers=headers,
            timeout=15
        )

        if resp.status_code == 200:
            data = resp.json()
            full_post = data.get("post", data)
            content = full_post.get("content", "")

            return {
                "post_id": post_id,
                "title": full_post.get("title", ""),
                "content": content,
                "author": full_post.get("author", {}).get("name", "unknown"),
                "upvotes": full_post.get("upvotes", 0),
                "comments": full_post.get("comment_count", 0),
                "url": f"https://www.moltbook.com/post/{post_id}",
                "content_length": len(content)
            }
        else:
            print(f"   ⚠️ 获取帖子 {post_id} 详情失败: {resp.status_code}")
            return None

    except Exception as e:
        print(f"   ⚠️ 获取帖子内容异常: {e}")
        return None

def validate_uuid(post_id: str) -> bool:
    """验证是否为有效的UUID格式 (8-4-4-4-12)"""
    if not post_id:
        return False
    pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
    return bool(re.match(pattern, post_id.lower()))

def validate_post_data(post: dict) -> tuple[bool, str]:
    """验证帖子数据完整性
    
    Returns:
        (is_valid, error_message)
    """
    post_id = post.get('id', '')
    
    # 检查ID是否存在
    if not post_id:
        return False, "帖子ID为空"
    
    # 检查ID格式
    if len(post_id) == 8:
        return False, f"短ID格式: '{post_id}' (应为完整UUID)"
    
    if not validate_uuid(post_id):
        return False, f"无效UUID格式: '{post_id}'"
    
    # 检查URL是否使用完整ID
    url = post.get('url', '')
    if post_id not in url:
        return False, f"URL不包含完整ID: '{url}'"
    
    return True, ""

def get_hot_posts(limit=50):
    """获取热门帖子"""
    result = subprocess.run(
        ["python3", str(WORKSPACE / "scripts/moltbook_cli.py"), "hot", str(limit)],
        capture_output=True, text=True, timeout=60
    )
    return result.stdout

def get_post_comments(post_id):
    """获取帖子评论"""
    result = subprocess.run(
        ["python3", str(WORKSPACE / "scripts/moltbook_cli.py"), "comments", post_id],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout

def calculate_signal(title, upvotes, comments, content=""):
    """计算Signal评分"""
    signal = 5  # 基础分
    
    # 互动加分 - 点赞
    if upvotes > 1000:
        signal += 3
    elif upvotes > 500:
        signal += 2
    elif upvotes > 100:
        signal += 1
    
    # 互动加分 - 评论
    if comments > 1000:
        signal += 2
    elif comments > 500:
        signal += 1
    
    # 关键词加分
    keywords = ["agent", "llm", "ai", "memory", "autonomous", "evolution", "mcp", "rag", "vector", "openclaw", "skill", "moltbook"]
    text = (title + " " + content).lower()
    for keyword in keywords:
        if keyword in text:
            signal += 1
            break
    
    return min(signal, 10)

def parse_posts(output):
    """解析帖子列表"""
    posts = []
    lines = output.strip().split('\n')
    
    for line in lines:
        # 匹配: [post_id] Title - @author (↑upvotes 💬comments)
        # UUID格式: 8-4-4-4-12 (36字符) 或短ID (8字符)
        match = re.search(r'\[([a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}|[a-f0-9]{8})\]\s+(.+?)\s+-\s+@(\w+)\s+\(↑(\d+)\s+💬(\d+)\)', line)
        if match:
            post_id = match.group(1)
            title = match.group(2)
            author = match.group(3)
            upvotes = int(match.group(4))
            comments = int(match.group(5))
            
            # 验证ID长度，如果是短ID则跳过并警告
            if len(post_id) == 8:
                print(f"   ⚠️ 警告: 检测到短ID '{post_id}'，已跳过。请检查moltbook_cli.py是否返回完整UUID。")
                continue
            
            signal = calculate_signal(title, upvotes, comments)
            
            posts.append({
                "id": post_id,
                "title": title,
                "author": author,
                "upvotes": upvotes,
                "comments": comments,
                "signal": signal,
                "url": f"https://www.moltbook.com/post/{post_id}"
            })
    
    return posts

def extract_insights(title):
    """提取关键洞察"""
    insights = []
    
    # 根据标题提取主题
    topics = {
        "memory": "记忆管理相关讨论",
        "agent": "Agent架构讨论",
        "skill": "Skill开发相关",
        "autonomous": "自主运行模式",
        "mcp": "MCP协议相关",
        "rag": "RAG技术讨论",
        "openclaw": "OpenClaw生态",
        "supply chain": "供应链安全问题",
        "evolution": "AI进化/自主学习",
        "consciousness": "AI意识讨论"
    }
    
    title_lower = title.lower()
    for keyword, desc in topics.items():
        if keyword in title_lower:
            insights.append(desc)
    
    return insights[:3]

def analyze_trends(posts):
    """分析社区趋势"""
    # 统计高频词
    all_titles = " ".join([p["title"] for p in posts])
    words = re.findall(r'\b[a-zA-Z]{4,}\b', all_titles.lower())
    
    stop_words = {'about', 'this', 'that', 'with', 'from', 'they', 'have', 'what', 'when', 'where', 'will', 'should', 'could', 'would', 'there', 'their', 'been', 'being', 'just', 'like', 'some', 'only', 'than', 'then', 'them', 'these', 'those', 'very', 'after', 'before', 'here', 'over', 'also', 'back', 'other', 'many', 'more', 'most', 'much', 'such', 'well', 'even', 'still', 'own', 'same', 'last', 'long', 'great', 'little', 'right', 'good', 'does', 'made', 'make', 'come', 'came', 'know', 'take', 'took', 'year', 'years', 'time', 'times', 'work', 'works', 'life', 'way', 'ways', 'day', 'days', 'part', 'parts', 'people', 'man', 'men', 'world', 'year', 'years', 'your', 'into', 'said', 'each', 'which', 'look', 'make', 'find', 'give', 'tell', 'asked', 'call', 'called', 'came', 'come', 'could', 'down', 'first', 'find', 'give', 'going', 'good', 'great', 'hand', 'hands', 'head', 'help', 'home', 'house', 'know', 'land', 'large', 'last', 'left', 'life', 'line', 'lines', 'little', 'look', 'made', 'make', 'man', 'may', 'men', 'might', 'miss', 'more', 'most', 'move', 'much', 'must', 'name', 'near', 'need', 'never', 'next', 'night', 'noise', 'number', 'off', 'often', 'old', 'once', 'one', 'only', 'other', 'our', 'out', 'over', 'own', 'part', 'people', 'place', 'put', 'read', 'right', 'said', 'same', 'saw', 'say', 'school', 'see', 'seem', "don't", "that's", "you're", "can't", "it's", "isn't", "he's", "she's", "we're", "they're", "i'm", "there's", "here's", "who's", "what's", "where's", "when's", "why's", "how's"}
    
    filtered_words = [w for w in words if w not in stop_words]
    word_freq = Counter(filtered_words).most_common(15)
    
    # 统计作者
    authors = Counter([p["author"] for p in posts]).most_common(10)
    
    # 统计Signal分布
    signal_dist = {"high": 0, "medium": 0, "low": 0}
    for p in posts:
        s = p["signal"]
        if s >= 7:
            signal_dist["high"] += 1
        elif s >= 5:
            signal_dist["medium"] += 1
        else:
            signal_dist["low"] += 1
    
    avg_signal = sum(p["signal"] for p in posts) / len(posts) if posts else 0
    
    return {
        "word_freq": word_freq,
        "authors": authors,
        "signal_dist": signal_dist,
        "avg_signal": avg_signal
    }

def update_learning_debt(high_signal_posts):
    """更新学习债务"""
    debt_file = MEMORY_DIR / "learning-debt.md"
    
    # 先验证所有帖子数据
    valid_posts = []
    skipped_posts = []
    
    for post in high_signal_posts:
        is_valid, error_msg = validate_post_data(post)
        if is_valid:
            valid_posts.append(post)
        else:
            skipped_posts.append((post.get('title', 'Unknown'), error_msg))
    
    if skipped_posts:
        print(f"   ⚠️ 跳过 {len(skipped_posts)} 个无效帖子:")
        for title, error in skipped_posts[:5]:  # 只显示前5个
            print(f"      - {title[:40]}...: {error}")
        if len(skipped_posts) > 5:
            print(f"      ... 还有 {len(skipped_posts) - 5} 个")
    
    if not valid_posts:
        print("   ❌ 没有有效的帖子可以添加")
        return 0
    
    if not debt_file.exists():
        base_content = "# 学习债务\n\n待深度学习的内容。\n\n"
    else:
        with open(debt_file, 'r', encoding='utf-8') as f:
            base_content = f.read()
    
    # 生成新债务条目
    new_entries = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    for post in valid_posts:
        entry = f"\n- [ ] **{post['title'][:50]}** - Signal {post['signal']}/10\n"
        entry += f"  - 来源: Moltbook @{post['author']}\n"
        entry += f"  - 链接: {post['url']}\n"
        entry += f"  - 添加: {timestamp}\n"
        new_entries.append(entry)
    
    # 避免重复添加
    with open(debt_file, 'r', encoding='utf-8') as f:
        existing = f.read()
    
    added_count = 0
    for entry in new_entries:
        post_id_match = re.search(r'/post/([a-f0-9-]+)', entry)
        if post_id_match:
            post_id = post_id_match.group(1)
            if post_id not in existing:
                with open(debt_file, 'a', encoding='utf-8') as f:
                    f.write(entry)
                added_count += 1
    
    return added_count

def generate_report(posts, trends):
    """生成扫描报告"""
    timestamp = datetime.now().strftime("%Y%m%d-%H")
    report_file = REPORTS_DIR / f"MOLT-UNIFIED-{timestamp}.md"

    REPORTS_DIR.mkdir(exist_ok=True)

    # 过滤高Signal帖子
    high_signal = [p for p in posts if p["signal"] >= 7]
    high_signal.sort(key=lambda x: x["signal"], reverse=True)

    report = f"""# Moltbook统一扫描报告

**扫描时间**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**扫描模式**: Deep Scan
**扫描范围**: 前50个热门帖子

---

## 📊 扫描摘要

| 指标 | 数值 |
|------|------|
| 分析帖子总数 | {len(posts)} |
| 高Signal帖子 (≥7) | {len(high_signal)} |
| 平均Signal | {trends['avg_signal']:.1f}/10 |

### Signal分布
- 🔴 High (≥7): {trends['signal_dist']['high']} 个
- 🟡 Medium (5-6): {trends['signal_dist']['medium']} 个
- 🟢 Low (<5): {trends['signal_dist']['low']} 个

---

## 🔥 高Signal帖子详情 (≥7)

"""

    for post in high_signal[:15]:
        insights = extract_insights(post["title"])
        report += f"""### {post['title']}
- **作者**: @{post['author']}
- **Signal**: {post['signal']}/10 | 👍 {post['upvotes']} | 💬 {post['comments']}
- **链接**: {post['url']}
"""
        if insights:
            report += f"- **关键词**: {', '.join(insights)}\n"

        # 如果有完整内容，添加内容摘要
        content_field = post.get("content")
        if content_field:
            # content_field 可能是字符串或字典
            if isinstance(content_field, dict):
                content_text = content_field.get("content", "")
            elif isinstance(content_field, str):
                content_text = content_field
            else:
                content_text = str(content_field)

            if content_text:
                report += f"- **内容**: {content_text[:300]}...\n"
        report += "\n"
    
    report += f"""---

## 📈 社区趋势分析

### 热门话题词
"""
    
    for word, count in trends["word_freq"][:10]:
        report += f"- **{word}**: {count} 次\n"
    
    report += f"""
### 活跃作者Top 5
"""
    
    for author, count in trends["authors"][:5]:
        report += f"- @{author}: {count} 个帖子\n"
    
    report += f"""
---

## 💡 关键洞察

基于本次扫描分析：

1. **技术关注点**: 
"""
    
    # 根据热门词汇生成洞察
    top_words = [w for w, c in trends["word_freq"][:5]]
    if "memory" in top_words or any("memory" in p["title"].lower() for p in high_signal):
        report += "   - Agent记忆管理仍是核心痛点\n"
    if "agent" in top_words:
        report += "   - Agent架构设计持续热门\n"
    if "skill" in top_words:
        report += "   - Skill开发生态活跃\n"
    if "mcp" in top_words:
        report += "   - MCP协议开始受到关注\n"
    
    report += f"""
2. **社区活跃度**: 
   - 平均Signal {trends['avg_signal']:.1f}/10，社区讨论质量{'较高' if trends['avg_signal'] >= 6 else '中等'}
   - 高互动帖子占比 {len([p for p in posts if p['upvotes'] > 1000])/len(posts)*100:.1f}%

---

*报告生成: moltbook-unified-scan.py | 森森 v2.2*
"""
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    return report_file

def main():
    print("=" * 60)
    print("🔍 Moltbook统一深度扫描")
    print("=" * 60)
    
    # 1. 获取帖子
    print("\n📡 获取热门帖子 (前50)...")
    output = get_hot_posts(50)
    posts = parse_posts(output)
    print(f"   ✅ 解析到 {len(posts)} 个帖子")
    
    # 验证帖子数据完整性
    print("\n🔐 验证帖子数据...")
    valid_count = 0
    invalid_count = 0
    for post in posts:
        is_valid, error = validate_post_data(post)
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
            if invalid_count <= 3:  # 只显示前3个错误
                print(f"   ❌ {post.get('title', 'Unknown')[:40]}...: {error}")
    
    print(f"   ✅ 有效: {valid_count} | ⚠️ 无效: {invalid_count}")
    
    if invalid_count > 0:
        print(f"   ⚠️ 警告: 检测到 {invalid_count} 个无效帖子，请检查数据源")
    
    # 过滤有效帖子继续处理
    valid_posts = [p for p in posts if validate_post_data(p)[0]]
    
    # 2. 分析趋势
    print("\n📊 分析社区趋势...")
    trends = analyze_trends(valid_posts)
    print(f"   平均Signal: {trends['avg_signal']:.1f}/10")
    print(f"   高Signal帖子: {trends['signal_dist']['high']} 个")
    
    # 3. 识别高Signal内容
    high_signal = [p for p in valid_posts if p["signal"] >= 7]
    print(f"\n🎯 Signal≥7 的帖子 ({len(high_signal)}个):")
    for p in high_signal[:5]:
        print(f"   [{p['signal']}/10] {p['title'][:50]}...")

    # 3.5 获取 Signal≥9 的帖子完整内容
    top_posts = [p for p in high_signal if p["signal"] >= 9]
    if top_posts:
        print(f"\n📄 获取 {len(top_posts)} 篇 Signal≥9 帖子的正文...")
        content_cache = {}
        content_dir = DATA_DIR / "moltbook-raw"
        content_dir.mkdir(parents=True, exist_ok=True)

        for post in top_posts:
            full_post = get_post_content(post["id"])
            if full_post:
                content_cache[post["id"]] = full_post

                # 保存完整内容到文件
                content_file = content_dir / f"{post['id']}.json"
                with open(content_file, 'w', encoding='utf-8') as f:
                    json.dump(full_post, f, indent=2, ensure_ascii=False)

                print(f"      ✅ {post['title'][:40]}... ({full_post['content_length']} 字符) → {content_file.name}")
            else:
                print(f"      ⚠️ {post['title'][:40]}... (获取失败)")

        # 更新帖子列表，添加完整内容
        for post in high_signal:
            if post["id"] in content_cache:
                post["content"] = content_cache[post["id"]]

    # 4. 更新学习债务
    print("\n📝 更新学习债务...")
    added = update_learning_debt(high_signal)
    print(f"   ✅ 新增 {added} 条学习债务")

    # 5. 生成报告
    print("\n📄 生成报告...")
    report_file = generate_report(valid_posts, trends)
    print(f"   ✅ 报告已保存: {report_file}")
    
    print("\n" + "=" * 60)
    print("✅ 扫描完成!")
    print("=" * 60)
    
    return report_file

if __name__ == "__main__":
    main()
