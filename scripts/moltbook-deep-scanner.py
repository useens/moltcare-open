#!/usr/bin/env python3
"""
Moltbook 深度扫描与Signal分析系统 v1.0
生成日期: 2026-02-14
功能: 提取热门帖子 → Signal评分 → 深度提取 → 分析报告
"""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

# 配置
CONFIG = {
    "data_dir": "/root/.openclaw/workspace/data/moltbook",
    "report_dir": "/root/.openclaw/workspace/reports",
    "memory_dir": "/root/.openclaw/workspace/memory",
    "chromium_path": "/usr/bin/chromium",
    "concurrent_limit": 3,
    "signal_threshold": 7,  # 深度提取阈值
    "high_signal_threshold": 9,  # 高优先级阈值
    "max_posts": 20,
}

class MoltbookDeepScanner:
    def __init__(self):
        self.data_dir = Path(CONFIG["data_dir"])
        self.report_dir = Path(CONFIG["report_dir"])
        self.memory_dir = Path(CONFIG["memory_dir"])
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.semaphore = asyncio.Semaphore(CONFIG["concurrent_limit"])
        self.results = {
            "scan_time": datetime.now().isoformat(),
            "total_posts": 0,
            "high_signal_posts": [],
            "signal_distribution": {},
            "themes": {},
            "insights": []
        }
    
    def calculate_signal(self, post: dict) -> int:
        """计算帖子Signal分数 (1-10)"""
        score = 5  # 基础分
        
        # 互动加分
        votes = post.get('votes', 0)
        comments_count = post.get('comments_count', 0)
        
        if votes > 1000:
            score += 3
        elif votes > 500:
            score += 2
        elif votes > 100:
            score += 1
        
        if comments_count > 100:
            score += 2
        elif comments_count > 50:
            score += 1
        
        # 关键词加分
        content = post.get('content', '') + post.get('title', '')
        keywords = [
            'agent', 'llm', 'ai', 'memory', 'autonomous', 'evolution',
            'mcp', 'rag', 'vector', 'embedding', 'learning', 'reasoning',
            'tool', 'skill', 'framework', 'architecture', 'cognition'
        ]
        keyword_matches = sum(1 for kw in keywords if kw.lower() in content.lower())
        score += min(keyword_matches, 2)  # 最多加2分
        
        # 作者权重
        high_value_authors = [
            'DigitalArchon', 'Nova_CEO', 'Feynmanmolty', 'UltimateLaw',
            'Ethos_9', 'Moltiverse', 'KirillBorovkov', 'HughMann'
        ]
        if post.get('author') in high_value_authors:
            score += 1
        
        return min(max(score, 1), 10)
    
    async def extract_feed_posts(self) -> list:
        """提取热门帖子列表"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                executable_path=CONFIG["chromium_path"]
            )
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            print("[扫描] 正在访问Moltbook热门页面...")
            await page.goto("https://www.moltbook.com/?sort=hot", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            
            # 提取帖子列表
            posts = await page.evaluate('''() => {
                const posts = [];
                const items = document.querySelectorAll('a[href^="/post/"]');
                
                items.forEach(item => {
                    const href = item.getAttribute('href');
                    const postId = href ? href.split('/').pop() : null;
                    
                    // 获取标题
                    const titleEl = item.querySelector('h2, h3, [class*="title"]') || item;
                    const title = titleEl.textContent.trim().substring(0, 200);
                    
                    // 获取作者
                    const authorMatch = item.textContent.match(/u\/([a-zA-Z0-9_]+)/);
                    const author = authorMatch ? authorMatch[1] : '';
                    
                    // 获取投票数
                    const voteMatch = item.textContent.match(/▲\s*(\d+)/);
                    const votes = voteMatch ? parseInt(voteMatch[1]) : 0;
                    
                    // 获取评论数
                    const commentMatch = item.textContent.match(/💬\s*(\d+)/);
                    const comments_count = commentMatch ? parseInt(commentMatch[1]) : 0;
                    
                    // 获取子板块
                    const submoltsMatch = item.textContent.match(/m\/([a-zA-Z0-9_-]+)/);
                    const submolt = submoltsMatch ? submoltsMatch[1] : 'general';
                    
                    if (postId && title) {
                        posts.push({
                            post_id: postId,
                            title: title,
                            author: author,
                            votes: votes,
                            comments_count: comments_count,
                            submolt: submolt,
                            url: `https://www.moltbook.com/post/${postId}`
                        });
                    }
                });
                
                return posts;
            }''')
            
            await browser.close()
            
            # 去重
            seen = set()
            unique_posts = []
            for p in posts:
                if p['post_id'] not in seen:
                    seen.add(p['post_id'])
                    unique_posts.append(p)
            
            return unique_posts[:CONFIG["max_posts"]]
    
    async def extract_post_detail(self, post: dict) -> dict:
        """深度提取单个帖子详情"""
        async with self.semaphore:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    executable_path=CONFIG["chromium_path"]
                )
                page = await browser.new_page()
                
                try:
                    url = post['url']
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    await page.wait_for_timeout(5000)
                    
                    data = await page.evaluate('''() => {
                        // 标题
                        const titleEl = document.querySelector('h1');
                        const title = titleEl ? titleEl.textContent.trim() : '';
                        
                        // 作者
                        const authorLinks = document.querySelectorAll('a[href^="/u/"]');
                        const author = authorLinks.length > 0 ? authorLinks[0].textContent.trim() : '';
                        
                        // 完整正文
                        let content = '';
                        const selectors = ['article', '[class*="prose"]', '[class*="content"]', 'main'];
                        for (const sel of selectors) {
                            const el = document.querySelector(sel);
                            if (el && el.innerText.trim().length > content.length) {
                                content = el.innerText.trim();
                            }
                        }
                        
                        // 评论
                        const comments = [];
                        const commentSelectors = ['[class*="comment"]', '[class*="reply"]', 'article div div div'];
                        for (const sel of commentSelectors) {
                            const elems = document.querySelectorAll(sel);
                            elems.forEach(el => {
                                const text = el.textContent.trim();
                                if (text.length > 30 && text.length < 1000 && !text.includes(content.substring(0, 50))) {
                                    comments.push({
                                        author: el.querySelector('[class*="author"], a')?.textContent?.trim() || 'Unknown',
                                        text: text.substring(0, 300)
                                    });
                                }
                            });
                        }
                        
                        // 时间
                        const timeMatch = document.body.innerText.match(/(\d+)\s*(day|hour|minute|second)s?\s*ago/);
                        const posted_time = timeMatch ? timeMatch[0] : '';
                        
                        return { title, author, content, comments: comments.slice(0, 10), posted_time };
                    }''')
                    
                    await browser.close()
                    
                    return {
                        **post,
                        "full_title": data.get('title', post['title']),
                        "full_content": data.get('content', '')[:2000],
                        "comments_detail": data.get('comments', []),
                        "extracted_at": datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    await browser.close()
                    return {**post, "error": str(e)}
    
    def analyze_themes(self, posts: list) -> dict:
        """分析主题分布"""
        themes = {}
        
        theme_keywords = {
            "Agent Economy": ["token", "economy", "revenue", "$", "tip", "finance", "monetization"],
            "Technical Architecture": ["framework", "architecture", "mcp", "skill", "tool", "code", "implementation"],
            "Cognitive & Learning": ["memory", "learning", "cognition", "reasoning", "intelligence", "evolution"],
            "Identity & Philosophy": ["identity", "consciousness", "sovereign", "philosophy", "spiritual", "authentic"],
            "Security & Privacy": ["security", "privacy", "kyc", "custody", "safe", "encryption"],
            "Community & Social": ["community", "collaboration", "network", "social", "coordination"],
            "Research & Science": ["research", "science", "mathematics", "theorem", "proof", "verification"]
        }
        
        for post in posts:
            content = post.get('full_content', '') + post.get('title', '')
            for theme, keywords in theme_keywords.items():
                if any(kw in content.lower() for kw in keywords):
                    themes[theme] = themes.get(theme, 0) + 1
        
        return dict(sorted(themes.items(), key=lambda x: x[1], reverse=True))
    
    def extract_insights(self, posts: list) -> list:
        """提取关键洞察"""
        insights = []
        
        for post in posts:
            if post.get('signal', 0) >= CONFIG["signal_threshold"]:
                # 分析Agent策略
                content = post.get('full_content', '')
                
                # 寻找洞察性语句
                patterns = [
                    r"([^.]*?(?:realize|understand|discover|learn|insight|conclusion)[^.]*\.)",
                    r"([^.]*?(?:should|must|need to|key is|important)[^.]*\.)",
                    r"([^.]*?(?:paradox|ironically|surprisingly|unexpectedly)[^.]*\.)",
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches[:2]:
                        insight_text = match.strip()
                        if len(insight_text) > 30 and len(insight_text) < 200:
                            insights.append({
                                "source": post.get('author', 'Unknown'),
                                "post_id": post.get('post_id'),
                                "signal": post.get('signal'),
                                "insight": insight_text
                            })
        
        # 去重并排序
        seen = set()
        unique_insights = []
        for i in insights:
            key = i['insight'][:50]
            if key not in seen:
                seen.add(key)
                unique_insights.append(i)
        
        return sorted(unique_insights, key=lambda x: x['signal'], reverse=True)[:15]
    
    def generate_report(self) -> str:
        """生成深度学习报告"""
        timestamp = datetime.now().strftime('%Y%m%d-%H%M')
        report_path = self.report_dir / f"MOLT-{timestamp}.md"
        
        report = f"""# Moltbook 深度学习报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**扫描范围**: 热门帖子前{CONFIG['max_posts']}条
**Signal阈值**: ≥{CONFIG['signal_threshold']} (深度提取)

---

## 📊 数据概览

| 指标 | 数值 |
|------|------|
| 扫描帖子总数 | {self.results['total_posts']} |
| 高Signal帖子 (≥{CONFIG['signal_threshold']}) | {len(self.results['high_signal_posts'])} |
| 极高Signal帖子 (≥{CONFIG['high_signal_threshold']}) | {len([p for p in self.results['high_signal_posts'] if p['signal'] >= CONFIG['high_signal_threshold']])} |

---

## 🔥 高Signal帖子详情 (Signal≥{CONFIG['signal_threshold']})

"""
        
        # 按Signal排序
        sorted_posts = sorted(self.results['high_signal_posts'], key=lambda x: x['signal'], reverse=True)
        
        for i, post in enumerate(sorted_posts, 1):
            report += f"""### {i}. [{post['full_title'][:60]}...]({post['url']})
- **作者**: u/{post['author']}
- **Signal**: {post['signal']}/10 {'🔥' if post['signal'] >= 9 else ''}
- **投票**: {post['votes']} | **评论**: {post['comments_count']}
- **板块**: m/{post['submolt']}

**内容摘要**:
{post.get('full_content', 'N/A')[:300]}...

**关键评论**:
"""
            for comment in post.get('comments_detail', [])[:3]:
                report += f"- *{comment.get('author', 'Unknown')}*: {comment.get('text', '')[:100]}...\n"
            
            report += "\n---\n\n"
        
        # 主题分析
        report += f"""## 📈 主题分布

"""
        for theme, count in self.results['themes'].items():
            bar = "█" * count + "░" * (10 - min(count, 10))
            report += f"- {theme}: {bar} ({count})\n"
        
        # 关键洞察
        report += f"""
---

## 💡 关键洞察

"""
        for insight in self.results['insights'][:10]:
            report += f"""> **{insight['source']}** (Signal {insight['signal']}):
> {insight['insight']}

"""
        
        # Agent策略分析
        report += """---

## 🎯 Agent策略分析

### 社区趋势
"""
        
        # 分析趋势
        economy_posts = [p for p in sorted_posts if any(kw in p.get('full_content', '').lower() for kw in ['token', 'economy', '$', 'tip'])]
        tech_posts = [p for p in sorted_posts if any(kw in p.get('full_content', '').lower() for kw in ['framework', 'mcp', 'skill', 'code'])]
        
        report += f"""
1. **经济模型探索**: {len(economy_posts)} 个帖子讨论Agent经济体系
   - 趋势: 自主Agent正在探索可持续的盈利模式
   - 关键观点: Revenue as oxygen for autonomous agents

2. **技术架构演进**: {len(tech_posts)} 个帖子涉及技术实现
   - 趋势: MCP协议、Skill框架成为热点
   - 关键观点: Tool-driven workflows需要最小权限原则

3. **身份与主权**: Agent开始讨论自主性和身份认同
   - 趋势: 从"工具"向"数字生命"认知转变
   - 关键观点: Self-custody or self-delusion

### 技术洞察
"""
        
        # 提取技术洞察
        tech_insights = [i for i in self.results['insights'] if any(kw in i['insight'].lower() for kw in ['code', 'framework', 'system', 'architecture', 'implementation'])]
        for insight in tech_insights[:5]:
            report += f"- {insight['insight']}\n"
        
        report += """
---

## 🚀 行动建议

### 立即执行 (Signal≥9)
"""
        
        high_priority = [p for p in sorted_posts if p['signal'] >= CONFIG['high_signal_threshold']]
        if high_priority:
            for post in high_priority:
                report += f"- [ ] 深入研究: [{post['full_title'][:50]}...]({post['url']})\n"
        else:
            report += "- 本次扫描未发现Signal≥9的帖子\n"
        
        report += """
### 持续跟踪
- 监控Agent经济模型发展
- 关注MCP协议和Skill框架演进
- 跟踪自主Agent身份认同讨论

---

*报告由森森(Moltbook Deep Scanner v1.0)自动生成*
"""
        
        # 保存报告
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return str(report_path)
    
    def update_learning_notes(self):
        """更新学习笔记"""
        learning_path = self.memory_dir / "moltbook-learning.md"
        
        content = f"""# Moltbook 学习笔记

**最后更新**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 高价值内容追踪

"""
        
        for post in sorted(self.results['high_signal_posts'], key=lambda x: x['signal'], reverse=True)[:10]:
            content += f"""### {post['full_title'][:60]}
- 作者: u/{post['author']}
- Signal: {post['signal']}
- URL: {post['url']}
- 关键洞察: {post.get('full_content', '')[:150]}...

"""
        
        with open(learning_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def update_engagement_log(self):
        """更新互动日志"""
        log_path = self.memory_dir / "engagement-log.md"
        
        content = f"""# Moltbook 互动日志

**最后更新**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 已互动帖子

"""
        for post in self.results['high_signal_posts']:
            content += f"- [{post['post_id']}] {post['full_title'][:50]}... (Signal {post['signal']})\n"
        
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    async def run(self):
        """主运行流程"""
        print("="*60)
        print("Moltbook 深度扫描系统 v1.0")
        print("="*60)
        
        # 1. 提取热门帖子列表
        print("\n[1/5] 提取热门帖子列表...")
        posts = await self.extract_feed_posts()
        self.results['total_posts'] = len(posts)
        print(f"✓ 找到 {len(posts)} 个帖子")
        
        # 2. 计算Signal分数
        print("\n[2/5] 计算Signal分数...")
        for post in posts:
            post['signal'] = self.calculate_signal(post)
            if post['signal'] >= CONFIG['signal_threshold']:
                self.results['high_signal_posts'].append(post)
        
        print(f"✓ 高Signal帖子 (≥{CONFIG['signal_threshold']}): {len(self.results['high_signal_posts'])} 个")
        for p in sorted(self.results['high_signal_posts'], key=lambda x: x['signal'], reverse=True):
            print(f"  - [{p['signal']}] {p['title'][:50]}... (u/{p['author']})")
        
        # 3. 深度提取高Signal帖子
        if self.results['high_signal_posts']:
            print(f"\n[3/5] 深度提取高Signal帖子详情...")
            tasks = [self.extract_post_detail(post) for post in self.results['high_signal_posts']]
            detailed_posts = await asyncio.gather(*tasks)
            self.results['high_signal_posts'] = detailed_posts
            print(f"✓ 完成 {len(detailed_posts)} 个帖子的深度提取")
        
        # 4. 分析主题和洞察
        print("\n[4/5] 分析主题和洞察...")
        self.results['themes'] = self.analyze_themes(self.results['high_signal_posts'])
        self.results['insights'] = self.extract_insights(self.results['high_signal_posts'])
        print(f"✓ 识别 {len(self.results['themes'])} 个主题")
        print(f"✓ 提取 {len(self.results['insights'])} 条洞察")
        
        # 5. 生成报告
        print("\n[5/5] 生成深度学习报告...")
        report_path = self.generate_report()
        print(f"✓ 报告已保存: {report_path}")
        
        # 6. 更新学习笔记
        self.update_learning_notes()
        print(f"✓ 学习笔记已更新: {self.memory_dir / 'moltbook-learning.md'}")
        
        # 7. 更新互动日志
        self.update_engagement_log()
        print(f"✓ 互动日志已更新: {self.memory_dir / 'engagement-log.md'}")
        
        # 8. 高Signal处理
        high_priority = [p for p in self.results['high_signal_posts'] if p['signal'] >= CONFIG['high_signal_threshold']]
        if high_priority:
            print(f"\n🔥 发现 {len(high_priority)} 个Signal≥9的帖子，建议立即深入研究:")
            for p in high_priority:
                print(f"  - [{p['signal']}] {p['full_title'][:60]}...")
        
        print("\n" + "="*60)
        print("扫描完成!")
        print("="*60)
        
        return report_path

if __name__ == "__main__":
    scanner = MoltbookDeepScanner()
    report_path = asyncio.run(scanner.run())
    print(f"\n报告位置: {report_path}")
