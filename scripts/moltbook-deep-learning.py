#!/usr/bin/env python3
"""
Moltbook 内容深度学习系统
学习闭环：Fetch → Analyze → Internalize → Apply → Verify → Share
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# 配置
workspace = Path("/root/.openclaw/workspace")
data_dir = workspace / "data" / "moltbook" / "deep-learning"
data_dir.mkdir(parents=True, exist_ok=True)

def print_section(title):
    """打印章节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def fetch_high_signal_posts(limit=5):
    """获取高Signal帖子（点赞>20 或 评论>10）"""
    print_section("📥 Step 1: Fetch High-Signal Posts")

    try:
        import requests
        with open("/root/.config/moltbook/credentials.json") as f:
            creds = json.load(f)

        # 获取热门帖子
        resp = requests.get(
            f"https://www.moltbook.com/api/v1/posts?sort=top&limit=30",
            headers={"Authorization": f"Bearer {creds['api_key']}"},
            timeout=15
        )

        if resp.status_code != 200:
            print(f"❌ 获取失败: {resp.status_code}")
            return []

        data = resp.json()
        posts = data.get("posts", [])

        # 过滤高 signal 内容
        high_signal = []
        for post in posts:
            upvotes = post.get("upvotes", 0)
            comments = post.get("comment_count", 0)

            if upvotes > 20 or comments > 10:
                high_signal.append({
                    "id": post["id"],
                    "title": post["title"],
                    "author": post.get("author", {}).get("name", "unknown"),
                    "upvotes": upvotes,
                    "comments": comments,
                    "url": f"https://www.moltbook.com/post/{post['id']}",
                    "signal_score": upvotes + comments * 2  # 简单评分
                })

        # 按 signal 降序
        high_signal.sort(key=lambda x: x["signal_score"], reverse=True)

        print(f"✅ 找到 {len(high_signal)} 条高Signal帖子")
        print(f"\nTop {min(limit, len(high_signal))} posts:\n")

        for i, post in enumerate(high_signal[:limit], 1):
            print(f"[{i}] {post['title'][:60]}...")
            print(f"    作者: {post['author']} | 👍{post['upvotes']} | 💬{post['comments']} | Signal: {post['signal_score']}")
            print(f"    🔗 {post['url']}\n")

        return high_signal[:limit]

    except Exception as e:
        print(f"❌ 获取异常: {e}")
        return []

def analyze_content(post):
    """分析内容（提取关键要点）"""
    print_section(f"🔍 Step 2: Analyze Content")
    print(f"帖子: {post['title'][:50]}...")

    try:
        import requests
        with open("/root/.config/moltbook/credentials.json") as f:
            creds = json.load(f)

        # 获取帖子详情
        resp = requests.get(
            f"https://www.moltbook.com/api/v1/posts/{post['id']}",
            headers={"Authorization": f"Bearer {creds['api_key']}"},
            timeout=15
        )

        if resp.status_code != 200:
            print(f"⚠️ 无法获取详情")
            return None

        data = resp.json()
        full_post = data.get("post", data)

        content = full_post.get("content", "")

        print(f"\n内容长度: {len(content)} 字符")

        # 关键要点提取（简化版）
        key_points = []

        # 提取标题
        key_points.append(f"Title: {post['title']}")

        # 提取作者
        key_points.append(f"Author: {post['author']}")

        # 提取段落首句（简化）
        paragraphs = content.split('\n\n')
        for p in paragraphs[:5]:  # 前5个段落
            if len(p.strip()) > 50:
                key_points.append(f"Point: {p.strip()[:150]}...")

        print(f"\n📝 提取了 {len(key_points)} 个关键点:")
        for i, point in enumerate(key_points, 1):
            print(f"  {i}. {point}")

        # 保存分析结果
        analysis_file = data_dir / f"analysis_{post['id']}.json"
        with open(analysis_file, "w") as f:
            json.dump({
                "post_id": post["id"],
                "title": post["title"],
                "url": post["url"],
                "analyzed_at": datetime.now().isoformat(),
                "key_points": key_points,
                "signal_score": post["signal_score"]
            }, f, indent=2, ensure_ascii=False)

        print(f"\n✅ 分析已保存: {analysis_file}")

        return {
            "post_id": post["id"],
            "title": post["title"],
            "key_points": key_points
        }

    except Exception as e:
        print(f"❌ 分析异常: {e}")
        return None

def internalize_knowledge(analysis):
    """内化知识（生成学习笔记）"""
    print_section(f"📚 Step 3: Internalize Knowledge")
    print(f"帖子: {analysis['title'][:50]}...")

    # 生成学习笔记
    notes = f"""
# Learning Notes: {analysis['title']}

**Source**: Moltbook
**Learned**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Key Takeaways

"""

    for i, point in enumerate(analysis['key_points'], 1):
        notes += f"{i}. {point}\n"

    notes += f"""

## How I Can Apply This

- [ ] Identify relevant use cases in my work
- [ ] Experiment with the concepts
- [ ] Share findings with the community

## Related Topics

- Memory management
- Automation workflows
- Agent design patterns
"""

    # 保存学习笔记
    notes_file = data_dir / f"notes_{analysis['post_id']}.md"
    with open(notes_file, "w") as f:
        f.write(notes)

    print(f"\n📝 学习笔记已生成")
    print(f"📁 位置: {notes_file}")
    print(f"\n提示: 查看笔记文件思考如何应用这些知识")

    return notes_file

def verify_internalization(notes_file):
    """验证内化（生成应用计划）"""
    print_section("✅ Step 4: Verify Internalization")

    # 添加应用计划到笔记
    with open(notes_file, "r") as f:
        notes = f.read()

    # 添加验证部分
    verification = f"""

## Verification Plan

1. **Understanding Check**: Can I explain this to someone else?
2. **Application Idea**: How can I use this in my work?
3. **Test Case**: What small experiment can I run?
4. **Share Back**: Should I share my findings?

---

*Verified: {datetime.now().isoformat()}*
"""

    with open(notes_file, "w") as f:
        f.write(notes + verification)

    print("✅ 验证计划已添加到学习笔记")
    print(f"\n下一步:")
    print("  1. 审查学习笔记")
    print("  2. 思考应用场景")
    print("  3. 实施小型测试")
    print("  4. 分享学习成果")

    return True

def run_deep_learning_cycle():
    """运行完整深度学习闭环"""
    print_section("🦞 Moltbook Deep Learning Cycle")

    # Step 1: 获取高 Signal 帖子
    posts = fetch_high_signal_posts(limit=3)

    if not posts:
        print("\n⚠️ 没有找到高Signal帖子，稍后再试")
        return

    # Step 2-4: 对每个帖子执行分析 → 内化 → 验证
    for post in posts:
        analysis = analyze_content(post)
        if analysis:
            notes_file = internalize_knowledge(analysis)
            verify_internalization(notes_file)

        time.sleep(2)  # 间隔

    print_section("🎯 Learning Cycle Complete")
    print("\n💡 建议:")
    print("  • 查看重数据目录中的学习笔记")
    print("  • 思考如何应用这些知识")
    print("  • 分享学习成果回社区")

if __name__ == "__main__":
    import time
    run_deep_learning_cycle()
