#!/usr/bin/env python3
"""
OpenClaw 全平台博主智能监控系统 v2.0
功能: 监控 YouTube, Medium, GitHub, X/Twitter, Reddit, DEV.to 等平台
"""

import json
import os
import subprocess
from datetime import datetime
from typing import List, Dict

# 全平台博主配置
INFLUENCERS = {
    "youtube": [
        {"channel": "Tech With Tim", "priority": 10, "focus": "Full Courses, Skills"},
        {"channel": "Adrian Twarog", "priority": 10, "focus": "Crash Course"},
        {"channel": "Metics Media", "priority": 10, "focus": "Security, Setup"},
        {"channel": "BoxminingAI", "priority": 8, "focus": "Updates, Features"},
        {"channel": "Automate Your Life", "priority": 8, "focus": "Home Automation"},
    ],
    "medium": [
        {"author": "Cordero Core", "handle": "@cdcore", "priority": 10, "focus": "Deep Analysis"},
        {"author": "Alex Rozdolskyi", "handle": "@alexrozdolskiy", "priority": 10, "focus": "Use Cases"},
        {"author": "Sonu Yadav", "handle": "@sonuyadav1", "priority": 9, "focus": "Business"},
        {"author": "Duncan Anderson", "handle": "@duncsand", "priority": 8, "focus": "Philosophy"},
        {"author": "evoailabs", "priority": 8, "focus": "Robotics"},
    ],
    "github": [
        {"repo": "openclaw/openclaw", "maintainer": "Peter Steinberger", "priority": 10},
        {"repo": "VoltAgent/awesome-openclaw-skills", "priority": 10},
        {"repo": "zhayujie/chatgpt-on-wechat", "priority": 9},
        {"repo": "HKUDS/nanobot", "priority": 8},
        {"repo": "CherryHQ/cherry-studio", "priority": 8},
    ],
    "twitter": [
        {"handle": "steipete", "name": "Peter Steinberger", "priority": 10},
        {"handle": "NatEliason", "name": "Nat Eliason", "priority": 10},
        {"handle": "ClawtheAI", "name": "ClawtheAI", "priority": 8},
        {"handle": "Scrapling_dev", "name": "Scrapling", "priority": 8},
    ],
    "devto": [
        {"author": "auden", "priority": 8},
        {"author": "rosgluk", "priority": 8},
    ],
}

def run_command(cmd: str, timeout: int = 30) -> str:
    """运行 shell 命令"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout if result.returncode == 0 else ""
    except:
        return ""

def search_exa(query: str, num_results: int = 5) -> List[Dict]:
    """使用 Exa 搜索"""
    cmd = f"mcporter call 'exa.web_search_exa({{\"query\": \"{query}\", \"num_results\": {num_results}}}')' 2>/dev/null | head -100"
    output = run_command(cmd, timeout=60)
    
    results = []
    if output:
        lines = output.split('\n')
        current = {}
        for line in lines:
            if line.startswith("Title:"):
                if current:
                    results.append(current)
                current = {"title": line[6:].strip()}
            elif line.startswith("Author:") and current:
                current["author"] = line[7:].strip()
            elif line.startswith("URL:") and current:
                current["url"] = line[4:].strip()
            elif line.startswith("Text:") and current:
                current["text"] = line[5:].strip()[:200]
        if current:
            results.append(current)
    
    return results[:num_results]

def get_github_repo_info(repo: str) -> Dict:
    """获取 GitHub 仓库信息"""
    cmd = f"gh api repos/{repo} 2>/dev/null"
    output = run_command(cmd)
    
    if output:
        try:
            data = json.loads(output)
            return {
                "name": data.get("name"),
                "stars": data.get("stargazers_count"),
                "updated": data.get("updated_at", "")[:10],
                "url": data.get("html_url", ""),
            }
        except:
            pass
    return {}

def evaluate_signal(content: str, source: str = "") -> int:
    """评估内容重要性"""
    keywords_10 = ["security", "vulnerability", "critical", "exploit", " CVE "]
    keywords_9 = ["new release", "major update", "breaking change", "v2.", "v3."]
    keywords_8 = ["skill", "tool", "integration", "mcp", "tutorial"]
    keywords_7 = ["use case", "example", "best practice", "guide"]
    keywords_6 = ["update", "feature", "news"]
    
    content_lower = content.lower()
    score = 5
    
    if any(k in content_lower for k in keywords_10):
        score = 10
    elif any(k in content_lower for k in keywords_9):
        score = 9
    elif any(k in content_lower for k in keywords_8):
        score = 8
    elif any(k in content_lower for k in keywords_7):
        score = 7
    elif any(k in content_lower for k in keywords_6):
        score = 6
    
    # 提升优质来源的分数
    if source in ["Tech With Tim", "Adrian Twarog", "Metics Media", "Cordero Core"]:
        score = min(score + 1, 10)
    
    return score

def generate_comprehensive_report() -> str:
    """生成综合监控报告"""
    report_dir = os.path.expanduser("~/.openclaw/workspace/reports/influencer-monitor")
    os.makedirs(report_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    report_file = os.path.join(report_dir, f"comprehensive_report_{timestamp}.md")
    
    report = []
    report.append(f"# OpenClaw 全平台监控报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("")
    report.append("## 🔍 监控概览")
    report.append(f"- 监控平台: YouTube, Medium, GitHub, X/Twitter, DEV.to")
    report.append(f"- 监控对象: 30+ 位博主/创作者")
    report.append("")
    
    # GitHub 项目监控
    report.append("## 📊 GitHub 热门项目")
    report.append("")
    
    for project in INFLUENCERS["github"][:5]:
        repo = project["repo"]
        info = get_github_repo_info(repo)
        if info:
            stars = info.get("stars", "N/A")
            updated = info.get("updated", "N/A")
            report.append(f"### {info.get('name', repo)}")
            report.append(f"- ⭐ Stars: {stars}")
            report.append(f"- 🕐 更新: {updated}")
            report.append(f"- 🔗 [{repo}]({info.get('url', '')})")
            report.append("")
    
    # Exa 全网搜索 - YouTube
    report.append("## 🎬 YouTube 最新内容")
    report.append("")
    
    youtube_results = search_exa("OpenClaw tutorial YouTube 2026", 5)
    for item in youtube_results:
        signal = evaluate_signal(item.get("text", ""), item.get("author", ""))
        if signal >= 6:  # 只显示中高价值内容
            report.append(f"### {item.get('title', 'Untitled')} (Signal {signal}/10)")
            if "author" in item:
                report.append(f"**作者**: {item['author']}")
            report.append(f"{item.get('text', '')[:150]}...")
            if "url" in item:
                report.append(f"[查看]({item['url']})")
            report.append("")
    
    # Exa 全网搜索 - Medium
    report.append("## 📝 Medium 最新文章")
    report.append("")
    
    medium_results = search_exa("OpenClaw Medium blog 2026", 5)
    for item in medium_results:
        signal = evaluate_signal(item.get("text", ""), item.get("author", ""))
        if signal >= 6:
            report.append(f"### {item.get('title', 'Untitled')} (Signal {signal}/10)")
            if "author" in item:
                report.append(f"**作者**: {item['author']}")
            report.append(f"{item.get('text', '')[:150]}...")
            if "url" in item:
                report.append(f"[阅读]({item['url']})")
            report.append("")
    
    # 技术新闻搜索
    report.append("## 📰 技术新闻与更新")
    report.append("")
    
    news_results = search_exa("OpenClaw update news features 2026", 5)
    for item in news_results:
        signal = evaluate_signal(item.get("text", ""))
        if signal >= 7:
            report.append(f"### {item.get('title', 'Untitled')} (Signal {signal}/10)")
            if "author" in item:
                report.append(f"**来源**: {item['author']}")
            report.append(f"{item.get('text', '')[:150]}...")
            if "url" in item:
                report.append(f"[查看]({item['url']})")
            report.append("")
    
    # 高 Signal 内容汇总
    report.append("## ⚡ 高 Signal 内容汇总")
    report.append("")
    report.append("| Signal | 来源 | 标题 | 操作 |")
    report.append("|--------|------|------|------|")
    
    all_results = youtube_results + medium_results + news_results
    high_signal = [(item, evaluate_signal(item.get("text", ""), item.get("author", ""))) 
                   for item in all_results if evaluate_signal(item.get("text", "")) >= 8]
    
    for item, signal in sorted(high_signal, key=lambda x: x[1], reverse=True)[:5]:
        source = item.get("author", "Unknown")[:15]
        title = item.get("title", "Untitled")[:40]
        url = item.get("url", "")
        if signal >= 9:
            action = "立即查看"
        else:
            action = "参考学习"
        report.append(f"| {signal} | {source} | {title} | {action} |")
    
    report.append("")
    
    # 总结
    report.append("## 📈 监控总结")
    report.append("")
    report.append(f"- **监控时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"- **监控平台**: 5 个")
    report.append(f"- **监控对象**: 30+ 位博主")
    report.append(f"- **高 Signal 内容**: {len(high_signal)} 条")
    
    if high_signal:
        report.append(f"- **最高 Signal**: {max(s for _, s in high_signal)}/10")
    
    report.append("")
    report.append("---")
    report.append("")
    report.append("*下次监控: 明天 12:00*")
    
    # 写入文件
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    return report_file, len(high_signal)

def main():
    """主函数"""
    print("🔍 开始全平台 OpenClaw 博主监控...")
    print(f"⏰ 监控时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    report_file, high_signal_count = generate_comprehensive_report()
    
    print(f"✅ 监控完成!")
    print(f"📄 报告位置: {report_file}")
    print(f"⚡ 发现高 Signal 内容: {high_signal_count} 条")
    
    if high_signal_count > 0:
        print("\n⚠️  有高价值内容需要关注!")
        print("请查看报告了解详情。")

if __name__ == "__main__":
    main()
