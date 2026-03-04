#!/usr/bin/env python3
"""
OpenClaw 博主智能监控系统
功能: 自动监控核心博主，筛选高价值内容
"""

import json
import os
import subprocess
from datetime import datetime
from typing import List, Dict, Optional

# 监控配置
INFLUENCERS = {
    "core": [
        {"name": "Peter Steinberger", "handle": "steipete", "platform": "X", "priority": 10},
        {"name": "Nat Eliason", "handle": "NatEliason", "platform": "X", "priority": 10},
    ],
    "community": [
        {"name": "ClawtheAI", "handle": "ClawtheAI", "platform": "X", "priority": 8},
        {"name": "Samanyou Garg", "handle": "samanyougarg", "platform": "LinkedIn", "priority": 7},
    ],
    "projects": [
        {"name": "awesome-openclaw-skills", "repo": "VoltAgent/awesome-openclaw-skills", "priority": 9},
        {"name": "chatgpt-on-wechat", "repo": "zhayujie/chatgpt-on-wechat", "priority": 8},
    ]
}

def run_command(cmd: str) -> str:
    """运行 shell 命令"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout if result.returncode == 0 else ""
    except:
        return ""

def search_x_tweets(handle: str) -> List[Dict]:
    """搜索 X/Twitter 推文"""
    cmd = f"xreach search 'from:{handle}' --json 2>/dev/null"
    output = run_command(cmd)
    
    tweets = []
    if output:
        for line in output.split('\n')[:5]:  # 最近5条
            if line.strip():
                tweets.append({
                    "content": line[:200],
                    "url": f"https://x.com/{handle}"
                })
    return tweets

def search_github_repo(repo: str) -> Dict:
    """获取 GitHub 仓库信息"""
    cmd = f"gh api repos/{repo} 2>/dev/null"
    output = run_command(cmd)
    
    if output:
        try:
            data = json.loads(output)
            return {
                "name": data.get("name"),
                "stars": data.get("stargazers_count"),
                "updated": data.get("updated_at"),
                "url": data.get("html_url")
            }
        except:
            pass
    return {}

def search_exa_content(query: str) -> List[Dict]:
    """使用 Exa 搜索新内容"""
    cmd = f"mcporter call 'exa.web_search_exa({{\"query\": \"{query}\", \"num_results\": 5}})' 2>/dev/null | head -50"
    output = run_command(cmd)
    
    results = []
    if output and "Title:" in output:
        # 简单解析
        lines = output.split('\n')
        current = {}
        for line in lines:
            if line.startswith("Title:"):
                if current:
                    results.append(current)
                current = {"title": line[6:].strip()}
            elif line.startswith("URL:") and current:
                current["url"] = line[4:].strip()
            elif line.startswith("Text:") and current:
                current["text"] = line[5:].strip()[:200]
        if current:
            results.append(current)
    
    return results[:3]  # 返回前3条

def evaluate_signal(content: str) -> int:
    """评估内容重要性 (1-10)"""
    keywords = {
        10: ["security", "vulnerability", "critical", "exploit"],
        9: ["new release", "major update", "breaking change"],
        8: ["skill", "tool", "integration", "mcp"],
        7: ["tutorial", "guide", "best practice"],
        6: ["use case", "example", "showcase"]
    }
    
    content_lower = content.lower()
    score = 5  # 基础分
    
    for points, words in keywords.items():
        if any(word in content_lower for word in words):
            score = max(score, points)
    
    return min(score, 10)

def generate_report() -> str:
    """生成监控报告"""
    report_dir = os.path.expanduser("~/.openclaw/workspace/reports/influencer-monitor")
    os.makedirs(report_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    report_file = os.path.join(report_dir, f"report_{timestamp}.md")
    
    report = []
    report.append(f"# OpenClaw 博主监控报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("")
    report.append("## 🌟 核心人物动态")
    report.append("")
    
    # 监控核心人物
    for person in INFLUENCERS["core"]:
        report.append(f"### {person['name']} (@{person['handle']})")
        report.append("")
        
        if person["platform"] == "X":
            tweets = search_x_tweets(person["handle"])
            if tweets:
                for tweet in tweets[:3]:
                    signal = evaluate_signal(tweet["content"])
                    report.append(f"- Signal {signal}/10: {tweet['content'][:150]}...")
                    report.append(f"  [查看]({tweet['url']})")
                    report.append("")
            else:
                report.append("- 暂无新内容")
                report.append("")
    
    # 监控项目
    report.append("## 📊 热门项目更新")
    report.append("")
    
    for project in INFLUENCERS["projects"]:
        repo_info = search_github_repo(project["repo"])
        if repo_info:
            report.append(f"### {repo_info.get('name', project['name'])}")
            report.append(f"- ⭐ Stars: {repo_info.get('stars', 'N/A')}")
            report.append(f"- 🕐 最后更新: {repo_info.get('updated', 'N/A')}")
            report.append(f"- 🔗 [查看仓库]({repo_info.get('url', '')})")
            report.append("")
    
    # Exa 全网搜索
    report.append("## 🔍 全网新内容")
    report.append("")
    
    exa_results = search_exa_content("OpenClaw AI agent best practices")
    if exa_results:
        for item in exa_results:
            signal = evaluate_signal(item.get("text", ""))
            report.append(f"### {item.get('title', 'Untitled')} (Signal {signal}/10)")
            report.append(f"{item.get('text', '')[:200]}...")
            if "url" in item:
                report.append(f"[查看原文]({item['url']})")
            report.append("")
    else:
        report.append("- 暂无新内容")
        report.append("")
    
    # 摘要
    report.append("## 📈 监控摘要")
    report.append("")
    report.append(f"- 监控时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"- 监控人物: {len(INFLUENCERS['core']) + len(INFLUENCERS['community'])} 位")
    report.append(f"- 监控项目: {len(INFLUENCERS['projects'])} 个")
    report.append("")
    
    # 写入文件
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    return report_file

def main():
    """主函数"""
    print("🔍 开始监控 OpenClaw 博主...")
    
    report_file = generate_report()
    
    print(f"✅ 监控完成: {report_file}")
    
    # 显示报告摘要
    with open(report_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if "Signal 9" in content or "Signal 10" in content:
            print("⚠️  发现高 Signal 内容！请查看报告。")

if __name__ == "__main__":
    main()
