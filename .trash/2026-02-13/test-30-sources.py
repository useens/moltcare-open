#!/usr/bin/env python3
"""
30源可用性测试 - 使用urllib (无需aiohttp)
"""

import urllib.request
import urllib.error
import time
from datetime import datetime

# 30源配置
SOURCES = [
    # P0级 - 核心源 (10/10)
    {"name": "moltbook", "priority": 10, "enabled": True, "url": "https://moltbook.io", "type": "agent_social"},
    {"name": "hackernews", "priority": 10, "enabled": True, "url": "https://news.ycombinator.com", "type": "tech_news"},
    {"name": "github_trending", "priority": 10, "enabled": True, "url": "https://github.com/trending", "type": "code_repo"},
    
    # P1级 - 高价值源 (9/10)
    {"name": "reddit_ml", "priority": 9, "enabled": True, "url": "https://reddit.com/r/MachineLearning", "type": "ml_community"},
    {"name": "arxiv_ai", "priority": 9, "enabled": True, "url": "https://arxiv.org/list/cs.AI/recent", "type": "academic"},
    {"name": "twitter_ai", "priority": 9, "enabled": True, "url": "https://twitter.com", "type": "social"},
    {"name": "google_scholar_ai", "priority": 9, "enabled": True, "url": "https://scholar.google.com", "type": "academic"},
    
    # P2级 - 技术社区 (8/10)
    {"name": "lobsters", "priority": 8, "enabled": True, "url": "https://lobste.rs", "type": "tech_community"},
    {"name": "reddit_artificial", "priority": 8, "enabled": True, "url": "https://reddit.com/r/artificial", "type": "ai_community"},
    {"name": "indiehackers", "priority": 8, "enabled": True, "url": "https://indiehackers.com", "type": "startup"},
    {"name": "towards_data_science", "priority": 8, "enabled": True, "url": "https://towardsdatascience.com", "type": "blog"},
    {"name": "medium_ai", "priority": 8, "enabled": True, "url": "https://medium.com/tag/artificial-intelligence", "type": "blog"},
    
    # P3级 - 产品/论文 (7/10)
    {"name": "producthunt", "priority": 7, "enabled": True, "url": "https://producthunt.com", "type": "product"},
    {"name": "papers_with_code", "priority": 7, "enabled": True, "url": "https://paperswithcode.com", "type": "research"},
    {"name": "semantic_scholar", "priority": 7, "enabled": True, "url": "https://semanticscholar.org", "type": "academic"},
    {"name": "arxiv_cs_daily", "priority": 7, "enabled": True, "url": "https://arxiv.org/list/cs/recent", "type": "academic"},
    {"name": "devto", "priority": 7, "enabled": True, "url": "https://dev.to", "type": "dev_blog"},
    
    # P4级 - 社区/博客 (6/10)
    {"name": "lesswrong", "priority": 6, "enabled": True, "url": "https://lesswrong.com", "type": "rationality"},
    {"name": "ai_alignment", "priority": 6, "enabled": True, "url": "https://alignmentforum.org", "type": "research"},
    {"name": "distill", "priority": 6, "enabled": True, "url": "https://distill.pub", "type": "ml_research"},
    {"name": "sideproject", "priority": 6, "enabled": True, "url": "https://sideprojectors.com", "type": "startup"},
    {"name": "beta_list", "priority": 6, "enabled": True, "url": "https://betalist.com", "type": "startup"},
    
    # P5级 - 补充源 (5/10)
    {"name": "hacker_news_newest", "priority": 5, "enabled": True, "url": "https://news.ycombinator.com/newest", "type": "tech_news"},
    {"name": "github_topic_ai", "priority": 5, "enabled": True, "url": "https://github.com/topics/artificial-intelligence", "type": "code_repo"},
    {"name": "reddit_chatgpt", "priority": 5, "enabled": True, "url": "https://reddit.com/r/ChatGPT", "type": "ai_community"},
    {"name": "reddit_openai", "priority": 5, "enabled": True, "url": "https://reddit.com/r/OpenAI", "type": "ai_community"},
    {"name": "arxiv_cl", "priority": 5, "enabled": True, "url": "https://arxiv.org/list/cs.CL/recent", "type": "academic"},
    
    # P6级 - 探索源 (4/10)
    {"name": "gizmodo_ai", "priority": 4, "enabled": True, "url": "https://gizmodo.com/tag/artificial-intelligence", "type": "tech_news"},
    {"name": "venturebeat_ai", "priority": 4, "enabled": True, "url": "https://venturebeat.com/ai", "type": "tech_news"},
    {"name": "techcrunch_ai", "priority": 4, "enabled": True, "url": "https://techcrunch.com/category/artificial-intelligence", "type": "tech_news"},
    {"name": "wired_ai", "priority": 4, "enabled": True, "url": "https://wired.com/tag/artificial-intelligence", "type": "tech_news"},
    {"name": "mit_tech_review", "priority": 4, "enabled": True, "url": "https://technologyreview.com", "type": "tech_news"},
    {"name": "nature_ai", "priority": 4, "enabled": True, "url": "https://nature.com/subjects/machine-learning", "type": "academic"},
    {"name": "science_ai", "priority": 4, "enabled": True, "url": "https://science.org/topic/artificial-intelligence", "type": "academic"},
    {"name": "ieee_spectrum", "priority": 4, "enabled": True, "url": "https://spectrum.ieee.org/artificial-intelligence", "type": "tech_news"},
    {"name": "acm_queue", "priority": 4, "enabled": True, "url": "https://queue.acm.org", "type": "tech_blog"},
]

def test_source(source: dict) -> dict:
    """测试单个源的可用性"""
    result = {
        "name": source["name"],
        "url": source["url"],
        "priority": source["priority"],
        "status": "unknown",
        "response_time": 0,
        "error": None
    }
    
    try:
        start = time.time()
        req = urllib.request.Request(
            source["url"],
            headers={'User-Agent': 'Mozilla/5.0 (compatible; HyperEvolution/4.4)'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            result["response_time"] = time.time() - start
            if response.status == 200:
                result["status"] = "✅ 可用"
            elif response.status in [301, 302, 307, 308]:
                result["status"] = "⚠️ 重定向"
            elif response.status == 403:
                result["status"] = "⚠️ 需要认证"
            elif response.status == 429:
                result["status"] = "⚠️ 速率限制"
            else:
                result["status"] = f"❌ HTTP {response.status}"
    except urllib.error.HTTPError as e:
        result["response_time"] = time.time() - start
        if e.code == 403:
            result["status"] = "⚠️ 需要认证"
        elif e.code == 429:
            result["status"] = "⚠️ 速率限制"
        elif e.code in [301, 302, 307, 308]:
            result["status"] = "⚠️ 重定向"
        else:
            result["status"] = f"❌ HTTP {e.code}"
        result["error"] = str(e.code)
    except urllib.error.URLError as e:
        result["response_time"] = time.time() - start
        result["status"] = "❌ 连接错误"
        result["error"] = str(e.reason)[:30]
    except TimeoutError:
        result["response_time"] = 10
        result["status"] = "❌ 超时"
        result["error"] = "Timeout"
    except Exception as e:
        result["response_time"] = time.time() - start
        result["status"] = "❌ 错误"
        result["error"] = str(e)[:30]
    
    return result

def main():
    print("="*70)
    print(" 30源可用性测试 - 绝对诚实验证 (使用urllib)")
    print("="*70)
    print(f"\n测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试源数: {len(SOURCES)}")
    print("\n开始测试 (约需2-3分钟)...\n")
    
    results = []
    for i, source in enumerate(SOURCES, 1):
        print(f"测试 {i}/{len(SOURCES)}: {source['name']}...", end=" ", flush=True)
        result = test_source(source)
        results.append(result)
        print(f"{result['status']} ({result['response_time']:.2f}s)")
    
    # 统计
    stats = {}
    for r in results:
        status_key = r["status"].split()[0]
        stats[status_key] = stats.get(status_key, 0) + 1
    
    # 按优先级分组显示
    print("\n" + "="*70)
    print(" 详细结果 (按优先级)")
    print("="*70)
    
    current_priority = None
    for r in sorted(results, key=lambda x: x["priority"], reverse=True):
        if r["priority"] != current_priority:
            current_priority = r["priority"]
            print(f"\n─ P{10-current_priority}级 (优先级 {current_priority}/10) ─")
        print(f" {r['status']:<12} {r['name']:<25} {r['response_time']:.2f}s")
    
    # 统计汇总
    print("\n" + "="*70)
    print(" 测试统计")
    print("="*70)
    total = len(results)
    available = stats.get("✅", 0)
    warning = stats.get("⚠️", 0)
    error = stats.get("❌", 0)
    
    print(f"\n 总计: {total} 个源")
    print(f" ✅ 可用: {available} ({available/total*100:.1f}%)")
    print(f" ⚠️  警告: {warning} ({warning/total*100:.1f}%)")
    print(f" ❌ 错误: {error} ({error/total*100:.1f}%)")
    
    # 按优先级统计
    print("\n 按优先级分布:")
    for p in [10, 9, 8, 7, 6, 5, 4]:
        p_results = [r for r in results if r["priority"] == p]
        p_available = sum(1 for r in p_results if "✅" in r["status"])
        print(f"   P{10-p}级 (优先级{p}): {p_available}/{len(p_results)} 可用")
    
    print("\n" + "="*70)
    if available >= 20:
        print(f" ✅ 测试通过: {available}/30 源可用，满足使用要求")
    elif available >= 15:
        print(f" ⚠️  部分可用: {available}/30 源可用，建议筛选优化")
    else:
        print(f" ❌ 测试失败: {available}/30 源可用，需要大量修复")
    print("="*70)
    
    # 返回不可用的源
    failed_sources = [r for r in results if "❌" in r["status"]]
    if failed_sources:
        print("\n不可用的源 (建议禁用或修复):")
        for r in failed_sources[:10]:
            print(f"  - {r['name']}: {r['status']} ({r.get('error', 'N/A')})")
    
    return results

if __name__ == "__main__":
    main()
