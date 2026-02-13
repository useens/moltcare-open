#!/usr/bin/env python3
"""
30源并发验证测试 - 仅无需API的源
"""

import urllib.request
import urllib.error
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 30源配置 - 移除需要API的源
SOURCES = [
    # P0级 - 核心源 (10/10) - 无需API
    {"name": "moltbook", "priority": 10, "enabled": True, "url": "https://moltbook.io"},
    {"name": "hackernews", "priority": 10, "enabled": True, "url": "https://news.ycombinator.com"},
    {"name": "github_trending", "priority": 10, "enabled": True, "url": "https://github.com/trending"},
    
    # P1级 - 高价值源 (9/10) - 仅保留arxiv
    {"name": "arxiv_ai", "priority": 9, "enabled": True, "url": "https://arxiv.org/list/cs.AI/recent"},
    
    # P2级 - 技术社区 (8/10) - 移除reddit
    {"name": "lobsters", "priority": 8, "enabled": True, "url": "https://lobste.rs"},
    {"name": "indiehackers", "priority": 8, "enabled": True, "url": "https://indiehackers.com"},
    {"name": "towards_data_science", "priority": 8, "enabled": True, "url": "https://towardsdatascience.com"},
    {"name": "devto_ai", "priority": 8, "enabled": True, "url": "https://dev.to/t/ai"},
    
    # P3级 - 产品/论文 (7/10)
    {"name": "producthunt", "priority": 7, "enabled": True, "url": "https://producthunt.com"},
    {"name": "papers_with_code", "priority": 7, "enabled": True, "url": "https://paperswithcode.com"},
    {"name": "arxiv_cs_daily", "priority": 7, "enabled": True, "url": "https://arxiv.org/list/cs/recent"},
    {"name": "huggingface_papers", "priority": 7, "enabled": True, "url": "https://huggingface.co/papers"},
    
    # P4级 - 社区/博客 (6/10)
    {"name": "lesswrong", "priority": 6, "enabled": True, "url": "https://lesswrong.com"},
    {"name": "distill", "priority": 6, "enabled": True, "url": "https://distill.pub"},
    {"name": "sideproject", "priority": 6, "enabled": True, "url": "https://sideprojectors.com"},
    {"name": "beta_list", "priority": 6, "enabled": True, "url": "https://betalist.com"},
    
    # P5级 - 补充源 (5/10)
    {"name": "hacker_news_newest", "priority": 5, "enabled": True, "url": "https://news.ycombinator.com/newest"},
    {"name": "github_topic_ai", "priority": 5, "enabled": True, "url": "https://github.com/topics/artificial-intelligence"},
    {"name": "arxiv_cl", "priority": 5, "enabled": True, "url": "https://arxiv.org/list/cs.CL/recent"},
    {"name": "ai_weirdness", "priority": 5, "enabled": True, "url": "https://aiweirdness.com"},
    
    # P6级 - 科技新闻 (4/10)
    {"name": "gizmodo_ai", "priority": 4, "enabled": True, "url": "https://gizmodo.com/tag/artificial-intelligence"},
    {"name": "venturebeat_ai", "priority": 4, "enabled": True, "url": "https://venturebeat.com/ai"},
    {"name": "techcrunch_ai", "priority": 4, "enabled": True, "url": "https://techcrunch.com/category/artificial-intelligence"},
    {"name": "mit_tech_review", "priority": 4, "enabled": True, "url": "https://technologyreview.com"},
    {"name": "ieee_spectrum", "priority": 4, "enabled": True, "url": "https://spectrum.ieee.org/artificial-intelligence"},
    {"name": "acm_queue", "priority": 4, "enabled": True, "url": "https://queue.acm.org"},
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
        with urllib.request.urlopen(req, timeout=15) as response:
            result["response_time"] = time.time() - start
            if response.status == 200:
                result["status"] = "✅ 可用"
            else:
                result["status"] = f"⚠️ HTTP {response.status}"
    except urllib.error.HTTPError as e:
        result["response_time"] = time.time() - start
        if e.code in [301, 302, 307, 308]:
            result["status"] = "⚠️ 重定向"
        elif e.code == 403:
            result["status"] = "⚠️ 限制访问"
        elif e.code == 429:
            result["status"] = "⚠️ 速率限制"
        else:
            result["status"] = f"❌ HTTP {e.code}"
        result["error"] = str(e.code)
    except urllib.error.URLError as e:
        result["response_time"] = time.time() - start
        result["status"] = "❌ 连接失败"
        result["error"] = str(e.reason)[:30]
    except TimeoutError:
        result["response_time"] = 15
        result["status"] = "❌ 超时"
        result["error"] = "Timeout"
    except Exception as e:
        result["response_time"] = time.time() - start
        result["status"] = "❌ 错误"
        result["error"] = str(e)[:30]
    
    return result

def main():
    print("="*75)
    print(" 🔥 30源并发验证测试 - 无需API版本")
    print("="*75)
    print(f"\n测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试源数: {len(SOURCES)}")
    print(f"并发数: 30 (ThreadPoolExecutor)")
    print("\n开始并发测试...\n")
    
    start_time = time.time()
    results = []
    
    # 并发测试 - 30线程
    with ThreadPoolExecutor(max_workers=30) as executor:
        future_to_source = {executor.submit(test_source, s): s for s in SOURCES}
        
        for future in as_completed(future_to_source):
            result = future.result()
            results.append(result)
            print(f"✓ {result['name']:<25} {result['status']:<12} ({result['response_time']:.2f}s)")
    
    elapsed = time.time() - start_time
    
    # 统计
    stats = {}
    for r in results:
        status_key = r["status"].split()[0]
        stats[status_key] = stats.get(status_key, 0) + 1
    
    # 按优先级分组显示
    print("\n" + "="*75)
    print(" 详细结果 (按优先级)")
    print("="*75)
    
    current_priority = None
    for r in sorted(results, key=lambda x: x["priority"], reverse=True):
        if r["priority"] != current_priority:
            current_priority = r["priority"]
            print(f"\n─ P{10-current_priority}级 (优先级 {current_priority}/10) ─")
        print(f" {r['status']:<12} {r['name']:<25} {r['response_time']:.2f}s")
    
    # 统计汇总
    print("\n" + "="*75)
    print(" 📊 并发测试统计")
    print("="*75)
    total = len(results)
    available = stats.get("✅", 0)
    warning = stats.get("⚠️", 0)
    error = stats.get("❌", 0)
    
    print(f"\n 总计测试: {total} 个源")
    print(f" 并发时间: {elapsed:.2f} 秒")
    print(f" 平均响应: {sum(r['response_time'] for r in results)/total:.2f} 秒")
    print(f"")
    print(f" ✅ 可用: {available} ({available/total*100:.1f}%)")
    print(f" ⚠️  警告: {warning} ({warning/total*100:.1f}%)")
    print(f" ❌ 错误: {error} ({error/total*100:.1f}%)")
    
    # 按优先级统计
    print("\n 按优先级分布:")
    for p in [10, 9, 8, 7, 6, 5, 4]:
        p_results = [r for r in results if r["priority"] == p]
        if p_results:
            p_available = sum(1 for r in p_results if "✅" in r["status"])
            print(f"   P{10-p}级 (优先级{p}): {p_available}/{len(p_results)} 可用")
    
    print("\n" + "="*75)
    if available >= 20:
        print(f" 🎉 并发验证通过: {available}/{total} 源可用，满足使用要求")
    elif available >= 15:
        print(f" ⚠️  部分可用: {available}/{total} 源可用，建议筛选优化")
    else:
        print(f" ❌ 验证失败: {available}/{total} 源可用，需要修复")
    print("="*75)
    
    # 列出不可用的源
    failed_sources = [r for r in results if "❌" in r["status"]]
    warning_sources = [r for r in results if "⚠️" in r["status"]]
    
    if warning_sources:
        print("\n⚠️  警告的源 (可能需要关注):")
        for r in warning_sources:
            print(f"  - {r['name']}: {r['status']}")
    
    if failed_sources:
        print("\n❌ 不可用的源 (建议禁用):")
        for r in failed_sources:
            print(f"  - {r['name']}: {r['status']} ({r.get('error', 'N/A')})")
    
    return results

if __name__ == "__main__":
    main()
